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

# Import comprehensive translation libraries
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    INDIC_AVAILABLE = True
except ImportError:
    INDIC_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator, LibreTranslator, LingueeTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False

try:
    from googletrans import Translator as GoogleTranslator2
    GOOGLETRANS_AVAILABLE = True
except ImportError:
    GOOGLETRANS_AVAILABLE = False

try:
    from transliterate import translit
    TRANSLITERATE_AVAILABLE = True
except ImportError:
    TRANSLITERATE_AVAILABLE = False

try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

import requests_cache

# Setup cached session for faster API calls
session = requests_cache.CachedSession('translation_cache', expire_after=3600)

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
    allow_headers=["*", "Content-Type"],
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
        
        # Check for question marks or garbled text (encoding issues)
        if '?' in text and len(text.replace('?', '').strip()) == 0:
            logger.warning("Detected garbled text, likely encoding issue")
            # Try to detect if this should be Marathi based on context
            return 'mr'
        
        # Devanagari script detection (most reliable for Marathi)
        marathi_pattern = re.compile(r'[\u0900-\u097F]')
        devanagari_chars = len(marathi_pattern.findall(text))
        
        if devanagari_chars > 0:
            logger.info(f"Detected Marathi (Devanagari script - {devanagari_chars} chars)")
            return 'mr'
        
        # Check for Marathi Unicode characters more thoroughly
        marathi_char_count = 0
        for char in text:
            char_code = ord(char)
            if 0x0900 <= char_code <= 0x097F:
                marathi_char_count += 1
        
        if marathi_char_count > 0:
            logger.info(f"Detected Marathi (Unicode range - {marathi_char_count} chars)")
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
            'chya', 'pudhe', 'maghe', 'varti', 'khali', 'jevan', 'kaam',
            'shikat', 'programming', 'computer', 'software', 'engineering'
        ]
        
        # Marathi phrases that are strong indicators
        marathi_phrases = [
            'tumhi kasa ahat', 'tumhi kase ahat', 'kasa ahat', 'kase ahat',
            'majhe nav', 'maza nav', 'tumche nav', 'dhanyawad tumhi',
            'namaskar tumhi', 'maaf kara', 'krupa kara', 'programming shikat',
            'mala programming shikayche', 'mi programming shikto', 'computer chalav'
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
            # Need a higher threshold for Marathi detection in multi-word phrases
            # Don't classify as Marathi unless it's clearly Marathi-dominant
            if marathi_word_count > 0 and len(words) > 0:
                marathi_ratio = marathi_word_count / len(words)
                # Require at least 30% of words to be Marathi AND at least 2 Marathi words
                # This prevents English sentences with borrowed Marathi words from being misclassified
                if marathi_ratio >= 0.30 and marathi_word_count >= 2:
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
    
    def advanced_language_detection(self, text: str) -> str:
        """Advanced language detection using multiple methods"""
        logger.info(f"Advanced language detection for: {text[:50]}...")
        
        # Method 1: Check for Devanagari script
        devanagari_pattern = re.compile(r'[\u0900-\u097F]')
        if devanagari_pattern.search(text):
            logger.info("Detected Marathi (Devanagari script)")
            return 'mr'
        
        # Method 2: Use langdetect library if available
        if LANGDETECT_AVAILABLE:
            try:
                detected = detect(text)
                if detected in ['hi', 'mr']:  # Hindi/Marathi often confused
                    logger.info(f"langdetect suggests: {detected}, checking for Marathi patterns")
                    # Additional Marathi-specific check
                    marathi_indicators = ['kasa', 'ahat', 'namaskar', 'dhanyawad', 'tumhi', 'majhe', 'ahe', 'aahe']
                    text_lower = text.lower()
                    for indicator in marathi_indicators:
                        if indicator in text_lower:
                            logger.info(f"Found Marathi indicator: {indicator}")
                            return 'mr'
                    return 'mr' if detected == 'mr' else 'en'
                elif detected == 'en':
                    return 'en'
            except Exception as e:
                logger.warning(f"langdetect failed: {e}")
        
        # Method 3: Enhanced pattern matching (fallback)
        return self.detect_language(text)

    def comprehensive_transliteration(self, text: str) -> list:
        """Generate multiple transliteration variants"""
        variants = [text]  # Original text
        
        # Method 1: Indic transliteration
        if INDIC_AVAILABLE:
            try:
                # Try multiple schemes
                schemes = [
                    (sanscript.ITRANS, sanscript.DEVANAGARI),
                    (sanscript.HK, sanscript.DEVANAGARI),
                    (sanscript.VELTHUIS, sanscript.DEVANAGARI),
                    (sanscript.BARAHA, sanscript.DEVANAGARI)
                ]
                
                for src_scheme, dest_scheme in schemes:
                    try:
                        converted = transliterate(text, src_scheme, dest_scheme)
                        if converted and converted != text and converted not in variants:
                            variants.append(converted)
                            logger.info(f"Transliterated: {text} -> {converted}")
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Indic transliteration failed: {e}")
        
        # Method 2: Manual mapping for common words
        manual_converted = self.romanized_to_devanagari(text)
        if manual_converted != text and manual_converted not in variants:
            variants.append(manual_converted)
        
        return variants

    def romanized_to_devanagari(self, text: str) -> str:
        """Convert romanized Marathi to Devanagari using multiple methods"""
        try:
            if INDIC_AVAILABLE:
                # Use proper Indic transliteration
                converted = transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
                if converted and converted != text:
                    logger.info(f"Transliterated '{text}' to '{converted}'")
                    return converted
        except Exception as e:
            logger.warning(f"Indic transliteration failed: {e}")
        
        # Enhanced manual mapping with comprehensive coverage
        romanized_to_devanagari_map = {
            # Common greetings
            'namaskar': 'नमस्कार', 'namaste': 'नमस्ते', 'dhanyawad': 'धन्यवाद',
            # Personal info
            'majhe nav': 'माझे नाव', 'maza nav': 'माझं नाव', 'tumche nav': 'तुमचं नाव',
            # Questions
            'tumhi kasa ahat': 'तुम्ही कसे आहात', 'kasa ahat': 'कसे आहात',
            # Actions
            'mi programming shikat ahe': 'मी प्रोग्रामिंग शिकत आहे',
            'programming shikat': 'प्रोग्रामिंग शिकत',
            # Basic words
            'aahe': 'आहे', 'ahe': 'आहे', 'ahat': 'आहात', 'kasa': 'कसा', 'kay': 'काय',
            'tumhi': 'तुम्ही', 'mi': 'मी', 'mala': 'मला', 'hoye': 'होय', 'nahi': 'नाही',
            # Tech terms
            'programming': 'प्रोग्रामिंग', 'computer': 'संगणक', 'software': 'सॉफ्टवेअर'
        }
        
        converted_text = text.lower()
        sorted_map = sorted(romanized_to_devanagari_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for roman, devanagari in sorted_map:
            converted_text = converted_text.replace(roman, devanagari)
        
        return converted_text

    def translate_with_multiple_variants(self, text, source_lang, target_lang):
        """
        Try all available translation methods and return the best result
        """
        translations = []
        
        # Method 1: GoogleTrans library (best for Marathi)
        if GOOGLETRANS_AVAILABLE:
            try:
                result = self.translate_with_googletrans(text, source_lang, target_lang)
                if result and result.lower().strip() != text.lower().strip():
                    translations.append(('googletrans', result))
                    logger.info(f"GoogleTrans variant: {result}")
            except Exception as e:
                logger.warning(f"GoogleTrans variant failed: {e}")
        
        # Method 2: Deep Translator
        if DEEP_TRANSLATOR_AVAILABLE:
            try:
                result = self.translate_with_deep_translator(text, source_lang, target_lang)
                if result and result.lower().strip() != text.lower().strip():
                    translations.append(('deep_translator', result))
                    logger.info(f"DeepTranslator variant: {result}")
            except Exception as e:
                logger.warning(f"DeepTranslator variant failed: {e}")
        
        # Method 3: Microsoft Translator
        try:
            result = self.translate_with_microsoft(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('microsoft', result))
                logger.info(f"Microsoft variant: {result}")
        except Exception as e:
            logger.warning(f"Microsoft variant failed: {e}")
        
        # Method 4: Yandex Translator
        try:
            result = self.translate_with_yandex(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('yandex', result))
                logger.info(f"Yandex variant: {result}")
        except Exception as e:
            logger.warning(f"Yandex variant failed: {e}")
        
        # Method 5: Bing Translator
        try:
            result = self.translate_with_bing(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('bing', result))
                logger.info(f"Bing variant: {result}")
        except Exception as e:
            logger.warning(f"Bing variant failed: {e}")
        
        # Method 6: Apertium
        try:
            result = self.translate_with_apertium(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('apertium', result))
                logger.info(f"Apertium variant: {result}")
        except Exception as e:
            logger.warning(f"Apertium variant failed: {e}")
        
        # Method 7: MyMemory API
        try:
            result = self.translate_with_mymemory(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('mymemory', result))
                logger.info(f"MyMemory variant: {result}")
        except Exception as e:
            logger.warning(f"MyMemory variant failed: {e}")
        
        # Method 8: Google Free
        try:
            result = self.translate_with_google_free(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('google_free', result))
                logger.info(f"Google Free variant: {result}")
        except Exception as e:
            logger.warning(f"Google Free variant failed: {e}")
        
        # Method 9: Lingva Translate
        try:
            result = self.translate_with_lingva(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('lingva', result))
                logger.info(f"Lingva variant: {result}")
        except Exception as e:
            logger.warning(f"Lingva variant failed: {e}")
        
        # Method 10: LibreTranslate
        try:
            result = self.translate_with_libre(text, source_lang, target_lang)
            if result and result.lower().strip() != text.lower().strip():
                translations.append(('libre', result))
                logger.info(f"LibreTranslate variant: {result}")
        except Exception as e:
            logger.warning(f"LibreTranslate variant failed: {e}")
        
        if not translations:
            logger.warning("All translation methods failed")
            return None
        
        # For Marathi, prioritize GoogleTrans and Deep Translator results
        if source_lang == 'mr' or target_lang == 'mr':
            for method, result in translations:
                if method in ['googletrans', 'deep_translator', 'microsoft']:
                    logger.info(f"Selected {method} for Marathi translation: {result}")
                    return result
        
        # Return the first successful translation
        best_result = translations[0][1]
        logger.info(f"Selected best translation from {translations[0][0]}: {best_result}")
        return best_result

    def translate_with_microsoft(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Microsoft Translator (free tier)"""
        try:
            # Microsoft Translator endpoint (no API key required for basic usage)
            url = "https://api.cognitive.microsofttranslator.com/translate"
            params = {
                'api-version': '3.0',
                'from': source_lang,
                'to': target_lang
            }
            headers = {
                'Content-Type': 'application/json'
            }
            data = [{'text': text}]
            
            response = session.post(url, params=params, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and 'translations' in result[0]:
                    translation = result[0]['translations'][0]['text']
                    logger.info(f"Microsoft Translator successful: {translation}")
                    return translation
            
            logger.warning("Microsoft Translator API failed")
            return None
            
        except Exception as e:
            logger.error(f"Microsoft Translator error: {e}")
            return None

    def translate_with_yandex(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Yandex Translate (free service)"""
        try:
            # Yandex Translate free endpoint
            url = "https://translate.yandex.net/api/v1.5/tr/translate"
            params = {
                'key': 'free',  # Some free keys available
                'text': text,
                'lang': f'{source_lang}-{target_lang}',
                'format': 'plain'
            }
            
            response = session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                if root.tag == 'Translation' and root.text:
                    translation = root.text
                    logger.info(f"Yandex Translate successful: {translation}")
                    return translation
            
            logger.warning("Yandex Translate API failed")
            return None
            
        except Exception as e:
            logger.error(f"Yandex Translate error: {e}")
            return None

    def translate_with_bing(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Bing Translator (free web service)"""
        try:
            # Bing Translator web endpoint
            url = "https://www.bing.com/translator/api/Translate/TranslateArray"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
            
            data = {
                'fromLang': source_lang,
                'toLang': target_lang,
                'texts': [text]
            }
            
            response = session.post(url, headers=headers, json=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and 'text' in result[0]:
                    translation = result[0]['text']
                    logger.info(f"Bing Translator successful: {translation}")
                    return translation
            
            logger.warning("Bing Translator API failed")
            return None
            
        except Exception as e:
            logger.error(f"Bing Translator error: {e}")
            return None

    def translate_with_apertium(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using Apertium (free open-source)"""
        try:
            # Apertium API
            url = "https://apertium.org/apy/translate"
            
            # Map language codes for Apertium
            lang_map = {'mr': 'hi', 'en': 'eng'}  # Apertium uses hi for Marathi-like languages
            src_code = lang_map.get(source_lang, source_lang)
            tgt_code = lang_map.get(target_lang, target_lang)
            
            params = {
                'q': text,
                'langpair': f'{src_code}|{tgt_code}'
            }
            
            response = session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'translatedText' in result:
                    translation = result['translatedText']
                    logger.info(f"Apertium successful: {translation}")
                    return translation
            
            logger.warning("Apertium API failed")
            return None
            
        except Exception as e:
            logger.error(f"Apertium error: {e}")
            return None

    def translate_with_multiple_variants(self, text: str, source_lang: str, target_lang: str) -> str:
        """Try translation with multiple text variants"""
        variants = self.comprehensive_transliteration(text)
        
        translation_methods = [
            self.translate_with_googletrans,
            self.translate_with_deep_translator,
            self.translate_with_google_free,
            self.translate_with_mymemory,
            self.translate_with_microsoft,
            self.translate_with_bing,
            self.translate_with_lingva,
            self.translate_with_libre,
            self.translate_with_apertium
        ]
        
        for variant in variants:
            logger.info(f"Trying translation variant: {variant}")
            
            for method in translation_methods:
                try:
                    result = method(variant, source_lang, target_lang)
                    if (result and 
                        result.strip() != variant.strip() and 
                        len(result.strip()) > 0 and
                        not any(error_phrase in result.lower() for error_phrase in 
                               ['error', 'failed', 'please select', 'distinct languages'])):
                        logger.info(f"Successful translation: {variant} -> {result}")
                        return result
                except Exception as e:
                    logger.warning(f"Translation method failed: {e}")
                    continue
        
        return None
        """Convert romanized Marathi to Devanagari using proper library"""
        try:
            if INDIC_AVAILABLE:
                # Use proper Indic transliteration
                converted = transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
                if converted and converted != text:
                    logger.info(f"Transliterated '{text}' to '{converted}'")
                    return converted
        except Exception as e:
            logger.warning(f"Indic transliteration failed: {e}")
        
        # Fallback to manual mapping
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
            'mi kaam karat ahe': 'मी काम करत आहे',
            'mi school la jatoy': 'मी शाळेत जातोय',
            'mi ghari jatoy': 'मी घरी जातोय',
            'mala programming shikayche ahe': 'मला प्रोग्रामिंग शिकायचे आहे',
            'programming shikat': 'प्रोग्रामिंग शिकत',
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
            'khana': 'खाना',
            'jevan': 'जेवण',
            'madad': 'मदत',
            'ghar': 'घर',
            'ghara': 'घर',
            'school': 'शाळा',
            'kaam': 'काम',
            'paisa': 'पैसा',
            'mitra': 'मित्र',
            'engineer': 'अभियंता',
            'doctor': 'डॉक्टर',
            'teacher': 'शिक्षक',
            'programming': 'प्रोग्रामिंग',
            'computer': 'संगणक',
            'software': 'सॉफ्टवेअर',
            'tumhi': 'तुम्ही',
            'tumi': 'तुमी',
            'mi': 'मी',
            'amhi': 'आम्ही',
            'te': 'ते',
            'mala': 'मला',
            'tula': 'तुला',
            'hoye': 'होय',
            'hoy': 'होय',
            'nahi': 'नाही',
            'aaj': 'आज',
            'udya': 'उद्या',
            'kal': 'काल',
            'jatoy': 'जातोय',
            'yetoy': 'येतोय',
            'karat': 'करत',
            'khattoy': 'खातोय',
            'pitoy': 'पितोय',
            'boltoy': 'बोलतोय',
            'shikat': 'शिकत',
            'shikayche': 'शिकायचे'
        }
        
        converted_text = text.lower()
        # Sort by length (longest first) to handle longer phrases first
        sorted_map = sorted(romanized_to_devanagari_map.items(), key=lambda x: len(x[0]), reverse=True)
        
        for roman, devanagari in sorted_map:
            converted_text = converted_text.replace(roman, devanagari)
        
        return converted_text

    def translate_with_googletrans(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using googletrans library for better Marathi support"""
        try:
            if not GOOGLETRANS_AVAILABLE:
                return None
                
            translator = GoogleTranslator2()
            
            # Map language codes
            lang_map = {'mr': 'mr', 'en': 'en'}
            source_code = lang_map.get(source_lang, source_lang)
            target_code = lang_map.get(target_lang, target_lang)
            
            logger.info(f"GoogleTrans API call: {source_code} -> {target_code}")
            
            result = translator.translate(text, src=source_code, dest=target_code)
            
            if result and result.text and result.text.strip() != text.strip():
                translation = result.text
                logger.info(f"GoogleTrans successful: {translation}")
                return translation
            
            logger.warning("GoogleTrans API failed or returned same text")
            return None
            
        except Exception as e:
            logger.error(f"GoogleTrans API error: {e}")
            return None

    def translate_with_deep_translator(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using deep-translator library"""
        try:
            if not DEEP_TRANSLATOR_AVAILABLE:
                return None
                
            # Map language codes
            lang_map = {'mr': 'mr', 'en': 'en'}
            source_code = lang_map.get(source_lang, source_lang)
            target_code = lang_map.get(target_lang, target_lang)
            
            logger.info(f"DeepTranslator API call: {source_code} -> {target_code}")
            
            translator = GoogleTranslator(source=source_code, target=target_code)
            result = translator.translate(text)
            
            if result and result.strip() != text.strip():
                logger.info(f"DeepTranslator successful: {result}")
                return result
            
            logger.warning("DeepTranslator API failed or returned same text")
            return None
            
        except Exception as e:
            logger.error(f"DeepTranslator API error: {e}")
            return None

    def translate_with_mymemory(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using MyMemory API with enhanced Marathi support"""
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
            
            url = "https://api.mymemory.translated.net/get"
            
            # For Marathi translations, try multiple approaches
            if source_lang == 'mr' or target_lang == 'mr':
                # Try 1: Direct Marathi codes
                api_source = 'mr' if source_lang == 'mr' else 'en'
                api_target = 'mr' if target_lang == 'mr' else 'en'
                
                attempts = [
                    (api_source, api_target, api_text),  # Original text with proper Marathi
                    ('mr', 'en' if target_lang == 'en' else 'mr', text),  # Original romanized
                    ('hi', 'en' if target_lang == 'en' else 'hi', api_text)  # Hindi as last fallback
                ]
                
                for attempt_source, attempt_target, attempt_text in attempts:
                    try:
                        langpair = f'{attempt_source}|{attempt_target}'
                        params = {
                            'q': attempt_text,
                            'langpair': langpair,
                            'de': 'shabdsetu@example.com'
                        }
                        
                        logger.info(f"MyMemory API attempt: {langpair} for '{attempt_text[:30]}...'")
                        
                        response = requests.get(url, params=params, timeout=10)
                        self.last_api_call_time = time.time()
                        
                        if response.status_code == 200:
                            data = response.json()
                            if (data.get('responseData') and 
                                data['responseData'].get('translatedText') and
                                data['responseData']['translatedText'].lower().strip() != attempt_text.lower().strip() and
                                len(data['responseData']['translatedText'].strip()) > 0 and
                                'PLEASE SELECT TWO DISTINCT LANGUAGES' not in data['responseData']['translatedText'].upper()):
                                
                                translation = data['responseData']['translatedText']
                                logger.info(f"MyMemory translation successful: {translation}")
                                return translation
                        
                        time.sleep(0.5)  # Small delay between attempts
                    except Exception as e:
                        logger.warning(f"MyMemory attempt failed: {e}")
                        continue
            else:
                # For non-Marathi translations
                params = {
                    'q': api_text,
                    'langpair': f'{source_lang}|{target_lang}',
                    'de': 'shabdsetu@example.com'
                }
                
                response = requests.get(url, params=params, timeout=10)
                self.last_api_call_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    if (data.get('responseData') and 
                        data['responseData'].get('translatedText') and
                        data['responseData']['translatedText'].lower().strip() != api_text.lower().strip()):
                        
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
            lang_map = {'mr': 'mr', 'en': 'en'}  # Use proper Marathi code
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
            lang_map = {'mr': 'mr', 'en': 'en'}  # Use proper Marathi code
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
            lang_map = {'mr': 'mr', 'en': 'en'}  # Use proper Marathi code
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
        
        return None
    
    async def translate(self, text: str, source_lang: str = "auto", target_lang: str = "auto") -> dict:
        """Main translation function with auto-detection and multiple fallbacks"""
        try:
            # Clean input text
            text = text.strip()
            if not text:
                raise ValueError("Empty text provided")
            
            # Auto-detect source language with advanced detection
            if source_lang == "auto":
                detected_lang = self.advanced_language_detection(text)
            elif source_lang == "English":
                detected_lang = 'en'
            elif source_lang == "Marathi":
                detected_lang = 'mr'
            else:
                detected_lang = source_lang
            
            # Auto-determine target language (always opposite of source if auto)
            if target_lang == "auto":
                auto_target = 'en' if detected_lang == 'mr' else 'mr'
            elif target_lang == "English":
                auto_target = 'en'
            elif target_lang == "Marathi":
                auto_target = 'mr'
            else:
                # User explicitly provided 'en' or 'mr'
                auto_target = target_lang
            
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
            
            # If dictionary fails, try comprehensive translation with multiple variants
            logger.info("Dictionary translation not found, trying comprehensive API approach...")
            
            comprehensive_translation = self.translate_with_multiple_variants(text, detected_lang, auto_target)
            if comprehensive_translation:
                self.translation_cache[cache_key] = comprehensive_translation
                logger.info(f"Comprehensive translation successful: {comprehensive_translation}")
                return {
                    'translated_text': comprehensive_translation,
                    'source_language': detected_lang,
                    'target_language': auto_target,
                    'method': 'comprehensive_api'
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
        test_en_result = translation_service.translate_with_dictionary("hello", "en", "mr")
        test_mr_result = translation_service.translate_with_dictionary("namaskar", "mr", "en")
        
        return {
            "status": "healthy",
            "version": "3.0.0",
            "api_calls_made": translation_service.api_call_count,
            "cache_size": len(translation_service.translation_cache),
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
        "cache_size": len(translation_service.translation_cache),
        "cached_translations": list(translation_service.translation_cache.keys())[:10]  # First 10
    }

@app.post("/clear-cache")
async def clear_cache():
    """Clear translation cache"""
    cache_size = len(translation_service.translation_cache)
    translation_service.translation_cache.clear()
    return {
        "message": f"Cache cleared. Removed {cache_size} cached translations.",
        "cache_size": len(translation_service.translation_cache)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
