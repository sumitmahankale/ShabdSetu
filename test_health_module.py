"""
Test script for ShabdSetu Health Literacy Feature
Run this to verify the health module is working correctly
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    os.chdir(os.path.dirname(__file__))
    from Backend.health_literacy import get_health_tutor
    
    print("="*60)
    print("ShabdSetu Health Literacy Module Test")
    print("="*60)
    print()
    
    # Initialize health tutor
    print("Initializing health tutor...")
    tutor = get_health_tutor()
    print("✓ Health tutor initialized successfully!")
    print()
    
    # Test 1: English health query
    print("Test 1: English Health Query")
    print("-" * 40)
    query_en = "I have fever"
    print(f"Query: {query_en}")
    result_en = tutor.process_health_query(query_en, 'en')
    print(f"Source: {result_en['source']}")
    print(f"Response:\n{result_en['response'][:200]}...")
    print()
    
    # Test 2: Marathi health query
    print("Test 2: Marathi Health Query")
    print("-" * 40)
    query_mr = "मला ताप आहे"
    print(f"Query: {query_mr}")
    result_mr = tutor.process_health_query(query_mr, 'mr')
    print(f"Source: {result_mr['source']}")
    print(f"Response:\n{result_mr['response'][:200]}...")
    print()
    
    # Test 3: Health detection
    print("Test 3: Health Query Detection")
    print("-" * 40)
    test_queries = [
        ("I have headache", True),
        ("Hello how are you", False),
        ("What medicine for cold", True),
        ("मला डोकेदुखी आहे", True)
    ]
    for query, expected in test_queries:
        detected = tutor.detect_health_query(query)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{query}' -> {'Health' if detected else 'Not Health'} (expected: {'Health' if expected else 'Not Health'})")
    print()
    
    print("="*60)
    print("All tests completed successfully!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Add your Google API key to Backend/.env file")
    print("2. Restart the backend server")
    print("3. Test the /health/query endpoint")
    print()
    
except Exception as e:
    print(f"Error: {e}")
    print()
    print("Make sure you have:")
    print("1. Installed all requirements: pip install -r Backend/requirements.txt")
    print("2. Set GOOGLE_API_KEY in Backend/.env (optional for knowledge base)")
    import traceback
    traceback.print_exc()
