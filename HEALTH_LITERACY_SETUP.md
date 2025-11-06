# ShabdSetu Health Literacy Feature Setup

## Overview

ShabdSetu has been upgraded to be a **Lang-chain Powered Interactive Literacy Tutor for Low-Literate Populations**. It now includes:

1. **Translation Mode** - Bidirectional English-Marathi translation (existing feature)
2. **Health Information Mode** - AI-powered health literacy tutor providing medical information in English and Marathi

## New Features

### Health Literacy Tutor
- Detects health-related queries automatically
- Provides information about common health conditions
- Offers home remedies, medicines, and when to see a doctor
- Responds in the user's language (English or Marathi)
- Powered by Google Gemini Pro via LangChain

### Supported Health Topics

**Common Conditions:**
- Fever (ताप)
- Cold (सर्दी)
- Cough (खोकला)
- Headache (डोकेदुखी)
- Stomach Pain (पोटदुखी)
- Diarrhea (अतिसार)
- Diabetes (मधुमेह)
- Hypertension (उच्च रक्तदाब)

## Setup Instructions

### 1. Get Google API Key

To use the health literacy feature, you need a Google Gemini API key:

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key

### 2. Configure Environment Variables

1. Navigate to the Backend folder:
   ```bash
   cd Backend
   ```

2. Create a `.env` file (copy from `.env.example`):
   ```bash
   copy .env.example .env
   ```

3. Open `.env` file and add your API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   PORT=8003
   ```

### 3. Install Dependencies

Backend dependencies are already installed. If needed, run:
```bash
cd Backend
pip install -r requirements.txt
```

### 4. Start the Servers

**Backend:**
```bash
cd Backend
python main.py
```

**Frontend:**
```bash
cd Frontend
npm run dev
```

## How to Use

### Using the Web Interface

1. **Select Mode:**
   - Click the mode toggle button (top left, below language selector)
   - Choose between "Translation" or "Health Info"

2. **Translation Mode:**
   - Select language (English or Marathi)
   - Click microphone and speak
   - Get translation with voice output

3. **Health Info Mode:**
   - Select your language (English or Marathi)
   - Click microphone and ask health question
   - Example queries:
     - English: "I have fever", "What to do for cold?", "Headache remedies"
     - Marathi: "मला ताप आहे", "सर्दीसाठी काय करावे?", "डोकेदुखीचे उपाय"
   - Get health information with voice output

### API Endpoints

#### Health Query Endpoint
```http
POST http://localhost:8003/health/query
Content-Type: application/json

{
  "query": "I have fever",
  "language": "en"
}
```

#### Smart Query Endpoint (Auto-detects health vs translation)
```http
POST http://localhost:8003/smart/query
Content-Type: application/json

{
  "text": "I have headache"
}
```

## Features by Mode

### Translation Mode
- Bidirectional English ↔ Marathi translation
- Voice input and output
- Multiple translation APIs with fallback
- Supports Devanagari and romanized Marathi
- Conversation history

### Health Info Mode
- Health condition detection
- Symptoms explanation
- Home remedies
- Medicine suggestions
- Warning signs
- When to consult a doctor
- AI-powered responses for complex queries
- Knowledge base for common conditions

## Technical Architecture

### Backend Stack
- **FastAPI** - Web framework
- **LangChain** - AI orchestration framework
- **Google Gemini Pro** - Large language model
- **Translation APIs** - MyMemory, Google Translate, LibreTranslate, Lingva

### Health Module Components
1. **Health Knowledge Base** - Pre-loaded information for common conditions
2. **LangChain Integration** - AI-powered responses for complex queries
3. **Bilingual Support** - English and Marathi responses
4. **Safety Disclaimers** - Reminds users to consult healthcare professionals

## Limitations & Disclaimers

⚠️ **Important Medical Disclaimer:**
- This tool provides **educational information only**
- **NOT a substitute for professional medical advice**
- Always consult qualified healthcare professionals for:
  - Diagnosis
  - Treatment plans
  - Medical emergencies
  - Prescription medications

### Known Limitations
1. **Internet Required** - Both translation and AI features need internet
2. **Language Support** - Currently only English and Marathi
3. **Health Topics** - Best for common conditions; may not cover rare diseases
4. **AI Accuracy** - AI responses should be verified with medical professionals
5. **Emergency Care** - For emergencies, call local emergency services immediately

## Troubleshooting

### "AI health response failed"
- Check if `GOOGLE_API_KEY` is set in `.env` file
- Verify API key is valid
- Check internet connection
- Fallback to knowledge base will be used

### Health query not detected
- Use clear health-related terms (fever, pain, cough, etc.)
- Include symptoms in your query
- Try switching between English and Marathi

### Voice input not working
- Grant microphone permissions in browser
- Use Chrome or Edge for best compatibility
- Check if microphone is not used by other apps

## Future Enhancements

- [ ] More Indian languages (Hindi, Tamil, Telugu)
- [ ] Expanded health topics database
- [ ] Image-based symptom detection
- [ ] Medication reminders
- [ ] Health tracking features
- [ ] Offline mode with cached responses
- [ ] Integration with telemedicine services

## Support

For issues or questions:
- Check TROUBLESHOOTING.md
- Create an issue on GitHub
- Contact: github.com/sumitmahankale/ShabdSetu

---

**Built with care for low-literate populations**  
Version 4.0.0 | November 2025
