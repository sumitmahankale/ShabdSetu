import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, Languages, Sun, Moon } from 'lucide-react';

function App() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [translatedText, setTranslatedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [waterScale, setWaterScale] = useState(1);
  const [ripples, setRipples] = useState([]);
  const [originalText, setOriginalText] = useState('');
  const recognitionRef = useRef(null);
  const recognitionResolveRef = useRef(null);
  const [detectedSource, setDetectedSource] = useState('');
  const [translationMethod, setTranslationMethod] = useState('');
  const attemptingLangsRef = useRef([]);
  const [theme, setTheme] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') || 'dark';
    }
    return 'dark';
  });
  const [attempts, setAttempts] = useState([]);
  const [languageMode, setLanguageMode] = useState('en'); // 'en' or 'mr' (removed 'auto')

  // Romanized Marathi clue words (subset of backend list)
  const romanMrClues = ['namaskar','majha','majhe','maza','nav','sumit','tumhi','kase','kasa','dhanyavad','dhanyawad','dhanyabad','pani','madat','aaj','udya','kal','sakal','ratri'];

  const detectSource = (text) => {
    const hasDev = /[\u0900-\u097F]/.test(text);
    if (hasDev) return 'mr';
    const words = text.toLowerCase().match(/[a-z']+/g) || [];
    const hits = words.filter(w => romanMrClues.includes(w)).length;
    if (hits && hits >= Math.max(1, Math.floor(words.length/3))) return 'mr';
    return 'en';
  };

  const translateText = async (text, forcedSrc) => {
    setIsLoading(true);
    try {
      // Determine source based on mode (only 'en' or 'mr')
      let srcLang = languageMode;
      
      const hasDevanagari = /[\u0900-\u097F]/.test(text);
      const source_language = (languageMode === 'mr' || hasDevanagari) ? 'Marathi' : 'English';
      const target_language = (languageMode === 'mr' || hasDevanagari) ? 'English' : 'Marathi';
      
      const response = await fetch(`http://localhost:8003/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, source_language, target_language })
      });
      const data = await response.json();
      setTranslatedText(data.translated_text);
      setDetectedSource(data.source_language || '');
      setTranslationMethod(data.translation_method || '');
      setAttempts(data.attempts || []);
      const tgtLangFinal = (data.target_language || (data.source_language === 'mr' ? 'en' : 'mr'));
      
      // Always speak the translated text if translation was successful
      console.log('Translation result:', {
        original: text,
        translated: data.translated_text,
        source: data.source_language,
        target: tgtLangFinal,
        method: data.translation_method
      });
      
      if (data.translated_text && !data.translated_text.includes('Translation unavailable')) {
        speakText(data.translated_text, tgtLangFinal);
      }
      return data.translation_method || '';
    } catch (e) {
      console.error('Translation error', e);
      setTranslatedText('Translation failed.');
      return '';
    } finally {
      setIsLoading(false);
    }
  };

  // Apply theme class to html root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') root.classList.add('dark'); else root.classList.remove('dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');
  
  // Initialize speech recognition
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;

    rec.onstart = () => {
      setIsListening(true);
      setWaterScale(0.8);
      createRipple();
    };
    rec.onend = () => {
      setIsListening(false);
      setWaterScale(1);
      if (recognitionResolveRef.current) {
        recognitionResolveRef.current('');
        recognitionResolveRef.current = null;
      }
    };
    rec.onerror = (e) => {
      console.warn('Speech recognition error', e);
      if (recognitionResolveRef.current) {
        recognitionResolveRef.current('');
        recognitionResolveRef.current = null;
      }
    };
    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (recognitionResolveRef.current) {
        recognitionResolveRef.current(transcript);
        recognitionResolveRef.current = null;
      }
    };
    recognitionRef.current = rec;
  }, []);

  // Create ripple effect
  const createRipple = () => {
    const id = Date.now();
    setRipples(prev => [...prev, id]);
    setTimeout(() => {
      setRipples(prev => prev.filter(rippleId => rippleId !== id));
    }, 2000);
  };

  // (Removed old translateText implementation)

  // Text to speech with voice availability check
  const speakText = (text, targetLang = 'mr') => {
    if (!('speechSynthesis' in window) || !text) {
      console.warn('Speech synthesis not supported or no text');
      return;
    }
    
    speechSynthesis.cancel();
    setIsSpeaking(true);
    
    // Wait for voices to be loaded
    const speak = () => {
      const utterance = new SpeechSynthesisUtterance(text);
      
      if (targetLang === 'mr') {
        utterance.lang = 'mr-IN';
        utterance.rate = 0.85;
        
        // Try to find a Marathi voice, fallback to Hindi or default
        const voices = speechSynthesis.getVoices();
        console.log('Available voices:', voices.map(v => `${v.name} (${v.lang})`));
        
        const marathiVoice = voices.find(v => v.lang.startsWith('mr'));
        const hindiVoice = voices.find(v => v.lang.startsWith('hi'));
        const englishVoice = voices.find(v => v.lang.startsWith('en'));
        
        if (marathiVoice) {
          utterance.voice = marathiVoice;
          console.log('Using Marathi voice:', marathiVoice.name);
        } else if (hindiVoice) {
          utterance.voice = hindiVoice;
          utterance.lang = 'hi-IN';
          console.log('Using Hindi voice (fallback):', hindiVoice.name);
        } else if (englishVoice) {
          utterance.voice = englishVoice;
          utterance.lang = 'en-IN';
          console.log('Using English-India voice (fallback):', englishVoice.name);
        } else {
          console.warn('No suitable voice found for Marathi, using default');
        }
      } else {
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        
        // Select English voice
        const voices = speechSynthesis.getVoices();
        const englishVoice = voices.find(v => v.lang.startsWith('en'));
        if (englishVoice) {
          utterance.voice = englishVoice;
          console.log('Using English voice:', englishVoice.name);
        }
      }
      
      utterance.volume = 1.0; // Increased volume
      utterance.pitch = 1.0;
      
      utterance.onstart = () => {
        console.log('Speech started:', text);
      };
      
      utterance.onend = () => {
        setIsSpeaking(false);
        console.log('Speech synthesis completed');
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
      };
      
      console.log(`Speaking: "${text}" in language: ${utterance.lang}`);
      speechSynthesis.speak(utterance);
    };
    
    // Ensure voices are loaded
    if (speechSynthesis.getVoices().length > 0) {
      speak();
    } else {
      speechSynthesis.onvoiceschanged = () => {
        speak();
      };
    }
  };

  const recognizeOnce = (lang) => new Promise((resolve) => {
    if (!recognitionRef.current) return resolve('');
    recognitionResolveRef.current = resolve;
    try {
      recognitionRef.current.lang = lang;
      recognitionRef.current.start();
    } catch (e) {
      console.warn('Failed to start recognition for', lang, e);
      resolve('');
    }
  });

  // Try Marathi first (captures Devanagari & romanized Marathi), then fallback to English.
  const languageAttempts = ['mr-IN','en-US'];

  const startListening = async () => {
    if (!recognitionRef.current || isListening) return;
    attemptingLangsRef.current = [...languageAttempts];
    setTranslatedText('');
    setDetectedSource('');
    setTranslationMethod('');
    setOriginalText('');
    
    // Use recognition based on language mode (no auto mode)
    let recognitionLang = languageMode === 'mr' ? 'mr-IN' : 'en-US';
    
    // Single recognition for the selected language mode
    const transcript = await recognizeOnce(recognitionLang);
    if (!transcript) return;
    setOriginalText(transcript);
    await translateText(transcript, languageMode);
  };

  const cycleLanguageMode = () => {
    // Toggle between English and Marathi only
    setLanguageMode(mode => mode === 'en' ? 'mr' : 'en');
  };

  const getLanguageModeLabel = () => {
    if (languageMode === 'en') return '🇬🇧 English';
    return '🇮🇳 मराठी';
  };

  const gradientClass = theme === 'dark'
    ? 'bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900'
    : 'bg-gradient-to-br from-amber-50 via-orange-100 to-pink-100';

  const bubbleColors = theme === 'dark'
    ? ['bg-blue-400', 'bg-cyan-400', 'bg-teal-400', 'bg-purple-400']
    : ['bg-yellow-300', 'bg-orange-300', 'bg-pink-300', 'bg-rose-300'];

  const orbGradient = theme === 'dark'
    ? 'from-cyan-300 via-blue-400 to-blue-600'
    : 'from-amber-300 via-orange-400 to-pink-500';

  const shadowColor = theme === 'dark' ? 'shadow-blue-500/50' : 'shadow-orange-400/50';
  const hoverShadow = theme === 'dark' ? 'hover:shadow-blue-400/70' : 'hover:shadow-orange-500/70';

  return (
    <div className={`min-h-screen ${gradientClass} flex items-center justify-center relative overflow-hidden transition-all duration-700 ease-in-out`}>
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(12)].map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full opacity-30"
            style={{
              width: `${Math.random() * 60 + 20}px`,
              height: `${Math.random() * 60 + 20}px`,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              backgroundColor: theme === 'dark' 
                ? `hsl(${200 + Math.random() * 60}, 70%, 60%)`
                : `hsl(${30 + Math.random() * 60}, 80%, 70%)`,
              animation: `floatParticle ${3 + Math.random() * 4}s ease-in-out infinite`,
              animationDelay: `${Math.random() * 5}s`
            }}
          />
        ))}
      </div>

      {/* Background water effect */}
      <div className="absolute inset-0 opacity-25">
        {bubbleColors.map((color, i) => (
          <div
            key={i}
            className={`absolute w-96 h-96 ${color} rounded-full mix-blend-multiply filter blur-xl animate-pulse`}
            style={{
              left: `${25 + (i * 25)}%`,
              top: `${25 + (i % 2) * 50}%`,
              animationDelay: `${i * 2}s`,
              transform: `translate(-50%, -50%)`
            }}
          />
        ))}
      </div>

      {/* Magical theme toggle */}
      <button
        onClick={toggleTheme}
        className={`absolute top-6 right-6 z-20 group p-3 rounded-full transition-all duration-500 transform hover:scale-110 hover:rotate-12 ${
          theme === 'dark' 
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 shadow-lg shadow-blue-500/30' 
            : 'bg-gradient-to-r from-yellow-400 to-orange-500 shadow-lg shadow-orange-400/40'
        }`}
        aria-label="Toggle theme"
      >
        <div className="relative overflow-hidden">
          {theme === 'dark' ? (
            <Sun className="w-6 h-6 text-yellow-200 group-hover:animate-spin transition-transform duration-300" />
          ) : (
            <Moon className="w-6 h-6 text-purple-100 group-hover:animate-bounce transition-transform duration-300" />
          )}
          <div className={`absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
            theme === 'dark' ? 'bg-yellow-300/20' : 'bg-purple-300/20'
          }`} />
        </div>
      </button>

      {/* Language mode toggle */}
      <button
        onClick={cycleLanguageMode}
        className={`absolute top-6 left-6 z-20 group px-4 py-2 rounded-full transition-all duration-500 transform hover:scale-105 ${
          theme === 'dark' 
            ? 'bg-gradient-to-r from-cyan-600 to-blue-600 shadow-lg shadow-cyan-500/30' 
            : 'bg-gradient-to-r from-pink-400 to-rose-500 shadow-lg shadow-pink-400/40'
        }`}
        aria-label="Cycle language mode"
      >
        <div className="relative overflow-hidden flex items-center gap-2">
          <Languages className={`w-5 h-5 transition-transform duration-300 group-hover:rotate-12 ${
            theme === 'dark' ? 'text-cyan-100' : 'text-white'
          }`} />
          <span className={`text-sm font-semibold ${theme === 'dark' ? 'text-cyan-50' : 'text-white'}`}>
            {getLanguageModeLabel()}
          </span>
          <div className={`absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
            theme === 'dark' ? 'bg-cyan-300/20' : 'bg-pink-300/20'
          }`} />
        </div>
      </button>

      {/* Main water orb */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Water orb container */}
        <div 
          className={`relative transition-transform duration-300 ease-out ${
            isListening ? 'animate-pulse' : ''
          }`}
          style={{ transform: `scale(${waterScale})` }}
        >
          {/* Ripple effects */}
          {ripples.map((id) => (
            <div
              key={id}
              className={`absolute inset-0 border-2 rounded-full animate-ping transition-colors duration-300 ${
                theme === 'dark' ? 'border-white/30' : 'border-orange-400/40'
              }`}
              style={{
                width: '300px',
                height: '300px',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)'
              }}
            />
          ))}
          
          {/* Main water orb */}
          <div
            className={`w-80 h-80 rounded-full bg-gradient-to-br ${orbGradient} 
              shadow-2xl ${shadowColor} relative overflow-hidden cursor-pointer
              transition-all duration-500 ${hoverShadow} hover:scale-105 group
              ${isLoading ? 'animate-spin' : ''}
              ${isSpeaking ? 'animate-bounce' : ''}`}
            onClick={startListening}
          >
            {/* Dynamic glow effect */}
            <div className={`absolute inset-0 rounded-full transition-opacity duration-300 ${
              theme === 'dark' 
                ? 'bg-gradient-to-t from-blue-600/20 via-cyan-400/10 to-white/30' 
                : 'bg-gradient-to-t from-orange-400/20 via-yellow-300/10 to-white/40'
            }`} />
            
            {/* Floating bubbles */}
            <div className="absolute inset-0">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className={`absolute rounded-full transition-colors duration-500 ${
                    theme === 'dark' ? 'bg-white/20' : 'bg-white/40'
                  }`}
                  style={{
                    width: `${Math.random() * 20 + 10}px`,
                    height: `${Math.random() * 20 + 10}px`,
                    left: `${Math.random() * 80 + 10}%`,
                    top: `${Math.random() * 80 + 10}%`,
                    animation: `float ${Math.random() * 3 + 2}s ease-in-out infinite`,
                    animationDelay: `${Math.random() * 3}s`
                  }}
                />
              ))}
            </div>

            {/* Magical sparkles */}
            {isListening && (
              <div className="absolute inset-0 pointer-events-none">
                {[...Array(6)].map((_, i) => (
                  <div
                    key={i}
                    className={`absolute w-2 h-2 rounded-full animate-ping ${
                      theme === 'dark' ? 'bg-cyan-300' : 'bg-yellow-400'
                    }`}
                    style={{
                      left: `${20 + Math.random() * 60}%`,
                      top: `${20 + Math.random() * 60}%`,
                      animationDelay: `${i * 0.1}s`
                    }}
                  />
                ))}
              </div>
            )}

            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
              {isListening ? (
                <MicOff className={`w-16 h-16 animate-pulse transition-colors duration-300 ${
                  theme === 'dark' ? 'text-cyan-100' : 'text-orange-100'
                }`} />
              ) : isSpeaking ? (
                <Volume2 className={`w-16 h-16 animate-bounce transition-colors duration-300 ${
                  theme === 'dark' ? 'text-blue-100' : 'text-pink-100'
                }`} />
              ) : isLoading ? (
                <Languages className={`w-16 h-16 animate-spin transition-colors duration-300 ${
                  theme === 'dark' ? 'text-purple-100' : 'text-amber-100'
                }`} />
              ) : (
                <Mic className="w-16 h-16 text-white transition-colors duration-300" />
              )}
            </div>
          </div>
        </div>

        {/* Status text */}
        <div className="mt-8 text-center">
          <h1 className={`text-4xl font-bold mb-4 bg-gradient-to-r bg-clip-text text-transparent transition-all duration-500 ${
            theme === 'dark' 
              ? 'from-cyan-300 to-blue-300' 
              : 'from-orange-500 to-pink-500'
          }`}>
            ShabdSetu
          </h1>
          <p className={`text-lg mb-2 transition-colors duration-300 ${
            theme === 'dark' ? 'text-white/80' : 'text-gray-700'
          }`}>
            {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : isLoading ? 'Translating...' : 'Tap the orb to speak'}
          </p>
          <p className={`text-sm mb-4 transition-colors duration-300 ${theme === 'dark' ? 'text-white/70' : 'text-gray-600'}`}>
            Mode: {getLanguageModeLabel()} → {languageMode === 'en' ? 'Marathi' : 'English'}
          </p>
          
          {/* Translated text display */}
          {translatedText && (
            <div className={`backdrop-blur-lg rounded-2xl p-6 mt-6 max-w-md mx-auto border transition-all duration-500 transform animate-fadeIn ${
              theme === 'dark'
                ? 'bg-white/10 border-white/20 shadow-lg shadow-blue-500/10'
                : 'bg-white/80 border-orange-200/50 shadow-lg shadow-orange-300/20'
            }`}>
              {originalText && (
                <p className={`text-sm mb-2 italic ${theme === 'dark' ? 'text-white/60' : 'text-gray-600'}`}>You said: {originalText}</p>
              )}
              <p className={`text-xl font-medium leading-relaxed transition-colors duration-300 ${
                theme === 'dark' ? 'text-white' : 'text-gray-800'
              }`}>
                {translatedText}
              </p>
                {attempts.length > 0 && (
                  <div className="mt-4 text-xs font-mono max-h-32 overflow-auto opacity-70 text-left whitespace-pre-wrap break-all">
                    {attempts.map((a,i)=>(<div key={i}>{a}</div>))}
                  </div>
                )}
            </div>
          )}
        </div>
      </div>

      {/* Enhanced animations */}
  <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.7; }
          50% { transform: translateY(-20px) rotate(180deg); opacity: 1; }
        }
        @keyframes floatParticle {
          0%, 100% { transform: translateY(0px) translateX(0px); }
          33% { transform: translateY(-30px) translateX(10px); }
          66% { transform: translateY(-10px) translateX(-15px); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0px); }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out;
        }
  `}</style>
    </div>
  );
}

export default App;
