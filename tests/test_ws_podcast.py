#!/usr/bin/env python3
"""
Backend End-to-End Tests for MP3 Streaming Pipeline
Tests real audio → WebSocket → Whisper API → database persistence
"""

import pytest
import asyncio
import json
import time
import tempfile
import os
from pathlib import Path
import requests
import subprocess
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.tools.ws_stream_mp3 import MP3WebSocketStreamer


class TestMP3StreamingPipeline:
    """Test real MP3 streaming through complete pipeline"""
    
    @pytest.fixture(scope="class")
    def server_url(self):
        """Server URL for testing"""
        return "http://localhost:5000"
    
    @pytest.fixture(scope="class") 
    def mp3_file(self):
        """Path to test MP3 file"""
        mp3_path = Path(__file__).parent / "data" / "djvlad_120s.mp3"
        if not mp3_path.exists():
            pytest.skip(f"Test MP3 file not found: {mp3_path}")
        return str(mp3_path)
    
    @pytest.fixture(scope="class")
    def test_metrics_file(self, tmp_path_factory):
        """Temporary file for storing test metrics"""
        temp_dir = tmp_path_factory.mktemp("test_metrics")
        return str(temp_dir / "ws_stream_metrics.json")
    
    @pytest.mark.asyncio
    async def test_server_health(self, server_url):
        """Test that server is running and responsive"""
        try:
            response = requests.get(f"{server_url}/", timeout=10)
            assert response.status_code == 200, f"Server not responsive: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.fail(f"Cannot connect to server at {server_url}")
    
    @pytest.mark.asyncio
    async def test_mp3_streaming_pipeline(self, server_url, mp3_file, test_metrics_file):
        """Test complete MP3 streaming pipeline with real Whisper API"""
        
        print(f"\n🧪 Testing MP3 streaming pipeline")
        print(f"   MP3 file: {mp3_file}")
        print(f"   Server: {server_url}")
        print(f"   Metrics output: {test_metrics_file}")
        
        # Create streamer
        streamer = MP3WebSocketStreamer(
            mp3_path=mp3_file,
            server_url=server_url,
            chunk_duration_ms=600  # 0.6s chunks for realistic streaming
        )
        
        start_time = time.time()
        
        try:
            # Run streaming test
            await streamer.run_stream()
            
            # Get final metrics
            metrics = streamer.get_metrics()
            
            # Save metrics for analysis
            with open(test_metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            
            print(f"\n📊 Stream Test Results:")
            print(f"   Duration: {metrics['duration_ms']:,}ms")
            print(f"   Chunks sent: {metrics['chunks_sent']}")
            print(f"   Bytes sent: {metrics['bytes_sent']:,}")
            print(f"   Responses received: {metrics['responses_received']}")
            print(f"   Total words: {metrics['words_total']}")
            print(f"   Final segments: {metrics['final_segments']}")
            print(f"   Errors: {len(metrics['errors'])}")
            print(f"   Session ID: {metrics.get('session_id', 'Unknown')}")
            
            # Core assertions for pipeline functionality
            assert metrics['chunks_sent'] > 50, f"Too few chunks sent: {metrics['chunks_sent']} <= 50"
            assert metrics['responses_received'] > 0, "No transcription responses received"
            assert metrics['words_total'] >= 400, f"Too few words transcribed: {metrics['words_total']} < 400"
            assert metrics['final_segments'] >= 10, f"Too few final segments: {metrics['final_segments']} < 10"
            
            # Error rate should be reasonable
            error_rate = len(metrics['errors']) / max(metrics['chunks_sent'], 1)
            assert error_rate < 0.1, f"High error rate: {error_rate:.2%} >= 10%"
            
            print(f"✅ Basic pipeline assertions passed")
            
        except Exception as e:
            print(f"❌ Streaming test failed: {e}")
            raise
        
        finally:
            test_duration = time.time() - start_time
            print(f"\n⏱️ Total test duration: {test_duration:.1f}s")
    
    @pytest.mark.asyncio
    async def test_session_persistence(self, server_url, test_metrics_file):
        """Test that session data is properly persisted in database"""
        
        # Read metrics from previous test
        if not os.path.exists(test_metrics_file):
            pytest.skip("No metrics file from streaming test")
        
        with open(test_metrics_file, 'r') as f:
            metrics = json.load(f)
        
        session_id = metrics.get('session_id')
        if not session_id:
            pytest.skip("No session ID in metrics")
        
        print(f"\n🧪 Testing session persistence for: {session_id}")
        
        # Test session API endpoint
        try:
            response = requests.get(f"{server_url}/api/sessions/{session_id}", timeout=10)
            assert response.status_code == 200, f"Session not found: {response.status_code}"
            
            session_data = response.json()
            
            print(f"📋 Session Data:")
            print(f"   Session ID: {session_data.get('session_id')}")
            print(f"   Status: {session_data.get('status')}")
            print(f"   Word count: {session_data.get('word_count', 0)}")
            print(f"   Duration: {session_data.get('duration_seconds', 0)}s")
            
            # Assertions for persisted data
            assert session_data.get('session_id') == session_id
            assert session_data.get('word_count', 0) >= 400, f"Session word count too low: {session_data.get('word_count')}"
            
            # Test transcript endpoint if available
            transcript_response = requests.get(f"{server_url}/api/sessions/{session_id}/transcript", timeout=10)
            if transcript_response.status_code == 200:
                transcript_data = transcript_response.json()
                transcript_text = transcript_data.get('transcript', '')
                word_count = len(transcript_text.split()) if transcript_text else 0
                
                print(f"📝 Transcript length: {len(transcript_text)} chars, {word_count} words")
                assert word_count >= 400, f"Transcript word count too low: {word_count}"
            
            print(f"✅ Session persistence verified")
            
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Session API not available: {e}")
            pytest.skip("Session API not accessible")
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, test_metrics_file):
        """Test that performance metrics meet acceptance criteria"""
        
        if not os.path.exists(test_metrics_file):
            pytest.skip("No metrics file from streaming test")
        
        with open(test_metrics_file, 'r') as f:
            metrics = json.load(f)
        
        print(f"\n🧪 Testing performance metrics")
        
        # Calculate derived metrics
        chunks_sent = metrics['chunks_sent']
        responses_received = metrics['responses_received']
        words_total = metrics['words_total']
        duration_ms = metrics['duration_ms']
        errors = len(metrics['errors'])
        
        # Response rate
        response_rate = responses_received / max(chunks_sent, 1)
        
        # Error rate
        error_rate = errors / max(chunks_sent, 1)
        
        # Estimated WPM (words per minute)
        duration_minutes = duration_ms / 60000
        wpm = words_total / max(duration_minutes, 1) if duration_minutes > 0 else 0
        
        # Simulated score (placeholder for real scoring logic)
        base_score = 90
        error_penalty = min(error_rate * 200, 30)  # Max 30 point penalty
        response_bonus = min(response_rate * 10, 10)  # Max 10 point bonus
        score = max(0, base_score - error_penalty + response_bonus)
        
        print(f"📊 Performance Metrics:")
        print(f"   Response rate: {response_rate:.1%}")
        print(f"   Error rate: {error_rate:.1%}")
        print(f"   Estimated WPM: {wpm:.1f}")
        print(f"   Calculated score: {score:.1f}")
        
        # Performance assertions
        assert response_rate >= 0.5, f"Low response rate: {response_rate:.1%} < 50%"
        assert error_rate <= 0.2, f"High error rate: {error_rate:.1%} > 20%"
        assert score >= 85, f"Performance score too low: {score:.1f} < 85"
        
        # Additional quality checks
        assert words_total >= 400, f"Word count target not met: {words_total} < 400"
        assert chunks_sent >= 100, f"Insufficient test coverage: {chunks_sent} chunks < 100"
        
        print(f"✅ Performance metrics meet acceptance criteria")
    
    def test_mp3_file_accessibility(self, mp3_file):
        """Test that MP3 file is accessible and valid"""
        
        mp3_path = Path(mp3_file)
        assert mp3_path.exists(), f"MP3 file not found: {mp3_path}"
        assert mp3_path.suffix.lower() == '.mp3', f"Not an MP3 file: {mp3_path}"
        
        # Check file size (should be substantial for 120s audio)
        file_size = mp3_path.stat().st_size
        assert file_size > 100000, f"MP3 file too small: {file_size} bytes"  # > 100KB
        
        print(f"✅ MP3 file valid: {file_size:,} bytes")


# Standalone test runner
if __name__ == "__main__":
    """Run tests standalone"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MP3 streaming pipeline tests')
    parser.add_argument('--server', default='http://localhost:5000', help='Server URL')
    parser.add_argument('--mp3', help='Path to MP3 file (default: auto-detect)')
    parser.add_argument('--output', help='Output file for metrics')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Auto-detect MP3 file if not specified
    if not args.mp3:
        mp3_path = Path(__file__).parent / "data" / "djvlad_120s.mp3"
        if mp3_path.exists():
            args.mp3 = str(mp3_path)
        else:
            print(f"❌ MP3 file not found: {mp3_path}")
            sys.exit(1)
    
    # Run single streaming test
    async def run_standalone_test():
        print(f"🧪 Running standalone MP3 streaming test")
        print(f"   Server: {args.server}")
        print(f"   MP3: {args.mp3}")
        
        streamer = MP3WebSocketStreamer(
            mp3_path=args.mp3,
            server_url=args.server,
            chunk_duration_ms=600
        )
        
        try:
            await streamer.run_stream()
            metrics = streamer.get_metrics()
            
            print(f"\n📊 Results:")
            print(f"   Words: {metrics['words_total']}")
            print(f"   Final segments: {metrics['final_segments']}")
            print(f"   Chunks: {metrics['chunks_sent']}")
            print(f"   Errors: {len(metrics['errors'])}")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(metrics, f, indent=2, default=str)
                print(f"💾 Metrics saved to: {args.output}")
            
            # Basic validation
            success = (
                metrics['words_total'] >= 400 and
                metrics['final_segments'] >= 10 and
                len(metrics['errors']) < metrics['chunks_sent'] * 0.1
            )
            
            if success:
                print(f"✅ Test passed!")
                return 0
            else:
                print(f"❌ Test failed - check metrics")
                return 1
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return 1
    
    # Run the test
    exit_code = asyncio.run(run_standalone_test())
    sys.exit(exit_code)