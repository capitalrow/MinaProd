#!/usr/bin/env python3
"""
🧪 WEBSOCKET & FRONTEND INTEGRATION TESTS
Focused tests for WebSocket connection and frontend transcription updates
"""

import asyncio
import json
import logging
import os
import time
import numpy as np
import requests
import socketio
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTranscriptionTest:
    """Test WebSocket connection and transcription flow."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.websocket_messages = []
        self.transcription_received = False
        self.session_joined = False
        self.connection_successful = False
        
    def generate_conversation_audio_bytes(self, duration_seconds: float = 120.0) -> bytes:
        """Generate longer conversation-like audio for comprehensive testing."""
        try:
            import wave
            from io import BytesIO
            
            sample_rate = 16000
            t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
            
            # Create conversation-like audio with varying patterns
            conversation_audio = np.zeros_like(t)
            
            # Simulate conversation segments with pauses
            segment_duration = 8.0  # Each speaking segment
            pause_duration = 2.0    # Pause between speakers
            
            current_time = 0
            while current_time < duration_seconds - segment_duration:
                # Speaking segment 1 (Person A)
                start_idx = int(current_time * sample_rate)
                end_idx = int((current_time + segment_duration) * sample_rate)
                if end_idx <= len(conversation_audio):
                    segment_t = t[start_idx:end_idx] - current_time
                    
                    # Generate speech-like patterns with varying formants
                    speech = (
                        0.4 * np.sin(2 * np.pi * 200 * segment_t) +  # Fundamental
                        0.3 * np.sin(2 * np.pi * 400 * segment_t) +  # First formant
                        0.2 * np.sin(2 * np.pi * 800 * segment_t) +  # Second formant
                        0.1 * np.sin(2 * np.pi * 1600 * segment_t)   # Third formant
                    )
                    
                    # Add amplitude modulation to simulate speech patterns
                    envelope = 0.5 * (1 + np.sin(2 * np.pi * 3 * segment_t))
                    speech *= envelope
                    
                    # Add realistic noise
                    noise = 0.05 * np.random.normal(0, 1, len(speech))
                    conversation_audio[start_idx:end_idx] = speech + noise
                
                current_time += segment_duration + pause_duration
                
                # Speaking segment 2 (Person B) - different characteristics
                if current_time < duration_seconds - segment_duration:
                    start_idx = int(current_time * sample_rate)
                    end_idx = int((current_time + segment_duration) * sample_rate)
                    if end_idx <= len(conversation_audio):
                        segment_t = t[start_idx:end_idx] - current_time
                        
                        # Different speaker characteristics (higher pitch)
                        speech = (
                            0.3 * np.sin(2 * np.pi * 250 * segment_t) +  # Higher fundamental
                            0.4 * np.sin(2 * np.pi * 500 * segment_t) +  # First formant
                            0.2 * np.sin(2 * np.pi * 1000 * segment_t) + # Second formant
                            0.1 * np.sin(2 * np.pi * 2000 * segment_t)   # Third formant
                        )
                        
                        # Different speech rhythm
                        envelope = 0.6 * (1 + np.sin(2 * np.pi * 4 * segment_t))
                        speech *= envelope
                        
                        noise = 0.05 * np.random.normal(0, 1, len(speech))
                        conversation_audio[start_idx:end_idx] = speech + noise
                
                current_time += segment_duration + pause_duration
            
            # Normalize and convert to 16-bit PCM
            conversation_audio = np.clip(conversation_audio, -1.0, 1.0)
            audio_int16 = (conversation_audio * 32767).astype(np.int16)
            
            # Create proper WAV file in memory
            wav_buffer = BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to generate conversation audio: {e}")
            # Fallback to simple audio
            return self.generate_test_audio_bytes(duration_seconds)

    def generate_test_audio_bytes(self, duration_seconds: float = 2.0) -> bytes:
        """Generate basic test audio for simple tests."""
        try:
            import wave
            from io import BytesIO
            
            sample_rate = 16000
            t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
            
            # Generate speech-like audio with multiple frequencies
            frequencies = [440, 880, 1320]  # A4, A5, E6
            audio = np.sum([0.3 * np.sin(2 * np.pi * f * t) for f in frequencies], axis=0)
            
            # Add noise to make it more realistic
            noise = 0.1 * np.random.normal(0, 1, len(audio))
            audio = audio + noise
            
            # Convert to 16-bit PCM
            audio = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio * 32767).astype(np.int16)
            
            # Create proper WAV file in memory
            wav_buffer = BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            wav_buffer.seek(0)
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Failed to generate WAV: {e}, using fallback")
            # Fallback to PCM if WAV generation fails
            sample_rate = 16000
            t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds), False)
            frequencies = [440, 880, 1320]
            audio = np.sum([0.3 * np.sin(2 * np.pi * f * t) for f in frequencies], axis=0)
            audio = np.clip(audio, -1.0, 1.0)
            audio_int16 = (audio * 32767).astype(np.int16)
            return audio_int16.tobytes()

    async def test_basic_connection(self) -> Dict[str, Any]:
        """Test basic WebSocket connection."""
        logger.info("🧪 Testing basic WebSocket connection...")
        
        result = {
            'test_name': 'Basic Connection',
            'status': 'running',
            'connection_successful': False,
            'error': None
        }
        
        sio = socketio.AsyncClient()
        
        @sio.event
        async def connect():
            logger.info("✅ WebSocket connected")
            result['connection_successful'] = True
            self.connection_successful = True
            
        @sio.event
        async def error(data):
            logger.error(f"❌ Connection error: {data}")
            result['error'] = data
        
        try:
            await sio.connect(self.base_url, wait_timeout=10)
            await asyncio.sleep(2)  # Allow connection to stabilize
            result['status'] = 'completed'
        except Exception as e:
            logger.error(f"💥 Connection failed: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
        finally:
            try:
                await sio.disconnect()
            except:
                pass
                
        return result

    async def test_session_joining(self) -> Dict[str, Any]:
        """Test session joining protocol."""
        logger.info("🧪 Testing session joining...")
        
        result = {
            'test_name': 'Session Joining',
            'status': 'running',
            'session_joined': False,
            'session_data': None,
            'error': None
        }
        
        sio = socketio.AsyncClient()
        
        @sio.event
        async def connect():
            logger.info("✅ Connected for session test")
            
        @sio.event
        async def joined_session(data):
            logger.info(f"✅ Session joined successfully: {data}")
            result['session_joined'] = True
            result['session_data'] = data
            self.session_joined = True
            
        @sio.event
        async def error(data):
            logger.error(f"❌ Session join error: {data}")
            result['error'] = data
        
        try:
            await sio.connect(self.base_url, wait_timeout=10)
            await asyncio.sleep(1)
            
            # Test session joining
            session_id = f"test_session_{int(time.time())}"
            logger.info(f"🔗 Attempting to join session: {session_id}")
            
            await sio.emit('join_session', {'session_id': session_id})
            await asyncio.sleep(3)  # Wait for response
            
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"💥 Session join test failed: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
        finally:
            try:
                await sio.disconnect()
            except:
                pass
                
        return result

    async def test_conversation_transcription(self) -> Dict[str, Any]:
        """Test comprehensive conversation transcription over 2+ minutes."""
        logger.info("🧪 Testing full conversation transcription (2+ minutes)...")
        
        result = {
            'test_name': 'Conversation Transcription',
            'status': 'running',
            'audio_chunks_sent': 0,
            'audio_acknowledged': 0,
            'transcription_responses': 0,
            'pipeline_working': False,
            'messages_received': [],
            'conversation_segments': [],
            'total_transcribed_text': '',
            'test_duration_seconds': 0,
            'error': None
        }
        
        sio = socketio.AsyncClient()
        session_id = f"conversation_test_{int(time.time())}"
        start_time = time.time()
        
        @sio.event
        async def connect():
            logger.info("✅ Connected for conversation test")
            
        @sio.event
        async def joined_session(data):
            logger.info(f"✅ Conversation test session joined: {data}")
            
        @sio.event
        async def audio_received(data):
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def audio_acknowledged(data):
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def ack(data):
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def interim_transcript(data):
            logger.info(f"📝 Interim transcript: {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('interim', data))
            result['conversation_segments'].append(data.get('text', ''))
            result['total_transcribed_text'] += data.get('text', '') + ' '
            result['pipeline_working'] = True
            
        @sio.event
        async def final_transcript(data):
            logger.info(f"📝 Final transcript: {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('final', data))
            result['conversation_segments'].append(data.get('text', ''))
            result['total_transcribed_text'] += data.get('text', '') + ' '
            result['pipeline_working'] = True
            
        @sio.event
        async def error(data):
            logger.error(f"❌ Conversation test error: {data}")
            result['error'] = data
        
        try:
            # Connect and join session
            await sio.connect(self.base_url, wait_timeout=15)
            await asyncio.sleep(2)
            
            await sio.emit('join_session', {'session_id': session_id})
            await asyncio.sleep(3)
            
            # Generate and send 2+ minute conversation
            logger.info("🎵 Generating 2+ minute conversation audio...")
            conversation_audio = self.generate_conversation_audio_bytes(duration_seconds=130.0)
            chunk_size = 8192  # Larger chunks for longer audio
            
            logger.info(f"🎵 Sending {len(conversation_audio)} bytes of conversation audio...")
            
            # Send audio in chunks with realistic timing
            import base64
            for i in range(0, len(conversation_audio), chunk_size):
                chunk = conversation_audio[i:i + chunk_size]
                
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                # Calculate RMS for the chunk
                if len(chunk) >= 2:
                    audio_chunk = chunk[44:] if i == 0 and chunk.startswith(b'RIFF') else chunk
                    if len(audio_chunk) >= 2:
                        try:
                            chunk_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                            rms = float(np.sqrt(np.mean(chunk_array ** 2)))
                        except:
                            rms = 0.15  # Default for conversation audio
                    else:
                        rms = 0.15
                else:
                    rms = 0.15
                
                await sio.emit('audio_chunk', {
                    'session_id': session_id,
                    'audio_data_b64': chunk_b64,
                    'is_final_chunk': False,
                    'mime_type': 'audio/wav',
                    'rms': rms,
                    'ts_client': int(time.time() * 1000)
                })
                
                result['audio_chunks_sent'] += 1
                
                # Realistic delay between chunks (simulate real-time)
                await asyncio.sleep(0.5)
                
                if result['audio_chunks_sent'] % 10 == 0:
                    logger.info(f"📊 Sent {result['audio_chunks_sent']} conversation chunks, received {result['transcription_responses']} transcriptions...")
            
            # Send final chunk signal
            await sio.emit('audio_data', {
                'session_id': session_id,
                'audio_data_b64': '',
                'is_final_chunk': True,
                'mime_type': 'audio/wav',
                'rms': 0.0,
                'ts_client': int(time.time() * 1000)
            })
            result['audio_chunks_sent'] += 1
            logger.info("🏁 Sent final conversation chunk signal")
            
            # Wait for all transcription processing to complete
            logger.info("⏳ Waiting for complete conversation transcription...")
            await asyncio.sleep(30)  # Longer wait for full conversation
            
            result['test_duration_seconds'] = time.time() - start_time
            result['status'] = 'completed'
            
            # Log conversation results
            logger.info(f"🎭 Conversation transcription complete:")
            logger.info(f"   📊 Chunks sent: {result['audio_chunks_sent']}")
            logger.info(f"   📝 Transcriptions received: {result['transcription_responses']}")
            logger.info(f"   📰 Total text: '{result['total_transcribed_text'][:100]}...'")
            logger.info(f"   ⏱️  Test duration: {result['test_duration_seconds']:.1f}s")
            
        except Exception as e:
            logger.error(f"💥 Conversation transcription test failed: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
        finally:
            try:
                await sio.disconnect()
            except:
                pass
                
        return result

    async def test_audio_transmission(self) -> Dict[str, Any]:
        """Test audio data transmission and transcription response."""
        logger.info("🧪 Testing audio transmission and transcription...")
        
        result = {
            'test_name': 'Audio Transmission',
            'status': 'running',
            'audio_chunks_sent': 0,
            'audio_acknowledged': 0,
            'transcription_responses': 0,
            'pipeline_working': False,
            'messages_received': [],
            'error': None
        }
        
        sio = socketio.AsyncClient()
        session_id = f"test_audio_{int(time.time())}"
        
        @sio.event
        async def connect():
            logger.info("✅ Connected for audio test")
            
        @sio.event
        async def joined_session(data):
            logger.info(f"✅ Audio test session joined: {data}")
            
        @sio.event
        async def audio_received(data):
            logger.info(f"🎵 Server acknowledged audio: {data}")
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def audio_acknowledged(data):
            logger.info(f"🎵 Audio acknowledged: {data}")
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def ack(data):
            logger.info(f"🎵 Audio ack: {data}")
            result['audio_acknowledged'] += 1
            
        @sio.event
        async def interim_transcript(data):
            logger.info(f"📝 Interim transcript: {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('interim', data))
            result['pipeline_working'] = True
            
        @sio.event
        async def transcript_partial(data):
            logger.info(f"📝 Partial transcript: {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('partial', data))
            result['pipeline_working'] = True
            
        @sio.event
        async def transcript_final(data):
            logger.info(f"📝 Final transcript: {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('final', data))
            result['pipeline_working'] = True
            
        @sio.event
        async def final_transcript(data):
            logger.info(f"📝 Final transcript (alt): {data}")
            result['transcription_responses'] += 1
            result['messages_received'].append(('final_alt', data))
            result['pipeline_working'] = True
            
        @sio.event
        async def error(data):
            logger.error(f"❌ Audio test error: {data}")
            result['error'] = data
        
        try:
            # Connect and join session
            await sio.connect(self.base_url, wait_timeout=10)
            await asyncio.sleep(1)
            
            await sio.emit('join_session', {'session_id': session_id})
            await asyncio.sleep(2)
            
            # Generate and send test audio
            logger.info("🎵 Generating test audio...")
            test_audio = self.generate_test_audio_bytes(duration_seconds=3.0)
            chunk_size = 4096  # Send in reasonable chunks
            
            logger.info(f"🎵 Sending {len(test_audio)} bytes of audio in chunks...")
            
            # Send audio in chunks with correct WebSocket format
            import base64
            for i in range(0, len(test_audio), chunk_size):
                chunk = test_audio[i:i + chunk_size]
                
                # Encode chunk as base64 (as expected by the WebSocket handler)
                chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                
                # Calculate RMS for the chunk (handle WAV data properly)
                if len(chunk) >= 2:
                    # For WAV data, skip header if this is the first chunk and calculate RMS from audio data
                    audio_chunk = chunk[44:] if i == 0 and chunk.startswith(b'RIFF') else chunk
                    if len(audio_chunk) >= 2:
                        try:
                            chunk_array = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                            rms = float(np.sqrt(np.mean(chunk_array ** 2)))
                        except:
                            rms = 0.1  # Default for valid audio
                    else:
                        rms = 0.1  # Default for valid audio
                else:
                    rms = 0.1
                
                await sio.emit('audio_chunk', {
                    'session_id': session_id,
                    'audio_data_b64': chunk_b64,
                    'is_final_chunk': False,
                    'mime_type': 'audio/wav',  # Proper MIME type for WAV
                    'rms': rms,
                    'ts_client': int(time.time() * 1000)  # milliseconds
                })
                
                result['audio_chunks_sent'] += 1
                await asyncio.sleep(0.2)  # Slightly longer delay between chunks
                
                if result['audio_chunks_sent'] % 3 == 0:
                    logger.info(f"📊 Sent {result['audio_chunks_sent']} chunks so far...")
            
            # Send final chunk signal
            await sio.emit('audio_data', {
                'session_id': session_id,
                'audio_data_b64': '',
                'is_final_chunk': True,
                'mime_type': 'audio/pcm',
                'rms': 0.0,
                'ts_client': int(time.time() * 1000)
            })
            result['audio_chunks_sent'] += 1
            logger.info("🏁 Sent final chunk signal")
            
            # Wait for transcription responses
            logger.info("⏳ Waiting for transcription responses...")
            await asyncio.sleep(8)  # Wait longer for processing
            
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"💥 Audio transmission test failed: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
        finally:
            try:
                await sio.disconnect()
            except:
                pass
                
        return result

    async def test_frontend_integration(self) -> Dict[str, Any]:
        """Test frontend page loading and basic functionality."""
        logger.info("🧪 Testing frontend integration...")
        
        result = {
            'test_name': 'Frontend Integration',
            'status': 'running',
            'homepage_accessible': False,
            'live_page_accessible': False,
            'api_stats_working': False,
            'static_assets_loading': False,
            'error': None
        }
        
        try:
            # Test homepage
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                result['homepage_accessible'] = True
                logger.info("✅ Homepage accessible")
            
            # Test live transcription page
            response = requests.get(f"{self.base_url}/live", timeout=10)
            if response.status_code == 200:
                result['live_page_accessible'] = True
                logger.info("✅ Live transcription page accessible")
                
                # Check if page contains expected elements
                if 'websocket' in response.text.lower() or 'recording' in response.text.lower():
                    logger.info("✅ Live page contains transcription elements")
            
            # Test API stats endpoint
            response = requests.get(f"{self.base_url}/api/stats", timeout=10)
            if response.status_code == 200:
                try:
                    stats_data = response.json()
                    result['api_stats_working'] = True
                    result['stats_data'] = stats_data
                    logger.info(f"✅ API stats working: {stats_data}")
                except:
                    logger.warning("⚠️ API stats endpoint returns non-JSON data")
            
            # Test static asset loading
            response = requests.get(f"{self.base_url}/static/js/websocket_streaming.js", timeout=10)
            if response.status_code == 200:
                result['static_assets_loading'] = True
                logger.info("✅ Static assets loading correctly")
            
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"💥 Frontend integration test failed: {e}")
            result['error'] = str(e)
            result['status'] = 'failed'
        
        return result

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all WebSocket and frontend tests."""
        logger.info("🚀 Starting WebSocket and Frontend Integration Tests...")
        
        comprehensive_results = {
            'test_run_id': f"websocket_test_{int(time.time())}",
            'start_time': time.time(),
            'tests': {},
            'summary': {},
            'status': 'running'
        }
        
        tests = [
            self.test_frontend_integration,
            self.test_basic_connection,
            self.test_session_joining,
            self.test_conversation_transcription,  # Comprehensive 2+ minute conversation test
            self.test_audio_transmission,
        ]
        
        passed = 0
        failed = 0
        
        for test_func in tests:
            try:
                result = await test_func()
                test_name = result['test_name']
                comprehensive_results['tests'][test_name] = result
                
                if result['status'] == 'completed' and not result.get('error'):
                    passed += 1
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    failed += 1
                    logger.warning(f"❌ {test_name} FAILED: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                failed += 1
                logger.error(f"💥 Test error: {e}")
        
        comprehensive_results['end_time'] = time.time()
        comprehensive_results['duration'] = comprehensive_results['end_time'] - comprehensive_results['start_time']
        comprehensive_results['status'] = 'completed'
        
        # Generate summary
        total_tests = passed + failed
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        comprehensive_results['summary'] = {
            'total_tests': total_tests,
            'tests_passed': passed,
            'tests_failed': failed,
            'success_rate': success_rate,
            'overall_status': 'PASS' if failed == 0 else 'FAIL',
            'recommendations': self._generate_recommendations(comprehensive_results)
        }
        
        return comprehensive_results
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on test results."""
        recommendations = []
        
        # Check each test
        tests = results.get('tests', {})
        
        frontend_test = tests.get('Frontend Integration', {})
        if not frontend_test.get('homepage_accessible'):
            recommendations.append("Homepage not accessible - check server routing")
        if not frontend_test.get('live_page_accessible'):
            recommendations.append("Live transcription page not accessible - check /live route")
        if not frontend_test.get('api_stats_working'):
            recommendations.append("API stats endpoint not working - check /api/stats route")
        
        connection_test = tests.get('Basic Connection', {})
        if not connection_test.get('connection_successful'):
            recommendations.append("WebSocket connection failing - check socketio configuration and on_connect handler")
        
        session_test = tests.get('Session Joining', {})
        if not session_test.get('session_joined'):
            recommendations.append("Session joining not working - check join_session WebSocket handler")
        
        audio_test = tests.get('Audio Transmission', {})
        if audio_test.get('audio_chunks_sent', 0) > 0 and audio_test.get('audio_acknowledged', 0) == 0:
            recommendations.append("Audio not being acknowledged by server - check audio_data WebSocket handler")
        if not audio_test.get('pipeline_working'):
            recommendations.append("Transcription pipeline not working - check audio processing and OpenAI integration")
        
        if not recommendations:
            recommendations.append("All tests passed! WebSocket and frontend integration working correctly.")
        
        return recommendations

async def main():
    """Run the WebSocket integration tests."""
    # Check if server is running
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        logger.info("✅ Server is running, starting WebSocket tests...")
    except Exception as e:
        logger.error(f"❌ Server not accessible: {e}")
        logger.info("Please ensure the server is running with: python main.py")
        return
    
    tester = WebSocketTranscriptionTest()
    results = await tester.run_all_tests()
    
    # Print formatted results
    print("\n" + "="*80)
    print("🧪 WEBSOCKET & FRONTEND INTEGRATION TEST RESULTS")
    print("="*80)
    print(f"Test Run ID: {results['test_run_id']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Tests Passed: {results['summary']['tests_passed']}")
    print(f"Tests Failed: {results['summary']['tests_failed']}")
    print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
    print(f"Overall Status: {results['summary']['overall_status']}")
    print()
    
    print("📊 DETAILED TEST RESULTS:")
    for test_name, test_result in results['tests'].items():
        status = test_result.get('status', 'unknown')
        error = test_result.get('error', '')
        
        if status == 'completed' and not error:
            print(f"  ✅ {test_name}: PASSED")
        else:
            print(f"  ❌ {test_name}: FAILED")
            if error:
                print(f"      Error: {error}")
        
        # Show specific metrics for audio test
        if test_name == 'Audio Transmission':
            print(f"      Audio chunks sent: {test_result.get('audio_chunks_sent', 0)}")
            print(f"      Audio acknowledged: {test_result.get('audio_acknowledged', 0)}")
            print(f"      Transcription responses: {test_result.get('transcription_responses', 0)}")
    
    print("\n💡 RECOMMENDATIONS:")
    for rec in results['summary']['recommendations']:
        print(f"  • {rec}")
    
    print("\n📋 FULL RESULTS (JSON):")
    print(json.dumps(results, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())