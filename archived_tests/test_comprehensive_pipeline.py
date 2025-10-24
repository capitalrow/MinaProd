#!/usr/bin/env python3
"""
🎯 Comprehensive Pipeline Test & Performance Profiling
Tests the entire transcription pipeline end-to-end with detailed metrics.
"""

import time
import json
import requests
import numpy as np
import wave
import struct
import tempfile
import os
from datetime import datetime

class PipelineProfiler:
    """Profile the live transcription pipeline comprehensively."""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.metrics = {
            'latency': [],
            'chunk_sizes': [],
            'response_times': [],
            'errors': [],
            'success_rate': 0
        }
        
    def create_test_audio(self, duration=3, sample_rate=16000):
        """Generate test audio with speech-like patterns."""
        samples = []
        for i in range(sample_rate * duration):
            t = i / sample_rate
            # Create modulated noise to simulate speech
            amplitude = np.sin(2 * np.pi * 2 * t) * 0.3 + 0.5  # Modulation
            noise = np.random.normal(0, amplitude * 16000, 1)[0]
            value = int(np.clip(noise, -32767, 32767))
            samples.append(struct.pack('<h', value))
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(samples))
        
        return temp_file.name
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        print("\n🔍 Testing Health Endpoint...")
        try:
            start = time.time()
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health Check: {data.get('status', 'unknown')}")
                print(f"   API Key: {data.get('api_key_status', 'unknown')}")
                print(f"   Database: {data.get('database_status', 'unknown')}")
                print(f"   Latency: {latency:.2f}ms")
                return True
            else:
                print(f"❌ Health Check Failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            return False
    
    def test_transcription(self, audio_file, session_id=None):
        """Test transcription endpoint with timing."""
        if not session_id:
            session_id = f"test_{int(time.time())}"
        
        print(f"\n📤 Testing Transcription (Session: {session_id})...")
        
        try:
            start = time.time()
            
            with open(audio_file, 'rb') as f:
                files = {'audio': ('test.wav', f, 'audio/wav')}
                data = {'session_id': session_id}
                
                response = requests.post(
                    f"{self.base_url}/api/transcribe",
                    files=files,
                    data=data,
                    timeout=30
                )
            
            latency = (time.time() - start) * 1000
            self.metrics['response_times'].append(latency)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Transcription Success!")
                print(f"   Transcript: {result.get('transcript', 'N/A')[:100]}...")
                print(f"   Segments: {result.get('segment_count', 0)}")
                print(f"   Confidence: {result.get('average_confidence', 0):.2%}")
                print(f"   Latency: {latency:.2f}ms")
                
                # Calculate metrics
                processing_time = result.get('processing_time', 0) * 1000
                if processing_time > 0:
                    print(f"   Processing: {processing_time:.2f}ms")
                
                return True, result
            else:
                print(f"❌ Transcription Failed: HTTP {response.status_code}")
                if response.text:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    print(f"   Error: {error_data.get('error', response.text[:200])}")
                self.metrics['errors'].append({
                    'timestamp': time.time(),
                    'status_code': response.status_code,
                    'error': response.text[:200]
                })
                return False, None
                
        except Exception as e:
            print(f"❌ Transcription Error: {e}")
            self.metrics['errors'].append({
                'timestamp': time.time(),
                'error': str(e)
            })
            return False, None
    
    def run_load_test(self, num_requests=5):
        """Run multiple transcription requests to test load."""
        print(f"\n🚀 Running Load Test ({num_requests} requests)...")
        
        audio_file = self.create_test_audio(duration=2)
        successes = 0
        
        for i in range(num_requests):
            session_id = f"load_test_{i}_{int(time.time())}"
            success, _ = self.test_transcription(audio_file, session_id)
            if success:
                successes += 1
            time.sleep(0.5)  # Small delay between requests
        
        os.unlink(audio_file)
        
        self.metrics['success_rate'] = successes / num_requests
        print(f"\n📊 Load Test Results:")
        print(f"   Success Rate: {self.metrics['success_rate']:.1%}")
        print(f"   Avg Latency: {np.mean(self.metrics['response_times']):.2f}ms")
        print(f"   Max Latency: {np.max(self.metrics['response_times']):.2f}ms")
        print(f"   Min Latency: {np.min(self.metrics['response_times']):.2f}ms")
        print(f"   Errors: {len(self.metrics['errors'])}")
    
    def generate_report(self):
        """Generate comprehensive performance report."""
        print("\n" + "="*60)
        print("📈 COMPREHENSIVE PIPELINE REPORT")
        print("="*60)
        
        print("\n🎯 Performance Metrics:")
        if self.metrics['response_times']:
            print(f"   Average Latency: {np.mean(self.metrics['response_times']):.2f}ms")
            print(f"   P95 Latency: {np.percentile(self.metrics['response_times'], 95):.2f}ms")
            print(f"   P99 Latency: {np.percentile(self.metrics['response_times'], 99):.2f}ms")
        
        print(f"\n📊 Reliability:")
        print(f"   Success Rate: {self.metrics['success_rate']:.1%}")
        print(f"   Total Errors: {len(self.metrics['errors'])}")
        
        if self.metrics['errors']:
            print(f"\n❌ Recent Errors:")
            for error in self.metrics['errors'][-3:]:
                print(f"   - {error}")
        
        print("\n✅ Acceptance Criteria Check:")
        criteria = {
            'Latency < 500ms': np.mean(self.metrics['response_times']) < 500 if self.metrics['response_times'] else False,
            'Success Rate > 90%': self.metrics['success_rate'] > 0.9,
            'Health Check Passing': self.test_health_endpoint()
        }
        
        for criterion, passed in criteria.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {criterion}: {status}")
        
        overall = all(criteria.values())
        print(f"\n{'✅ OVERALL: PASS' if overall else '❌ OVERALL: FAIL'}")
        
        return overall

def main():
    """Run comprehensive pipeline tests."""
    print("🚀 Starting Comprehensive Pipeline Testing...")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    profiler = PipelineProfiler()
    
    # Test health endpoint
    profiler.test_health_endpoint()
    
    # Test single transcription
    audio_file = profiler.create_test_audio()
    profiler.test_transcription(audio_file)
    os.unlink(audio_file)
    
    # Run load test
    profiler.run_load_test(num_requests=3)
    
    # Generate report
    passed = profiler.generate_report()
    
    return 0 if passed else 1

if __name__ == "__main__":
    exit(main())