#!/usr/bin/env python3
"""
Demo test script for AI Agent Builder
Tests the chat functionality with various prompts
"""

import requests
import json
import time
import sys

BASE_URL = "http://127.0.0.1:7860"

def test_prompt(prompt, description):
    """Test a single prompt"""
    print(f"\n{'='*60}")
    print(f"📝 Test: {description}")
    print(f"{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Waiting for response...")
    
    start_time = time.time()
    
    # Make API call
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json={"data": [prompt, [], None, "builder"]},
            timeout=180
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                result = data["data"][0]
                print(f"✅ Response received in {elapsed:.1f}s")
                print(f"Response: {result[:300]}..." if len(str(result)) > 300 else f"Response: {result}")
            else:
                print(f"❌ Invalid response format: {data}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {time.time() - start_time:.1f}s")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("🚀 AI Agent Builder - Demo Test Suite")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}", timeout=5)
        print("✅ Server is running!")
    except:
        print("❌ Server is not responding. Start it with: python3 app.py")
        sys.exit(1)
    
    # Test 1: Simple question
    test_prompt(
        "What is 2+2?",
        "Simple Math Question"
    )
    
    # Test 2: Greeting
    test_prompt(
        "Hello, who are you?",
        "Greeting Test"
    )
    
    # Test 3: List generation
    test_prompt(
        "List 3 colors",
        "List Generation"
    )
    
    # Test 4: Code generation
    test_prompt(
        "Write a simple Python function to add two numbers",
        "Code Generation"
    )
    
    # Test 5: Email task
    test_prompt(
        "send an email to john@example.com with subject Welcome and body Hello John, welcome aboard!",
        "Email Task"
    )
    
    print(f"\n{'='*60}")
    print("✅ Demo test suite completed!")
    print("="*60)

if __name__ == "__main__":
    main()
