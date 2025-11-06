#!/usr/bin/env python3
"""
PDF Report Generator for ShabdSetu System Design Diagrams
"""

import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_diagram_report():
    """Generate a PDF report with system design diagrams for ShabdSetu."""
    
    filename = f"ShabdSetu_System_Design_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    try:
        pdfmetrics.registerFont(TTFont('Times-Roman', 'times.ttf'))
    except Exception:
        print("Times New Roman font not found. Using default Helvetica.")
        # Fallback to a standard font if Times New Roman is not available
        pass

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    def set_font(size=12):
        try:
            c.setFont('Times-Roman', size)
        except Exception:
            c.setFont('Helvetica', size)

    def draw_page(title, description, diagram_lines):
        c.saveState()
        set_font(18)
        c.drawCentredString(width / 2.0, height - 1 * inch, title)
        
        set_font(12)
        text = c.beginText(1 * inch, height - 1.5 * inch)
        text.setFont('Times-Roman', 12)
        for line in description.split('\n'):
            text.textLine(line)
        c.drawText(text)

        set_font(11) # Slightly smaller for diagram
        diagram_text = c.beginText(1.5 * inch, height - 3.5 * inch)
        diagram_text.setFont('Times-Roman', 11)
        for line in diagram_lines:
            diagram_text.textLine(line)
        c.drawText(diagram_text)
        
        c.restoreState()
        c.showPage()

    # --- Title Page ---
    c.saveState()
    set_font(24)
    c.drawCentredString(width / 2.0, height / 2 + 1.5 * inch, "ShabdSetu System Design Report")
    set_font(16)
    c.drawCentredString(width / 2.0, height / 2 + 0.5 * inch, "Architectural Diagrams")
    set_font(12)
    c.drawCentredString(width / 2.0, height / 2 - 0.5 * inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    c.drawCentredString(width / 2.0, height / 2 - 0.8 * inch, "Version: 3.0.0")
    c.showPage()

    # --- 1. Module Hierarchy Diagram ---
    title = "1. Module Hierarchy Diagram"
    description = (
        "This diagram illustrates the high-level structure of ShabdSetu, breaking it down into its primary modules and sub-modules.\n"
        "It shows the separation of concerns between the frontend (user interface and interaction) and the backend (logic and translation)."
    )
    diagram = [
        "ShabdSetu (Main System)",
        "|",
        "|-- Frontend (React + Vite)",
        "|   |-- UI Components (App.jsx, Animated Orb)",
        "|   |-- Speech Recognition (Web Speech API Wrapper)",
        "|   |-- Speech Synthesis (SpeechSynthesis API Wrapper)",
        "|   |-- API Client (Axios for backend communication)",
        "|   `-- State Management (React Hooks)",
        "|",
        "`-- Backend (FastAPI)",
        "    |-- API Endpoints (/translate, /health)",
        "    |-- Translation Service (BilingualTranslationService)",
        "    |   |-- Language Detection Logic",
        "    |   `-- Multi-Tier Fallback System",
        "    |-- External API Wrappers",
        "    |   |-- Dictionary Lookup",
        "    |   |-- Google Translate API",
        "    |   |-- MyMemory API",
        "    |   `-- Other APIs (Libre, Lingva)",
        "    `-- Caching Mechanism (In-Memory LRU Cache)"
    ]
    draw_page(title, description, diagram)

    # --- 2. Entity-Relationship (E-R) Diagram ---
    title = "2. Entity-Relationship (E-R) Diagram"
    description = (
        "This conceptual E-R diagram models the key data entities in ShabdSetu. As the application is stateless and does not use a\n"
        "persistent database, these entities represent transient data objects that are created and processed during the translation workflow."
    )
    diagram = [
        "[User] --(submits)--> [TranslationRequest]",
        "  - Actor",
        "  - Interacts with UI",
        "",
        "[TranslationRequest]",
        "  - text: string",
        "  - source_lang: string ('en', 'mr', 'auto')",
        "  - target_lang: string ('en', 'mr', 'auto')",
        "",
        "[System] --(generates)--> [TranslationResponse]",
        "  |",
        "  `--(stores in)--> [CacheEntry]",
        "",
        "[TranslationResponse]",
        "  - original_text: string",
        "  - translated_text: string",
        "  - source_language: string",
        "  - target_language: string",
        "  - translation_method: string",
        "",
        "[CacheEntry]",
        "  - request_key: string (hash of request)",
        "  - response: TranslationResponse"
    ]
    draw_page(title, description, diagram)

    # --- 3. Class Diagram ---
    title = "3. Class Diagram"
    description = (
        "This diagram details the primary classes in the backend system, focusing on the `BilingualTranslationService`.\n"
        "It shows the attributes and methods that encapsulate the core translation logic, including the various API call handlers."
    )
    diagram = [
        "-----------------------------------------",
        "| BilingualTranslationService           |",
        "-----------------------------------------",
        "| - cache: dict                         |",
        "| - api_call_count: int                 |",
        "-----------------------------------------",
        "| + translate(text, src, target): dict  |",
        "| - _detect_language(text): str         |",
        "| - _is_valid_marathi(text): bool       |",
        "| - _google_free(text, src, target): str|",
        "| - _mymemory(text, src, target): str   |",
        "| - _libre(text, src, target): str      |",
        "| - _lingva(text, src, target): str     |",
        "-----------------------------------------",
        "          ^",
        "          | uses",
        "-----------------------------------------",
        "| FastAPI Application                   |",
        "-----------------------------------------",
        "| + /translate (POST)                   |",
        "| + /health (GET)                       |",
        "-----------------------------------------"
    ]
    draw_page(title, description, diagram)

    # --- 4. Use Case Diagram ---
    title = "4. Use Case Diagram"
    description = (
        "This diagram shows the interactions between the user (Actor) and the ShabdSetu system. It highlights the main functionalities\n"
        "available to the user, with 'Translate Speech' being the primary use case that involves several sub-actions."
    )
    diagram = [
        "Actor: User",
        "",
        "Use Cases:",
        "  1. Translate Speech",
        "     - Description: User speaks and receives a spoken translation.",
        "     - Includes:",
        "       - Record Audio",
        "       - Convert Speech to Text",
        "       - Send Text to Backend",
        "       - Receive Translation",
        "       - Synthesize Translated Text to Speech",
        "",
        "  2. Select Language Mode",
        "     - Description: User toggles the translation direction (EN <-> MR).",
        "",
        "  3. Copy Translation",
        "     - Description: User copies the translated text to the clipboard.",
        "",
        "  (User) ---|> (Translate Speech)",
        "  (User) ---|> (Select Language Mode)",
        "  (User) ---|> (Copy Translation)"
    ]
    draw_page(title, description, diagram)

    # --- 5. Activity Diagram ---
    title = "5. Activity Diagram"
    description = (
        "This diagram models the workflow of a complete speech-to-speech translation process from the user's perspective.\n"
        "It shows the sequence of activities from the initial user action to the final audio output, including system decisions."
    )
    diagram = [
        "(Start) --> User Clicks Microphone",
        "--> [Activity] Start Speech Recognition",
        "--> User Speaks",
        "--> [Activity] Convert Speech to Text",
        "--> [Activity] Send Text to Backend API",
        "--> [Decision] Is translation in cache?",
        "    |",
        "    |-- Yes --> [Activity] Return Cached Translation",
        "    |",
        "    `-- No --> [Activity] Perform Multi-Tier Translation",
        "        --> [Activity] Store Result in Cache",
        "        --> [Activity] Return New Translation",
        "--> [Merge]",
        "--> [Activity] Receive Translation on Frontend",
        "--> [Activity] Synthesize Text to Speech",
        "--> [Activity] Play Audio Output to User",
        "--> (End)"
    ]
    draw_page(title, description, diagram)

    # --- 6. Sequence Diagram ---
    title = "6. Sequence Diagram"
    description = (
        "This diagram illustrates the interactions between different components of the system over time for a single translation request.\n"
        "It clearly shows the flow of messages from the user's browser to the backend service and back."
    )
    diagram = [
        "User -> Browser(Frontend) : clickMicrophone()",
        "Browser(Frontend) -> WebSpeechAPI : startRecognition()",
        "WebSpeechAPI -> Browser(Frontend) : onResult(speechText)",
        "Browser(Frontend) -> Backend(FastAPI) : POST /translate {text: speechText}",
        "Backend(FastAPI) -> BilingualTranslationService : translate(speechText)",
        "BilingualTranslationService -> BilingualTranslationService : _detect_language()",
        "BilingualTranslationService -> Cache : check(key)",
        "alt [Not in Cache]",
        "  BilingualTranslationService -> ExternalAPI : translate()",
        "  ExternalAPI -> BilingualTranslationService : translatedText",
        "  BilingualTranslationService -> Cache : store(key, translatedText)",
        "end",
        "BilingualTranslationService -> Backend(FastAPI) : return {translation}",
        "Backend(FastAPI) -> Browser(Frontend) : 200 OK {translation}",
        "Browser(Frontend) -> WebSpeechAPI : speak(translatedText)",
        "WebSpeechAPI -> User : audioOutput"
    ]
    draw_page(title, description, diagram)

    c.save()
    print(f"✅ PDF report generated successfully: {filename}")
    return filename

if __name__ == "__main__":
    print("🚀 Generating ShabdSetu System Design Report PDF...")
    try:
        pdf_file = create_diagram_report()
        print(f"🎉 Success! Open the file: {pdf_file}")
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
