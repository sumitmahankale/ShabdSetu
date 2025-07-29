# ShabdSetu - English to Marathi Translator

A powerful translation service that converts English text to Marathi using LangChain and Large Language Models.

## Features

- 🌐 English to Marathi translation
- 🚀 FastAPI-based REST API
- 🔗 LangChain integration
- 🤖 Support for multiple LLM providers (OpenAI, Ollama)
- 📝 Configurable translation prompts
- 🏥 Health check endpoints

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd Backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file and add your API keys:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key
   MODEL_PROVIDER=openai
   MODEL_NAME=gpt-3.5-turbo
   ```

### Running the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Usage

### Translate Text

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

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration Options

### Model Providers

1. **OpenAI** (Recommended for quality)
   ```
   MODEL_PROVIDER=openai
   MODEL_NAME=gpt-3.5-turbo
   OPENAI_API_KEY=your_key
   ```

2. **Ollama** (Free, local)
   ```
   MODEL_PROVIDER=ollama
   MODEL_NAME=llama2
   ```

## Example Usage with curl

```bash
# Translate text
curl -X POST "http://localhost:8000/translate" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Good morning! Have a great day.",
       "source_language": "English",
       "target_language": "Marathi"
     }'
```

## Project Structure

```
Backend/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .env               # Your actual environment variables (create this)
└── README.md          # This file
```

## Future Enhancements

- [ ] Support for more language pairs
- [ ] Batch translation endpoint
- [ ] Translation history and caching
- [ ] Audio input/output support
- [ ] Web frontend interface
- [ ] Docker containerization

## Contributing

Feel free to contribute by submitting issues or pull requests!

## License

MIT License
