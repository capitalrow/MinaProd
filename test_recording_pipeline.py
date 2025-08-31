#!/usr/bin/env python3
"""Test the recording pipeline after fixes."""

import requests
import json
import time
import os

def test_health():
    """Test the health endpoint."""
    print("Testing health endpoint...")
    r = requests.get('http://localhost:5000/api/health')
    if r.status_code == 200:
        health = r.json()
        print(f"✅ Health check passed: {health['status']}")
        print(f"   Database: {health['database']}")
        print(f"   System: {health['system']}")
        return True
    else:
        print(f"❌ Health check failed: {r.status_code}")
        return False

def test_frontend():
    """Test frontend page loads."""
    print("\nTesting frontend page...")
    r = requests.get('http://localhost:5000/live')
    if r.status_code == 200:
        # Check for critical elements
        content = r.text
        checks = {
            'Toast system': 'toast_notifications.js' in content,
            'Professional recorder': 'professional_recorder.js' in content,
            'Real Whisper': 'real_whisper_integration.js' in content,
            'Record button': 'recordButton' in content,
            'Transcript display': 'transcript-container' in content
        }
        
        all_passed = True
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
            if not result:
                all_passed = False
        
        return all_passed
    else:
        print(f"❌ Frontend page failed: {r.status_code}")
        return False

def generate_test_audio():
    """Generate a test audio file."""
    import wave
    import struct
    
    print("\nGenerating test audio...")
    sample_rate = 16000
    duration = 2
    samples = []
    
    for i in range(sample_rate * duration):
        value = int(16000 * (0.5 + 0.5 * (i % 1000) / 1000))
        samples.append(struct.pack('<h', value))
    
    with wave.open('/tmp/test_audio.wav', 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b''.join(samples))
    
    print("✅ Test audio generated")
    return '/tmp/test_audio.wav'

def test_transcription():
    """Test the transcription endpoint."""
    print("\nTesting transcription endpoint...")
    
    # Generate test audio
    audio_path = generate_test_audio()
    
    # Test transcription
    with open(audio_path, 'rb') as f:
        files = {'audio': ('test.wav', f, 'audio/wav')}
        data = {'session_id': f'test_{int(time.time())}'}
        
        start = time.time()
        r = requests.post('http://localhost:5000/api/transcribe', 
                         files=files, data=data, timeout=15)
        elapsed = time.time() - start
        
        print(f"   Response time: {elapsed:.2f}s")
        
        if r.status_code == 200:
            result = r.json()
            print(f"✅ Transcription successful")
            print(f"   Transcript: {result.get('transcript', '')[:100]}")
            print(f"   Processing time: {result.get('processing_time', 0):.2f}s")
            print(f"   Segments: {result.get('segment_count', 0)}")
            return True
        else:
            print(f"❌ Transcription failed: {r.status_code}")
            print(f"   Error: {r.text[:200]}")
            return False

def main():
    """Run all tests."""
    print("="*60)
    print("🧪 TESTING MINA RECORDING PIPELINE")
    print("="*60)
    
    results = {
        'Health Check': test_health(),
        'Frontend Load': test_frontend(),
        'Transcription': test_transcription()
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! The recording pipeline is working.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please review the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)