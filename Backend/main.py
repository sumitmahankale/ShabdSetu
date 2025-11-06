from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import requests
import re
import time
import urllib.parse
import os
from functools import lru_cache
from health_literacy import get_health_tutor, HealthLiteracyTutor

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

try:
    # Light-weight extra engine
    from deep_translator import GoogleTranslator as DeepGoogleTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShabdSetu - Lang-chain Powered Interactive Literacy Tutor",
    description="Bidirectional translation and health information system for low-literate populations",
    version="4.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3002", "http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Content-Type"],
)

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "auto"  # auto-detect by default
    target_language: str = "auto"  # auto-determine target

class HealthQueryRequest(BaseModel):
    query: str
    language: str = "en"  # 'en' or 'mr'

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    translation_method: str

class BilingualTranslationService:
    """Lean translation service focused on reliable English↔Marathi output.
    Strategy:
      1. Detect language (script + simple heuristics).
      2. Exact phrase dictionary.
      3. External APIs in order: Google (unofficial) → MyMemory → LibreTranslate → Lingva.
      4. For English→Marathi require Devanagari; otherwise try next API.
      5. Cache successful translations in-memory.
    Removed brittle/blocked services (Microsoft, Bing, Yandex, Apertium, deep_translator, googletrans)
    to prevent silent failures and speed up responses.
    """
    DEVANAGARI_RE = re.compile(r'[\u0900-\u097F]')

    def __init__(self):
        self.cache = {}
        self.api_call_count = 0
        self.last_api_call_time = 0
        # Precompile regexes / maps
        self._roman_common_map = self._build_roman_map()

    # ---------------- Language Detection -----------------
    def detect_language(self, text: str) -> str:
        if self.DEVANAGARI_RE.search(text):
            return 'mr'
        # Simple romanized Marathi clue set
        roman_mr_clues = {'namaskar','dhanyawad','dhanyabad','kasa','kase','kuthe','kiti','pani','anna','madad','hoye','nahi','aaj','udya','kal','sakal','sandhya','ratri','jevan','kaam','mitra','maaf','krupa','tumhi','majhe','maza'}
        words = re.findall(r'[a-zA-Z]+', text.lower())
        if words and sum(1 for w in words if w in roman_mr_clues) >= max(1, len(words)//3):
            return 'mr'
        return 'en'

    def advanced_language_detection(self, text: str) -> str:
        if self.DEVANAGARI_RE.search(text):
            return 'mr'
        if LANGDETECT_AVAILABLE:
            try:
                d = detect(text)
                if d == 'mr':
                    return 'mr'
                if d == 'en':
                    return 'en'
            except Exception:
                pass
        return self.detect_language(text)

    # ---------------- Dictionary -----------------
    EN_TO_MR = {
    'hello':'नमस्कार','how are you':'तुम्ही कसे आहात','good morning':'सुप्रभात',
        'good night':'शुभ रात्री','thank you':'धन्यवाद','thanks':'धन्यवाद','please':'कृपया',
        'yes':'होय','no':'नाही','sorry':'माफ करा','what is your name':'तुमचे नाव काय आहे',
        'my name is':'माझे नाव','i am fine':'मी ठीक आहे','good evening':'शुभ संध्या',
        'good afternoon':'शुभ दुपार','water':'पाणी','food':'अन्न','help':'मदत',
        'where is the bathroom':'स्नानगृह कुठे आहे','how much':'किती','today':'आज',
        'tomorrow':'उद्या','yesterday':'काल','computer':'संगणक','software':'सॉफ्टवेअर',
        'i love you':'मी तुझ्यावर प्रेम करतो','i love programming':'मला प्रोग्रामिंग आवडते',
        'good afternoon':'शुभ दुपार','good day':'सुखद दिवस','good to see you':'तुम्हाला भेटून आनंद झाला'
    }
    MR_TO_EN = {v:k for k,v in EN_TO_MR.items()}

    def dictionary_translate(self, text: str, src: str, tgt: str):
        key = text.lower().strip()
        # Normalize multiple spaces
        key = re.sub(r'\s+', ' ', key)
        if src=='en' and tgt=='mr':
            return self.EN_TO_MR.get(key)
        if src=='mr' and tgt=='en':
            # Try exact Devanagari
            if text.strip() in self.MR_TO_EN:
                return self.MR_TO_EN[text.strip()]
            # Try normalized (remove punctuation)
            stripped = re.sub(r'[!?।,.]+','', text.strip())
            return self.MR_TO_EN.get(stripped)
        return None

    # ---------------- Romanized support -----------------
    def _build_roman_map(self):
        # Minimal transliteration map (phrase-first sorted by length)
        base = {
            'namaskar':'नमस्कार','dhanyawad':'धन्यवाद','dhanyabad':'धन्यवाद','kasa ahat':'कसे आहात',
            'kase ahat':'कसे आहात','pani':'पाणी','anna':'अन्न','madad':'मदत','kaam':'काम',
            'tumhi':'तुम्ही','majhe':'माझे','maza':'माझे','aaj':'आज','udya':'उद्या','kal':'काल',
            'jevan':'जेवण','mitra':'मित्र','sakal':'सकाळ','ratri':'रात्र','sandhya':'संध्या'
        }
        # Sort keys by length descending for greedy replacement
        return dict(sorted(base.items(), key=lambda x: len(x[0]), reverse=True))

    def roman_to_devanagari_greedy(self, text: str) -> str:
        low = text.lower()
        for k,v in self._roman_common_map.items():
            low = re.sub(rf'\b{k}\b', v, low)
        return low

    # ---------------- External APIs -----------------
    def _google_free(self, text, src, tgt):
        url = 'https://translate.googleapis.com/translate_a/single'
        params = {'client':'gtx','sl':src,'tl':tgt,'dt':'t','q':text}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code==200:
            data = r.json()
            if data and data[0]:
                return ''.join(part[0] for part in data[0] if part[0])
        return None

    def _mymemory(self, text, src, tgt):
        url='https://api.mymemory.translated.net/get'
        params={'q':text,'langpair':f'{src}|{tgt}','de':'demo@example.com'}
        r = requests.get(url, params=params, timeout=8)
        if r.status_code==200:
            js=r.json(); rd=js.get('responseData',{})
            out=rd.get('translatedText')
            if out and out.lower().strip()!=text.lower().strip():
                return out
        return None

    def _libre(self, text, src, tgt):
        url='https://libretranslate.de/translate'
        data={'q':text,'source':src,'target':tgt,'format':'text'}
        r = requests.post(url, data=data, timeout=10)
        if r.status_code==200:
            js=r.json(); out=js.get('translatedText')
            if out and out.lower().strip()!=text.lower().strip():
                return out
        return None

    def _lingva(self, text, src, tgt):
        url=f"https://lingva.ml/api/v1/{src}/{tgt}/{urllib.parse.quote(text)}"
        r = requests.get(url, timeout=8)
        if r.status_code==200:
            js=r.json(); out=js.get('translation')
            if out and out.lower().strip()!=text.lower().strip():
                return out
        return None

    def _deep_google(self, text, src, tgt):
        if not DEEP_TRANSLATOR_AVAILABLE:
            return None
        try:
            return DeepGoogleTranslator(source=src, target=tgt).translate(text)
        except Exception:
            return None

    def _is_valid_marathi(self, text):
        return bool(text and self.DEVANAGARI_RE.search(text))

    def translate_via_apis(self, text, src, tgt):
        order = [self._google_free, self._deep_google, self._mymemory, self._libre, self._lingva]
        for func in order:
            try:
                res = func(text, src, tgt)
            except Exception as e:
                logger.warning(f"{func.__name__} failed: {e}")
                continue
            if not res:
                continue
            if tgt=='mr' and not self._is_valid_marathi(res):
                logger.info(f"Discarding non-Devanagari result from {func.__name__}: {res}")
                continue
            if tgt=='en':
                # Basic sanity: result should be mostly ASCII (allow % of non-ASCII < 30%)
                non_ascii = sum(1 for c in res if ord(c) > 127)
                if non_ascii > max(2, len(res)//3):
                    logger.info(f"Discarding likely wrong English result from {func.__name__}: {res}")
                    continue
            logger.info(f"API {func.__name__} success: {res}")
            return res, func.__name__
        return None, None

    def _generate_variants(self, text: str, src: str):
        """Generate variant inputs to boost success especially for romanized Marathi."""
        variants = [text]
        if src == 'mr':
            # If romanized (no Devanagari) attempt greedy replacement
            if not self.DEVANAGARI_RE.search(text):
                replaced = self.roman_to_devanagari_greedy(text)
                if replaced != text:
                    variants.append(replaced)
        return list(dict.fromkeys(variants))  # dedupe, keep order

    async def translate(self, text: str, source_lang: str = 'auto', target_lang: str = 'auto'):
        text = text.strip()
        if not text:
            raise ValueError('Empty text')
        # detect
        src = self.advanced_language_detection(text) if source_lang=='auto' else ('en' if source_lang.lower().startswith('en') else 'mr')
        tgt = ('mr' if src=='en' else 'en') if target_lang=='auto' else ('en' if target_lang.lower().startswith('en') else 'mr')
        cache_key = f"{text.lower()}::{src}->{tgt}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return {'translated_text': cached['text'], 'source_language': src, 'target_language': tgt, 'method': cached['method']}
        # dictionary
        d = self.dictionary_translate(text, src, tgt)
        if d:
            self.cache[cache_key] = {'text': d, 'method': 'dictionary'}
            return {'translated_text': d,'source_language': src,'target_language': tgt,'method':'dictionary'}
        # variants (esp. for romanized mr)
        for variant in self._generate_variants(text, src):
            translated, method = self.translate_via_apis(variant, src, tgt)
            if translated:
                self.api_call_count += 1
                self.cache[cache_key] = {'text': translated, 'method': method}
                return {'translated_text': translated,'source_language': src,'target_language': tgt,'method': method}
        # fallback
        fallback = f"Translation unavailable for '{text}'."
        return {'translated_text': fallback,'source_language': src,'target_language': tgt,'method': 'fallback'}

    # Removed obsolete translation methods (Microsoft, Yandex, Bing, Apertium, deep_translator, googletrans) for reliability.

    # (Legacy method stubs removed.)

    # (Legacy method stubs removed.)

    # (Legacy method stubs removed.)

    # (Legacy multi-variant method removed.)

    # (Removed googletrans dependency)

    # (Removed deep_translator dependency)

    # (Replaced by lean _mymemory wrapper)

    # (Replaced by lean _google_free)

    # (Replaced by lean _lingva)

    # (Replaced by lean _libre)
    
    def translate_with_dictionary(self, text: str, source_lang: str, target_lang: str) -> str:
        """Comprehensive bidirectional dictionary translation"""
        logger.info(f"Using dictionary translation: {source_lang} -> {target_lang}")
        
        # English to Marathi dictionary
        en_to_mr = {
            'hello': 'नमस्कार',
            'hi': 'नमस्कार',
            'hello how are you': 'नमस्कार तुम्ही कसे आहात',
            'how are you': 'तुम्ही कसे आहात',
            'how are you?': 'तुम्ही कसे आहात?',
            'i am fine': 'मी ठीक आहे',
            'i am good': 'मी चांगला आहे',
            'good morning': 'सुप्रभात',
            'good evening': 'शुभ संध्या',
            'good night': 'शुभ रात्री',
            'good afternoon': 'शुभ दुपार',
            'thank you': 'धन्यवाद',
            'thank you so much': 'खूप खूप धन्यवाद',
            'thanks': 'धन्यवाद',
            'please': 'कृपया',
            'yes': 'होय',
            'no': 'नाही',
            'sorry': 'माफ करा',
            'excuse me': 'माफ करा',
            'what is your name': 'तुमचे नाव काय आहे',
            'what is your name?': 'तुमचे नाव काय आहे?',
            'my name is': 'माझे नाव',
            'nice to meet you': 'तुम्हाला भेटून आनंद झाला',
            'goodbye': 'निरोप',
            'bye': 'निरोप',
            'see you later': 'पुन्हा भेटू',
            'where': 'कुठे',
            'what': 'काय',
            'when': 'केव्हा',
            'how': 'कसे',
            'why': 'का',
            'water': 'पाणी',
            'food': 'अन्न',
            'help': 'मदत',
            'i need help': 'मला मदत हवी',
            'where is the bathroom': 'स्नानगृह कुठे आहे',
            'how much': 'किती',
            'how much?': 'किती?',
            'today': 'आज',
            'tomorrow': 'उद्या',
            'yesterday': 'काल',
            'i want to learn programming': 'मला प्रोग्रामिंग शिकायचे आहे',
            'i love programming': 'मला प्रोग्रामिंग आवडते',
            'computer': 'संगणक',
            'software': 'सॉफ्टवेअर'
        }
        
        # Marathi to English dictionary
        mr_to_en = {
            'नमस्कार': 'hello',
            'तुम्ही कसे आहात': 'how are you',
            'तुम्ही कसे आहात?': 'how are you?',
            'मी काम करत आहे': 'I am working',
            'मी शाळेत जातोय': 'I am going to school',
            'मी घरी जातोय': 'I am going home',
            'मला प्रोग्रामिंग शिकायचे आहे': 'I want to learn programming',
            'मला प्रोग्रामिंग आवडते': 'I love programming',
            'सुप्रभात': 'good morning',
            'शुभ संध्या': 'good evening',
            'शुभ रात्री': 'good night',
            'धन्यवाद': 'thank you',
            'होय': 'yes',
            'नाही': 'no',
            'माफ करा': 'sorry',
            'कृपया': 'please',
            'तुमचे नाव काय आहे': 'what is your name',
            'तुमचे नाव काय आहे?': 'what is your name?',
            'माझे नाव': 'my name is',
            'तुम्हाला भेटून आनंद झाला': 'nice to meet you',
            'निरोप': 'goodbye',
            'पुन्हा भेटू': 'see you later',
            'कुठे': 'where',
            'काय': 'what',
            'केव्हा': 'when',
            'कसे': 'how',
            'का': 'why',
            'पाणी': 'water',
            'अन्न': 'food',
            'मदत': 'help',
            'मला मदत हवी': 'i need help',
            'स्नानगृह कुठे आहे': 'where is the bathroom',
            'किती': 'how much',
            'किती?': 'how much?',
            'आज': 'today',
            'उद्या': 'tomorrow',
            'काल': 'yesterday',
            'संगणक': 'computer',
            'सॉफ्टवेअर': 'software'
        }
        
        # Romanized Marathi to English
        romanized_mr_to_en = {
            'namaskar': 'hello',
            'namaste': 'hello',
            'dhanyawad': 'thank you',
            'dhanyabad': 'thank you',
            'kasa ahat': 'how are you',
            'kasa ahes': 'how are you',
            'kasa kay': 'how are you',
            'tumhi kasa ahat': 'how are you',
            'tumhi kase ahat': 'how are you',
            'tumche nav kay ahe': 'what is your name',
            'majhe nav': 'my name is',
            'maza nav': 'my name is',
            'mi kaam karat ahe': 'I am working',
            'mi school la jatoy': 'I am going to school',
            'mi ghari jatoy': 'I am going home',
            'mi khana khattoy': 'I am eating food',
            'mala programming shikayche ahe': 'I want to learn programming',
            'mala programming shikayche': 'I want to learn programming',
            'mi programming shikat ahe': 'I am learning programming',
            'programming shikat': 'learning programming',
            'pani': 'water',
            'anna': 'food',
            'khana': 'food',
            'jevan': 'meal',
            'madad': 'help',
            'maddat': 'help',
            'kuthe': 'where',
            'kay': 'what',
            'kasa': 'how',
            'kase': 'how',
            'kiti': 'how much',
            'kevha': 'when',
            'kon': 'who',
            'hoye': 'yes',
            'hoy': 'yes',
            'nahi': 'no',
            'maaf kara': 'sorry',
            'krupa kara': 'please',
            'aaj': 'today',
            'udya': 'tomorrow',
            'kal': 'yesterday',
            'ratri': 'night',
            'sakal': 'morning',
            'sandhya': 'evening',
            'dupari': 'afternoon',
            'ghar': 'home',
            'ghara': 'home',
            'school': 'school',
            'kaam': 'work',
            'nokri': 'job',
            'paisa': 'money',
            'vel': 'time',
            'mitra': 'friend',
            'family': 'kutumb',
            'aai': 'mother',
            'baba': 'father',
            'bhau': 'brother',
            'bahin': 'sister',
            'tumhi': 'you',
            'tumi': 'you',
            'mi': 'I',
            'amhi': 'we',
            'te': 'they',
            'tyanche': 'their',
            'tyachi': 'his/her',
            'mala': 'to me',
            'tula': 'to you',
            'aahe': 'is',
            'ahe': 'is',
            'ahat': 'are',
            'ahes': 'are',
            'chya': 'of',
            'madhe': 'in',
            'var': 'on',
            'pasun': 'from',
            'saathi': 'for',
            'barobar': 'with',
            'shivay': 'without',
            'pudhe': 'ahead',
            'maghe': 'behind',
            'varti': 'above',
            'khali': 'below',
            'jatoy': 'going',
            'yetoy': 'coming',
            'karat': 'doing',
            'khattoy': 'eating',
            'pitoy': 'drinking',
            'boltoy': 'speaking',
            'aikttoy': 'listening',
            'baghtoy': 'watching',
            'vachtoy': 'reading',
            'lihtoy': 'writing',
            'zoptoy': 'sleeping',
            'uthttoy': 'waking up',
            'chaltoy': 'walking',
            'dhavttoy': 'running',
            'hasttoy': 'laughing',
            'rudttoy': 'crying',
            'shikat': 'learning',
            'shikayche': 'want to learn',
            'computer': 'computer',
            'software': 'software',
            'programming': 'programming'
        }
        
        # English to romanized Marathi  
        en_to_romanized_mr = {
            'hello': 'namaskar',
            'thank you': 'dhanyawad', 
            'how are you': 'kasa ahat',
            'what is your name': 'tumche nav kay ahe',
            'my name is': 'majhe nav',
            'water': 'pani',
            'food': 'anna',
            'help': 'madad',
            'where': 'kuthe',
            'what': 'kay',
            'how': 'kasa',
            'yes': 'hoye',
            'no': 'nahi',
            'sorry': 'maaf kara',
            'please': 'krupa kara',
            'today': 'aaj',
            'tomorrow': 'udya',
            'yesterday': 'kal',
            'night': 'ratri',
            'morning': 'sakal',
            'evening': 'sandhya',
            'home': 'ghar',
            'school': 'school',
            'work': 'kaam',
            'meal': 'jevan',
            'money': 'paisa',
            'time': 'vel',
            'friend': 'mitra',
            'mother': 'aai',
            'father': 'baba',
            'brother': 'bhau',
            'sister': 'bahin'
        }
        
        text_lower = text.lower().strip()
        
        # Choose appropriate dictionary
        if source_lang == 'en' and target_lang == 'mr':
            # English to Marathi - only exact matches, no partial matching for individual words
            if text_lower in en_to_mr:
                return en_to_mr[text_lower]
            
            # For English, if no exact dictionary match, let API handle it
            # This prevents poor word-by-word translations
            return None
                    
        elif source_lang == 'mr' and target_lang == 'en':
            # Marathi to English - handle both Devanagari and romanized
            
            # Handle garbled text (encoding issues)
            if '?' in text and len(text.replace('?', '').strip()) == 0:
                logger.warning("Detected garbled Devanagari text")
                return "Unable to translate garbled text. Please ensure proper UTF-8 encoding for Devanagari script."
            
            # First try exact Devanagari match
            if text in mr_to_en:
                return mr_to_en[text]
            
            # Try exact romanized match (full phrases first)
            if text_lower in romanized_mr_to_en:
                return romanized_mr_to_en[text_lower]
            
            # Try partial matches for Devanagari (only for longer phrases)
            if len(text.split()) >= 2:
                for mar_phrase, eng_phrase in mr_to_en.items():
                    if mar_phrase in text and len(mar_phrase.split()) >= 2:
                        return eng_phrase
            
            # Try partial matches for romanized (longer phrases first, minimum 2 words)
            if len(text_lower.split()) >= 2:
                sorted_romanized = sorted(romanized_mr_to_en.items(), key=lambda x: len(x[0]), reverse=True)
                for rom_phrase, eng_phrase in sorted_romanized:
                    if len(rom_phrase.split()) >= 2 and rom_phrase in text_lower:
                        return eng_phrase
            
            # For phrases with 3+ words, try word-by-word only if we can translate majority
            words = text_lower.split()
            if len(words) >= 3:
                translated_words = []
                found_translations = 0
                
                for word in words:
                    if word in romanized_mr_to_en:
                        translated_words.append(romanized_mr_to_en[word])
                        found_translations += 1
                    else:
                        # Try partial matching for compound words (but be stricter)
                        found_partial = False
                        for rom_word, eng_word in romanized_mr_to_en.items():
                            if len(rom_word) >= 4 and (word in rom_word or rom_word in word):
                                translated_words.append(eng_word)
                                found_partial = True
                                found_translations += 1
                                break
                        if not found_partial:
                            translated_words.append(word)  # Keep untranslated word
                
                # Return translation only if we found at least 70% of words
                if found_translations > 0 and found_translations >= len(words) * 0.7:
                    result = ' '.join(translated_words)
                    logger.info(f"Word-by-word translation: {text} -> {result} ({found_translations}/{len(words)} words translated)")
                    return result
            
            # If dictionary fails, return None to allow API fallback
            logger.info(f"Dictionary translation insufficient for: {text}, falling back to APIs")
            return None
        
# Initialize the translation service
translation_service = BilingualTranslationService()

# Initialize the health literacy tutor
health_tutor = get_health_tutor()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ShabdSetu - Lang-chain Powered Interactive Literacy Tutor is running!",
        "version": "4.0.0",
        "features": [
            "English to Marathi Translation", 
            "Marathi to English Translation", 
            "Health Information in English",
            "Health Information in Marathi",
            "AI-Powered Health Literacy",
            "Auto-detection", 
            "Real-time"
        ],
        "translation_apis": ["Dictionary", "MyMemory", "Google Translate (Free)", "Lingva Translate", "LibreTranslate"],
        "health_ai": "Google Gemini Pro with LangChain",
        "api_calls_made": translation_service.api_call_count
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Bidirectional translation endpoint with auto-detection"""
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to translate cannot be empty")
        
        # Log the raw input for debugging encoding issues
        logger.info(f"Raw translation request: '{request.text}' (len: {len(request.text)})")
        logger.info(f"Character codes: {[ord(c) for c in request.text[:10]]}")
        
        # Perform translation
        result = await translation_service.translate(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=result['translated_text'],
            source_language=result['source_language'],
            target_language=result['target_language'],
            translation_method=result['method']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in translation endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test translation functionality with simple dictionary words that should work
        test_en_result = translation_service.dictionary_translate("hello", "en", "mr")
        test_mr_result = translation_service.dictionary_translate("नमस्कार", "mr", "en")
        return {
            "status": "healthy",
            "version": "3.0.0",
            "api_calls_made": translation_service.api_call_count,
            "cache_size": len(translation_service.cache),
            "test_translations": {
                "en_to_mr": test_en_result or "dictionary test failed",
                "mr_to_en": test_mr_result or "dictionary test failed"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/stats")
async def get_stats():
    """Get translation service statistics"""
    return {
        "api_calls_made": translation_service.api_call_count,
        "cache_size": len(translation_service.cache),
        "cached_translations": list(translation_service.cache.keys())[:10]
    }

@app.post("/clear-cache")
async def clear_cache():
    """Clear translation cache"""
    cache_size = len(translation_service.cache)
    translation_service.cache.clear()
    return {
        "message": f"Cache cleared. Removed {cache_size} cached translations.",
        "cache_size": len(translation_service.cache)
    }

@app.post("/test-encoding")
async def test_encoding(request: TranslationRequest):
    """Test text encoding"""
    return {
        "received_text": request.text,
        "text_length": len(request.text),
        "char_codes": [ord(c) for c in request.text[:10]],  # First 10 chars
        "is_devanagari": bool(re.search(r'[\u0900-\u097F]', request.text))
    }

@app.post("/health/query")
async def health_query(request: HealthQueryRequest):
    """
    Health information endpoint - provides health information in English or Marathi
    Detects health-related queries and provides appropriate information
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Check if it's a health query
        is_health_query = health_tutor.detect_health_query(request.query)
        
        if not is_health_query:
            return {
                "is_health_query": False,
                "message": "This doesn't appear to be a health-related query. Please ask about health symptoms, conditions, or medical concerns.",
                "suggestion": "Try asking about: fever, cold, cough, headache, stomach pain, or other health issues."
            }
        
        # Process the health query
        result = health_tutor.process_health_query(request.query, request.language)
        
        return {
            "is_health_query": True,
            "query": request.query,
            "language": request.language,
            "response": result['response'],
            "source": result['source'],
            "disclaimer": "This information is for educational purposes only. Please consult a qualified healthcare professional for medical advice."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process health query")

@app.post("/smart/query")
async def smart_query(request: TranslationRequest):
    """
    Smart endpoint that detects if query is health-related or translation request
    Routes to appropriate service and returns response in user's language
    """
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Detect language
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', request.text))
        detected_lang = 'mr' if has_devanagari else 'en'
        
        # Check if it's a health query
        is_health_query = health_tutor.detect_health_query(request.text)
        
        if is_health_query:
            # Process as health query
            health_result = health_tutor.process_health_query(request.text, detected_lang)
            
            return {
                "type": "health",
                "original_query": request.text,
                "detected_language": detected_lang,
                "response": health_result['response'],
                "source": health_result['source'],
                "is_health_query": True
            }
        else:
            # Process as translation request
            source_language = "Marathi" if detected_lang == 'mr' else "English"
            target_language = "English" if detected_lang == 'mr' else "Marathi"
            
            translation_result = await translation_service.translate(
                text=request.text,
                source_lang=detected_lang,
                target_lang='en' if detected_lang == 'mr' else 'mr'
            )
            
            return {
                "type": "translation",
                "original_text": request.text,
                "translated_text": translation_result['translated_text'],
                "source_language": translation_result['source_language'],
                "target_language": translation_result['target_language'],
                "translation_method": translation_result['method'],
                "is_health_query": False
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart query error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
