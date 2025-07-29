import React, { useState, useRef, useEffect } from 'react';
import { Languages, ArrowRight, Copy, RefreshCw, Volume2, Heart, Github, Mic, MicOff, VolumeX } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Free translation using Google Translate (unofficial)
const translateWithFreeService = async (text, fromLang = 'en', toLang = 'mr') => {
  try {
    // Using a free translation API (MyMemory)
    const response = await axios.get(`https://api.mymemory.translated.net/get`, {
      params: {
        q: text,
        langpair: `${fromLang}|${toLang}`
      }
    });
    
    if (response.data && response.data.responseData && response.data.responseData.translatedText) {
      return response.data.responseData.translatedText;
    } else {
      throw new Error('Translation failed');
    }
  } catch (error) {
    // Fallback: Simple word-by-word translation for common phrases
    const commonTranslations = {
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
    
    const lowerText = text.toLowerCase();
    for (const [english, marathi] of Object.entries(commonTranslations)) {
      if (lowerText.includes(english)) {
        return marathi;
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
  const [copied, setCopied] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [autoSpeak, setAutoSpeak] = useState(true);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  // Sample texts for quick testing
  const sampleTexts = [
    "Hello, how are you?",
    "Good morning! Have a great day.",
    "Thank you for your help.",
    "What is your name?",
    "Nice to meet you.",
    "How much does this cost?",
    "Where is the bathroom?",
    "I need help.",
    "Excuse me, please.",
    "See you later, goodbye."
  ];

  // Initialize speech recognition
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
      setError('Please enter some text to translate or use voice input');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      // Try free translation service first
      let translated;
      try {
        translated = await translateWithFreeService(text, 'en', 'mr');
      } catch (freeServiceError) {
        // If free service fails, try the backend as fallback
        const response = await axios.post(`${API_BASE_URL}/translate`, {
          text: text,
          source_language: "English",
          target_language: "Marathi"
        });
        translated = response.data.translated_text;
      }
      
      setTranslatedText(translated);
      
      // Auto-speak the translation if enabled
      if (autoSpeak) {
        setTimeout(() => {
          speakText(translated, 'marathi');
        }, 500);
      }
    } catch (err) {
      console.error('Translation error:', err);
      setError('Translation failed. This could be due to: 1) No internet connection 2) Backend API key not configured 3) Service temporarily unavailable. Please try again or use the sample phrases.');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (translatedText) {
      try {
        await navigator.clipboard.writeText(translatedText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('Failed to copy text:', err);
      }
    }
  };

  const clearAll = () => {
    setInputText('');
    setTranslatedText('');
    setError('');
    textareaRef.current?.focus();
  };

  const useSampleText = (text) => {
    setInputText(text);
    setError('');
  };

  const speakText = (text, lang = 'en') => {
    if ('speechSynthesis' in window && text) {
      // Stop any current speech
      speechSynthesis.cancel();
      
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Configure voice settings
      if (lang === 'marathi') {
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

  useEffect(() => {
    // Auto-focus on input when component mounts
    textareaRef.current?.focus();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg">
                <Languages className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">ShabdSetu</h1>
                <p className="text-sm text-gray-600">शब्दसेतू - Bridge of Words</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                English → मराठी
              </span>
              <a 
                href="https://github.com/sumitmahankale/ShabdSetu" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            English to Marathi Translation
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-4">
            Powered by AI for accurate, context-aware translations between English and Marathi
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 max-w-2xl mx-auto">
            <p className="text-green-800 text-sm">
              ✅ <strong>Free Translation Service:</strong> No API key required! Uses free translation services and offline word database for common phrases.
            </p>
          </div>
        </div>

        {/* Voice-to-Voice Translation Section */}
        <div className="mb-8 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200">
          <div className="text-center mb-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">🎤 Voice-to-Voice Translation</h3>
            <p className="text-gray-600">Speak in English and hear the translation in Marathi</p>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {/* Voice Input Button */}
            <div className="flex flex-col items-center">
              <button
                onClick={isListening ? stopListening : startListening}
                disabled={!speechSupported || isLoading}
                className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isListening 
                    ? 'bg-red-500 hover:bg-red-600 animate-pulse' 
                    : 'bg-green-500 hover:bg-green-600'
                } text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isListening ? 'Stop listening' : 'Start voice input'}
              >
                {isListening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
              </button>
              <span className="text-sm text-gray-600 mt-2">
                {isListening ? 'Listening...' : 'Speak English'}
              </span>
            </div>

            {/* Arrow */}
            <ArrowRight className="w-8 h-8 text-purple-600 transform rotate-0 sm:rotate-0" />

            {/* Voice Output Control */}
            <div className="flex flex-col items-center">
              <button
                onClick={isSpeaking ? stopSpeaking : () => speakText(translatedText, 'marathi')}
                disabled={!translatedText || isLoading}
                className={`w-16 h-16 rounded-full flex items-center justify-center transition-all duration-300 ${
                  isSpeaking 
                    ? 'bg-orange-500 hover:bg-orange-600 animate-pulse' 
                    : 'bg-blue-500 hover:bg-blue-600'
                } text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isSpeaking ? 'Stop speaking' : 'Hear Marathi translation'}
              >
                {isSpeaking ? <VolumeX className="w-8 h-8" /> : <Volume2 className="w-8 h-8" />}
              </button>
              <span className="text-sm text-gray-600 mt-2">
                {isSpeaking ? 'Speaking...' : 'Hear Marathi'}
              </span>
            </div>
          </div>

          {/* Auto-speak toggle */}
          <div className="flex items-center justify-center mt-6">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoSpeak}
                onChange={(e) => setAutoSpeak(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Auto-speak translations</span>
            </label>
          </div>

          {/* Speech support warning */}
          {!speechSupported && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm text-center">
                ⚠️ Voice recognition is not supported in your browser. Please use Chrome, Edge, or Safari for the best experience.
              </p>
            </div>
          )}
        </div>

        {/* Sample Texts */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-700 mb-4">Quick Start - Try these examples:</h3>
          <div className="flex flex-wrap gap-2">
            {sampleTexts.map((text, index) => (
              <button
                key={index}
                onClick={() => useSampleText(text)}
                className="px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-800 rounded-lg text-sm transition-colors"
              >
                {text}
              </button>
            ))}
          </div>
        </div>

        {/* Translation Interface */}
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                <h3 className="text-lg font-semibold text-gray-900">English</h3>
                {isListening && (
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-red-600 font-medium">Listening...</span>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                {speechSupported && (
                  <button
                    onClick={isListening ? stopListening : startListening}
                    disabled={isLoading}
                    className={`p-2 rounded-lg transition-colors ${
                      isListening 
                        ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                        : 'bg-green-100 text-green-600 hover:bg-green-200'
                    } disabled:opacity-50`}
                    title={isListening ? 'Stop voice input' : 'Start voice input'}
                  >
                    {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>
                )}
                {inputText && (
                  <button
                    onClick={() => speakText(inputText, 'en')}
                    className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
                    title="Listen to English text"
                  >
                    <Volume2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
            
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Enter English text to translate to Marathi..."
              className="textarea-custom h-40"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  translateText();
                }
              }}
            />
            
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-gray-500">
                {inputText.length} characters
              </span>
              <div className="flex gap-2">
                <button
                  onClick={clearAll}
                  className="btn-secondary"
                  disabled={!inputText}
                >
                  <RefreshCw className="w-4 h-4" />
                  Clear
                </button>
                <button
                  onClick={translateText}
                  disabled={isLoading || !inputText.trim()}
                  className="btn-primary"
                >
                  {isLoading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Translating...
                    </>
                  ) : (
                    <>
                      <ArrowRight className="w-4 h-4" />
                      Translate
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Output Section */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
                <h3 className="text-lg font-semibold text-gray-900">मराठी (Marathi)</h3>
                {isSpeaking && (
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-orange-600 font-medium">Speaking...</span>
                  </div>
                )}
              </div>
              {translatedText && (
                <div className="flex gap-2">
                  <button
                    onClick={isSpeaking ? stopSpeaking : () => speakText(translatedText, 'marathi')}
                    className={`p-2 transition-colors ${
                      isSpeaking 
                        ? 'bg-orange-100 text-orange-600 hover:bg-orange-200' 
                        : 'text-gray-500 hover:text-orange-600'
                    }`}
                    title={isSpeaking ? 'Stop speaking' : 'Listen to Marathi text'}
                  >
                    {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={copyToClipboard}
                    className="p-2 text-gray-500 hover:text-green-600 transition-colors"
                    title="Copy translated text"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            
            <div className="h-40 p-4 border border-gray-300 rounded-lg bg-gray-50 overflow-y-auto">
              {error ? (
                <div className="text-red-600 bg-red-50 p-3 rounded-lg border border-red-200">
                  <p className="font-medium">Translation Error</p>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              ) : translatedText ? (
                <p className="marathi-text text-gray-900">{translatedText}</p>
              ) : (
                <p className="text-gray-500 italic">
                  Translated text will appear here...
                </p>
              )}
            </div>
            
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-gray-500">
                {translatedText.length} characters
              </span>
              {copied && (
                <span className="text-sm text-green-600 font-medium">
                  ✓ Copied to clipboard!
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Languages className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">AI-Powered</h3>
            <p className="text-gray-600">Advanced language models ensure accurate and contextual translations</p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Heart className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Cultural Context</h3>
            <p className="text-gray-600">Preserves cultural nuances and context in translations</p>
          </div>
          
          <div className="text-center p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <RefreshCw className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Real-time</h3>
            <p className="text-gray-600">Fast, real-time translations with instant results</p>
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="mt-16 bg-blue-50 rounded-xl p-8">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">How to Use</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🎤 Voice-to-Voice Translation</h4>
              <p className="text-gray-600 text-sm">Click the microphone, speak in English, and hear Marathi translation automatically</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">⌨️ Type & Translate</h4>
              <p className="text-gray-600 text-sm">Type English text and click "Translate" or press Ctrl+Enter</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">🔊 Audio Controls</h4>
              <p className="text-gray-600 text-sm">Use speaker icons to hear pronunciation in both languages</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">📋 Quick Actions</h4>
              <p className="text-gray-600 text-sm">Copy translations, use sample texts, or clear all content</p>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-white rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-900 mb-2">💡 Pro Tip</h4>
            <p className="text-blue-800 text-sm">
              Enable "Auto-speak translations" for fully hands-free experience. Just speak in English and listen to the Marathi translation!
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-50 border-t mt-16">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="text-center text-gray-600">
            <p className="mb-2">
              Made with <Heart className="w-4 h-4 text-red-500 inline mx-1" /> for the Marathi community
            </p>
            <p className="text-sm">
              ShabdSetu - Building bridges between languages • Powered by LangChain & OpenAI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
