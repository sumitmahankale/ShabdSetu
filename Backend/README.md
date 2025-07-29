# ShabdSetu - Bidirectional English-Marathi Speech Translator

A comprehensive speech-to-speech translation application that provides real-time bidirectional translation between English and Marathi with automatic language detection.

## Features

### Core Functionality
- Bidirectional translation (English to Marathi and Marathi to English)
- Automatic language detection for both text and speech input
- Real-time speech-to-speech translation with one-button operation
- Support for both Devanagari script and romanized Marathi input
- Intelligent voice synthesis with language-appropriate voice selection

### Translation Engine
- Multiple free translation APIs with automatic fallback system
- Dictionary-first approach for common phrases ensuring accuracy
- Romanized Marathi to Devanagari conversion for better API results
- Smart translation caching for improved performance
- Comprehensive phrase coverage for daily conversations

### User Interface
- Google Gemini-style modern UI with glassmorphic design
- One-touch speech translation button
- Visual feedback for recording, translation, and playback states
- Conversation history with copy functionality
- Debug information panel for troubleshooting

### Technical Architecture
- FastAPI-based REST API backend with comprehensive error handling
- React frontend with responsive design and accessibility features
- Web Speech API integration for speech recognition
- Speech Synthesis API with intelligent voice selection
- CORS-enabled for seamless frontend-backend communication

## Translation APIs

The system uses multiple free translation services with intelligent fallback:

1. **Local Dictionary** - Instant translation for common phrases
2. **MyMemory API** - Primary translation service with good Marathi support
3. **Google Translate (Free)** - High-quality translations via unofficial API
4. **Lingva Translate** - Privacy-focused Google Translate alternative
5. **LibreTranslate** - Open-source translation service

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- Modern web browser with Web Speech API support

### Backend Setup

1. **Navigate to Backend directory:**
   ```bash
   cd Backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux  
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install fastapi uvicorn python-dotenv requests
   ```

4. **Start the backend server:**
   ```bash
   python main.py
   ```
   
   The API will be available at `http://localhost:8003`

### Frontend Setup

1. **Navigate to Frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The application will be available at `http://localhost:3003`

## API Documentation

### Translation Endpoint

**POST** `/translate`

Request body:
```json
{
  "text": "Hello, how are you today?",
  "source_language": "auto",
  "target_language": "auto"
}
```

Response:
```json
{
  "original_text": "Hello, how are you today?",
  "translated_text": "नमस्कार, आज तुम्ही कसे आहात?",
  "source_language": "en",
  "target_language": "mr",
  "translation_method": "mymemory_api"
}
```

### Health Check

**GET** `/`

Response:
```json
{
  "message": "ShabdSetu Bidirectional Translation API is running!",
  "version": "3.0.0",
  "features": ["English to Marathi", "Marathi to English", "Auto-detection", "Real-time"],
  "translation_apis": ["Dictionary", "MyMemory", "Google Translate (Free)", "Lingva Translate", "LibreTranslate"],
  "api_calls_made": 0
}
```

### Statistics Endpoint

**GET** `/stats`

Response:
```json
{
  "api_calls_made": 25,
  "cache_size": 12,
  "cached_translations": ["hello_en_mr", "नमस्कार_mr_en", ...]
}
```

## Usage Examples

### Command Line Testing

```bash
# Test English to Marathi
curl -X POST "http://localhost:8003/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "Good morning, how is your day going?", "source_lang": "auto", "target_lang": "auto"}'

# Test Marathi to English (romanized)
curl -X POST "http://localhost:8003/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "namaskar majhe nav Sumit aahe", "source_lang": "auto", "target_lang": "auto"}'

# Test with Devanagari script
curl -X POST "http://localhost:8003/translate" \
     -H "Content-Type: application/json" \
     -d '{"text": "धन्यवाद", "source_lang": "auto", "target_lang": "auto"}'
```

### Web Application Usage

1. Open `http://localhost:3003` in your browser
2. Click the microphone button to start speech recognition
3. Speak in either English or Marathi
4. The system automatically detects the language and translates
5. Translation is spoken back in the target language
6. View conversation history and debug information

## Language Support

### Input Formats Supported
- English text and speech
- Marathi in Devanagari script (नमस्कार, धन्यवाद)
- Romanized Marathi (namaskar, dhanyawad)
- Mixed script conversations

### Voice Synthesis
- Intelligent voice selection based on target language
- Preference order: Native language voice > Regional voice > Fallback voice
- Adjustable speech rate for better pronunciation clarity

## Project Structure

```
ShabdSetu/
├── Backend/
│   ├── main.py                 # FastAPI application with multiple translation APIs
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment template
│   └── README.md              # This documentation
├── Frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React application
│   │   └── index.css          # Styling with Tailwind CSS
│   ├── package.json           # Node.js dependencies
│   └── vite.config.js         # Vite configuration
└── test_marathi.html          # Speech synthesis testing tool
```

## Advanced Features

### Language Detection Algorithm
- Devanagari script recognition for Marathi text
- Romanized Marathi word pattern matching
- Statistical analysis with confidence thresholds
- Fallback to English for ambiguous inputs

### Translation Quality Optimization
- Dictionary-first approach for common phrases
- API result quality assessment and ranking
- Automatic fallback through multiple translation services
- Romanized text preprocessing for better API results

### Performance Enhancements
- Response caching with intelligent cache keys
- Rate limiting for external API calls
- Optimized voice loading and selection
- Minimal UI re-renders for smooth user experience

## Browser Compatibility

### Fully Supported
- Chrome 70+
- Firefox 65+
- Safari 14+
- Edge 79+

### Requirements
- Web Speech API support for speech recognition
- Speech Synthesis API for text-to-speech
- Modern JavaScript (ES6+) support
- CORS-enabled fetch API

## Troubleshooting

### Common Issues

**Speech recognition not working:**
- Ensure microphone permissions are granted
- Check browser Web Speech API support
- Verify HTTPS connection (required for some browsers)

**Translation quality issues:**
- Try shorter, simpler phrases for better accuracy
- Use common words found in the built-in dictionary
- For Marathi input, try both romanized and Devanagari scripts

**API connection errors:**
- Verify backend server is running on port 8003
- Check CORS configuration if using custom ports
- Ensure frontend and backend are on compatible origins

### Debug Features
- Real-time translation method logging
- Speech recognition confidence scores
- API response time monitoring
- Voice selection information display

## Development Guidelines

### Adding New Translation APIs
1. Implement new method in `BilingualTranslationService` class
2. Add to the fallback chain in the main `translate` method
3. Update health check endpoint to include new API
4. Test with various input types and languages

### Frontend Customization
- Modify `App.jsx` for UI changes
- Update Tailwind classes for styling adjustments
- Add new speech synthesis voices in `speakText` function
- Extend language detection in `detectLanguage` function

## Future Roadmap

### Planned Features
- Offline translation capability with local models
- Support for additional Indian languages (Hindi, Tamil, Telugu)
- Voice training for improved recognition accuracy
- Mobile application for iOS and Android
- Translation confidence scoring and user feedback
- Custom vocabulary management for technical terms

### Performance Improvements
- WebAssembly integration for faster local processing
- Progressive Web App (PWA) functionality
- Voice recognition model fine-tuning for Indian accents
- Edge computing deployment for reduced latency

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository and create a feature branch
2. Test thoroughly with both English and Marathi inputs
3. Update documentation for any API changes
4. Submit pull requests with clear descriptions

## License

MIT License - see LICENSE file for details

## Acknowledgments

- MyMemory Translation API for reliable translation services
- Google Translate for high-quality language processing
- LibreTranslate for open-source translation capabilities
- Web Speech API community for browser integration standards
