#!/usr/bin/env python3
"""Quick transcription test to validate endpoints"""

import requests
import io
import time

def test_transcription():
    url = "http://localhost:5000/api/transcribe-audio"
    
    # Create simple test audio data
    test_data = b'webm\x00\x00\x00\x1a\x45\xdf\xa3' + b'\x01\x02\x03\x04' * 1000
    
    files = {'audio': ('test.webm', test_data, 'audio/webm')}
    data = {
        'session_id': f'test_session_{int(time.time())}',
        'chunk_id': '1'
    }
    
    print("🧪 Testing transcription endpoint...")
    
    try:
        response = requests.post(url, files=files, data=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            result = response.json()
            print(f"Response: {result}")
            
            if result.get('success'):
                print("✅ Transcription successful!")
                if result.get('transcript'):
                    print(f"Transcript: {result['transcript']}")
            else:
                print("❌ Transcription failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
        else:
            print("❌ Non-JSON response:")
            print(response.text[:200])
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def test_health():
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(response.json())
    except Exception as e:
        print(f"Health check failed: {e}")

if __name__ == "__main__":
    test_health()
    test_transcription()