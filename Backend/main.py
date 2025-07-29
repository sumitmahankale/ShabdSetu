from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ShabdSetu - English to Marathi Translator",
    description="A translation service that converts English text to Marathi using LangChain and LLMs",
    version="1.0.0"
)

class TranslationRequest(BaseModel):
    text: str
    source_language: str = "English"
    target_language: str = "Marathi"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str

class TranslationService:
    def __init__(self):
        self.model_provider = os.getenv("MODEL_PROVIDER", "openai")
        self.model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        self.llm = self._initialize_llm()
        self.translation_prompt = self._create_translation_prompt()
    
    def _initialize_llm(self):
        """Initialize the LLM based on the configured provider"""
        try:
            if self.model_provider.lower() == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found in environment variables")
                return ChatOpenAI(
                    model=self.model_name,
                    api_key=api_key,
                    temperature=0.1  # Low temperature for consistent translations
                )
            elif self.model_provider.lower() == "ollama":
                return Ollama(model=self.model_name)
            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def _create_translation_prompt(self):
        """Create a prompt template for translation"""
        template = """You are an expert translator specializing in English to Marathi translation. 
        
Your task is to translate the given English text to accurate, natural-sounding Marathi.

Guidelines:
1. Maintain the original meaning and context
2. Use appropriate Marathi grammar and sentence structure
3. Consider cultural nuances when translating
4. For technical terms, use commonly accepted Marathi equivalents or keep English terms if widely used
5. Return ONLY the translated text, no explanations or additional comments

English text to translate: {text}

Marathi translation:"""
        
        return PromptTemplate(
            input_variables=["text"],
            template=template
        )
    
    async def translate(self, text: str, source_lang: str = "English", target_lang: str = "Marathi") -> str:
        """Translate text from source language to target language"""
        try:
            # Format the prompt with the input text
            formatted_prompt = self.translation_prompt.format(text=text)
            
            # Get translation from LLM
            if hasattr(self.llm, 'ainvoke'):
                # For async-supported models
                response = await self.llm.ainvoke([HumanMessage(content=formatted_prompt)])
                translated_text = response.content.strip()
            else:
                # For sync models
                response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
                translated_text = response.content.strip()
            
            logger.info(f"Successfully translated text: '{text[:50]}...' -> '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

# Initialize the translation service
translation_service = TranslationService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ShabdSetu Translation API is running!",
        "model_provider": translation_service.model_provider,
        "model_name": translation_service.model_name
    }

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate English text to Marathi"""
    try:
        # Validate input
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text to translate cannot be empty")
        
        # Perform translation
        translated_text = await translation_service.translate(
            text=request.text,
            source_lang=request.source_language,
            target_lang=request.target_language
        )
        
        return TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in translation endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test if LLM is accessible
        test_translation = await translation_service.translate("Hello")
        return {
            "status": "healthy",
            "model_provider": translation_service.model_provider,
            "model_name": translation_service.model_name,
            "test_translation": test_translation
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
