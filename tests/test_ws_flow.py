"""
M1 WebSocket Flow Tests
Tests for M1 quality improvements including bounded queues, VAD gating, and metrics.
"""

import pytest
import json
import time
import threading
from unittest.mock import patch, MagicMock, Mock
import socketio
from queue import Queue

from services.whisper_streaming_enhanced import M1WhisperStreamingService, M1TranscriptionConfig
from services.vad_service import VADService


class TestM1WebSocketFlow:
    """Test M1 WebSocket flow with quality improvements."""
    
    @pytest.fixture
    def m1_service(self):
        """Create M1 enhanced service for testing."""
        config = M1TranscriptionConfig(
            max_queue_len=4,  # Small queue for testing backpressure
            max_chunk_ms=500,
            voice_tail_ms=200,
            min_confidence=0.5,
            dedup_overlap_threshold=0.8
        )
        return M1WhisperStreamingService(config)
    
    @pytest.fixture
    def mock_audio_data(self):
        """Generate mock audio data for testing."""
        def generate_chunk(size_bytes=1024):
            return b'\\x00\\x01' * (size_bytes // 2)
        return generate_chunk
    
    def test_m1_session_start_and_metrics_initialization(self, m1_service):
        """Test M1 session starts with proper metrics initialization."""
        session_id = "test-session-m1"
        
        # Start session
        m1_service.start_session(session_id)
        
        # Verify session is tracked
        assert session_id in m1_service.active_sessions
        assert session_id in m1_service.session_metrics
        
        # Verify metrics initialization
        metrics = m1_service.get_session_metrics(session_id)
        assert metrics.session_id == session_id
        assert metrics.chunks_received == 0
        assert metrics.chunks_processed == 0
        assert metrics.chunks_dropped == 0
        assert metrics.interim_events == 0
        assert metrics.final_events == 0
    
    def test_m1_voiced_chunks_processing(self, m1_service, mock_audio_data):
        """Test that voiced chunks are processed through the pipeline."""
        session_id = "test-voiced-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Enqueue voiced chunks
        for i in range(5):
            audio_chunk = mock_audio_data(512)
            timestamp = time.time() + i * 0.1
            success = m1_service.enqueue_audio_chunk(session_id, audio_chunk, timestamp, is_voiced=True)
            assert success
        
        # Process queue multiple times to handle all chunks
        for _ in range(10):  # Process more times than chunks to ensure all are handled
            m1_service.process_queue(result_callback)
            time.sleep(0.01)  # Small delay for async processing
        
        # Verify results
        assert len(results) >= 1  # Should have at least one interim result
        
        # Verify metrics
        metrics = m1_service.get_session_metrics(session_id)
        assert metrics.chunks_received == 5
        assert metrics.chunks_processed >= 1
    
    def test_m1_silence_filtering_vad_gate(self, m1_service, mock_audio_data):
        """Test that silence is filtered by VAD gating."""
        session_id = "test-silence-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Enqueue silence chunks (is_voiced=False)
        for i in range(5):
            audio_chunk = mock_audio_data(512)
            timestamp = time.time() + i * 0.1
            success = m1_service.enqueue_audio_chunk(session_id, audio_chunk, timestamp, is_voiced=False)
            assert success  # Enqueue succeeds but chunk is filtered
        
        # Process queue
        for _ in range(10):
            m1_service.process_queue(result_callback)
            time.sleep(0.01)
        
        # Verify no results from silence
        assert len(results) == 0
        
        # Verify metrics show received but filtered chunks
        metrics = m1_service.get_session_metrics(session_id)
        assert metrics.chunks_received == 5
        assert metrics.chunks_processed == 0  # None processed due to VAD filtering
    
    def test_m1_backpressure_queue_overflow(self, m1_service, mock_audio_data):
        """Test backpressure handling when queue overflows."""
        session_id = "test-backpressure-session"
        m1_service.start_session(session_id)
        
        # Fill queue beyond capacity (max_queue_len=4)
        enqueued_count = 0
        for i in range(10):  # Try to enqueue more than max_queue_len
            audio_chunk = mock_audio_data(512)
            timestamp = time.time() + i * 0.1
            success = m1_service.enqueue_audio_chunk(session_id, audio_chunk, timestamp, is_voiced=True)
            if success:
                enqueued_count += 1
        
        # Verify queue status
        queue_status = m1_service.get_queue_status()
        assert queue_status['queue_size'] <= 4  # Should not exceed max
        assert queue_status['dropped_chunks'] > 0  # Should have dropped chunks
        
        # Verify metrics show drops
        metrics = m1_service.get_session_metrics(session_id)
        assert metrics.chunks_received == 10
        assert metrics.chunks_dropped > 0
    
    def test_m1_end_of_stream_finalization(self, m1_service, mock_audio_data):
        """Test end of stream finalization produces final transcript."""
        session_id = "test-finalization-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Enqueue some voiced chunks
        for i in range(3):
            audio_chunk = mock_audio_data(512)
            timestamp = time.time() + i * 0.1
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, timestamp, is_voiced=True)
        
        # Process some interim results
        for _ in range(5):
            m1_service.process_queue(result_callback)
            time.sleep(0.01)
        
        interim_results = len(results)
        
        # Finalize session
        final_metrics = m1_service.finalize_session(session_id, result_callback)
        
        # Verify finalization
        assert final_metrics is not None
        assert final_metrics.session_id == session_id
        
        # Should have final results
        final_results = [r for r in results if r.is_final]
        assert len(final_results) >= 1  # Should have at least one final transcript
        
        # Verify session cleanup
        assert session_id not in m1_service.active_sessions
    
    def test_m1_confidence_filtering(self, m1_service, mock_audio_data):
        """Test min-confidence filtering of low quality results."""
        session_id = "test-confidence-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Mock transcription to return low confidence
        with patch.object(m1_service, '_transcribe_chunk') as mock_transcribe:
            from services.whisper_streaming_enhanced import M1TranscriptionResult
            
            # Return low confidence result
            low_conf_result = M1TranscriptionResult(
                text="low confidence text",
                avg_confidence=0.3,  # Below min_confidence=0.5
                is_final=False,
                language="en",
                duration=1.0,
                timestamp=time.time(),
                words=[],
                metadata={},
                latency_ms=100,
                chunk_index=1
            )
            mock_transcribe.return_value = low_conf_result
            
            # Enqueue chunk
            audio_chunk = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, time.time(), is_voiced=True)
            
            # Process queue
            m1_service.process_queue(result_callback)
        
        # Should have no results due to confidence filtering
        assert len(results) == 0
    
    def test_m1_deduplication_logic(self, m1_service, mock_audio_data):
        """Test deduplication of repeated text."""
        session_id = "test-dedup-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Mock transcription to return similar text
        with patch.object(m1_service, '_transcribe_chunk') as mock_transcribe:
            from services.whisper_streaming_enhanced import M1TranscriptionResult
            
            def create_result(text):
                return M1TranscriptionResult(
                    text=text,
                    avg_confidence=0.8,
                    is_final=False,
                    language="en",
                    duration=1.0,
                    timestamp=time.time(),
                    words=[],
                    metadata={},
                    latency_ms=100,
                    chunk_index=1
                )
            
            # First result
            mock_transcribe.return_value = create_result("hello world this is a test")
            audio_chunk = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, time.time(), is_voiced=True)
            m1_service.process_queue(result_callback)
            
            # Second result with high overlap (should be filtered)
            mock_transcribe.return_value = create_result("hello world this is a test message")
            audio_chunk2 = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk2, time.time(), is_voiced=True)
            m1_service.process_queue(result_callback)
        
        # Should only have one result due to deduplication
        assert len(results) == 1
        assert "hello world this is a test" in results[0].text
    
    def test_m1_latency_metrics_tracking(self, m1_service, mock_audio_data):
        """Test latency metrics are properly tracked."""
        session_id = "test-latency-session"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Enqueue chunks with some processing delay
        for i in range(3):
            audio_chunk = mock_audio_data(512)
            timestamp = time.time() + i * 0.1
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, timestamp, is_voiced=True)
            
            # Add delay to simulate processing time
            time.sleep(0.05)
            m1_service.process_queue(result_callback)
        
        # Verify latency metrics
        metrics = m1_service.get_session_metrics(session_id)
        if results:
            assert metrics.latency_avg_ms > 0
            
            # Check individual result latencies
            for result in results:
                assert result.latency_ms >= 0
    
    def test_m1_metrics_comprehensive(self, m1_service, mock_audio_data):
        """Test comprehensive metrics collection."""
        session_id = "test-comprehensive-metrics"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Mixed scenario: voiced chunks, silence, queue overflow
        chunks_sent = 0
        
        # Send voiced chunks
        for i in range(3):
            audio_chunk = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, time.time(), is_voiced=True)
            chunks_sent += 1
        
        # Send silence (filtered)
        for i in range(2):
            audio_chunk = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, time.time(), is_voiced=False)
            chunks_sent += 1
        
        # Overflow queue
        for i in range(6):  # More than max_queue_len=4
            audio_chunk = mock_audio_data(512)
            m1_service.enqueue_audio_chunk(session_id, audio_chunk, time.time(), is_voiced=True)
            chunks_sent += 1
        
        # Process queue
        for _ in range(15):
            m1_service.process_queue(result_callback)
            time.sleep(0.01)
        
        # Finalize and get final metrics
        final_metrics = m1_service.finalize_session(session_id, result_callback)
        
        # Verify comprehensive metrics
        assert final_metrics.chunks_received == chunks_sent
        assert final_metrics.chunks_dropped > 0  # From queue overflow
        assert final_metrics.chunks_processed >= 0
        if results:
            interim_count = len([r for r in results if not r.is_final])
            final_count = len([r for r in results if r.is_final])
            assert final_metrics.interim_events >= interim_count
            assert final_metrics.final_events >= final_count


@pytest.mark.integration
class TestM1SocketIOIntegration:
    """Integration tests for M1 WebSocket events."""
    
    def test_audio_chunk_event_handling(self, client):
        """Test audio_chunk event with M1 enhancements."""
        # This would require actual Socket.IO client connection
        # Skipping for now as it requires running server
        pytest.skip("Integration test requires running Socket.IO server")
    
    def test_end_of_stream_event_handling(self, client):
        """Test end_of_stream event produces final metrics."""
        pytest.skip("Integration test requires running Socket.IO server")


# Standalone function tests for specific M1 components

def test_bounded_queue_drop_policy():
    """Test bounded queue drop-oldest policy."""
    from services.whisper_streaming_enhanced import BoundedAudioQueue
    
    queue = BoundedAudioQueue(max_size=3)
    
    # Fill queue
    for i in range(3):
        item = {'chunk_index': i, 'data': f'chunk_{i}'}
        success = queue.enqueue(item)
        assert success
    
    assert queue.size() == 3
    assert queue.is_full()
    
    # Add one more - should drop oldest
    item = {'chunk_index': 3, 'data': 'chunk_3'}
    success = queue.enqueue(item)
    assert success
    assert queue.size() == 3
    assert queue.dropped_count == 1
    
    # Dequeue and verify order (oldest should be gone)
    first = queue.dequeue()
    assert first['chunk_index'] == 1  # 0 was dropped


def test_vad_voice_tail_logic():
    """Test VAD voice tail allows chunks after speech ends."""
    from services.vad_service import VADService, VADConfig
    
    config = VADConfig(sensitivity=0.5)
    vad = VADService(config)
    vad.set_voice_tail_ms(300)  # 300ms tail
    
    current_time = time.time()
    
    # Mock audio data
    voiced_audio = b'\\x00\\x01' * 512  # Simulate voiced audio
    silence_audio = b'\\x00\\x00' * 512  # Simulate silence
    
    # First, process voiced chunk
    with patch.object(vad, 'process_audio_chunk') as mock_process:
        from services.vad_service import VADResult
        mock_process.return_value = VADResult(True, 0.8, 0.1, current_time)
        
        is_voiced = vad.is_voiced(voiced_audio, current_time)
        assert is_voiced  # Should be voiced
    
    # Then process silence within voice tail period
    silence_time = current_time + 0.2  # 200ms later, within 300ms tail
    with patch.object(vad, 'process_audio_chunk') as mock_process:
        mock_process.return_value = VADResult(False, 0.2, 0.01, silence_time)
        
        is_voiced = vad.is_voiced(silence_audio, silence_time)
        assert is_voiced  # Should still be considered voiced due to tail
    
    # Process silence after voice tail expires
    late_silence_time = current_time + 0.4  # 400ms later, beyond 300ms tail
    with patch.object(vad, 'process_audio_chunk') as mock_process:
        mock_process.return_value = VADResult(False, 0.2, 0.01, late_silence_time)
        
        is_voiced = vad.is_voiced(silence_audio, late_silence_time)
        assert not is_voiced  # Should be filtered out


def test_deduplication_similarity_calculation():
    """Test text deduplication similarity calculation."""
    from services.whisper_streaming_enhanced import M1WhisperStreamingService, M1TranscriptionConfig
    
    config = M1TranscriptionConfig(dedup_overlap_threshold=0.8)
    service = M1WhisperStreamingService(config)
    
    # Set up buffer with initial text
    service._update_dedup_buffer("hello world this is a test")
    
    # Test high similarity (should be duplicate)
    is_duplicate = service._is_duplicate("hello world this is a test message")
    assert is_duplicate
    
    # Test low similarity (should not be duplicate)
    is_duplicate = service._is_duplicate("completely different text here")
    assert not is_duplicate
    
    # Test empty text
    is_duplicate = service._is_duplicate("")
    assert not is_duplicate