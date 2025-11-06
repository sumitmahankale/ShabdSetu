"""
ShabdSetu Health Literacy Module
Lang-chain Powered Interactive Health Information System for Low-Literate Populations
Provides health information in English and Marathi
"""

import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import LangChain components (optional)
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import HumanMessage, SystemMessage
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    logger.warning(f"LangChain not available: {e}. Using knowledge base only.")

class HealthLiteracyTutor:
    """
    Interactive health literacy tutor using LangChain and Google Gemini
    Provides health information in simple language for low-literate populations
    """
    
    def __init__(self):
        self.cache = {}
        self.api_call_count = 0
        self.last_api_call_time = 0
        
        # Initialize LLM if API key is available and LangChain is installed
        self.api_key = os.getenv('GOOGLE_API_KEY', '')
        self.llm = None
        self.conversation_history = []
        
        if LANGCHAIN_AVAILABLE and self.api_key and self.api_key != 'your_google_api_key_here':
            try:
                self._initialize_llm()
            except Exception as e:
                logger.error(f"Failed to initialize LangChain: {e}")
        else:
            if not LANGCHAIN_AVAILABLE:
                logger.info("LangChain not available. Using knowledge base only.")
            elif not self.api_key or self.api_key == 'your_google_api_key_here':
                logger.info("No valid API key. Using knowledge base only.")
        
        # Health knowledge base for common conditions
        self.health_knowledge_base = {
            'en': {
                'fever': {
                    'symptoms': 'High body temperature, chills, sweating, headache, muscle pain, weakness',
                    'causes': 'Viral infection, bacterial infection, heat exhaustion, inflammatory conditions',
                    'home_remedies': 'Rest, drink plenty of water, use cold compress, wear light clothing',
                    'medicines': 'Paracetamol (500-1000mg every 6 hours), Ibuprofen (200-400mg every 6 hours)',
                    'warning': 'Consult doctor if fever above 103°F (39.4°C) or lasts more than 3 days'
                },
                'cold': {
                    'symptoms': 'Runny nose, sore throat, cough, sneezing, mild fever, congestion',
                    'causes': 'Viral infection, weather change, weak immunity',
                    'home_remedies': 'Rest, warm liquids, steam inhalation, gargle with salt water, honey and ginger',
                    'medicines': 'Cetirizine, Paracetamol, Vitamin C',
                    'warning': 'See doctor if symptoms worsen after 7 days or breathing difficulty occurs'
                },
                'cough': {
                    'symptoms': 'Dry or wet cough, throat irritation, chest discomfort',
                    'causes': 'Cold, flu, allergies, smoking, pollution, asthma',
                    'home_remedies': 'Warm water with honey, steam inhalation, avoid cold drinks, stay hydrated',
                    'medicines': 'Cough syrup (as per type - dry or wet), lozenges',
                    'warning': 'Consult doctor if cough persists beyond 3 weeks or blood in cough'
                },
                'headache': {
                    'symptoms': 'Pain in head, pressure in temples, sensitivity to light or sound',
                    'causes': 'Stress, dehydration, lack of sleep, eye strain, tension',
                    'home_remedies': 'Rest in quiet dark room, cold compress, hydration, gentle head massage',
                    'medicines': 'Paracetamol, Aspirin, Ibuprofen',
                    'warning': 'Seek immediate help if sudden severe headache with vision changes or confusion'
                },
                'stomach_pain': {
                    'symptoms': 'Abdominal pain, cramping, bloating, nausea',
                    'causes': 'Indigestion, gas, food poisoning, acidity, infection',
                    'home_remedies': 'Light food, ginger tea, avoid spicy food, warm compress on stomach',
                    'medicines': 'Antacid, ORS, Digene',
                    'warning': 'Emergency if severe pain, vomiting blood, or pain with fever'
                },
                'diarrhea': {
                    'symptoms': 'Loose watery stools, abdominal cramps, urgency, dehydration',
                    'causes': 'Food poisoning, contaminated water, viral infection, spoiled food',
                    'home_remedies': 'ORS solution, boiled rice water, banana, curd, avoid milk and spicy food',
                    'medicines': 'ORS packets, Loperamide (if needed), Zinc tablets',
                    'warning': 'See doctor if blood in stool, severe dehydration, or lasts more than 2 days'
                },
                'diabetes': {
                    'symptoms': 'Increased thirst, frequent urination, fatigue, blurred vision, slow healing',
                    'causes': 'Insulin deficiency, lifestyle, genetics, obesity',
                    'home_remedies': 'Regular exercise, balanced diet, avoid sugar, manage stress, regular monitoring',
                    'medicines': 'Consult doctor for proper medication (Metformin, Insulin etc)',
                    'warning': 'This is chronic condition - requires regular medical supervision'
                },
                'hypertension': {
                    'symptoms': 'Often no symptoms, sometimes headache, dizziness, chest pain',
                    'causes': 'Stress, salt intake, obesity, lack of exercise, genetics',
                    'home_remedies': 'Reduce salt, regular exercise, weight management, stress reduction, meditation',
                    'medicines': 'Consult doctor for prescription (ACE inhibitors, Beta blockers etc)',
                    'warning': 'Silent killer - requires regular BP monitoring and medical care'
                }
            },
            'mr': {
                'ताप': {
                    'symptoms': 'शरीराचे तापमान वाढणे, थंडी वाजणे, घाम येणे, डोकेदुखी, स्नायूंमध्ये दुखणे, अशक्तपणा',
                    'causes': 'विषाणूजन्य संसर्ग, जीवाणूजन्य संसर्ग, उष्णतेचा थकवा, दाहक स्थिती',
                    'home_remedies': 'विश्रांती घ्या, भरपूर पाणी प्या, थंड पट्टी वापरा, हलके कपडे घाला',
                    'medicines': 'पॅरासिटामॉल (500-1000 मिग्रॅ दर 6 तासांनी), आयब्युप्रोफेन (200-400 मिग्रॅ दर 6 तासांनी)',
                    'warning': 'ताप 103°F (39.4°C) पेक्षा जास्त असेल किंवा 3 दिवसांपेक्षा जास्त काळ राहिल्यास डॉक्टरांचा सल्ला घ्या'
                },
                'सर्दी': {
                    'symptoms': 'नाक वाहणे, घसा दुखणे, खोकला, शिंका येणे, हलका ताप, नाक बंद होणे',
                    'causes': 'विषाणूजन्य संसर्ग, हवामान बदल, कमकुवत रोगप्रतिकारक शक्ती',
                    'home_remedies': 'विश्रांती, कोमट पाणी, वाफ घेणे, मिठाच्या पाण्याने गार्गल करा, मध आणि आले',
                    'medicines': 'सेटिरिझिन, पॅरासिटामॉल, व्हिटॅमिन सी',
                    'warning': '7 दिवसांनंतर लक्षणे वाढल्यास किंवा श्वास घेण्यास त्रास झाल्यास डॉक्टर भेटा'
                },
                'खोकला': {
                    'symptoms': 'कोरडा किंवा ओला खोकला, घसा खवखवणे, छातीत अस्वस्थता',
                    'causes': 'सर्दी, फ्लू, ऍलर्जी, धूम्रपान, प्रदूषण, दमा',
                    'home_remedies': 'मधासह कोमट पाणी, वाफ घेणे, थंड पेये टाळा, हायड्रेटेड रहा',
                    'medicines': 'खोकल्याचे सिरप (प्रकारानुसार - कोरडे किंवा ओले), लॉझेंजेस',
                    'warning': 'खोकला 3 आठवड्यांपेक्षा जास्त काळ राहिल्यास किंवा खोकल्यात रक्त आल्यास डॉक्टरांचा सल्ला घ्या'
                },
                'डोकेदुखी': {
                    'symptoms': 'डोक्यात दुखणे, कानात दाब, प्रकाश किंवा आवाजास संवेदनशीलता',
                    'causes': 'तणाव, निर्जलीकरण, झोप कमी, डोळ्यांचा ताण, तणाव',
                    'home_remedies': 'शांत अंधाऱ्या खोलीत विश्रांती, थंड पट्टी, पाणी पिणे, हलके डोके मसाज',
                    'medicines': 'पॅरासिटामॉल, ऍस्पिरिन, आयब्युप्रोफेन',
                    'warning': 'अचानक तीव्र डोकेदुखी दृष्टी बदलासह किंवा गोंधळासह असल्यास तात्काळ मदत घ्या'
                },
                'पोटदुखी': {
                    'symptoms': 'ओटीपोटात दुखणे, पोटात मुरगळणे, फुगणे, मळमळ',
                    'causes': 'अपचन, गॅस, अन्न विषबाधा, आम्लपित्त, संसर्ग',
                    'home_remedies': 'हलके अन्न, आल्याचा चहा, मसालेदार अन्न टाळा, पोटावर कोमट पट्टी',
                    'medicines': 'अँटासिड, ओआरएस, डायजीन',
                    'warning': 'तीव्र वेदना, रक्त उलटी किंवा तापासह वेदना असल्यास आपत्कालीन'
                },
                'अतिसार': {
                    'symptoms': 'पाणी सारखी विष्ठा, ओटीपोटात मुरगळणे, तातडीने शौच जाण्याची गरज, निर्जलीकरण',
                    'causes': 'अन्न विषबाधा, दूषित पाणी, विषाणूजन्य संसर्ग, खराब झालेले अन्न',
                    'home_remedies': 'ओआरएस द्रावण, उकडलेल्या तांदळाचे पाणी, केळी, दही, दूध आणि मसालेदार अन्न टाळा',
                    'medicines': 'ओआरएस पाकीट, लोपेरामाइड (आवश्यक असल्यास), झिंक गोळ्या',
                    'warning': 'विष्ठेत रक्त, तीव्र निर्जलीकरण किंवा 2 दिवसांपेक्षा जास्त काळ असल्यास डॉक्टर भेटा'
                },
                'मधुमेह': {
                    'symptoms': 'वाढलेली तहान, वारंवार लघवी होणे, थकवा, अंधुक दृष्टी, जखमा मंद बऱ्या होणे',
                    'causes': 'इन्सुलिनची कमतरता, जीवनशैली, आनुवंशिकता, लठ्ठपणा',
                    'home_remedies': 'नियमित व्यायाम, संतुलित आहार, साखर टाळा, तणाव व्यवस्थापन, नियमित तपासणी',
                    'medicines': 'योग्य औषधांसाठी डॉक्टरांचा सल्ला घ्या (मेटफॉर्मिन, इन्सुलिन इ.)',
                    'warning': 'ही दीर्घकालीन स्थिती आहे - नियमित वैद्यकीय देखरेख आवश्यक आहे'
                },
                'उच्च_रक्तदाब': {
                    'symptoms': 'अनेकदा लक्षणे नसतात, कधीकधी डोकेदुखी, चक्कर, छातीत दुखणे',
                    'causes': 'तणाव, मीठ सेवन, लठ्ठपणा, व्यायामाचा अभाव, आनुवंशिकता',
                    'home_remedies': 'मीठ कमी करा, नियमित व्यायाम, वजन व्यवस्थापन, तणाव कमी करा, ध्यान',
                    'medicines': 'प्रिस्क्रिप्शनसाठी डॉक्टरांचा सल्ला घ्या (ACE inhibitors, Beta blockers इ.)',
                    'warning': 'मूक किलर - नियमित रक्तदाब तपासणी आणि वैद्यकीय काळजी आवश्यक आहे'
                }
            }
        }
        
        # Initialize LLM if API key is available
        if self.api_key:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize Google Gemini LLM with LangChain"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available")
            return
            
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                google_api_key=self.api_key,
                temperature=0.3  # Lower temperature for more factual responses
            )
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def detect_health_query(self, text: str) -> bool:
        """
        Detect if the input text is a health-related query
        """
        health_keywords_en = [
            'fever', 'cold', 'cough', 'headache', 'pain', 'ache', 'sick', 'ill',
            'disease', 'symptom', 'medicine', 'doctor', 'treatment', 'cure',
            'diabetes', 'blood pressure', 'hypertension', 'stomach', 'diarrhea',
            'vomit', 'nausea', 'dizzy', 'weakness', 'tired', 'infection',
            'health', 'medical', 'remedy', 'tablet', 'drug'
        ]
        
        health_keywords_mr = [
            'ताप', 'सर्दी', 'खोकला', 'डोकेदुखी', 'दुखणे', 'आजारी', 'रोग',
            'लक्षण', 'औषध', 'डॉक्टर', 'उपचार', 'इलाज', 'मधुमेह', 'रक्तदाब',
            'पोट', 'अतिसार', 'उलटी', 'मळमळ', 'चक्कर', 'कमकुवत', 'थकवा',
            'संसर्ग', 'आरोग्य', 'वैद्यकीय', 'उपाय', 'गोळी'
        ]
        
        text_lower = text.lower()
        
        # Check English keywords
        if any(keyword in text_lower for keyword in health_keywords_en):
            return True
        
        # Check Marathi keywords (Devanagari)
        if any(keyword in text for keyword in health_keywords_mr):
            return True
        
        return False
    
    def get_basic_health_info(self, query: str, language: str = 'en') -> Optional[Dict]:
        """
        Get basic health information from knowledge base
        """
        query_lower = query.lower()
        knowledge = self.health_knowledge_base.get(language, {})
        
        # Keywords for matching
        condition_keywords = {
            'en': {
                'fever': ['fever', 'temperature', 'hot body', 'burning'],
                'cold': ['cold', 'runny nose', 'sneezing'],
                'cough': ['cough', 'coughing', 'throat'],
                'headache': ['headache', 'head pain', 'migraine'],
                'stomach_pain': ['stomach', 'belly', 'abdomen', 'tummy'],
                'diarrhea': ['diarrhea', 'loose motion', 'loose stool'],
                'diabetes': ['diabetes', 'sugar', 'blood sugar'],
                'hypertension': ['blood pressure', 'bp', 'hypertension']
            },
            'mr': {
                'ताप': ['ताप', 'तापमान', 'गरम शरीर'],
                'सर्दी': ['सर्दी', 'नाक वाहणे', 'शिंका'],
                'खोकला': ['खोकला', 'घसा'],
                'डोकेदुखी': ['डोकेदुखी', 'डोके दुखणे'],
                'पोटदुखी': ['पोट', 'पोटदुखी', 'ओटीपोट'],
                'अतिसार': ['अतिसार', 'जुलाब'],
                'मधुमेह': ['मधुमेह', 'साखर', 'शुगर'],
                'उच्च_रक्तदाब': ['रक्तदाब', 'बीपी', 'उच्च रक्तदाब']
            }
        }
        
        # Find matching condition
        keywords_map = condition_keywords.get(language, {})
        for condition, keywords in keywords_map.items():
            if any(kw in query_lower for kw in keywords):
                return knowledge.get(condition)
        
        return None
    
    def format_health_response(self, condition_info: Dict, language: str = 'en') -> str:
        """
        Format health information into a readable response
        """
        if language == 'en':
            response = f"""
**Health Information**

**Symptoms:** {condition_info.get('symptoms', 'Not available')}

**Common Causes:** {condition_info.get('causes', 'Not available')}

**Home Remedies:** {condition_info.get('home_remedies', 'Not available')}

**Medicines:** {condition_info.get('medicines', 'Not available')}

**⚠️ Important:** {condition_info.get('warning', 'Please consult a doctor for proper diagnosis and treatment')}

**Note:** This information is for educational purposes only. Always consult a qualified healthcare professional for medical advice.
"""
        else:  # Marathi
            response = f"""
**आरोग्य माहिती**

**लक्षणे:** {condition_info.get('symptoms', 'उपलब्ध नाही')}

**सामान्य कारणे:** {condition_info.get('causes', 'उपलब्ध नाही')}

**घरगुती उपाय:** {condition_info.get('home_remedies', 'उपलब्ध नाही')}

**औषधे:** {condition_info.get('medicines', 'उपलब्ध नाही')}

**⚠️ महत्त्वाचे:** {condition_info.get('warning', 'योग्य निदान आणि उपचारांसाठी डॉक्टरांचा सल्ला घ्या')}

**टीप:** ही माहिती केवळ शैक्षणिक उद्देशांसाठी आहे. वैद्यकीय सल्ल्यासाठी नेहमी पात्र आरोग्य व्यावसायिकाचा सल्ला घ्या.
"""
        
        return response.strip()
    
    def get_ai_health_response(self, query: str, language: str = 'en') -> str:
        """
        Get AI-powered health response using LangChain and Gemini
        """
        if not LANGCHAIN_AVAILABLE or not self.llm:
            return self._get_fallback_response(language)
        
        try:
            # Create prompt based on language
            if language == 'en':
                system_msg = """You are a health literacy tutor for low-literate populations. 
Provide simple, clear health information in easy-to-understand English.

Please provide:
1. Brief explanation in simple words
2. Common symptoms (if applicable)
3. Simple home remedies
4. When to see a doctor
5. Basic prevention tips

Keep your response simple, avoid medical jargon, and use short sentences.
Always remind users to consult a doctor for serious conditions."""
            else:  # Marathi
                system_msg = """तुम्ही कमी साक्षर लोकसंख्येसाठी आरोग्य साक्षरता शिक्षक आहात.
सोप्या, समजण्यायोग्य मराठीमध्ये आरोग्य माहिती द्या.

कृपया प्रदान करा:
1. सोप्या शब्दांत संक्षिप्त स्पष्टीकरण
2. सामान्य लक्षणे (लागू असल्यास)
3. साधे घरगुती उपाय
4. डॉक्टरांना केव्हा भेटावे
5. मूलभूत प्रतिबंधात्मक उपाय

तुमचा प्रतिसाद सोपा ठेवा, वैद्यकीय शब्दजाल टाळा आणि लहान वाक्ये वापरा.
गंभीर परिस्थितीसाठी डॉक्टरांचा सल्ला घेण्याची आठवण करून द्या."""
            
            # Import message classes inline to avoid top-level import issues
            if LANGCHAIN_AVAILABLE:
                from langchain_core.messages import HumanMessage, SystemMessage
                
                messages = [
                    SystemMessage(content=system_msg),
                    HumanMessage(content=query)
                ]
                
                response = self.llm.invoke(messages)
                
                # Store in history
                self.conversation_history.append({
                    'query': query,
                    'response': response.content,
                    'language': language
                })
                
                return response.content.strip()
            else:
                return self._get_fallback_response(language)
            
        except Exception as e:
            logger.error(f"AI health response failed: {e}")
            return self._get_fallback_response(language)
    
    def _get_fallback_response(self, language: str = 'en') -> str:
        """Fallback response when AI is not available"""
        if language == 'en':
            return """I can provide basic health information. Please describe your symptoms or health concern, and I'll try to help with:
- Common causes
- Home remedies
- When to see a doctor
- Basic prevention tips

Note: For accurate diagnosis and treatment, please consult a qualified doctor."""
        else:
            return """मी मूलभूत आरोग्य माहिती देऊ शकतो. कृपया तुमची लक्षणे किंवा आरोग्य समस्या वर्णन करा आणि मी मदत करण्याचा प्रयत्न करेन:
- सामान्य कारणे
- घरगुती उपाय
- डॉक्टरांना केव्हा भेटावे
- मूलभूत प्रतिबंधात्मक उपाय

टीप: अचूक निदान आणि उपचारांसाठी, कृपया पात्र डॉक्टरांचा सल्ला घ्या."""
    
    def process_health_query(self, query: str, language: str = 'en') -> Dict:
        """
        Main method to process health queries
        """
        # First try to get basic info from knowledge base
        basic_info = self.get_basic_health_info(query, language)
        
        if basic_info:
            response = self.format_health_response(basic_info, language)
            return {
                'response': response,
                'source': 'knowledge_base',
                'language': language
            }
        
        # If not in knowledge base and LLM is available, use AI
        if self.llm:
            ai_response = self.get_ai_health_response(query, language)
            return {
                'response': ai_response,
                'source': 'ai',
                'language': language
            }
        
        # Fallback
        return {
            'response': self._get_fallback_response(language),
            'source': 'fallback',
            'language': language
        }


# Singleton instance
_health_tutor_instance = None

def get_health_tutor() -> HealthLiteracyTutor:
    """Get or create health literacy tutor instance"""
    global _health_tutor_instance
    if _health_tutor_instance is None:
        _health_tutor_instance = HealthLiteracyTutor()
    return _health_tutor_instance
