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
  const [showWelcome, setShowWelcome] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false); // For floating interface
  const recognitionRef = useRef(null);
  const chatEndRef = useRef(null);

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

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversationHistory]);

  // Toggle floating interface
  const toggleInterface = () => {
    setIsExpanded(!isExpanded);
    if (!isExpanded) {
      setShowWelcome(false);
    }
  };

  return (
    <div className="fixed inset-0 pointer-events-none">
      {/* Floating Interface Container */}
      <div className={`fixed transition-all duration-500 ease-in-out pointer-events-auto ${
        isExpanded 
          ? 'inset-4 md:inset-8' 
          : 'bottom-6 right-6 w-16 h-16'
      }`}>
        
        {/* Expanded Chat Interface */}
        {isExpanded && (
          <div className="w-full h-full bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-gray-200/50 flex flex-col overflow-hidden animate-in fade-in duration-300">
            
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200/50 bg-white/80">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                    <Languages className="w-4 h-4 text-white" />
                  </div>
                  {isListening && (
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl opacity-30 animate-ping"></div>
                  )}
                </div>
                <div>
                  <h1 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    ShabdSetu AI
                  </h1>
                  <p className="text-xs text-gray-500">Real-time translator</p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1 px-2 py-1 bg-green-50 border border-green-200 rounded-full">
                  <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-medium text-green-700">Online</span>
                </div>
                {conversationHistory.length > 0 && (
                  <button
                    onClick={clearAll}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all duration-200"
                    title="Clear conversation"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={toggleInterface}
                  className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all duration-200"
                  title="Minimize"
                >
                  <ArrowRight className="w-4 h-4 rotate-45" />
                </button>
              </div>
            </div>

            {/* Chat Messages Area */}
            <div className="flex-1 overflow-y-auto p-4">
              {/* Welcome Message */}
              {showWelcome && conversationHistory.length === 0 && (
                <div className="text-center space-y-4 py-8">
                  <div className="inline-block">
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl flex items-center justify-center shadow-xl mb-4 mx-auto">
                      <Sparkles className="w-8 h-8 text-white" />
                    </div>
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      Hello! I'm your AI translator
                    </h2>
                    <p className="text-gray-600 max-w-md mx-auto mb-6">
                      Speak in <span className="font-semibold text-blue-600">English</span> or 
                      <span className="font-semibold text-purple-600"> मराठी</span> and I'll translate instantly
                    </p>
                  </div>

                  {/* Quick Suggestions */}
                  <div className="space-y-3 max-w-sm mx-auto">
                    <div className="bg-blue-50 rounded-2xl p-4 border border-blue-200/50">
                      <h3 className="font-semibold text-blue-600 mb-2 text-sm">🇺🇸 Try in English</h3>
                      <div className="space-y-1 text-xs text-gray-600">
                        <p>"Hello, how are you?"</p>
                        <p>"What is your name?"</p>
                        <p>"Thank you very much"</p>
                      </div>
                    </div>
                    <div className="bg-purple-50 rounded-2xl p-4 border border-purple-200/50">
                      <h3 className="font-semibold text-purple-600 mb-2 text-sm">🇮🇳 मराठीत म्हणा</h3>
                      <div className="space-y-1 text-xs text-gray-600">
                        <p>"नमस्कार, तुम्ही कसे आहात?"</p>
                        <p>"तुमचे नाव काय आहे?"</p>
                        <p>"धन्यवाद"</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Conversation Messages */}
              <div className="space-y-4">
                {conversationHistory.map((entry) => (
                  <div key={entry.id} className="space-y-3">
                    {/* User Message */}
                    <div className="flex justify-end">
                      <div className="max-w-[70%]">
                        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
                          <p className="text-sm font-medium mb-1">{entry.input}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-blue-100 bg-white/20 px-2 py-0.5 rounded-full">
                              {getLanguageDisplayName(entry.inputLang)}
                            </span>
                            <span className="text-xs text-blue-100">{entry.timestamp}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* AI Response */}
                    <div className="flex justify-start">
                      <div className="flex items-start gap-2 max-w-[70%]">
                        <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                          <Languages className="w-3 h-3 text-white" />
                        </div>
                        <div className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-200">
                          <p className="text-gray-900 font-medium mb-2 text-sm">{entry.output}</p>
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                              {getLanguageDisplayName(entry.outputLang)}
                            </span>
                            <button
                              onClick={() => speakText(entry.output, entry.outputLang)}
                              className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-all duration-200"
                              title="Speak translation"
                            >
                              <Volume2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Current Input/Translation in Progress */}
                {(inputText || isLoading) && (
                  <div className="space-y-3">
                    {/* User's current input */}
                    {inputText && (
                      <div className="flex justify-end">
                        <div className="max-w-[70%]">
                          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl rounded-br-md px-4 py-3 shadow-lg">
                            <p className="text-sm font-medium mb-1">{inputText}</p>
                            {detectedLanguage && (
                              <span className="text-xs text-blue-100 bg-white/20 px-2 py-0.5 rounded-full">
                                {getLanguageDisplayName(detectedLanguage)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {/* AI thinking/responding */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-start gap-2">
                          <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center shadow-md">
                            <Languages className="w-3 h-3 text-white" />
                          </div>
                          <div className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-200">
                            <div className="flex items-center gap-2">
                              <div className="flex space-x-1">
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                              </div>
                              <span className="text-xs text-gray-500">Translating...</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Current translation result */}
                    {translatedText && !isLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-start gap-2 max-w-[70%]">
                          <div className="w-6 h-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center shadow-md">
                            <Languages className="w-3 h-3 text-white" />
                          </div>
                          <div className="bg-gray-50 rounded-2xl rounded-bl-md px-4 py-3 shadow-sm border border-gray-200">
                            <p className="text-gray-900 font-medium mb-2 text-sm">{translatedText}</p>
                            <div className="flex items-center justify-between gap-2">
                              {targetLanguage && (
                                <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                                  {getLanguageDisplayName(targetLanguage)}
                                </span>
                              )}
                              <div className="flex items-center gap-1">
                                <button
                                  onClick={() => speakText(translatedText, targetLanguage)}
                                  className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-all duration-200"
                                  title="Speak translation"
                                >
                                  <Volume2 className="w-3 h-3" />
                                </button>
                                <button
                                  onClick={() => navigator.clipboard.writeText(translatedText)}
                                  className="p-1 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-md transition-all duration-200"
                                  title="Copy translation"
                                >
                                  <Copy className="w-3 h-3" />
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  <div className="flex justify-start">
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center shadow-md">
                        <span className="text-white text-xs">⚠️</span>
                      </div>
                      <div className="bg-red-50 border border-red-200 rounded-2xl rounded-bl-md px-4 py-3 max-w-[70%]">
                        <p className="text-red-800 text-sm font-medium mb-1">Sorry, I encountered an issue</p>
                        <p className="text-red-600 text-xs">{error}</p>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>
            </div>

            {/* Input Area */}
            <div className="flex-shrink-0 bg-white/90 backdrop-blur-xl border-t border-gray-200/50 p-4">
              {/* Speech support warning */}
              {!speechSupported && (
                <div className="mb-3 p-2 bg-amber-50 border border-amber-200 rounded-xl text-center">
                  <p className="text-amber-800 text-xs">
                    ⚠️ Voice recognition not supported. Please use Chrome, Edge, or Safari.
                  </p>
                </div>
              )}

              {/* Voice Control */}
              <div className="flex items-center justify-center gap-4">
                {/* Language Indicator */}
                {(detectedLanguage || isListening) && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-gray-100 rounded-full">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                    <span className="text-xs font-medium text-gray-700">
                      {isListening ? 'Listening...' : getLanguageDisplayName(detectedLanguage)}
                    </span>
                  </div>
                )}

                {/* Main Voice Button */}
                <div className="relative">
                  <button
                    onClick={isListening ? stopListening : startListening}
                    onMouseDown={() => setShowWelcome(false)}
                    disabled={!speechSupported || isLoading}
                    className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shadow-lg ${
                      isListening 
                        ? 'bg-gradient-to-r from-red-500 to-pink-500 scale-110' 
                        : isSpeaking
                        ? 'bg-gradient-to-r from-orange-500 to-amber-500 scale-105 animate-pulse'
                        : isLoading
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500'
                        : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:scale-105 hover:shadow-xl'
                    } text-white disabled:opacity-50 disabled:cursor-not-allowed group`}
                    title={isListening ? 'Stop listening' : 'Start speaking'}
                  >
                    {isListening ? (
                      <div className="flex items-center justify-center">
                        <div className="w-3 h-3 bg-white rounded-sm"></div>
                      </div>
                    ) : isSpeaking ? (
                      <Volume2 className="w-5 h-5" />
                    ) : isLoading ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                      <Mic className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
                    )}
                    
                    {/* Animated Ring for Active States */}
                    {(isListening || isSpeaking) && (
                      <div className="absolute inset-0 rounded-full border-2 border-white/30 animate-ping"></div>
                    )}
                  </button>
                  
                  {/* Ripple Effect */}
                  {isListening && (
                    <div className="absolute inset-0 rounded-full bg-red-400/20 animate-ping"></div>
                  )}
                </div>

                {/* Stop Speaking Button */}
                {isSpeaking && (
                  <button
                    onClick={stopSpeaking}
                    className="p-2 bg-gray-100 hover:bg-gray-200 rounded-full transition-all duration-200"
                    title="Stop speaking"
                  >
                    <VolumeX className="w-4 h-4 text-gray-600" />
                  </button>
                )}
              </div>

              {/* Status Text */}
              <div className="text-center mt-2">
                {isListening && (
                  <p className="text-red-600 font-medium animate-pulse text-xs">🎤 Listening...</p>
                )}
                {isSpeaking && (
                  <p className="text-orange-600 font-medium animate-pulse text-xs">🔊 Speaking...</p>
                )}
                {isLoading && (
                  <p className="text-blue-600 font-medium text-xs">🤖 Processing...</p>
                )}
                {!isListening && !isSpeaking && !isLoading && (
                  <p className="text-gray-500 text-xs">
                    {conversationHistory.length === 0 ? 'Tap the mic to start' : 'Tap to continue'}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Floating Button (when collapsed) */}
        {!isExpanded && (
          <div className="relative group">
            <button
              onClick={toggleInterface}
              className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-2xl flex items-center justify-center text-white hover:scale-110 transition-all duration-300 group-hover:shadow-[0_0_30px_rgba(99,102,241,0.5)]"
              title="Open ShabdSetu AI Translator"
            >
              {isListening ? (
                <div className="relative">
                  <Mic className="w-8 h-8 animate-pulse" />
                  <div className="absolute inset-0 rounded-full border-4 border-white/30 animate-ping"></div>
                </div>
              ) : isSpeaking ? (
                <Volume2 className="w-8 h-8 animate-pulse" />
              ) : (
                <Languages className="w-8 h-8 group-hover:rotate-12 transition-transform duration-300" />
              )}
            </button>
            
            {/* Floating Badge */}
            {conversationHistory.length > 0 && (
              <div className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center text-xs font-bold shadow-lg animate-bounce">
                {conversationHistory.length}
              </div>
            )}
            
            {/* Tooltip */}
            <div className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-gray-900 text-white text-sm px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 whitespace-nowrap pointer-events-none">
              ShabdSetu AI Translator
              <div className="absolute left-full top-1/2 -translate-y-1/2 border-4 border-transparent border-l-gray-900"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
