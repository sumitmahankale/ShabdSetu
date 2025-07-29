from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import logging
import requests
import re
import time
import json
import urllib.parse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShabdSetu - Bidirectional English-Marathi Translator",
    description="A fast, reliable translation service for English-Marathi bidirectional translation",
    version="3.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3003", "http://localhost:3002", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "auto"  # auto-detect by default
    target_language: str = "auto"  # auto-determine target

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    translation_method: str

class BilingualTranslationService:
    def __init__(self):
        self.translation_cache = {}
        self.api_call_count = 0
        self.last_api_call_time = 0
        
    def detect_language(self, text: str) -> str:
        """Enhanced language detection for English and Marathi"""
        logger.info(f"Detecting language for: {text[:50]}...")
        
        # Devanagari script detection (most reliable for Marathi)
        marathi_pattern = re.compile(r'[\u0900-\u097F]')
        if marathi_pattern.search(text):
            logger.info("Detected Marathi (Devanagari script)")
            return 'mr'
        
        # Enhanced romanized Marathi detection
        marathi_words = [
            'namaskar', 'namaste', 'dhanyawad', 'dhanyabad', 'kasa', 'kase', 
            'kay', 'kuthe', 'kiti', 'majhe', 'tumche', 'ahe', 'ahes', 'ahat',
            'pau', 'pahije', 'pani', 'anna', 'madad', 'maddat', 'hoye', 'nahi',
            'krupa', 'maaf', 'kara', 'pudhil', 'maga', 'pudhe', 'magun', 'vel',
            'aaj', 'udya', 'kal', 'sandhya', 'ratri', 'sakal', 'dupari',
            'tumi', 'tumhi', 'mi', 'amhi', 'tyanche', 'tyachi', 'mala', 'tula',
            'aahe', 'aahet', 'aahat', 'navyane', 'juna', 'mottha', 'chota',
            'ghara', 'ghar', 'gaon', 'shahar', 'rasta', 'dukan', 'school',
            'nav', 'saathi', 'barobar', 'shivay', 'madhe', 'var', 'pasun',
            'chya', 'pudhe', 'maghe', 'varti', 'khali', 'jevan', 'kaam'
        ]
        
        # Marathi phrases that are strong indicators
        marathi_phrases = [
            'tumhi kasa ahat', 'tumhi kase ahat', 'kasa ahat', 'kase ahat',
            'majhe nav', 'maza nav', 'tumche nav', 'dhanyawad tumhi',
            'namaskar tumhi', 'maaf kara', 'krupa kara'
        ]
        
        text_lower = text.lower().strip()
        words = text_lower.split()
        marathi_word_count = 0
        
        # Check for Marathi phrases first (stronger indicators)
        for phrase in marathi_phrases:
            if phrase in text_lower:
                logger.info(f"Found Marathi phrase: {phrase}")
                return 'mr'
        
        # Check for exact Marathi words and partial matches
        for word in marathi_words:
            if word in text_lower:
                marathi_word_count += 1
                logger.info(f"Found Marathi word: {word}")
        
        # More aggressive Marathi detection for single words
        if len(words) == 1:
            if text_lower in marathi_words:
                logger.info(f"Single Marathi word detected: {text_lower}")
                return 'mr'
        
        # Check for multi-word Marathi phrases
        if len(words) >= 2:
            # If more than 15% of recognizable words are Marathi, classify as Marathi
            if marathi_word_count > 0 and len(words) > 0:
                marathi_ratio = marathi_word_count / len(words)
                if marathi_ratio >= 0.15 or marathi_word_count >= 1:  # Even lower threshold for phrases
                    logger.info(f"Detected Marathi phrase (romanized words: {marathi_word_count}/{len(words)})")
                    return 'mr'
        else:
            # For single words, be more lenient
            if marathi_word_count >= 1:
                logger.info(f"Detected single Marathi word")
                return 'mr'
        
        # Check for common English words
        english_words = ['hello', 'hi', 'how', 'are', 'you', 'what', 'where', 'thank', 'please', 
                        'yes', 'no', 'sorry', 'good', 'morning', 'evening', 'night', 'name', 'nice', 'today', 'tomorrow']
        english_word_count = 0
        
        for word in english_words:
            if word in text_lower:
                english_word_count += 1
                logger.info(f"Found English word: {word}")
        
        # English detection with better logic
        if english_word_count > 0:
            logger.info(f"Detected English (common words: {english_word_count})")
            return 'en'
        
        # English pattern check (after word-based detection)
        english_pattern = re.compile(r'^[a-zA-Z\s.,!?\'"-]+$')
        if english_pattern.match(text.strip()):
            logger.info("Detected English (pattern match)")
            return 'en'
        
        # Default to English if uncertain
        logger.info("Defaulting to English")
        return 'en'
    
    def romanized_to_devanagari(self, text: str) -> str:
        """Convert common romanized Marathi words to Devanagari for better API translation"""
        romanized_to_devanagari_map = {
            'namaskar': 'नमस्कार',
            'namaste': 'नमस्ते', 
            'majhe nav': 'माझे नाव',
            'maza nav': 'माझं नाव',
            'tumche nav': 'तुमचं नाव',
            'tumhi kasa ahat': 'तुम्ही कसे आहात',
            'tumhi kase ahat': 'तुम्ही कसे आहात',
            'kasa ahat': 'कसे आहात',
            'kase ahat': 'कसे आहात',
            'aahe': 'आहे',
            'ahe': 'आहे',
            'ahat': 'आहात',
            'ahes': 'आहेस',
            'kasa': 'कसा',
            'kase': 'कसे',
            'kay': 'काय',
            'kuthe': 'कुठे',
            'dhanyawad': 'धन्यवाद',
            'dhanyabad': 'धन्यवाद',
            'pani': 'पाणी',
            'anna': 'अन्न',
            'madad': 'मदत',
            'ghar': 'घर',
            'school': 'शाळा',
            'kaam': 'काम',
            'paisa': 'पैसा',
            'mitra': 'मित्र',
            'engineer': 'अभियंता',
            'doctor': 'डॉक्टर',
            'teacher': 'शिक्षक',
            'tumhi': 'तुम्ही',
            'mi': 'मी',
            'amhi': 'आम्ही',
            'te': 'ते',
            'mala': 'मला',
            'tula': 'तुला',
            'hoye': 'होय',
            'nahi': 'नाही',
            'aaj': 'आज',
            'udya': 'उद्या',
            'kal': 'काल'
        }
        
        converted_text = text.lower()
        # Sort by length (longest first) to handle longer phrases first
        sorted_map = sorted(romanized_to_devanagari_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for roman, devanagari in sorted_map:
            converted_text = converted_text.replace(roman, devanagari)
        
        return converted_text

    def translate_with_mymemory(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using MyMemory API with proper Marathi support"""
        try:
            # Rate limiting - max 1 call per second
            current_time = time.time()
            if current_time - self.last_api_call_time < 1:
                time.sleep(1)
            
            # Convert romanized Marathi to Devanagari for better API results
            api_text = text
            if source_lang == 'mr':
                # Check if text contains romanized Marathi
                if not re.search(r'[\u0900-\u097F]', text):
                    # Text is romanized, convert to Devanagari
                    api_text = self.romanized_to_devanagari(text)
                    logger.info(f"Converted romanized text '{text}' to Devanagari: '{api_text}'")
            
            # Try direct Marathi first, then fallback to Hindi if needed
            url = "https://api.mymemory.translated.net/get"
            
            # First attempt with direct Marathi codes
            if source_lang == 'mr' or target_lang == 'mr':
                api_source = 'mr' if source_lang == 'mr' else source_lang
                api_target = 'mr' if target_lang == 'mr' else target_lang
                langpair = f'{api_source}|{api_target}'
                
                params = {
                    'q': api_text,
                    'langpair': langpair,
                    'de': 'shabdsetu@example.com'
                }
                
                logger.info(f"MyMemory API call (Marathi): {langpair} for '{api_text[:30]}...'")
                
                response = requests.get(url, params=params, timeout=10)
                self.last_api_call_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('responseData') and 
                        data['responseData'].get('translatedText') and
                        data['responseData']['translatedText'].lower() != api_text.lower()):
                        
                        translation = data['responseData']['translatedText']
                        logger.info(f"MyMemory Marathi translation successful: {translation}")
                        return translation
                
                # Fallback to Hindi if Marathi direct doesn't work
                logger.info("Trying Hindi fallback...")
                api_source_fallback = 'hi' if source_lang == 'mr' else source_lang
                api_target_fallback = 'hi' if target_lang == 'mr' else target_lang
                langpair_fallback = f'{api_source_fallback}|{api_target_fallback}'
                
                params_fallback = {
                    'q': api_text,
                    'langpair': langpair_fallback,
                    'de': 'shabdsetu@example.com'
                }
                
                logger.info(f"MyMemory API call (Hindi fallback): {langpair_fallback} for '{api_text[:30]}...'")
                
                response = requests.get(url, params=params_fallback, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('responseData') and 
                        data['responseData'].get('translatedText') and
                        data['responseData']['translatedText'].lower() != api_text.lower()):
                        
                        translation = data['responseData']['translatedText']
                        logger.info(f"MyMemory Hindi fallback successful: {translation}")
                        return translation
            else:
                # For non-Marathi translations, use direct codes
                params = {
                    'q': api_text,
                    'langpair': f'{source_lang}|{target_lang}',
                    'de': 'shabdsetu@example.com'
                }
                
                logger.info(f"MyMemory API call: {source_lang}|{target_lang} for '{api_text[:30]}...'")
                
                response = requests.get(url, params=params, timeout=10)
                self.last_api_call_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('responseData') and 
                        data['responseData'].get('translatedText') and
                        data['responseData']['translatedText'].lower() != api_text.lower()):
                        
                        translation = data['responseData']['translatedText']
                        logger.info(f"MyMemory translation successful: {translation}")
                        return translation
            
            self.api_call_count += 1
            logger.warning(f"MyMemory API failed or returned poor translation")
            return None
            
        except Exception as e:
            logger.error(f"MyMemory API error: {e}")
            return None

    def translate_with_google_free(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Google Translate (free/unofficial API)"""
        try:
            # Map language codes for Google
            lang_map = {'mr': 'hi', 'en': 'en'}  # Use Hindi for Marathi
            source_code = lang_map.get(source_lang, source_lang)
            target_code = lang_map.get(target_lang, target_lang)
            
            # Use Google Translate unofficial API
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': source_code,
                'tl': target_code,
                'dt': 't',
                'q': text
            }
            
            logger.info(f"Google Translate API call: {source_code} -> {target_code}")
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and result[0]:
                    translation = ''.join([item[0] for item in result[0] if item[0]])
                    logger.info(f"Google Translate successful: {translation}")
                    return translation
            
            logger.warning("Google Translate API failed")
            return None
            
        except Exception as e:
            logger.error(f"Google Translate API error: {e}")
            return None

    def translate_with_lingva(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Lingva Translate (free alternative to Google)"""
        try:
            # Map language codes
            lang_map = {'mr': 'hi', 'en': 'en'}
            source_code = lang_map.get(source_lang, source_lang)
            target_code = lang_map.get(target_lang, target_lang)
            
            # Use Lingva Translate API
            url = f"https://lingva.ml/api/v1/{source_code}/{target_code}/{urllib.parse.quote(text)}"
            
            logger.info(f"Lingva Translate API call: {source_code} -> {target_code}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and 'translation' in result:
                    translation = result['translation']
                    logger.info(f"Lingva Translate successful: {translation}")
                    return translation
            
            logger.warning("Lingva Translate API failed")
            return None
            
        except Exception as e:
            logger.error(f"Lingva Translate API error: {e}")
            return None

    def translate_with_libre(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using LibreTranslate (free and open source)"""
        try:
            # Map language codes
            lang_map = {'mr': 'hi', 'en': 'en'}
            source_code = lang_map.get(source_lang, source_lang)
            target_code = lang_map.get(target_lang, target_lang)
            
            # Use public LibreTranslate instance
            url = "https://libretranslate.de/translate"
            data = {
                'q': text,
                'source': source_code,
                'target': target_code,
                'format': 'text'
            }
            
            logger.info(f"LibreTranslate API call: {source_code} -> {target_code}")
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and 'translatedText' in result:
                    translation = result['translatedText']
                    logger.info(f"LibreTranslate successful: {translation}")
                    return translation
            
            logger.warning("LibreTranslate API failed")
            return None
            
        except Exception as e:
            logger.error(f"LibreTranslate API error: {e}")
            return None
    
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
            'yesterday': 'काल'
        }
        
        # Marathi to English dictionary
        mr_to_en = {
            'नमस्कार': 'hello',
            'तुम्ही कसे आहात': 'how are you',
            'तुम्ही कसे आहात?': 'how are you?',
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
            'काल': 'yesterday'
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
            'pani': 'water',
            'anna': 'food',
            'madad': 'help',
            'maddat': 'help',
            'kuthe': 'where',
            'kay': 'what',
            'kasa': 'how',
            'kase': 'how',
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
            'ghar': 'home',
            'ghara': 'home',
            'school': 'school',
            'kaam': 'work',
            'khana': 'food',
            'jevan': 'meal',
            'paisa': 'money',
            'vel': 'time',
            'mitra': 'friend',
            'family': 'kutumb',
            'aai': 'mother',
            'baba': 'father',
            'bhau': 'brother',
            'bahin': 'sister',
            'tumhi': 'you',
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
            'khali': 'below'
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
            # English to Marathi
            if text_lower in en_to_mr:
                return en_to_mr[text_lower]
            # Try partial matches
            for eng_phrase, mar_phrase in en_to_mr.items():
                if eng_phrase in text_lower:
                    return mar_phrase
                    
        elif source_lang == 'mr' and target_lang == 'en':
            # Marathi to English - handle both Devanagari and romanized
            # First try exact Devanagari match
            if text in mr_to_en:
                return mr_to_en[text]
            
            # Try exact romanized match
            if text_lower in romanized_mr_to_en:
                return romanized_mr_to_en[text_lower]
            
            # Try partial matches for Devanagari
            for mar_phrase, eng_phrase in mr_to_en.items():
                if mar_phrase in text:
                    return eng_phrase
            
            # Try partial matches for romanized (longer phrases first)
            sorted_romanized = sorted(romanized_mr_to_en.items(), key=lambda x: len(x[0]), reverse=True)
            for rom_phrase, eng_phrase in sorted_romanized:
                if rom_phrase in text_lower:
                    return eng_phrase
            
            # Try word-by-word translation for romanized Marathi
            words = text_lower.split()
            translated_words = []
            found_translations = 0
            
            for word in words:
                if word in romanized_mr_to_en:
                    translated_words.append(romanized_mr_to_en[word])
                    found_translations += 1
                else:
                    # Try partial matching for compound words
                    found_partial = False
                    for rom_word, eng_word in romanized_mr_to_en.items():
                        if word in rom_word or rom_word in word:
                            translated_words.append(eng_word)
                            found_partial = True
                            found_translations += 1
                            break
                    if not found_partial:
                        translated_words.append(word)  # Keep untranslated word
            
            # Return translation if we found at least one known word
            if found_translations > 0:
                result = ' '.join(translated_words)
                logger.info(f"Word-by-word translation: {text} -> {result} ({found_translations} words translated)")
                return result
                
        elif source_lang == 'en' and target_lang == 'mr':
            # English to Marathi - try Devanagari first, then romanized fallback
            if text_lower in en_to_mr:
                return en_to_mr[text_lower]
            
            # Try romanized Marathi as fallback
            if text_lower in en_to_romanized_mr:
                return en_to_romanized_mr[text_lower]
                
            # Try partial matches for English
            for eng_phrase, mar_phrase in en_to_mr.items():
                if eng_phrase in text_lower:
                    return mar_phrase
                    
            # Try word-by-word translation
            words = text_lower.split()
            translated_words = []
            for word in words:
                if word in en_to_mr:
                    translated_words.append(en_to_mr[word])
                elif word in en_to_romanized_mr:
                    translated_words.append(en_to_romanized_mr[word])
                else:
                    translated_words.append(word)
            
            if len(translated_words) > 0:
                return ' '.join(translated_words)
        
        return None
    
    async def translate(self, text: str, source_lang: str = "auto", target_lang: str = "auto") -> dict:
        """Main translation function with auto-detection and multiple fallbacks"""
        try:
            # Clean input text
            text = text.strip()
            if not text:
                raise ValueError("Empty text provided")
            
            # Auto-detect source language if needed
            if source_lang == "auto" or source_lang == "English":
                detected_lang = self.detect_language(text)
            else:
                detected_lang = 'mr' if source_lang == "Marathi" else 'en'
            
            # Auto-determine target language (always opposite of source)
            if target_lang == "auto" or target_lang == "English" or target_lang == "Marathi":
                auto_target = 'en' if detected_lang == 'mr' else 'mr'
            else:
                auto_target = 'mr' if target_lang == "Marathi" else 'en'
            
            logger.info(f"Translation: '{text}' from {detected_lang} to {auto_target}")
            
            # Check cache first
            cache_key = f"{text.lower()}_{detected_lang}_{auto_target}"
            if cache_key in self.translation_cache:
                logger.info("Using cached translation")
                cached_result = self.translation_cache[cache_key]
                return {
                    'translated_text': cached_result,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'cache'
                }
            
            # Try dictionary first for better Marathi accuracy
            dictionary_translation = self.translate_with_dictionary(text, detected_lang, auto_target)
            
            if dictionary_translation:
                # Dictionary gave a translation, use it
                self.translation_cache[cache_key] = dictionary_translation
                logger.info(f"Dictionary translation successful: {dictionary_translation}")
                return {
                    'translated_text': dictionary_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'dictionary'
                }
            
            # Fallback to multiple free APIs for phrases not in dictionary
            logger.info("Dictionary translation not found, trying API fallbacks...")
            
            # Try MyMemory API first
            mymemory_translation = self.translate_with_mymemory(text, detected_lang, auto_target)
            if mymemory_translation and mymemory_translation.lower().strip() != text.lower().strip():
                self.translation_cache[cache_key] = mymemory_translation
                logger.info(f"MyMemory translation successful: {mymemory_translation}")
                return {
                    'translated_text': mymemory_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'mymemory_api'
                }
            
            # Try Google Translate (free) as second option
            google_translation = self.translate_with_google_free(text, detected_lang, auto_target)
            if google_translation and google_translation.lower().strip() != text.lower().strip():
                self.translation_cache[cache_key] = google_translation
                logger.info(f"Google Translate successful: {google_translation}")
                return {
                    'translated_text': google_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'google_free'
                }
            
            # Try Lingva Translate as third option
            lingva_translation = self.translate_with_lingva(text, detected_lang, auto_target)
            if lingva_translation and lingva_translation.lower().strip() != text.lower().strip():
                self.translation_cache[cache_key] = lingva_translation
                logger.info(f"Lingva Translate successful: {lingva_translation}")
                return {
                    'translated_text': lingva_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'lingva_translate'
                }
            
            # Try LibreTranslate as fourth option
            libre_translation = self.translate_with_libre(text, detected_lang, auto_target)
            if libre_translation and libre_translation.lower().strip() != text.lower().strip():
                self.translation_cache[cache_key] = libre_translation
                logger.info(f"LibreTranslate successful: {libre_translation}")
                return {
                    'translated_text': libre_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'libretranslate'
                }
            
            # If all APIs fail, provide a helpful fallback message
            fallback_msg = f"Translation not available for '{text}'. Try common phrases like 'hello', 'thank you', 'namaskar', or 'dhanyawad'."
            logger.warning(f"All translation methods failed for: {text}")
            
            return {
                'translated_text': fallback_msg,
                'source_language': detected_lang,
                'target_language': auto_target,
                'method': 'fallback_message'
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

# Initialize the translation service
translation_service = BilingualTranslationService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ShabdSetu Bidirectional Translation API is running!",
        "version": "3.0.0",
        "features": ["English to Marathi", "Marathi to English", "Auto-detection", "Real-time"],
        "translation_apis": ["Dictionary", "MyMemory", "Google Translate (Free)", "Lingva Translate", "LibreTranslate"],
        "api_calls_made": translation_service.api_call_count
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Bidirectional translation endpoint with auto-detection"""
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to translate cannot be empty")
        
        logger.info(f"Translation request: '{request.text}' ({request.source_language} -> {request.target_language})")
        
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
        # Test translation functionality
        test_en = await translation_service.translate("hello", "en", "mr")
        test_mr = await translation_service.translate("नमस्कार", "mr", "en")
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "api_calls_made": translation_service.api_call_count,
            "cache_size": len(translation_service.translation_cache),
            "test_translations": {
                "en_to_mr": test_en['translated_text'],
                "mr_to_en": test_mr['translated_text']
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
        "cache_size": len(translation_service.translation_cache),
        "cached_translations": list(translation_service.translation_cache.keys())[:10]  # First 10
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
