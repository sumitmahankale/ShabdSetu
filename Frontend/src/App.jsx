import React, { useState, useRef, useEffect } from 'react';
import { Languages, ArrowRight, Copy, RefreshCw, Volume2, Heart, Github, Mic, MicOff, VolumeX, Sparkles, RotateCcw } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Language detection function
const detectLanguage = (text) => {
  // Simple language detection based on script
  const marathiPattern = /[\u0900-\u097F]/; // Devanagari script
  const englishPattern = /^[a-zA-Z\s.,!?'"()-]+$/;
  
  if (marathiPattern.test(text)) {
    return 'mr'; // Marathi
  } else if (englishPattern.test(text.trim())) {
    return 'en'; // English
  }
  
  // Default to English if uncertain
  return 'en';
};

// Free translation with bidirectional support
const translateWithFreeService = async (text, fromLang = null, toLang = null) => {
  try {
    // Auto-detect language if not provided
    const detectedLang = fromLang || detectLanguage(text);
    const targetLang = toLang || (detectedLang === 'en' ? 'mr' : 'en');
    
    // Using a free translation API (MyMemory)
    const response = await axios.get(`https://api.mymemory.translated.net/get`, {
      params: {
        q: text,
        langpair: `${detectedLang}|${targetLang}`
      }
    });
    
    if (response.data && response.data.responseData && response.data.responseData.translatedText) {
      return {
        translatedText: response.data.responseData.translatedText,
        detectedLanguage: detectedLang,
        targetLanguage: targetLang
      };
    } else {
      throw new Error('Translation failed');
    }
  } catch (error) {
    // Fallback: Bidirectional phrase dictionary
    const englishToMarathi = {
      'hello': 'नमस्कार',
      'how are you': 'तुम्ही कसे आहात',
      'good morning': 'सुप्रभात',
      'good evening': 'शुभ संध्या',
      'thank you': 'धन्यवाद',
      'please': 'कृपया',
      'yes': 'होय',
      'no': 'नाही',
      'sorry': 'माफ करा',
      'excuse me': 'माफ करा',
      'what is your name': 'तुमचे नाव काय आहे',
      'my name is': 'माझे नाव आहे',
      'nice to meet you': 'तुम्हाला भेटून आनंद झाला',
      'goodbye': 'निरोप',
      'see you later': 'पुन्हा भेटू',
      'i love you': 'मी तुझ्यावर प्रेम करतो',
      'how much': 'किती',
      'where is': 'कुठे आहे',
      'what time': 'काय वेळ',
      'today': 'आज',
      'tomorrow': 'उद्या',
      'yesterday': 'काल'
    };
    
    // Create reverse mapping for Marathi to English
    const marathiToEnglish = Object.fromEntries(
      Object.entries(englishToMarathi).map(([en, mr]) => [mr, en])
    );
    
    const lowerText = text.toLowerCase();
    const detectedLang = detectLanguage(text);
    
    if (detectedLang === 'en') {
      for (const [english, marathi] of Object.entries(englishToMarathi)) {
        if (lowerText.includes(english)) {
          return {
            translatedText: marathi,
            detectedLanguage: 'en',
            targetLanguage: 'mr'
          };
        }
      }
    } else {
      for (const [marathi, english] of Object.entries(marathiToEnglish)) {
        if (text.includes(marathi)) {
          return {
            translatedText: english,
            detectedLanguage: 'mr',
            targetLanguage: 'en'
          };
        }
      }
    }
    
    throw new Error('Translation not available. Please check your internet connection.');
  }
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
      recognitionRef.current.lang = 'en-US'; // Will be changed dynamically
      
      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setError('');
      };
      
      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputText(transcript);
        setIsListening(false);
        // Auto-translate after speech recognition
        setTimeout(() => {
          translateText(transcript);
        }, 500);
      };
      
      recognitionRef.current.onerror = (event) => {
        setIsListening(false);
        setError(`Speech recognition error: ${event.error}`);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const startListening = () => {
    if (recognitionRef.current && speechSupported) {
      try {
        // Set recognition language to auto-detect (start with English, can be changed)
        recognitionRef.current.lang = 'en-US';
        recognitionRef.current.start();
      } catch (error) {
        setError('Could not start speech recognition. Please try again.');
      }
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
    
    try {
      // Use free translation service with auto-detection
      const result = await translateWithFreeService(text);
      
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
        timestamp: new Date().toLocaleTimeString()
      };
      setConversationHistory(prev => [newEntry, ...prev.slice(0, 4)]); // Keep last 5 entries
      
      // Auto-speak the translation
      setTimeout(() => {
        speakText(result.translatedText, result.targetLanguage);
      }, 500);
    } catch (err) {
      console.error('Translation error:', err);
      setError('Translation failed. Please try again or check your internet connection.');
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
      
      // Configure voice settings based on language
      if (lang === 'mr') {
        utterance.lang = 'hi-IN'; // Hindi voice for Marathi (closest available)
        utterance.rate = 0.7;
        utterance.pitch = 1.0;
      } else {
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
            Start Talking
          </h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Speak in English or Marathi and get instant translation with voice response
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
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 text-center">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">How to Use</h3>
          <div className="max-w-2xl mx-auto space-y-3 text-gray-700">
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
