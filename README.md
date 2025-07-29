# ShabdSetu - शब्दसेतू
## English to Marathi Translation Service

**ShabdSetu** (meaning "bridge of words" in Marathi) is a modern, AI-powered translation service that bridges the gap between English and Marathi languages. Built with cutting-edge technology, it provides accurate, context-aware translations with a beautiful user interface.

## 🌟 Features

### Backend (FastAPI + LangChain)
- 🚀 **High-Performance API** built with FastAPI
- 🤖 **AI-Powered Translations** using LangChain and OpenAI GPT models
- 🔧 **Multiple LLM Support** (OpenAI, Ollama for local models)
- 📖 **Context-Aware** translations that preserve meaning and cultural nuances
- 🏥 **Health Monitoring** with comprehensive error handling
- 📚 **Auto-Generated API Documentation** (Swagger/ReDoc)

### Frontend (React + Vite)
- 🎨 **Modern UI** with responsive design using Tailwind CSS
- 🎤 **Speech-to-Speech Translation** - speak English, hear Marathi
- ⚡ **Real-Time Translation** interface with instant results
- 🔊 **Voice Recognition** with automatic transcription
- 📢 **Text-to-Speech** support for both English and Marathi
- 📋 **Copy to Clipboard** functionality
- 📱 **Mobile-Friendly** design that works on all devices
- ♿ **Accessible** with keyboard navigation and screen reader support
- 🎯 **Quick Samples** for easy testing
- 🤖 **Auto-speak** translations for hands-free experience

## 🏗️ Project Structure

```
ShabdSetu/
├── Backend/                 # FastAPI backend service
│   ├── main.py             # Main application file
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   ├── test_api.py        # API testing script
│   └── README.md          # Backend documentation
│
├── Frontend/               # React frontend application
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── main.jsx       # Entry point
│   │   └── index.css      # Global styles
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── README.md          # Frontend documentation
│
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **OpenAI API Key** (or Ollama for local models)

### Backend Setup

1. **Navigate to Backend directory:**
   ```bash
   cd Backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Start the backend server:**
   ```bash
   python main.py
   ```
   Backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to Frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

## 🎤 Voice-to-Voice Translation

ShabdSetu now supports complete **speech-to-speech translation**:

### Quick Start with Voice
1. **Open the app** at `http://localhost:3001`
2. **Click the green microphone** button
3. **Speak clearly in English** (e.g., "Hello, how are you?")
4. **Listen automatically** to the Marathi translation
5. **Enable auto-speak** for fully hands-free experience

### Voice Features
- 🎙️ **Speech Recognition** - converts your English speech to text
- 🔄 **Auto-Translation** - translates immediately after recognition
- 🔊 **Text-to-Speech** - speaks the Marathi translation aloud
- 🤖 **Auto-Speak Mode** - completely hands-free operation
- 📱 **Mobile Support** - works on smartphones and tablets

### Browser Compatibility
- ✅ **Chrome** (Recommended) - Full voice support
- ✅ **Edge** - Full voice support  
- ✅ **Safari** - Basic voice support
- ⚠️ **Firefox** - Limited speech recognition

## 🔧 Configuration

### Backend Configuration (.env)
```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL_PROVIDER=openai
MODEL_NAME=gpt-3.5-turbo
```

### Alternative: Local Models with Ollama
```env
MODEL_PROVIDER=ollama
MODEL_NAME=llama2
```

## 🌐 API Usage

### Translate Endpoint
**POST** `/translate`

```json
{
  "text": "Hello, how are you?",
  "source_language": "English",
  "target_language": "Marathi"
}
```

**Response:**
```json
{
  "original_text": "Hello, how are you?",
  "translated_text": "नमस्कार, तुम्ही कसे आहात?",
  "source_language": "English",
  "target_language": "Marathi"
}
```

### Health Check
**GET** `/health`
```json
{
  "status": "healthy",
  "model_provider": "openai",
  "model_name": "gpt-3.5-turbo",
  "test_translation": "नमस्कार"
}
```

## 📖 Documentation

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs**: http://localhost:8000/redoc (ReDoc)

## 🧪 Testing

### Backend Testing
```bash
cd Backend
python test_api.py
```

### Manual Testing with curl
```bash
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Good morning!",
       "source_language": "English",
       "target_language": "Marathi"
     }'
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern, fast web framework for building APIs
- **LangChain** - Framework for developing applications with LLMs
- **OpenAI** - GPT models for high-quality translations
- **Uvicorn** - ASGI server for running the application
- **Pydantic** - Data validation using Python type annotations

### Frontend
- **React 18** - Modern UI library with hooks
- **Vite** - Next-generation frontend tooling
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - Promise-based HTTP client
- **Lucide React** - Beautiful, customizable icons

## 🚧 Development

### Adding New Features

1. **Backend**: Add new endpoints in `Backend/main.py`
2. **Frontend**: Create new components in `Frontend/src/`
3. **Testing**: Update test files accordingly

### Code Style
- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: Use ESLint and Prettier for consistent formatting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing powerful language models
- **LangChain** for the excellent framework
- **Marathi Language Community** for inspiration
- **Open Source Community** for the amazing tools and libraries

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/sumitmahankale/ShabdSetu/issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the issue

---

**Made with ❤️ for the Marathi community**

*ShabdSetu - Building bridges between languages*
