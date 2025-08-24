"""
M1 VAD Gating Tests
Test VAD-based audio filtering and voice tail logic.
"""

import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock

from services.vad_service import VADService, VADConfig, VADResult


class TestVADGating:
    """Test VAD gating functionality for M1 quality improvements."""
    
    @pytest.fixture
    def vad_service(self):
        """Create VAD service with test configuration."""
        config = VADConfig(
            sensitivity=0.5,
            min_speech_duration=200,
            min_silence_duration=300,
            voice_tail_ms=300
        )
        service = VADService(config)
        service.set_voice_tail_ms(300)
        return service
    
    @pytest.fixture
    def silence_audio(self):
        """Generate mock silence audio data."""
        # Generate low-energy audio data (silence)
        silence = np.zeros(1024, dtype=np.int16)
        # Add minimal noise to make it realistic
        noise = np.random.normal(0, 0.01, 1024).astype(np.int16)
        return (silence + noise).tobytes()
    
    @pytest.fixture
    def voiced_audio(self):
        """Generate mock voiced audio data."""
        # Generate higher-energy audio data (speech-like)
        t = np.linspace(0, 1, 1024)
        # Simulate speech with multiple frequency components
        speech = (
            0.3 * np.sin(2 * np.pi * 200 * t) +  # Fundamental frequency
            0.2 * np.sin(2 * np.pi * 400 * t) +  # First harmonic
            0.1 * np.sin(2 * np.pi * 800 * t)    # Second harmonic
        )
        # Add some noise for realism
        noise = np.random.normal(0, 0.05, len(speech))
        speech_signal = (speech + noise) * 10000  # Scale to int16 range
        return speech_signal.astype(np.int16).tobytes()
    
    def test_vad_detects_silence(self, vad_service, silence_audio):
        """Test that VAD correctly identifies silence."""
        timestamp = time.time()
        
        result = vad_service.process_audio_chunk(silence_audio, timestamp)
        
        assert isinstance(result, VADResult)
        assert not result.is_speech
        assert result.confidence < 0.5
        assert result.energy < 0.1  # Low energy for silence
    
    def test_vad_detects_speech(self, vad_service, voiced_audio):
        """Test that VAD correctly identifies speech."""
        timestamp = time.time()
        
        result = vad_service.process_audio_chunk(voiced_audio, timestamp)
        
        assert isinstance(result, VADResult)
        assert result.is_speech
        assert result.confidence > 0.5
        assert result.energy > 0.01  # Higher energy for speech
    
    def test_is_voiced_method_basic(self, vad_service, voiced_audio, silence_audio):
        """Test is_voiced method for basic speech/silence detection."""
        timestamp = time.time()
        
        # Test voiced audio
        is_voiced = vad_service.is_voiced(voiced_audio, timestamp)
        assert is_voiced
        
        # Test silence
        is_voiced = vad_service.is_voiced(silence_audio, timestamp)
        assert not is_voiced
    
    def test_voice_tail_allows_silence_after_speech(self, vad_service, voiced_audio, silence_audio):
        """Test that silence is allowed within voice tail period after speech."""
        current_time = time.time()
        
        # First, process voiced audio to establish voice activity
        is_voiced = vad_service.is_voiced(voiced_audio, current_time)
        assert is_voiced
        
        # Now test silence shortly after (within voice tail)
        silence_time = current_time + 0.2  # 200ms later, within 300ms tail
        
        # Mock the VAD processing to return silence for this chunk
        with patch.object(vad_service, 'process_audio_chunk') as mock_process:
            mock_process.return_value = VADResult(False, 0.3, 0.005, silence_time)
            
            is_voiced = vad_service.is_voiced(silence_audio, silence_time)
            assert is_voiced  # Should be allowed due to voice tail
    
    def test_voice_tail_expires_after_period(self, vad_service, voiced_audio, silence_audio):
        """Test that voice tail expires and silence is filtered after the period."""
        current_time = time.time()
        
        # First, establish voice activity
        is_voiced = vad_service.is_voiced(voiced_audio, current_time)
        assert is_voiced
        
        # Test silence after voice tail expires
        late_silence_time = current_time + 0.5  # 500ms later, beyond 300ms tail
        
        # Mock VAD to return silence
        with patch.object(vad_service, 'process_audio_chunk') as mock_process:
            mock_process.return_value = VADResult(False, 0.2, 0.003, late_silence_time)
            
            is_voiced = vad_service.is_voiced(silence_audio, late_silence_time)
            assert not is_voiced  # Should be filtered out
    
    def test_voice_tail_configuration(self, vad_service):
        """Test voice tail duration can be configured."""
        # Test default configuration
        assert vad_service.voice_tail_ms == 300
        
        # Test changing voice tail duration
        vad_service.set_voice_tail_ms(500)
        assert vad_service.voice_tail_ms == 500
        
        # Test with zero voice tail (no tail)
        vad_service.set_voice_tail_ms(0)
        assert vad_service.voice_tail_ms == 0
    
    def test_continuous_voice_detection(self, vad_service, voiced_audio):
        """Test continuous voice detection updates last_voice_time."""
        timestamps = []
        current_time = time.time()
        
        # Process multiple voiced chunks
        for i in range(5):
            timestamp = current_time + i * 0.1  # 100ms apart
            is_voiced = vad_service.is_voiced(voiced_audio, timestamp)
            if is_voiced:
                timestamps.append(timestamp)
        
        # Verify last voice time is updated
        assert len(timestamps) > 0
        # Last voice time should be close to the most recent timestamp
        time_diff = abs(vad_service.last_voice_time - timestamps[-1])
        assert time_diff < 0.1  # Within 100ms
    
    def test_vad_with_empty_audio(self, vad_service):
        """Test VAD handles empty or invalid audio gracefully."""
        timestamp = time.time()
        
        # Test empty bytes
        result = vad_service.process_audio_chunk(b'', timestamp)
        assert not result.is_speech
        assert result.confidence == 0.0
        
        # Test very small audio chunk
        tiny_chunk = b'\\x00\\x01'
        result = vad_service.process_audio_chunk(tiny_chunk, timestamp)
        assert not result.is_speech
    
    def test_vad_noise_gate_threshold(self, vad_service):
        """Test VAD noise gate filters very low energy audio."""
        timestamp = time.time()
        
        # Generate very low energy audio (below noise gate)
        low_energy = np.zeros(1024, dtype=np.int16)
        low_energy[:100] = 1  # Very small signal
        low_energy_bytes = low_energy.tobytes()
        
        result = vad_service.process_audio_chunk(low_energy_bytes, timestamp)
        
        # Should be filtered by noise gate
        assert not result.is_speech
        assert result.energy <= vad_service.config.noise_gate_threshold
    
    def test_vad_statistics_tracking(self, vad_service, voiced_audio, silence_audio):
        """Test that VAD tracks statistics correctly."""
        initial_total = vad_service.total_frames
        initial_speech = vad_service.speech_frames_count
        
        # Process some audio
        vad_service.process_audio_chunk(voiced_audio, time.time())
        vad_service.process_audio_chunk(silence_audio, time.time())
        vad_service.process_audio_chunk(voiced_audio, time.time())
        
        # Verify statistics updated
        assert vad_service.total_frames > initial_total
        assert vad_service.speech_frames_count >= initial_speech
    
    def test_vad_temporal_logic_smoothing(self, vad_service):
        """Test VAD temporal logic provides smoothing over time."""
        current_time = time.time()
        
        # Create alternating speech/silence pattern
        speech_pattern = []
        for i in range(10):
            # Mock alternating speech/silence
            is_speech = (i % 2 == 0)
            timestamp = current_time + i * 0.05  # 50ms intervals
            
            with patch.object(vad_service, '_calculate_speech_probability') as mock_prob:
                mock_prob.return_value = 0.8 if is_speech else 0.2
                
                result = vad_service.process_audio_chunk(b'\\x00\\x01' * 512, timestamp)
                speech_pattern.append(result.is_speech)
        
        # Temporal smoothing should reduce rapid changes
        # Count transitions
        transitions = sum(1 for i in range(1, len(speech_pattern)) 
                         if speech_pattern[i] != speech_pattern[i-1])
        
        # Should have fewer transitions than the raw alternating pattern (10)
        assert transitions < 10
    
    def test_vad_energy_threshold_configuration(self):
        """Test VAD energy threshold affects detection."""
        # High threshold - should be harder to detect speech
        high_threshold_config = VADConfig(
            sensitivity=0.5,
            energy_threshold=0.1  # High threshold
        )
        high_threshold_vad = VADService(high_threshold_config)
        
        # Low threshold - should be easier to detect speech
        low_threshold_config = VADConfig(
            sensitivity=0.5,
            energy_threshold=0.001  # Low threshold
        )
        low_threshold_vad = VADService(low_threshold_config)
        
        # Generate moderate energy audio
        moderate_energy = np.sin(2 * np.pi * 300 * np.linspace(0, 1, 1024)) * 1000
        moderate_audio = moderate_energy.astype(np.int16).tobytes()
        
        timestamp = time.time()
        
        # High threshold should be less likely to detect
        high_result = high_threshold_vad.process_audio_chunk(moderate_audio, timestamp)
        
        # Low threshold should be more likely to detect
        low_result = low_threshold_vad.process_audio_chunk(moderate_audio, timestamp)
        
        # Low threshold should have higher confidence or detect speech where high doesn't
        assert low_result.confidence >= high_result.confidence


class TestVADIntegrationWithM1:
    """Integration tests for VAD with M1 quality system."""
    
    def test_vad_integration_with_chunking_pipeline(self):
        """Test VAD integration with M1 audio chunking pipeline."""
        from services.whisper_streaming_enhanced import M1WhisperStreamingService, M1TranscriptionConfig
        from services.vad_service import VADService, VADConfig
        
        # Create integrated services
        vad_config = VADConfig(sensitivity=0.5)
        vad_service = VADService(vad_config)
        vad_service.set_voice_tail_ms(200)
        
        m1_config = M1TranscriptionConfig(max_queue_len=4)
        m1_service = M1WhisperStreamingService(m1_config)
        
        session_id = "vad-integration-test"
        m1_service.start_session(session_id)
        
        results = []
        def result_callback(result):
            results.append(result)
        
        # Generate mixed audio sequence
        silence = np.zeros(512, dtype=np.int16).tobytes()
        voiced = (np.sin(2 * np.pi * 300 * np.linspace(0, 1, 512)) * 5000).astype(np.int16).tobytes()
        
        audio_sequence = [
            (silence, False),   # Should be filtered
            (voiced, True),     # Should be processed
            (silence, True),    # Should be allowed (voice tail)
            (voiced, True),     # Should be processed
            (silence, False)    # Should be filtered (after tail expires)
        ]
        
        processed_chunks = 0
        current_time = time.time()
        
        for i, (audio_data, expected_voiced) in enumerate(audio_sequence):
            timestamp = current_time + i * 0.1
            
            # Use VAD to determine if chunk should be processed
            is_voiced = vad_service.is_voiced(audio_data, timestamp)
            
            # Enqueue based on VAD result
            if m1_service.enqueue_audio_chunk(session_id, audio_data, timestamp, is_voiced):
                if is_voiced:
                    processed_chunks += 1
            
            # Process queue
            m1_service.process_queue(result_callback)
            
            # Small delay to allow voice tail to expire
            if i == 2:  # After silence chunk with voice tail
                time.sleep(0.25)  # Ensure voice tail expires
        
        # Verify filtering worked
        metrics = m1_service.get_session_metrics(session_id)
        assert metrics.chunks_received == 5  # All chunks received
        # Some chunks should have been filtered by VAD
        
    def test_vad_performance_with_real_time_constraints(self, vad_service):
        """Test VAD performance meets real-time processing constraints."""
        import time
        
        # Generate realistic audio chunk size (20ms at 16kHz)
        chunk_size = int(16000 * 0.02)  # 320 samples
        audio_chunk = np.random.randint(-1000, 1000, chunk_size, dtype=np.int16).tobytes()
        
        # Time VAD processing
        start_time = time.perf_counter()
        
        # Process multiple chunks
        for i in range(50):  # Simulate 1 second of audio (50 chunks of 20ms)
            result = vad_service.process_audio_chunk(audio_chunk, time.time())
            
        end_time = time.perf_counter()
        
        # Calculate processing time
        processing_time = end_time - start_time
        audio_duration = 1.0  # 1 second of audio processed
        
        # VAD should process faster than real-time
        assert processing_time < audio_duration, f"VAD too slow: {processing_time:.3f}s for {audio_duration}s audio"
        
        # Should be significantly faster (at least 10x real-time)
        assert processing_time < audio_duration / 10, f"VAD not fast enough: {processing_time:.3f}s"