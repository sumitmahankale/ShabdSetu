#!/usr/bin/env python3
"""
PDF Report Generator for ShabdSetu with Graphical UML Diagrams
"""

import os
import zlib
import base64
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import urllib.request
import urllib.parse
import io

# --- PlantUML Diagram Definitions ---

DIAGRAMS = {
    "Module Hierarchy Diagram": {
        "description": (
            "This Component diagram illustrates the high-level structure of ShabdSetu, breaking it down into its primary modules.\n"
            "It shows the separation of concerns between the Frontend (user interface) and the Backend (translation logic)."
        ),
        "plantuml": """
        @startuml
        skinparam packageStyle rect
        skinparam componentStyle rect

        package "ShabdSetu System" {
            package "Frontend (React)" as Frontend {
                [UI Components]
                [Speech Recognition]
                [Speech Synthesis]
                [API Client]
            }

            package "Backend (FastAPI)" as Backend {
                [API Endpoints]
                [Translation Service]
                [External API Wrappers]
                [Caching Mechanism]
            }
        }

        Frontend ..> Backend : "HTTP API Calls"
        @enduml
        """
    },
    "Entity-Relationship Diagram": {
        "description": (
            "This conceptual E-R diagram models the key data entities in ShabdSetu. As the application is stateless and does not use a\n"
            "persistent database, these entities represent transient data objects created during the translation workflow."
        ),
        "plantuml": """
        @startuml
        entity "TranslationRequest" as request {
          * text: string
          * source_lang: string
        }

        entity "TranslationResponse" as response {
          * original_text: string
          * translated_text: string
          * translation_method: string
        }

        entity "CacheEntry" as cache {
          * request_key: string
          --
          * response_data: json
        }

        request -- response : "generates"
        response -- cache : "is stored as"
        @enduml
        """
    },
    "Class Diagram": {
        "description": (
            "This diagram details the primary classes in the backend system, focusing on the `BilingualTranslationService`.\n"
            "It shows the attributes and methods that encapsulate the core translation logic and its relation to the FastAPI app."
        ),
        "plantuml": """
        @startuml
        class BilingualTranslationService {
          - cache: dict
          - api_call_count: int
          + translate(text, src, target): dict
          - _detect_language(text): str
          - _google_free(text, src, target): str
          - _mymemory(text, src, target): str
        }

        class FastAPIApp {
          + /translate (POST)
          + /health (GET)
        }

        FastAPIApp ..> BilingualTranslationService : "uses"
        @enduml
        """
    },
    "Use Case Diagram": {
        "description": (
            "This diagram shows the interactions between the user (Actor) and the ShabdSetu system. It highlights the main\n"
            "functionalities available to the user, with 'Translate Speech' being the primary use case."
        ),
        "plantuml": """
        @startuml
        left to right direction
        actor "User" as user
        rectangle "ShabdSetu System" {
            usecase "Translate Speech" as UC1
            usecase "Select Language Mode" as UC2
            usecase "Copy Translation" as UC3
        }
        user -- UC1
        user -- UC2
        user -- UC3
        @enduml
        """
    },
    "Activity Diagram": {
        "description": (
            "This diagram models the workflow of a complete speech-to-speech translation process from the user's perspective.\n"
            "It shows the sequence of activities from the initial user action to the final audio output."
        ),
        "plantuml": """
        @startuml
        start
        :User Clicks Microphone;
        :Start Speech Recognition;
        :User Speaks;
        :Convert Speech to Text;
        :Send Text to Backend API;
        if (Is translation in cache?) then (yes)
            :Return Cached Translation;
        else (no)
            :Perform Multi-Tier Translation;
            :Store Result in Cache;
            :Return New Translation;
        endif
        :Receive Translation on Frontend;
        :Synthesize Text to Speech;
        :Play Audio Output to User;
        stop
        @enduml
        """
    },
    "Sequence Diagram": {
        "description": (
            "This diagram illustrates the interactions between different components of the system over time for a single translation request.\n"
            "It clearly shows the flow of messages from the user's browser to the backend service and back."
        ),
        "plantuml": """
        @startuml
        actor User
        participant "Browser (Frontend)" as Frontend
        participant "Backend (FastAPI)" as Backend
        participant "External APIs" as External

        User -> Frontend : clickMicrophone()
        Frontend -> User : startListening()
        User -> Frontend : speaks
        Frontend -> Backend : POST /translate
        activate Backend
        alt translation not in cache
            Backend -> External : GET translation
            activate External
            External --> Backend : translated text
            deactivate External
            Backend -> Backend : store in cache
        end
        Backend --> Frontend : 200 OK {translation}
        deactivate Backend
        Frontend -> User : playAudio(translation)
        @enduml
        """
    }
}

def plantuml_deflate_and_encode(plantuml_text):
    """Deflate and encode PlantUML text for URL."""
    zlibbed_str = zlib.compress(plantuml_text.encode('utf-8'))
    compressed_string = zlibbed_str[2:-4]
    
    # Base64 encoding
    plantuml_alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    base64_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    encoded_b64 = base64.b64encode(compressed_string).decode('utf-8')
    
    # Remap to PlantUML's Base64
    trans = str.maketrans(base64_alphabet, plantuml_alphabet)
    return encoded_b64.translate(trans)

def get_plantuml_image_url(plantuml_text, server="http://www.plantuml.com/plantuml"):
    """Generate the URL for a PlantUML diagram."""
    encoded_text = plantuml_deflate_and_encode(plantuml_text)
    return f"{server}/png/{encoded_text}"

def create_uml_diagram_report():
    """Generate a PDF report with graphical UML diagrams for ShabdSetu."""
    
    filename = f"ShabdSetu_UML_Diagram_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    try:
        pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
        font_name = 'Times-Roman'
    except Exception:
        print("Times New Roman font not found. Using default Helvetica.")
        font_name = 'Helvetica'

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    def draw_page(title, description, image_url):
        c.saveState()
        
        # Title
        c.setFont(font_name, 18)
        c.drawCentredString(width / 2.0, height - 0.8 * inch, title)
        
        # Description
        c.setFont(font_name, 12)
        text = c.beginText(1 * inch, height - 1.3 * inch)
        for line in description.split('\n'):
            text.textLine(line)
        c.drawText(text)

        # Image
        try:
            with urllib.request.urlopen(image_url) as response:
                image_data = response.read()
                image = ImageReader(io.BytesIO(image_data))
                
                # Calculate image size to fit page
                img_width, img_height = image.getSize()
                aspect = img_height / float(img_width)
                
                display_width = width - 2 * inch
                display_height = aspect * display_width
                
                # Center image
                x = (width - display_width) / 2
                y = height - 2.5 * inch - display_height
                
                if y < 1 * inch: # Ensure it doesn't go off page
                    display_height = height - 3.5 * inch
                    display_width = display_height / aspect
                    x = (width - display_width) / 2
                    y = 1 * inch

                c.drawImage(image, x, y, width=display_width, height=display_height)
        except Exception as e:
            c.setFont('Helvetica-Bold', 12)
            c.drawCentredString(width / 2.0, height / 2, f"Error fetching diagram: {e}")
            print(f"Error fetching diagram for '{title}': {e}")

        c.restoreState()
        c.showPage()

    # --- Title Page ---
    c.saveState()
    c.setFont(font_name, 24)
    c.drawCentredString(width / 2.0, height / 2 + 1.5 * inch, "ShabdSetu System Design Report")
    c.setFont(font_name, 16)
    c.drawCentredString(width / 2.0, height / 2 + 0.5 * inch, "UML Architectural Diagrams")
    c.setFont(font_name, 12)
    c.drawCentredString(width / 2.0, height / 2 - 0.5 * inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    c.showPage()

    # --- Generate a page for each diagram ---
    for i, (title, data) in enumerate(DIAGRAMS.items(), 1):
        print(f"Generating diagram {i}/{len(DIAGRAMS)}: {title}...")
        page_title = f"{i}. {title}"
        image_url = get_plantuml_image_url(data["plantuml"])
        draw_page(page_title, data["description"], image_url)

    c.save()
    print(f"✅ PDF report with UML diagrams generated successfully: {filename}")
    return filename

if __name__ == "__main__":
    print("🚀 Generating ShabdSetu UML Diagram Report PDF...")
    try:
        pdf_file = create_uml_diagram_report()
        print(f"🎉 Success! Open the file: {pdf_file}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
