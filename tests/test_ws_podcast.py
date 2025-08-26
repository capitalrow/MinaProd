#!/usr/bin/env python3
"""
pytest for End-to-End WebSocket Podcast Streaming Validation
Tests the complete pipeline: file → chunks → transcription → UI → persistence
"""

import pytest
import asyncio
import time
from pathlib import Path
import requests
import json

# Import the streamer
import sys
sys.path.append('tests/tools')
from ws_stream_podcast import PodcastWebSocketStreamer

class TestE2EWebSocketPodcast:
    """End-to-End WebSocket Podcast Streaming Tests"""
    
    @pytest.fixture
    def podcast_file(self):
        """Provide path to test podcast file"""
        # Use the latest Boosie interview file
        file_path = "attached_assets/ytmp3free.cc_boosie-goes-off-on-irv-gotti-dying-he-got-hated-on-while-he-was-alive-now-they-show-love-part-5-youtubemp3free.org_1756227635769.mp3"
        
        if not Path(file_path).exists():
            pytest.skip(f"Podcast file not found: {file_path}")
        
        return file_path
    
    @pytest.fixture
    def server_url(self):
        """Server URL for testing"""
        return "http://localhost:5000"
    
    @pytest.mark.asyncio
    async def test_e2e_podcast_streaming_full_pipeline(self, podcast_file, server_url):
        """
        Test complete E2E pipeline:
        - Stream podcast audio via WebSocket
        - Verify interims within 2s
        - Verify ≥10 interims and ≥1 final
        - Check persistence with ≥200 words and ≥10 sentences
        """
        print("\n🎙️ E2E PODCAST STREAMING VALIDATION")
        print("="*50)
        
        # Initialize streamer
        streamer = PodcastWebSocketStreamer(podcast_file, server_url)
        
        # Run streaming test
        results = await streamer.stream_podcast()
        
        # Print detailed results
        print("\n📊 STREAMING RESULTS:")
        print(f"   Session ID: {results.get('session_id')}")
        print(f"   Success: {results.get('success')}")
        print(f"   Duration: {results.get('total_duration_seconds', 0):.1f}s")
        print(f"   Chunks sent: {results.get('chunks_sent', 0)}")
        print(f"   ACKs received: {results.get('acks_received', 0)}")
        print(f"   Interims received: {results.get('interim_received', 0)}")
        print(f"   Finals received: {results.get('final_received', 0)}")
        
        # Assertions for pipeline requirements
        
        # 1. Basic success check
        assert results.get('success', False), f"Streaming failed: {results.get('error', 'Unknown error')}"
        
        # 2. First interim within 2 seconds
        first_interim_latency = results.get('first_interim_latency_ms')
        assert first_interim_latency is not None, "No interim transcripts received"
        assert first_interim_latency <= 2000, f"First interim took {first_interim_latency:.1f}ms (>2000ms)"
        print(f"   ✅ First interim latency: {first_interim_latency:.1f}ms")
        
        # 3. Minimum interim count (≥10)
        interim_count = results.get('interim_received', 0)
        assert interim_count >= 10, f"Insufficient interims: {interim_count} < 10"
        print(f"   ✅ Interim count: {interim_count}")
        
        # 4. At least 1 final transcript
        final_count = results.get('final_received', 0)
        assert final_count >= 1, f"No final transcripts received: {final_count}"
        print(f"   ✅ Final count: {final_count}")
        
        # 5. Check session persistence
        session_id = results.get('session_id')
        assert session_id, "No session ID returned"
        
        # Wait a moment for persistence
        await asyncio.sleep(2)
        
        # Query session API to check persistence
        try:
            response = requests.get(f"{server_url}/api/sessions/{session_id}")
            assert response.status_code == 200, f"Session API failed: {response.status_code}"
            
            session_data = response.json()
            print(f"   📄 Session data retrieved: {len(str(session_data))} chars")
            
            # Check for transcript content
            transcript = session_data.get('transcript', '')
            segments = session_data.get('segments', [])
            
            print(f"   📝 Transcript length: {len(transcript)} chars")
            print(f"   📝 Segments count: {len(segments)}")
            
            # Word and sentence count validation
            if transcript:
                words = len(transcript.split())
                sentences = transcript.count('.') + transcript.count('!') + transcript.count('?')
                
                print(f"   📊 Words: {words}")
                print(f"   📊 Sentences: {sentences}")
                
                # Requirements: ≥200 words and ≥10 sentences
                assert words >= 200, f"Insufficient words in transcript: {words} < 200"
                assert sentences >= 10, f"Insufficient sentences in transcript: {sentences} < 10"
                
                print(f"   ✅ Transcript validation passed")
                print(f"   📄 Sample: '{transcript[:100]}...'")
            else:
                pytest.fail("No transcript found in persisted session")
                
        except requests.RequestException as e:
            pytest.fail(f"Failed to query session API: {e}")
        
        print("\n🎉 E2E PODCAST STREAMING VALIDATION PASSED!")
        print("✅ All requirements met:")
        print("   • Interims within 2s")
        print("   • ≥10 interims total")
        print("   • ≥1 final transcript")
        print("   • ≥200 words persisted")
        print("   • ≥10 sentences persisted")
    
    @pytest.mark.asyncio
    async def test_ws_podcast_performance_metrics(self, podcast_file, server_url):
        """Test performance metrics and quality indicators"""
        print("\n📈 PERFORMANCE METRICS TEST")
        print("="*40)
        
        streamer = PodcastWebSocketStreamer(podcast_file, server_url)
        results = await streamer.stream_podcast()
        
        assert results.get('success', False), "Streaming failed"
        
        # Performance assertions
        chunks_sent = results.get('chunks_sent', 0)
        acks_received = results.get('acks_received', 0)
        avg_interval = results.get('avg_interim_interval_ms', 0)
        
        print(f"   📦 Chunks sent: {chunks_sent}")
        print(f"   📩 ACKs received: {acks_received}")
        print(f"   ⏱️  Avg interim interval: {avg_interval:.1f}ms")
        
        # Quality checks
        if chunks_sent > 0:
            ack_rate = (acks_received / chunks_sent) * 100
            print(f"   📊 ACK rate: {ack_rate:.1f}%")
            # Allow some tolerance for ACK rate
            assert ack_rate >= 50, f"Low ACK rate: {ack_rate:.1f}%"
        
        # Interim interval should be reasonable (not too fast, not too slow)
        if avg_interval > 0:
            assert 200 <= avg_interval <= 4000, f"Interim interval out of range: {avg_interval:.1f}ms"
        
        print("   ✅ Performance metrics acceptable")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])