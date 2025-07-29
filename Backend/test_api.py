#!/usr/bin/env python3
"""
Test script for ShabdSetu Translation API
"""

import asyncio
import httpx
import json

async def test_translation_api():
    """Test the translation API with sample text"""
    
    base_url = "http://localhost:8000"
    
    # Test data
    test_cases = [
        "Hello, how are you?",
        "Good morning! Have a great day.",
        "I love learning new languages.",
        "The weather is beautiful today.",
        "Thank you for your help."
    ]
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing ShabdSetu Translation API\n")
        
        # Test health endpoint
        try:
            response = await client.get(f"{base_url}/")
            print(f"✅ API Status: {response.json()}")
            print()
        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            return
        
        # Test translations
        for i, text in enumerate(test_cases, 1):
            try:
                print(f"Test {i}: Translating '{text}'")
                
                response = await client.post(
                    f"{base_url}/translate",
                    json={
                        "text": text,
                        "source_language": "English",
                        "target_language": "Marathi"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"📝 Original:   {result['original_text']}")
                    print(f"🔄 Translated: {result['translated_text']}")
                    print("✅ Success!\n")
                else:
                    print(f"❌ Failed with status {response.status_code}: {response.text}\n")
                    
            except Exception as e:
                print(f"❌ Error during translation: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_translation_api())
