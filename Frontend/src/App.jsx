import React, { useState, useRef, useEffect } from 'react';
import { Languages, ArrowRight, Copy, RefreshCw, Volume2, Heart, Github, Mic, MicOff, VolumeX, Sparkles, RotateCcw } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8003';

// Enhanced language detection function
const detectLanguage = (text) => {
  console.log('detectLanguage called with:', text);
  
  // Devanagari script detection for Marathi (most reliable)
  const marathiPattern = /[\u0900-\u097F]/;
  
  // Check for Marathi script first (highest priority)
  if (marathiPattern.test(text)) {
    console.log('Detected as Marathi (Devanagari script)');
    return 'mr';
  }
  
  // Romanized Marathi words (common Marathi words written in English)
  const marathiWordsInRoman = [
    'namaskar', 'namaste', 'dhanyawad', 'dhanyabad', 'kasa', 'kase', 'kay', 'kuthe', 'kiti', 
    'ata', 'mag', 'pan', 'ani', 'tyala', 'tyachi', 'mala', 'amhi', 'tumhi', 'kasa ahat',
    'majhe nav', 'tumche nav', 'pau pahije', 'pani', 'anna', 'madad', 'maddat'
  ];
  
  const lowerText = text.toLowerCase().trim();
  
  // Check for romanized Marathi words
  for (const word of marathiWordsInRoman) {
    if (lowerText.includes(word)) {
      console.log('Detected as Marathi (romanized word):', word);
      return 'mr';
    }
  }
  
  // English pattern check (only pure English characters)
  const englishPattern = /^[a-zA-Z\s.,!?'"()-]+$/;
  if (englishPattern.test(text.trim())) {
    console.log('Detected as English (pattern match)');
    return 'en';
  }
  
  // If contains any non-English characters, assume Marathi
  const hasNonEnglish = /[^\u0000-\u007F]/.test(text);
  if (hasNonEnglish) {
    console.log('Detected as Marathi (non-English characters)');
    return 'mr';
  }
  
  // Default to English if uncertain
  console.log('Defaulting to English');
  return 'en';
};

// Simplified and more reliable translation service
const translateWithFreeService = async (text, fromLang = null, toLang = null) => {
  console.log('translateWithFreeService called with:', { text, fromLang, toLang });
  
  try {
    // Auto-detect language if not provided
    const detectedLang = fromLang || detectLanguage(text);
    const targetLang = toLang || (detectedLang === 'en' ? 'mr' : 'en');
    
    console.log(`Detected language: ${detectedLang}, Target: ${targetLang}`);
    
    // First try MyMemory API with proper language codes
    try {
      // Use proper language codes for MyMemory API
      const apiFromLang = detectedLang === 'mr' ? 'hi' : detectedLang; // Use Hindi for Marathi in API
      const apiToLang = targetLang === 'mr' ? 'hi' : targetLang;
      const langPair = `${apiFromLang}|${apiToLang}`;
      
      console.log('Trying MyMemory API with langpair:', langPair);
      
      const response = await axios.get(`https://api.mymemory.translated.net/get`, {
        params: {
          q: text,
          langpair: langPair
        },
        timeout: 8000
      });
      
      console.log('MyMemory response:', response.data);
      
      if (response.data && response.data.responseData && response.data.responseData.translatedText) {
        const translation = response.data.responseData.translatedText;
        
        // Check if translation is meaningful (not just echoing input)
        if (translation.toLowerCase() !== text.toLowerCase() && translation.trim().length > 0) {
          console.log('MyMemory translation successful:', translation);
          return {
            translatedText: translation,
            detectedLanguage: detectedLang,
            targetLanguage: targetLang
          };
        }
      }
    } catch (apiError) {
      console.log('MyMemory API failed:', apiError.message);
    }
    
    // Fallback to dictionary
    console.log('Using fallback dictionary...');
    return translateWithDictionary(text, detectedLang, targetLang);
    
  } catch (error) {
    console.error('Translation service error:', error);
    throw new Error(`Translation failed: ${error.message}`);
  }
};

// Separate dictionary function for better debugging
const translateWithDictionary = (text, detectedLang, targetLang) => {
  console.log('translateWithDictionary called:', { text, detectedLang, targetLang });
  
  // Comprehensive bidirectional dictionary
  const englishToMarathi = {
    'hello': 'नमस्कार',
    'hi': 'नमस्कार', 
    'how are you': 'तुम्ही कसे आहात',
    'how are you?': 'तुम्ही कसे आहात?',
    'good morning': 'सुप्रभात',
    'good evening': 'शुभ संध्या',
    'thank you': 'धन्यवाद',
    'thanks': 'धन्यवाद',
    'yes': 'होय',
    'no': 'नाही',
    'sorry': 'माफ करा',
    'please': 'कृपया',
    'what is your name': 'तुमचे नाव काय आहे',
    'what is your name?': 'तुमचे नाव काय आहे?',
    'my name is': 'माझे नाव',
    'goodbye': 'निरोप',
    'bye': 'निरोप',
    'water': 'पाणी',
    'food': 'अन्न',
    'help': 'मदत',
    'where': 'कुठे',
    'what': 'काय',
    'when': 'केव्हा',
    'how': 'कसे'
  };
  
  // Marathi to English dictionary
  const marathiToEnglish = {
    'नमस्कार': 'hello',
    'तुम्ही कसे आहात': 'how are you',
    'तुम्ही कसे आहात?': 'how are you?',
    'सुप्रभात': 'good morning',
    'शुभ संध्या': 'good evening',
    'धन्यवाद': 'thank you',
    'होय': 'yes',
    'नाही': 'no',
    'माफ करा': 'sorry',
    'कृपया': 'please',
    'तुमचे नाव काय आहे': 'what is your name',
    'तुमचे नाव काय आहे?': 'what is your name?',
    'माझे नाव': 'my name is',
    'निरोप': 'goodbye',
    'पाणी': 'water',
    'अन्न': 'food',
    'मदत': 'help',
    'कुठे': 'where',
    'काय': 'what',
    'केव्हा': 'when',
    'कसे': 'how'
  };
  
  // Romanized Marathi to English
  const romanMarathiToEnglish = {
    'namaskar': 'hello',
    'namaste': 'hello',
    'dhanyawad': 'thank you',
    'dhanyabad': 'thank you',
    'kasa ahat': 'how are you',
    'kasa ahes': 'how are you',
    'tumche nav kay ahe': 'what is your name',
    'majhe nav': 'my name is',
    'pani': 'water',
    'anna': 'food',
    'madad': 'help',
    'maddat': 'help',
    'kuthe': 'where',
    'kay': 'what',
    'kasa': 'how'
  };
  
  const lowerText = text.toLowerCase().trim();
  
  console.log('Trying translation from', detectedLang, 'to', targetLang);
  
  if (detectedLang === 'en' && targetLang === 'mr') {
    // English to Marathi
    console.log('Translating English to Marathi');
    
    // Try exact match
    if (englishToMarathi[lowerText]) {
      console.log('Exact match found:', englishToMarathi[lowerText]);
      return {
        translatedText: englishToMarathi[lowerText],
        detectedLanguage: 'en',
        targetLanguage: 'mr'
      };
    }
    
    // Try partial matches
    for (const [english, marathi] of Object.entries(englishToMarathi)) {
      if (lowerText.includes(english)) {
        console.log('Partial match found:', english, '->', marathi);
        return {
          translatedText: marathi,
          detectedLanguage: 'en',
          targetLanguage: 'mr'
        };
      }
    }
  } 
  else if (detectedLang === 'mr' && targetLang === 'en') {
    // Marathi to English
    console.log('Translating Marathi to English');
    
    // Try exact match for Devanagari
    if (marathiToEnglish[text]) {
      console.log('Exact Devanagari match found:', marathiToEnglish[text]);
      return {
        translatedText: marathiToEnglish[text],
        detectedLanguage: 'mr',
        targetLanguage: 'en'
      };
    }
    
    // Try exact match for romanized
    if (romanMarathiToEnglish[lowerText]) {
      console.log('Exact romanized match found:', romanMarathiToEnglish[lowerText]);
      return {
        translatedText: romanMarathiToEnglish[lowerText],
        detectedLanguage: 'mr',
        targetLanguage: 'en'
      };
    }
    
    // Try partial matches for Devanagari
    for (const [marathi, english] of Object.entries(marathiToEnglish)) {
      if (text.includes(marathi)) {
        console.log('Partial Devanagari match found:', marathi, '->', english);
        return {
          translatedText: english,
          detectedLanguage: 'mr',
          targetLanguage: 'en'
        };
      }
    }
    
    // Try partial matches for romanized
    for (const [romanMarathi, english] of Object.entries(romanMarathiToEnglish)) {
      if (lowerText.includes(romanMarathi)) {
        console.log('Partial romanized match found:', romanMarathi, '->', english);
        return {
          translatedText: english,
          detectedLanguage: 'mr',
          targetLanguage: 'en'
        };
      }
    }
  }
  
  console.log('No translation found in dictionary');
  throw new Error(`No translation found for "${text}". Available in dictionary: English words like "hello", "thank you" and Marathi words like "नमस्कार", "धन्यवाद"`);
};

function App() {
  const [inputText, setInputText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);
  const recognitionRef = useRef(null);

  // Initialize speech recognition with bidirectional support
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setSpeechSupported(true);
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';
      
      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setError('');
        console.log('Speech recognition started');
      };
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log('Speech recognized:', transcript);
        setInputText(transcript);
        setIsListening(false);
        
        // Auto-translate after speech recognition
        setTimeout(() => {
          translateText(transcript);
        }, 500);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.log('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'no-speech') {
          setError('No speech detected. Please try speaking again.');
        } else if (event.error === 'not-allowed') {
          setError('Microphone access denied. Please allow microphone access and reload the page.');
        } else {
          setError(`Speech recognition error: ${event.error}. Please try again.`);
        }
      };
      
      recognitionRef.current.onend = () => {
        console.log('Speech recognition ended');
        setIsListening(false);
      };
    } else {
      console.log('Speech recognition not supported');
    }
  }, []);

  const startListening = () => {
    if (recognitionRef.current && speechSupported) {
      try {
        console.log('Starting speech recognition...');
        recognitionRef.current.start();
      } catch (error) {
        console.error('Failed to start speech recognition:', error);
        setError('Could not start speech recognition. Please try again.');
      }
    } else {
      setError('Speech recognition is not supported in your browser.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const translateText = async (textToTranslate = null) => {
    const text = textToTranslate || inputText;
    if (!text.trim()) {
      setError('Please speak something or enter text to translate');
      return;
    }

    setIsLoading(true);
    setError('');
    console.log('Starting translation for:', text);
    
    try {
      let result;
      let translationMethod = 'unknown';
      
      // Try backend first (most reliable)
      try {
        console.log('Trying backend translation...');
        const response = await axios.post(`${API_BASE_URL}/translate`, {
          text: text,
          source_language: "auto",
          target_language: "auto"
        }, {
          timeout: 10000 // 10 second timeout
        });
        
        if (response.data && response.data.translated_text) {
          result = {
            translatedText: response.data.translated_text,
            detectedLanguage: response.data.source_language,
            targetLanguage: response.data.target_language
          };
          translationMethod = 'backend';
          console.log('Backend translation successful:', result);
        } else {
          throw new Error('Backend returned empty response');
        }
      } catch (backendError) {
        console.log('Backend failed, trying free service:', backendError.message);
        
        // Fallback to free service
        result = await translateWithFreeService(text);
        translationMethod = 'free_service';
        console.log('Free service translation successful:', result);
      }
      
      // Update UI with results
      setTranslatedText(result.translatedText);
      setDetectedLanguage(result.detectedLanguage);
      setTargetLanguage(result.targetLanguage);
      
      // Add to conversation history
      const newEntry = {
        id: Date.now(),
        input: text,
        output: result.translatedText,
        inputLang: result.detectedLanguage,
        outputLang: result.targetLanguage,
        method: translationMethod,
        timestamp: new Date().toLocaleTimeString()
      };
      setConversationHistory(prev => [newEntry, ...prev.slice(0, 4)]); // Keep last 5 entries
      
      // Auto-speak the translation
      setTimeout(() => {
        speakText(result.translatedText, result.targetLanguage);
      }, 500);
      
    } catch (err) {
      console.error('All translation methods failed:', err);
      const errorMessage = err.message || 'Translation failed. Please check your internet connection and try again.';
      setError(errorMessage);
      
      // If translation completely fails, at least show what was spoken
      if (text !== inputText) {
        setInputText(text);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = (text, lang = 'en') => {
    if ('speechSynthesis' in window && text) {
      // Stop any current speech
      speechSynthesis.cancel();
      
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Get available voices
      const voices = speechSynthesis.getVoices();
      
      // Configure voice settings based on language
      if (lang === 'mr') {
        // Try to find the best voice for Marathi
        let selectedVoice = null;
        
        // Priority 1: Look for Marathi voice (mr-IN)
        selectedVoice = voices.find(voice => 
          voice.lang.toLowerCase().includes('mr') || 
          voice.name.toLowerCase().includes('marathi')
        );
        
        // Priority 2: Look for Hindi voice (hi-IN) as fallback
        if (!selectedVoice) {
          selectedVoice = voices.find(voice => 
            voice.lang.toLowerCase().includes('hi') ||
            voice.name.toLowerCase().includes('hindi')
          );
        }
        
        // Priority 3: Look for Indian English voice
        if (!selectedVoice) {
          selectedVoice = voices.find(voice => 
            voice.lang.toLowerCase().includes('en-in') ||
            voice.name.toLowerCase().includes('indian')
          );
        }
        
        // Priority 4: Any female voice (often sounds better for Indian languages)
        if (!selectedVoice) {
          selectedVoice = voices.find(voice => 
            voice.name.toLowerCase().includes('female') ||
            voice.name.toLowerCase().includes('woman')
          );
        }
        
        if (selectedVoice) {
          utterance.voice = selectedVoice;
          console.log('Using voice for Marathi:', selectedVoice.name, selectedVoice.lang);
        }
        
        utterance.lang = 'hi-IN'; // Fallback language
        utterance.rate = 0.6; // Slower for better pronunciation
        utterance.pitch = 1.0;
      } else {
        // English voice selection
        const englishVoice = voices.find(voice => 
          voice.lang.toLowerCase().includes('en-us') ||
          voice.lang.toLowerCase().includes('en-gb')
        );
        
        if (englishVoice) {
          utterance.voice = englishVoice;
          console.log('Using voice for English:', englishVoice.name, englishVoice.lang);
        }
        
        utterance.lang = 'en-US';
        utterance.rate = 0.8;
        utterance.pitch = 1.0;
      }
      
      utterance.onend = () => {
        setIsSpeaking(false);
      };
      
      utterance.onerror = () => {
        setIsSpeaking(false);
        setError('Speech synthesis failed. Please try again.');
      };
      
      speechSynthesis.speak(utterance);
    } else {
      setError('Text-to-speech is not supported in your browser.');
    }
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  };

  const clearAll = () => {
    setInputText('');
    setTranslatedText('');
    setError('');
    setDetectedLanguage('');
    setTargetLanguage('');
    setConversationHistory([]);
  };

  const getLanguageDisplayName = (langCode) => {
    const languages = {
      'en': 'English',
      'mr': 'मराठी (Marathi)'
    };
    return languages[langCode] || langCode;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg">
                <Languages className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  ShabdSetu
                </h1>
                <p className="text-sm text-gray-600">शब्दसेतू - AI Translation</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 rounded-full text-sm font-medium shadow-sm">
                🔄 Auto-detect
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Central Voice Interface - Gemini Style */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm rounded-full border border-gray-200 shadow-sm mb-6">
            <Sparkles className="w-4 h-4 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Speak in any language</span>
          </div>
          
          <h2 className="text-4xl font-bold text-gray-900 mb-3">
            Start Speaking
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Speak in <span className="font-semibold text-blue-600">English</span> or <span className="font-semibold text-purple-600">मराठी</span> and get instant translation with voice response
          </p>

          {/* Main Voice Button - Gemini Style */}
          <div className="relative mb-8">
            <button
              onClick={isListening ? stopListening : startListening}
              disabled={!speechSupported || isLoading}
              className={`relative w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-2xl ${
                isListening 
                  ? 'bg-gradient-to-r from-red-500 to-pink-500 scale-110 animate-pulse' 
                  : isSpeaking
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 scale-105 animate-pulse'
                  : isLoading
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 animate-spin'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:scale-105'
              } text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              title={isListening ? 'Stop listening' : 'Start voice translation'}
            >
              {isListening ? (
                <MicOff className="w-10 h-10" />
              ) : isSpeaking ? (
                <Volume2 className="w-10 h-10" />
              ) : isLoading ? (
                <div className="w-8 h-8 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <Mic className="w-10 h-10" />
              )}
              
              {/* Animated Ring */}
              {(isListening || isSpeaking) && (
                <div className="absolute inset-0 rounded-full border-4 border-white/30 animate-ping"></div>
              )}
            </button>
            
            {/* Status Text */}
            <div className="mt-4">
              {isListening && (
                <p className="text-red-600 font-medium animate-pulse">🎤 Listening...</p>
              )}
              {isSpeaking && (
                <p className="text-orange-600 font-medium animate-pulse">🔊 Speaking...</p>
              )}
              {isLoading && (
                <p className="text-blue-600 font-medium">🔄 Translating...</p>
              )}
              {!isListening && !isSpeaking && !isLoading && (
                <p className="text-gray-600">Tap to start speaking</p>
              )}
            </div>
          </div>

          {/* Language Detection Display */}
          {detectedLanguage && targetLanguage && (
            <div className="flex items-center justify-center gap-4 mb-8">
              <div className="px-4 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                <span className="text-sm font-medium text-gray-700">
                  {getLanguageDisplayName(detectedLanguage)}
                </span>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400" />
              <div className="px-4 py-2 bg-white rounded-lg shadow-sm border border-gray-200">
                <span className="text-sm font-medium text-gray-700">
                  {getLanguageDisplayName(targetLanguage)}
                </span>
              </div>
            </div>
          )}

          {/* Speech support warning */}
          {!speechSupported && (
            <div className="mb-8 p-4 bg-amber-50 border border-amber-200 rounded-xl max-w-md mx-auto">
              <p className="text-amber-800 text-sm">
                ⚠️ Voice recognition not supported. Please use Chrome, Edge, or Safari.
              </p>
            </div>
          )}

          {/* Status Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl max-w-md mx-auto">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Current Translation Display */}
        {(inputText || translatedText || error) && (
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 mb-8">
            {error ? (
              <div className="text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-red-600 text-2xl">⚠️</span>
                </div>
                <p className="text-red-600 font-medium mb-2">Translation Error</p>
                <p className="text-red-500 text-sm">{error}</p>
              </div>
            ) : (
              <div className="space-y-6">
                {inputText && (
                  <div className="text-center">
                    <div className="text-sm text-gray-500 mb-2">You said:</div>
                    <p className="text-lg text-gray-900 font-medium">{inputText}</p>
                    {detectedLanguage && (
                      <div className="mt-2">
                        <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                          {getLanguageDisplayName(detectedLanguage)}
                        </span>
                      </div>
                    )}
                  </div>
                )}
                
                {translatedText && (
                  <div className="text-center border-t border-gray-100 pt-6">
                    <div className="text-sm text-gray-500 mb-2">Translation:</div>
                    <p className="text-xl text-gray-900 font-semibold mb-4">{translatedText}</p>
                    {targetLanguage && (
                      <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded-full">
                        {getLanguageDisplayName(targetLanguage)}
                      </span>
                    )}
                    
                    {/* Action Buttons */}
                    <div className="flex items-center justify-center gap-3 mt-4">
                      <button
                        onClick={() => speakText(translatedText, targetLanguage)}
                        className="p-2 text-gray-500 hover:text-blue-600 transition-colors rounded-lg hover:bg-blue-50"
                        title="Listen to translation"
                      >
                        <Volume2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => navigator.clipboard.writeText(translatedText)}
                        className="p-2 text-gray-500 hover:text-green-600 transition-colors rounded-lg hover:bg-green-50"
                        title="Copy translation"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Conversation History */}
        {conversationHistory.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Recent Translations</h3>
              <button
                onClick={clearAll}
                className="text-sm text-gray-500 hover:text-red-600 transition-colors flex items-center gap-1"
              >
                <RotateCcw className="w-4 h-4" />
                Clear all
              </button>
            </div>
            <div className="space-y-3">
              {conversationHistory.map((entry) => (
                <div key={entry.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                          {getLanguageDisplayName(entry.inputLang)}
                        </span>
                        <ArrowRight className="w-3 h-3 text-gray-400" />
                        <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded-full">
                          {getLanguageDisplayName(entry.outputLang)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{entry.input}</p>
                      <p className="text-sm text-gray-900 font-medium">{entry.output}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => speakText(entry.output, entry.outputLang)}
                        className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      >
                        <Volume2 className="w-3 h-3" />
                      </button>
                      <span className="text-xs text-gray-400">{entry.timestamp}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Features Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="text-center p-6 bg-white rounded-2xl shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Languages className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Auto-Detect</h3>
            <p className="text-gray-600 text-sm">Automatically detects whether you're speaking English or Marathi</p>
          </div>
          
          <div className="text-center p-6 bg-white rounded-2xl shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Volume2 className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Voice Response</h3>
            <p className="text-gray-600 text-sm">Automatically speaks the translation in the target language</p>
          </div>
          
          <div className="text-center p-6 bg-white rounded-2xl shadow-sm border border-gray-200">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Free & Fast</h3>
            <p className="text-gray-600 text-sm">No API keys required, works instantly with free translation services</p>
          </div>
        </div>

        {/* How to Use */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 text-center mb-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">How to Use</h3>
          <div className="max-w-2xl mx-auto space-y-3 text-gray-700 mb-6">
            <p className="flex items-center justify-center gap-2">
              <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</span>
              Tap the microphone button
            </p>
            <p className="flex items-center justify-center gap-2">
              <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</span>
              Speak in English or Marathi
            </p>
            <p className="flex items-center justify-center gap-2">
              <span className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</span>
              Listen to the automatic translation
            </p>
          </div>
          
          {/* Test Phrases */}
          <div className="border-t border-gray-200 pt-6">
            <h4 className="text-lg font-semibold text-gray-800 mb-4">Try These Phrases:</h4>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <h5 className="font-medium text-blue-600 mb-2">English Examples:</h5>
                <div className="space-y-1 text-gray-600">
                  <p>"Hello, how are you?"</p>
                  <p>"What is your name?"</p>
                  <p>"Thank you very much"</p>
                  <p>"Where is the bathroom?"</p>
                </div>
              </div>
              <div>
                <h5 className="font-medium text-purple-600 mb-2">Marathi Examples:</h5>
                <div className="space-y-1 text-gray-600">
                  <p>"नमस्कार, तुम्ही कसे आहात?"</p>
                  <p>"तुमचे नाव काय आहे?"</p>
                  <p>"धन्यवाद"</p>
                  <p>"स्नानगृह कुठे आहे?"</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-md border-t border-gray-200 mt-16">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center text-gray-600">
            <p className="mb-2">
              Made with <Heart className="w-4 h-4 text-red-500 inline mx-1" /> for seamless communication
            </p>
            <p className="text-sm">
              ShabdSetu - Bridging languages with AI • Powered by free translation services
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
