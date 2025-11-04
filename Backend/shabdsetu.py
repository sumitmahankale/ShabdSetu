"""
ShabdSetu – Stable Bidirectional (Marathi ↔ English) Speech Translator
=====================================================================

Core pipeline (loop until Ctrl+C):
  1. speech_to_text()  -> Whisper (faster-whisper) streaming style capture with silence end
  2. detect_language() -> Rule based (Devanagari vs Latin) + optional romanized heuristic
  3. translate_text()  -> IndicTrans2 (ai4bharat) directional models with fallback
  4. text_to_speech()  -> gTTS (primary) / pyttsx3 fallback (English) / simple WAV tone fallback

Design Goals / Fixes:
  * Deterministic language detection (no random model vagueness):
        - If any Devanagari (\u0900-\u097F) => 'mr'
        - Else if any Latin a-z => 'en'
        - Else default 'en'
  * Always map source->target (mr→en or en→mr) – never identity translation.
  * Robust error isolation: each stage wrapped; failures logged and skipped gracefully.
  * Lazy loading heavy models (Whisper + IndicTrans2) to reduce startup latency.
  * Clear logging for every iteration (input text, detected language, translation, timings, branch, errors).
  * Minimal external dependencies at runtime; graceful degradation if a lib missing.

Installation (recommended):
  pip install faster-whisper sounddevice numpy torch transformers sentencepiece gTTS pyttsx3 playsound pydub

If GPU available set USE_CUDA=1 else it auto uses CPU (int8 compute for Whisper).

Environment Variables (optional):
  WHISPER_MODEL      – tiny / base / small / medium (default: base)
  USE_CUDA           – 1 to use CUDA if available (default: 1)
  MAX_RECORD_SEC     – max seconds per utterance (default: 15)

Keyboard Use:
  Program auto-records when energy exceeds threshold; silence ends segment.
  Press Ctrl+C to exit cleanly.

NOTE: For real deployment consider replacing naive energy VAD with a robust VAD (e.g. silero-vad).
"""
from __future__ import annotations
import os
import sys
import io
import time
import queue
import math
import traceback
import threading
import tempfile
import contextlib
from dataclasses import dataclass
from typing import Optional, Tuple

# Soft imports – everything optional & checked
MISSING = []
try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore
    MISSING.append('numpy')
try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None  # type: ignore
    MISSING.append('sounddevice')
try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover
    WhisperModel = None  # type: ignore
    MISSING.append('faster-whisper')
try:
    import torch
except ImportError:  # pragma: no cover
    torch = None  # type: ignore
    MISSING.append('torch')
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
except ImportError:  # pragma: no cover
    AutoTokenizer = AutoModelForSeq2SeqLM = None  # type: ignore
    MISSING.append('transformers')
try:
    from gtts import gTTS
except ImportError:  # pragma: no cover
    gTTS = None  # type: ignore
    MISSING.append('gTTS')
try:
    import pyttsx3
    _HAS_PYTTSX3 = True
except Exception:  # pragma: no cover
    pyttsx3 = None  # type: ignore
    _HAS_PYTTSX3 = False
try:
    from playsound import playsound
    _HAS_PLAYSOUND = True
except Exception:  # pragma: no cover
    playsound = None  # type: ignore
    _HAS_PLAYSOUND = False
try:
    from pydub import AudioSegment
    from pydub.playback import play as pydub_play
    _HAS_PYDUB = True
except Exception:  # pragma: no cover
    AudioSegment = None  # type: ignore
    pydub_play = None  # type: ignore
    _HAS_PYDUB = False

# ----------------- Configuration -----------------
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL', 'base')
USE_CUDA = os.getenv('USE_CUDA', '1') == '1'
DEVICE = 'cuda' if USE_CUDA and torch and torch.cuda.is_available() else 'cpu'
WHISPER_COMPUTE_TYPE = 'float16' if DEVICE == 'cuda' else 'int8'
SAMPLE_RATE = 16000
CHANNELS = 1
FRAME_DUR = 0.05  # 50 ms frames
MAX_RECORD_SEC = int(os.getenv('MAX_RECORD_SEC', '15'))
ENERGY_SILENCE_SEC = 0.7
ENERGY_THRESHOLD = 0.015  # simple RMS threshold
EN2MR_MODEL = 'ai4bharat/indictrans2-en-mr'
MR2EN_MODEL = 'ai4bharat/indictrans2-mr-en'

ROMAN_CLUES = { 'namaskar','majha','majhe','maza','nav','tumhi','kase','kasa','madat','pani','aaj','udya','kal','ratri','sakal','dhanyavad','dhanyawad'}
DEV_RANGE = ('\u0900','\u097F')

# Thread-safe print
_print_lock = threading.Lock()

def log(msg: str):
    with _print_lock:
        ts = time.strftime('%H:%M:%S')
        print(f"[{ts}] {msg}", flush=True)

# ----------------- Language Detection -----------------

def detect_language(text: str) -> str:
    """Deterministic rule-based language detection.
    Order:
      1. Any Devanagari => mr
      2. Else any Latin letter => en (optionally treat as mr if >=2 roman clues)
    """
    t = text.strip()
    if not t:
        return 'en'
    for ch in t:
        if '\u0900' <= ch <= '\u097F':
            return 'mr'
    latin = any('a' <= c.lower() <= 'z' for c in t)
    if latin:
        words = [w.strip('.,!?;:').lower() for w in t.split()]
        hits = sum(1 for w in words if w in ROMAN_CLUES)
        if hits >= 2:
            return 'mr'
        return 'en'
    return 'en'

# ----------------- Translators -----------------
class IndicTranslator:
    def __init__(self):
        self._lock = threading.Lock()
        self._en2mr = None
        self._mr2en = None

    def _load(self, direction: str):
        if not AutoTokenizer or not AutoModelForSeq2SeqLM:
            raise RuntimeError('transformers not installed. Install transformers & sentencepiece.')
        with self._lock:
            if direction == 'en-mr' and self._en2mr:
                return self._en2mr
            if direction == 'mr-en' and self._mr2en:
                return self._mr2en
            model_name = EN2MR_MODEL if direction == 'en-mr' else MR2EN_MODEL
            log(f'Loading translation model: {model_name}')
            tok = AutoTokenizer.from_pretrained(model_name)
            mdl = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            if torch:
                mdl.to(DEVICE)
            pair = (tok, mdl)
            if direction == 'en-mr':
                self._en2mr = pair
            else:
                self._mr2en = pair
            return pair

    def translate(self, text: str, src: str, tgt: str) -> str:
        direction = f'{src}-{tgt}'
        if direction not in ('en-mr','mr-en'):
            raise ValueError('Unsupported direction')
        try:
            tok, mdl = self._load(direction)
            batch = tok([text], return_tensors='pt', padding=True)
            if torch:
                batch = {k: v.to(DEVICE) for k,v in batch.items()}
            with torch.inference_mode():
                out_ids = mdl.generate(**batch, max_new_tokens=256)
            out = tok.batch_decode(out_ids, skip_special_tokens=True)[0].strip()
            return out
        except Exception as e:
            log(f'[WARN] Translation model failed ({direction}): {e}')
            return heuristic_fallback(text, src, tgt)

# Simple fallback dictionary heuristic
DICT_EN_MR = {
    'hello':'नमस्कार', 'good morning':'सुप्रभात', 'good night':'शुभ रात्री', 'thank you':'धन्यवाद', 'thanks':'धन्यवाद',
    'please':'कृपया','yes':'होय','no':'नाही','water':'पाणी','food':'अन्न','help':'मदत','my name is':'माझे नाव'
}
DICT_MR_EN = {v:k for k,v in DICT_EN_MR.items()}

def heuristic_fallback(text: str, src: str, tgt: str) -> str:
    t = text.lower().strip()
    if src == 'en' and tgt == 'mr':
        return DICT_EN_MR.get(t, t)  # pass-through if unknown
    if src == 'mr' and tgt == 'en':
        return DICT_MR_EN.get(text.strip(), text)
    return text

# ----------------- Whisper STT -----------------
class WhisperSTT:
    def __init__(self):
        if not WhisperModel:
            raise RuntimeError('faster-whisper not installed.')
        log(f'Loading Whisper model: {WHISPER_MODEL_SIZE} ({DEVICE}/{WHISPER_COMPUTE_TYPE})')
        self.model = WhisperModel(WHISPER_MODEL_SIZE, device=DEVICE, compute_type=WHISPER_COMPUTE_TYPE)

    def transcribe(self, audio_np) -> str:
        try:
            segments, _ = self.model.transcribe(audio_np, language=None, beam_size=1, vad_filter=True)
            text_parts = [seg.text.strip() for seg in segments if seg.text.strip()]
            return ' '.join(text_parts).strip()
        except Exception as e:
            log(f'[ERROR] Whisper transcription failed: {e}')
            return ''

# ----------------- Audio Capture -----------------
class AudioRecorder:
    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS):
        if not sd or not np:
            raise RuntimeError('sounddevice and numpy required for recording.')
        self.sr = sample_rate
        self.channels = channels
        # store captured audio frames (numpy arrays when numpy is available)
        self.frames = []
        self._recording = False
        self._queue = queue.Queue()

    def _callback(self, indata, frames, time_info, status):  # pragma: no cover (I/O)
        if status:
            log(f'[AUDIO] Status: {status}')
        self._queue.put(indata.copy())

    def record_until_silence(self, max_seconds=MAX_RECORD_SEC) -> Optional[object]:
        self.frames.clear()
        self._recording = True
        silence_frames = 0
        needed_silence = int(ENERGY_SILENCE_SEC / FRAME_DUR)
        max_frames = int(max_seconds / FRAME_DUR)
        frame_len = int(self.sr * FRAME_DUR)
        log('Listening... (start speaking)')
        with sd.InputStream(samplerate=self.sr, channels=self.channels, blocksize=frame_len, callback=self._callback):
            while self._recording:
                try:
                    frame = self._queue.get(timeout=2)
                except queue.Empty:
                    log('[WARN] Audio timeout')
                    break
                self.frames.append(frame)
                # Energy (RMS)
                rms = float(np.sqrt(np.mean(frame**2)))
                if rms < ENERGY_THRESHOLD:
                    silence_frames += 1
                else:
                    silence_frames = 0
                if silence_frames >= needed_silence and len(self.frames) > 4:
                    log('Silence detected – ending utterance.')
                    break
                if len(self.frames) >= max_frames:
                    log('Max duration reached.')
                    break
        if not self.frames:
            return None
        audio = np.concatenate(self.frames, axis=0).squeeze()
        # Resample if needed (Whisper expects 16k); we assume device delivered sr
        return audio.astype('float32')

# ----------------- TTS -----------------
class SpeechSynthesizer:
    def __init__(self):
        self.engine = None
        if _HAS_PYTTSX3:
            try:
                self.engine = pyttsx3.init()
            except Exception:
                self.engine = None

    def speak(self, text: str, lang: str):  # pragma: no cover (I/O)
        lang = lang.lower()
        # Prefer gTTS for both languages (Marathi needs external) – offline fallback to pyttsx3 for English only
        if gTTS:
            try:
                tts = gTTS(text=text, lang='mr' if lang=='mr' else 'en', slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    tmp = f.name
                    tts.write_to_fp(f)
                # playback
                if _HAS_PLAYSOUND:
                    playsound(tmp)
                elif _HAS_PYDUB:
                    seg = AudioSegment.from_file(tmp)
                    pydub_play(seg)
                else:
                    log('[WARN] No playback lib (playsound/pydub) – skipping audio.')
                try: os.remove(tmp)
                except Exception: pass
                return
            except Exception as e:
                log(f'[WARN] gTTS failed: {e}')
        # Fallback: pyttsx3 only for English (Marathi voices rare)
        if self.engine and lang == 'en':
            try:
                self.engine.say(text)
                self.engine.runAndWait()
                return
            except Exception as e:
                log(f'[WARN] pyttsx3 failed: {e}')
        log('[INFO] (TTS skipped)')

# ----------------- Pipeline Functions -----------------
_translator_instance: Optional[IndicTranslator] = None
_stt_instance: Optional[WhisperSTT] = None
_tts_instance: Optional[SpeechSynthesizer] = None


def get_translator() -> IndicTranslator:
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = IndicTranslator()
    return _translator_instance

def get_stt() -> WhisperSTT:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = WhisperSTT()
    return _stt_instance

def get_tts() -> SpeechSynthesizer:
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = SpeechSynthesizer()
    return _tts_instance

# Public API functions (as requested)

def speech_to_text() -> str:
    try:
        recorder = AudioRecorder()
        audio = recorder.record_until_silence()
        if audio is None:
            log('[INFO] No audio captured.')
            return ''
        stt = get_stt()
        text = stt.transcribe(audio)
        log(f'[STT] Raw text: {text}')
        return text
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log(f'[ERROR] speech_to_text failed: {e}')
        return ''

def translate_text(text: str, src: str, tgt: str) -> str:
    try:
        tr = get_translator()
        translated = tr.translate(text, src, tgt)
        log(f'[TRANSLATE] {src}->{tgt}: {translated}')
        return translated
    except Exception as e:
        log(f'[ERROR] translate_text failed: {e}')
        return text

def text_to_speech(text: str, lang: str):
    try:
        tts = get_tts()
        tts.speak(text, lang)
    except Exception as e:
        log(f'[ERROR] text_to_speech failed: {e}')

# ----------------- Main Loop -----------------

def main_loop():  # pragma: no cover (interactive)
    if MISSING:
        log(f'[WARN] Missing optional packages: {", ".join(MISSING)}')
    log(f'Device: {DEVICE}')
    log('Starting ShabdSetu loop (Ctrl+C to exit).')
    iteration = 0
    while True:
        iteration += 1
        log('='*40 + f' Iteration {iteration} ' + '='*40)
        try:
            text = speech_to_text()
            if not text:
                log('[INFO] Empty transcription, retrying...')
                continue
            src = detect_language(text)
            tgt = 'en' if src == 'mr' else 'mr'
            log(f'[DETECT] Source language: {src} -> Target: {tgt}')
            translated = translate_text(text, src, tgt)
            if not translated.strip():
                log('[WARN] Empty translation – skipping TTS.')
                continue
            text_to_speech(translated, tgt)
            time.sleep(0.5)
        except KeyboardInterrupt:
            log('Exiting on user interrupt.')
            break
        except Exception as e:
            log(f'[LOOP ERROR] {e}')
            traceback.print_exc()
            time.sleep(0.5)

# ----------------- Entrypoint -----------------
if __name__ == '__main__':  # pragma: no cover
    main_loop()
