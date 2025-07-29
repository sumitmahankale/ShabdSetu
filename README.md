# ShabdSetu - शब्दसेतू
## Bidirectional English-Marathi Speech Translator

**ShabdSetu** (meaning "bridge of words" in Marathi) is a comprehensive real-time speech-to-speech translation application that provides seamless bidirectional translation between English and Marathi with intelligent language detection and one-button operation.

## Key Features

### Core Translation Capabilities
- **Bidirectional Translation** - English to Marathi and Marathi to English
- **Automatic Language Detection** - Detects input language automatically
- **Multiple Input Formats** - Supports Devanagari script, romanized Marathi, and English text
- **Real-Time Processing** - Instant translation with minimal latency
- **Speech-to-Speech** - Complete voice input to voice output workflow

### Advanced Translation Engine
- **5 Free Translation APIs** with intelligent fallback system
- **Dictionary-First Approach** for common phrases ensuring accuracy
- **Romanized to Devanagari Conversion** for better API results
- **Smart Caching System** for improved performance
- **Comprehensive Phrase Coverage** for daily conversations

### Modern User Interface
- **Google Gemini-Style Design** with glassmorphic effects
- **One-Touch Operation** - Single button for speech translation
- **Visual Feedback** for recording, processing, and playback states
- **Conversation History** with copy-to-clipboard functionality
- **Debug Information Panel** for troubleshooting
- **Mobile-Responsive Design** that works on all devices

### Intelligent Voice Features
- **Smart Voice Selection** - Chooses best available voice for target language
- **Adjustable Speech Rate** - Slower rate for better pronunciation
- **Cross-Platform Compatibility** - Works on desktop and mobile browsers
- **Accessibility Support** - Keyboard navigation and screen reader friendly

## Technology Stack

### Backend (FastAPI)
- **FastAPI** - High-performance async web framework
- **Multiple Translation APIs** - MyMemory, Google Translate, Lingva, LibreTranslate
- **Smart Language Detection** - Pattern matching and statistical analysis
- **Comprehensive Error Handling** - Graceful fallbacks and detailed logging
- **CORS-Enabled** - Seamless frontend-backend communication

### Frontend (React + Vite)
- **React 18** - Modern UI with hooks and context
- **Vite** - Lightning-fast development and build tool
- **Tailwind CSS** - Utility-first styling with custom components
- **Web Speech API** - Native browser speech recognition
- **Speech Synthesis API** - Text-to-speech with voice selection
- **Axios** - HTTP client for API communication

## Translation Services

The system uses multiple free translation services with intelligent fallback:

1. **Local Dictionary** - Instant translation for 100+ common phrases
2. **MyMemory API** - Primary service with good Marathi support
3. **Google Translate (Free)** - High-quality translations via unofficial API
4. **Lingva Translate** - Privacy-focused Google Translate alternative
5. **LibreTranslate** - Open-source translation service

## Quick Start

### Prerequisites
- **Python 3.8+** and **Node.js 16+**
- Modern web browser with microphone access
- Internet connection for translation APIs

### 1. Backend Setup (Terminal 1)
```bash
cd Backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install fastapi uvicorn python-dotenv requests
python main.py
```
Backend runs at: `http://localhost:8003`

### 2. Frontend Setup (Terminal 2)
```bash
cd Frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:3003`

### 3. Using the Application
1. Open `http://localhost:3003` in your browser
2. Allow microphone permissions when prompted
3. Click the microphone button to start
4. Speak in English or Marathi
5. Listen to the automatic translation

## Example Translations

### English to Marathi
- "Hello, how are you today?" → "नमस्कार, आज तुम्ही कसे आहात?"
- "Thank you very much" → "खूप खूप धन्यवाद"
- "I need help" → "मला मदत हवी"

### Marathi to English (Romanized)
- "namaskar majhe nav Sumit aahe" → "Hello, my name is Sumit"
- "dhanyawad tumhi kasa ahat" → "Thank you, how are you"

### Marathi to English (Devanagari)
- "धन्यवाद" → "Thank you"
- "नमस्कार" → "Hello"
- "तुम्ही कसे आहात?" → "How are you?"

## API Documentation

### Translation Endpoint
**POST** `/translate`
```json
{
  "text": "Good morning, how is your day going?",
  "source_lang": "auto",
  "target_lang": "auto"
}
```

**Response:**
```json
{
  "original_text": "Good morning, how is your day going?",
  "translated_text": "सुप्रभात, तुमचा दिवस कसा जात आहे?",
  "source_language": "en",
  "target_language": "mr",
  "translation_method": "mymemory_api"
}
```

### Health Check
**GET** `/`
```json
{
  "message": "ShabdSetu Bidirectional Translation API is running!",
  "version": "3.0.0",
  "features": ["English to Marathi", "Marathi to English", "Auto-detection", "Real-time"],
  "translation_apis": ["Dictionary", "MyMemory", "Google Translate (Free)", "Lingva Translate", "LibreTranslate"]
}
```

## Testing

### API Testing with curl
```bash
# Test English to Marathi
curl -X POST "http://localhost:8003/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Good morning", "source_lang": "auto", "target_lang": "auto"}'

# Test romanized Marathi to English
curl -X POST "http://localhost:8003/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "namaskar kasa ahat", "source_lang": "auto", "target_lang": "auto"}'

# Check API status
curl http://localhost:8003/
```

### Voice Testing Utility
Open `test_marathi.html` in your browser to test voice synthesis capabilities with different languages and voices.

## Project Structure

```
ShabdSetu/
├── Backend/                    # FastAPI translation server
│   ├── main.py                # Main application with 5 translation APIs
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example          # Environment template
│   └── README.md             # Detailed backend documentation
├── Frontend/                   # React speech interface
│   ├── src/
│   │   ├── App.jsx           # Main application with speech features
│   │   ├── main.jsx          # Entry point
│   │   └── index.css         # Tailwind CSS styling
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
├── test_marathi.html          # Voice synthesis testing tool
└── README.md                  # This documentation
```

## Browser Compatibility

### Fully Supported
- **Chrome 70+** - Complete feature support (Recommended)
- **Edge 79+** - Complete feature support
- **Firefox 65+** - Complete feature support
- **Safari 14+** - Complete feature support

### Requirements
- Web Speech API support for speech recognition
- Speech Synthesis API for text-to-speech
- Microphone permissions for voice input
- Internet connection for translation APIs

## Advanced Features

### Language Detection Algorithm
- **Devanagari Script Recognition** - Identifies Marathi text automatically
- **Romanized Marathi Detection** - Recognizes phonetic Marathi words
- **Statistical Analysis** - Uses word frequency and pattern matching
- **Confidence Scoring** - Provides detection reliability metrics

### Translation Quality Optimization
- **API Response Ranking** - Selects best translation from multiple sources
- **Context Preservation** - Maintains meaning across language boundaries
- **Cultural Adaptation** - Adjusts translations for local context
- **Quality Assessment** - Validates translation completeness

### Performance Enhancements
- **Intelligent Caching** - Stores frequently used translations
- **Rate Limiting** - Manages API calls to prevent throttling
- **Async Processing** - Non-blocking translation requests
- **Optimized Voice Loading** - Fast voice synthesis initialization

## Troubleshooting

### Common Issues

**Speech recognition not working:**
- Ensure microphone permissions are granted
- Check browser Web Speech API support
- Verify HTTPS connection (required for some browsers)
- Try speaking more clearly and at normal volume

**Translation accuracy issues:**
- Use shorter, clearer phrases for better results
- Try both romanized and Devanagari script for Marathi
- Check if the phrase exists in the built-in dictionary
- Ensure good internet connection for API access

**API connection errors:**
- Verify backend server is running on port 8003
- Check if frontend is accessing the correct API endpoint
- Ensure CORS configuration allows your browser origin
- Check network connectivity and firewall settings

### Debug Features
- **Real-time Logging** - View translation method and API responses
- **Language Detection Info** - See confidence scores and detected patterns
- **Voice Selection Details** - Monitor which voice is being used
- **Performance Metrics** - Track response times and cache hit rates

## Development

### Adding New Translation APIs
1. Implement new translation method in `BilingualTranslationService`
2. Add to the fallback chain in the main `translate` method
3. Update health check endpoint to include new API
4. Test with various input types and edge cases

### Frontend Customization
- Modify `App.jsx` for UI changes and new features
- Update Tailwind classes for visual styling
- Extend voice synthesis options in `speakText` function
- Enhance language detection in `detectLanguage` function

### Backend Extensions
- Add new language pairs by extending detection algorithms
- Implement additional translation APIs or local models
- Enhance caching strategies for better performance
- Add analytics and usage monitoring features

## Contributing

We welcome contributions! Please follow these guidelines:

1. **Fork** the repository and create a feature branch
2. **Test thoroughly** with both English and Marathi inputs
3. **Update documentation** for any API or feature changes
4. **Follow code style** guidelines for both frontend and backend
5. **Submit pull request** with clear description and test results

### Code Standards
- **Backend**: Follow PEP 8 Python conventions
- **Frontend**: Use ESLint and Prettier for consistency
- **Documentation**: Update README for any significant changes
- **Testing**: Include test cases for new features

## Future Roadmap

### Planned Features
- **Offline Translation** - Local model support for internet-free usage
- **Additional Languages** - Hindi, Tamil, Telugu, and other Indian languages
- **Mobile Applications** - Native iOS and Android apps
- **Voice Training** - Custom pronunciation and accent adaptation
- **Translation Confidence** - User feedback and quality scoring

### Technical Improvements
- **WebAssembly Integration** - Faster local processing
- **Progressive Web App** - Offline functionality and app-like experience
- **Edge Computing** - Reduced latency with edge deployment
- **Advanced Caching** - Intelligent prediction and pre-loading

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **MyMemory Translation API** for reliable translation services
- **Google Translate** for high-quality language processing
- **LibreTranslate** for open-source translation capabilities
- **Web Speech API Community** for browser integration standards
- **Marathi Language Community** for cultural insights and feedback

## Support

For issues, questions, or feature requests:

1. Check existing [Issues](https://github.com/sumitmahankale/ShabdSetu/issues)
2. Create new issue with detailed information
3. Provide browser, OS, and error details
4. Include steps to reproduce any problems

---

**Made with dedication for the Marathi community**

*ShabdSetu - Building intelligent bridges between languages*
