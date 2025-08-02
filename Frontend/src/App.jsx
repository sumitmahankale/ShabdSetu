import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Languages } from 'lucide-react';

function App() {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [translatedText, setTranslatedText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [waterScale, setWaterScale] = useState(1);
  const [ripples, setRipples] = useState([]);
  const recognitionRef = useRef(null);
  
  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      
      recognitionRef.current.onstart = () => {
        setIsListening(true);
        setWaterScale(0.8); // Shrink when speaking
        createRipple();
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
        setWaterScale(1); // Return to normal size
      };
      
      recognitionRef.current.onresult = async (event) => {
        const transcript = event.results[0][0].transcript;
        await translateText(transcript);
      };
    }
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
        utterance.lang = 'hi-IN'; // Use Hindi for better Marathi support
        utterance.rate = 0.8; // Slower rate for clarity
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
        if (targetLang === 'mr') {
          setTimeout(() => {
            const fallbackUtterance = new SpeechSynthesisUtterance(text);
            fallbackUtterance.lang = 'en-US';
            fallbackUtterance.rate = 0.8;
            speechSynthesis.speak(fallbackUtterance);
          }, 100);
        }
      };
      
      console.log(`Speaking: "${text}" in language: ${utterance.lang}`);
      speechSynthesis.speak(utterance);
    } else {
      console.warn('Speech synthesis not supported');
      setIsSpeaking(false);
    }
  };

  // Start listening
  const startListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = 'en-US';
      recognitionRef.current.start();
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
          <p className="text-white/80 text-lg mb-4">
            {isListening ? 'Listening...' : 
             isSpeaking ? 'Speaking...' : 
             isLoading ? 'Translating...' : 
             'Tap the orb to speak'}
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
