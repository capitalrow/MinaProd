#!/usr/bin/env python3
"""
Comprehensive Live Transcription System Test
Tests the complete workflow end-to-end before manual testing
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime

class LiveTranscriptionTester:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        result = f"{status} {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        print(result)
        
    async def test_enhanced_websocket_server(self):
        """Test 1: Enhanced WebSocket Server Connectivity"""
        print("\n🔍 TEST 1: Enhanced WebSocket Server")
        print("-" * 50)
        
        try:
            # Test connection to Enhanced WebSocket server
            async with websockets.connect('ws://localhost:8774') as ws:
                # Test welcome message
                welcome = await asyncio.wait_for(ws.recv(), timeout=5)
                welcome_data = json.loads(welcome)
                
                if welcome_data.get('type') == 'connected':
                    self.log_test("WebSocket Server Connection", True, f"Server: {welcome_data.get('server', 'Unknown')}")
                else:
                    self.log_test("WebSocket Server Connection", False, f"Unexpected welcome: {welcome_data}")
                    return False
                
                # Test session management
                session_id = f"test_session_{int(time.time())}"
                await ws.send(json.dumps({
                    'type': 'join_session',
                    'session_id': session_id
                }))
                
                session_response = await asyncio.wait_for(ws.recv(), timeout=5)
                session_data = json.loads(session_response)
                
                if session_data.get('type') == 'session_joined':
                    self.log_test("Session Management", True, f"Session: {session_id}")
                else:
                    self.log_test("Session Management", False, f"Session join failed: {session_data}")
                    return False
                
                return True
                
        except Exception as e:
            self.log_test("WebSocket Server Connection", False, f"Connection failed: {e}")
            return False
    
    async def test_audio_processing_pipeline(self):
        """Test 2: Audio Processing Pipeline"""
        print("\n🔍 TEST 2: Audio Processing Pipeline")
        print("-" * 50)
        
        try:
            async with websockets.connect('ws://localhost:8774') as ws:
                # Setup session
                welcome = await ws.recv()
                session_id = f"audio_test_{int(time.time())}"
                await ws.send(json.dumps({
                    'type': 'join_session', 
                    'session_id': session_id
                }))
                await ws.recv()  # session_joined response
                
                # Test different audio chunk sizes
                test_chunks = [
                    (b'\x1A\x45\xDF\xA3' + b'\x00' * 500, "Small chunk (504 bytes)"),
                    (b'\x1A\x45\xDF\xA3' + b'\x00' * 1500, "Medium chunk (1504 bytes)"),
                    (b'\x1A\x45\xDF\xA3' + b'\x00' * 3000, "Large chunk (3004 bytes)")
                ]
                
                for audio_data, description in test_chunks:
                    start_time = time.time()
                    await ws.send(audio_data)
                    
                    # Wait for interim response
                    try:
                        interim = await asyncio.wait_for(ws.recv(), timeout=5)
                        interim_data = json.loads(interim)
                        
                        if interim_data.get('processing'):
                            interim_latency = (time.time() - start_time) * 1000
                            self.log_test(f"Interim Response - {description}", True, f"{interim_latency:.1f}ms")
                            
                            # Wait for final response
                            try:
                                final = await asyncio.wait_for(ws.recv(), timeout=15)
                                final_data = json.loads(final)
                                
                                if final_data.get('type') == 'transcription_result':
                                    total_latency = (time.time() - start_time) * 1000
                                    self.log_test(f"Final Response - {description}", True, 
                                                f"{total_latency:.1f}ms, Text: \"{final_data.get('text', '')[:30]}\"")
                                else:
                                    self.log_test(f"Final Response - {description}", False, "Wrong response type")
                                    
                            except asyncio.TimeoutError:
                                self.log_test(f"Final Response - {description}", False, "Timeout waiting for final result")
                                
                        else:
                            self.log_test(f"Interim Response - {description}", False, "No processing indicator")
                            
                    except asyncio.TimeoutError:
                        self.log_test(f"Interim Response - {description}", False, "Timeout waiting for interim response")
                
                return True
                
        except Exception as e:
            self.log_test("Audio Processing Pipeline", False, f"Pipeline test failed: {e}")
            return False
    
    def test_frontend_integration(self):
        """Test 3: Frontend Integration"""
        print("\n🔍 TEST 3: Frontend Integration")
        print("-" * 50)
        
        try:
            # Check if live page loads
            response = requests.get('http://localhost:5000/live', timeout=10)
            if response.status_code == 200:
                self.log_test("Live Page Loading", True, f"Status: {response.status_code}")
                
                # Check for critical JavaScript files
                content = response.text
                
                js_checks = [
                    ('Real Whisper Integration Script', 'real_whisper_integration.js' in content),
                    ('Force Flag Set', 'FORCE_REAL_WHISPER_INTEGRATION = true' in content),
                    ('Competing Systems Disabled', 'DISABLE_RECORDING_WIRING = true' in content),
                    ('Button Event Binding', 'DOMContentLoaded' in content),
                    ('Performance Monitoring', 'performanceMonitor' in content)
                ]
                
                for check_name, passed in js_checks:
                    self.log_test(check_name, passed)
                
                return True
            else:
                self.log_test("Live Page Loading", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Frontend Integration", False, f"Request failed: {e}")
            return False
    
    async def test_complete_workflow_simulation(self):
        """Test 4: Complete Workflow Simulation"""
        print("\n🔍 TEST 4: Complete Workflow Simulation")
        print("-" * 50)
        
        try:
            # Simulate the exact user workflow
            print("    Simulating: 'This is an audio recording. I am testing this.'")
            
            async with websockets.connect('ws://localhost:8774') as ws:
                # Setup
                await ws.recv()  # welcome
                session_id = f"workflow_test_{int(time.time())}"
                await ws.send(json.dumps({'type': 'join_session', 'session_id': session_id}))
                await ws.recv()  # session_joined
                
                # Simulate audio chunks for the sentence
                test_chunks = [
                    (b'\x1A\x45\xDF\xA3' + b'chunk1_audio_data' * 50, "Chunk 1: 'This is an'"),
                    (b'\x1A\x45\xDF\xA3' + b'chunk2_audio_data' * 50, "Chunk 2: 'audio recording'"),
                    (b'\x1A\x45\xDF\xA3' + b'chunk3_audio_data' * 50, "Chunk 3: 'I am testing'"),
                    (b'\x1A\x45\xDF\xA3' + b'chunk4_audio_data' * 50, "Chunk 4: 'this'")
                ]
                
                cumulative_results = []
                
                for i, (audio_data, description) in enumerate(test_chunks, 1):
                    print(f"    📤 Sending {description}")
                    start_time = time.time()
                    
                    await ws.send(audio_data)
                    
                    # Get interim response
                    interim = await asyncio.wait_for(ws.recv(), timeout=5)
                    interim_data = json.loads(interim)
                    
                    # Get final response
                    final = await asyncio.wait_for(ws.recv(), timeout=15)
                    final_data = json.loads(final)
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    if final_data.get('text'):
                        cumulative_results.append(final_data['text'])
                        cumulative_text = ' '.join(cumulative_results)
                        
                        self.log_test(f"Chunk {i} Processing", True, 
                                    f"{processing_time:.1f}ms → \"{cumulative_text[:50]}\"")
                    else:
                        self.log_test(f"Chunk {i} Processing", False, "No transcription text")
                
                # Test progressive building
                if len(cumulative_results) >= 3:
                    self.log_test("Progressive Transcript Building", True, 
                                f"Built {len(cumulative_results)} chunks into continuous text")
                else:
                    self.log_test("Progressive Transcript Building", False, 
                                f"Only {len(cumulative_results)} chunks processed")
                
                return True
                
        except Exception as e:
            self.log_test("Complete Workflow Simulation", False, f"Workflow failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🧪 COMPREHENSIVE LIVE TRANSCRIPTION SYSTEM TEST")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        test_1 = await self.test_enhanced_websocket_server()
        test_2 = await self.test_audio_processing_pipeline() if test_1 else False
        test_3 = self.test_frontend_integration()
        test_4 = await self.test_complete_workflow_simulation() if test_1 else False
        
        # Summary
        print("\n📊 TEST SUMMARY")
        print("=" * 70)
        
        for result in self.test_results:
            print(result)
        
        print(f"\n🎯 OVERALL RESULT: {self.passed_tests}/{self.total_tests} tests passed")
        
        if self.passed_tests == self.total_tests:
            print("✅ ALL TESTS PASSED - System ready for manual testing!")
            print("\n🎤 You can now safely test:")
            print("  1. Click 'Start Recording'")
            print("  2. Say: 'This is an audio recording. I am testing this.'")
            print("  3. Watch progressive transcription appear")
            print("  4. Click 'Stop Recording' for final transcript")
        else:
            print("❌ SOME TESTS FAILED - Issues need to be fixed before manual testing")
            print("\n🔧 Recommended actions:")
            if not test_1:
                print("  - Check Enhanced WebSocket Server is running on port 8774")
            if not test_3:
                print("  - Verify frontend integration and script loading")
            if not test_4:
                print("  - Debug audio processing pipeline")
        
        return self.passed_tests == self.total_tests

async def main():
    tester = LiveTranscriptionTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test framework error: {e}")
        exit(1)