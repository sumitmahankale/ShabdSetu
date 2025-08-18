import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, Languages } from 'lucide-react';

function App() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [translatedText, setTranslatedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [waterScale, setWaterScale] = useState(1);
  const [ripples, setRipples] = useState([]);
  const recognitionRef = useRef(null);
  const recognitionResolveRef = useRef(null);
  const [detectedSource, setDetectedSource] = useState('');
  const [translationMethod, setTranslationMethod] = useState('');
  const attemptingLangsRef = useRef([]);
  
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
      // If ended without a result and we are in multi-attempt mode, trigger next
      if (recognitionResolveRef.current) {
        recognitionResolveRef.current(''); // resolve empty to continue flow
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

  // Translation function
  const translateText = async (text) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8003/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          text, 
          source_language: 'auto',
          target_language: 'auto' 
        })
      });
  const data = await response.json();
  setTranslatedText(data.translated_text);
  setDetectedSource(data.source_language || '');
  setTranslationMethod(data.translation_method || '');
      
      // Only speak if translation was successful and not a fallback message
      if (data.translated_text && !data.translated_text.includes('Translation not available')) {
        speakText(data.translated_text, data.target_language);
      }
    } catch (error) {
      console.error('Translation error:', error);
      setTranslatedText('Translation failed. Please try again.');
    }
    setIsLoading(false);
  };

  // Text to speech
  const speakText = (text, targetLang = 'mr') => {
    if ('speechSynthesis' in window && text) {
      // Stop any current speech
      speechSynthesis.cancel();
      
      setIsSpeaking(true);
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Set language based on target language
      if (targetLang === 'mr') {
        // Attempt Marathi locale; if unsupported browser may fallback automatically
        utterance.lang = 'mr-IN';
        utterance.rate = 0.85; // Slightly slower for clarity
      } else {
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
      }
      
      utterance.volume = 0.8;
      utterance.pitch = 1.0;
      
      utterance.onend = () => {
        setIsSpeaking(false);
        console.log('Speech synthesis completed');
      };
      
      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event);
        setIsSpeaking(false);
        
        // Fallback: try with different language
  // No Hindi fallback – only English if Marathi completely fails can be added explicitly by user
      };
      
      console.log(`Speaking: "${text}" in language: ${utterance.lang}`);
      speechSynthesis.speak(utterance);
    } else {
      console.warn('Speech synthesis not supported');
      setIsSpeaking(false);
    }
  };

  // Helper: single recognition attempt for one language returning transcript
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

  const languageAttempts = ['mr-IN','en-US'];

  const startListening = async () => {
    if (!recognitionRef.current || isListening) return;
    attemptingLangsRef.current = [...languageAttempts];
    setTranslatedText('');
    setDetectedSource('');
    setTranslationMethod('');
    for (const lang of languageAttempts) {
      const transcript = await recognizeOnce(lang);
      if (!transcript) continue; // try next
      await translateText(transcript);
      // Break if not fallback (avoid stale state by checking last translationMethod via ref after small delay)
      if (translationMethod !== 'fallback') break;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-blue-800 to-indigo-900 flex items-center justify-center relative overflow-hidden">
      {/* Background water effect */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-cyan-400 rounded-full mix-blend-multiply filter blur-xl animate-pulse" style={{animationDelay: '2s'}}></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-teal-400 rounded-full mix-blend-multiply filter blur-xl animate-pulse" style={{animationDelay: '4s'}}></div>
      </div>

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
              className="absolute inset-0 border-2 border-white/30 rounded-full animate-ping"
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
            className={`w-80 h-80 rounded-full bg-gradient-to-br from-cyan-300 via-blue-400 to-blue-600 
              shadow-2xl shadow-blue-500/50 relative overflow-hidden cursor-pointer
              transition-all duration-300 hover:shadow-blue-400/70 hover:scale-105
              ${isLoading ? 'animate-spin' : ''}
              ${isSpeaking ? 'animate-bounce' : ''}`}
            onClick={startListening}
          >
            {/* Water surface effect */}
            <div className="absolute inset-0 bg-gradient-to-t from-transparent via-white/10 to-white/30 rounded-full"></div>
            
            {/* Floating bubbles */}
            <div className="absolute inset-0">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className="absolute bg-white/20 rounded-full"
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

            {/* Center icon */}
            <div className="absolute inset-0 flex items-center justify-center">
              {isListening ? (
                <MicOff className="w-16 h-16 text-white animate-pulse" />
              ) : isSpeaking ? (
                <Volume2 className="w-16 h-16 text-white animate-bounce" />
              ) : isLoading ? (
                <Languages className="w-16 h-16 text-white animate-spin" />
              ) : (
                <Mic className="w-16 h-16 text-white" />
              )}
            </div>
          </div>
        </div>

        {/* Status text */}
        <div className="mt-8 text-center">
          <h1 className="text-4xl font-bold text-white mb-4 bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">
            ShabdSetu
          </h1>
          <p className="text-white/80 text-lg mb-2">
            {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : isLoading ? 'Translating...' : 'Tap the orb to speak'}
          </p>
          <p className="text-white/60 text-sm h-5">
            {detectedSource && `Detected: ${detectedSource.toUpperCase()} (${translationMethod})`}
          </p>
          
          {/* Translated text display */}
          {translatedText && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 mt-6 max-w-md mx-auto border border-white/20">
              <p className="text-white text-xl font-medium leading-relaxed">
                {translatedText}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Custom styles */}
      <style jsx>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(180deg); }
        }
      `}</style>
    </div>
  );
}

export default App;
