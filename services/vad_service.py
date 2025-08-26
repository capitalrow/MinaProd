"""
Voice Activity Detection (VAD) Service
Enhanced VAD processing with superior buffer management and noise reduction.
Integrates advanced algorithms from real-time transcription improvements.
"""

import logging
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from collections import deque
import time

logger = logging.getLogger(__name__)

@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection."""
    sensitivity: float = 0.5
    min_speech_duration: int = 10000  # ms
    min_silence_duration: int = 500  # ms
    sample_rate: int = 16000
    frame_duration: int = 20  # ms
    energy_threshold: float = 0.01
    zero_crossing_threshold: int = 10
    noise_gate_threshold: float = 0.005

class VADResult:
    """Result of VAD processing."""
    def __init__(self, is_speech: bool, confidence: float, energy: float, timestamp: float):
        self.is_speech = is_speech
        self.confidence = confidence
        self.energy = energy
        self.timestamp = timestamp

class VADService:
    """
    Enhanced Voice Activity Detection service with advanced buffer management.
    Consolidates superior VAD logic from real-time transcription improvements.
    """
    
    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self.frame_size = int(self.config.sample_rate * self.config.frame_duration / 1000)
        self.speech_frames = deque(maxlen=100)  # Keep last 100 frames for analysis
        self.silence_frames = deque(maxlen=50)  # Keep silence frames for noise estimation
        
        # State tracking
        self.current_state = 'silence'  # 'silence', 'speech', 'transition'
        self.speech_start_time = None
        self.silence_start_time = None
        self.last_speech_time = 0
        
        # Noise estimation
        self.noise_floor = 0.001
        self.noise_samples = deque(maxlen=20)
        
        # Statistics
        self.total_frames = 0
        self.speech_frames_count = 0
        self.false_positives = 0
        
        # M1 Voice gating
        self.last_voice_time = 0
        self.voice_tail_ms = 300  # Will be configurable from config
        
        logger.info(f"VAD Service initialized with config: {self.config}")
    
    def is_voiced(self, audio_data: bytes, timestamp: Optional[float] = None) -> bool:
        """
        Check if audio chunk contains voice or is within voice tail period.
        
        Args:
            audio_data: Raw audio bytes
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            bool: True if chunk should be processed (contains voice or in voice tail)
        """
        if timestamp is None:
            timestamp = time.time()
            
        # Process the chunk to detect voice
        result = self.process_audio_chunk(audio_data, timestamp)
        
        # Allow chunk if it contains voice OR within voice tail period
        time_since_last_voice = (timestamp - self.last_voice_time) * 1000  # Convert to ms
        is_in_voice_tail = time_since_last_voice <= self.voice_tail_ms
        
        return result.is_speech or is_in_voice_tail
    
    def set_voice_tail_ms(self, voice_tail_ms: int):
        """Set voice tail duration in milliseconds."""
        self.voice_tail_ms = voice_tail_ms
    
    def process_audio_chunk(self, audio_data: bytes, timestamp: Optional[float] = None) -> VADResult:
        """
        Process audio chunk and determine if it contains speech.
        
        Args:
            audio_data: Raw audio bytes
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            VADResult with speech detection information
        """
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Convert bytes to numpy array
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # Ensure minimum frame size
            if len(audio_array) < self.frame_size:
                return VADResult(False, 0.0, 0.0, timestamp)
            
            # Calculate features
            energy = self._calculate_energy(audio_array)
            zero_crossings = self._calculate_zero_crossings(audio_array)
            spectral_features = self._calculate_spectral_features(audio_array)
            
            # Update noise estimation
            self._update_noise_estimation(energy)
            
            # Determine speech probability
            speech_probability = self._calculate_speech_probability(
                energy, zero_crossings, spectral_features
            )
            
            # Apply temporal smoothing
            is_speech = self._apply_temporal_logic(speech_probability, timestamp)
            
            # Update last voice time for gating
            if is_speech:
                self.last_voice_time = timestamp
            
            # Update statistics
            self._update_statistics(is_speech)
            
            return VADResult(is_speech, float(speech_probability), float(energy), timestamp)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return VADResult(False, 0.0, 0.0, timestamp)
    
    def _calculate_energy(self, audio_array: np.ndarray) -> float:
        """Calculate RMS energy of audio frame."""
        if len(audio_array) == 0:
            return 0.0
        
        # RMS energy
        energy = np.sqrt(np.mean(audio_array ** 2))
        
        # Apply noise gate
        if energy < self.config.noise_gate_threshold:
            return 0.0
        
        return energy
    
    def _calculate_zero_crossings(self, audio_array: np.ndarray) -> int:
        """Calculate zero crossing rate."""
        if len(audio_array) <= 1:
            return 0
        
        # Count sign changes
        zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
        return zero_crossings
    
    def _calculate_spectral_features(self, audio_array: np.ndarray) -> dict:
        """Calculate spectral features for enhanced detection."""
        if len(audio_array) < 64:  # Minimum for FFT
            return {'spectral_centroid': 0.0, 'spectral_rolloff': 0.0}
        
        # Apply windowing
        windowed = audio_array * np.hanning(len(audio_array))
        
        # FFT
        fft = np.fft.rfft(windowed)
        magnitude = np.abs(fft)
        
        # Spectral centroid
        freqs = np.fft.rfftfreq(len(audio_array), 1/self.config.sample_rate)
        spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-7)
        
        # Spectral rolloff (85% of energy)
        cumsum = np.cumsum(magnitude)
        rolloff_idx = np.where(cumsum >= 0.85 * cumsum[-1])[0]
        spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0.0
        
        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff
        }
    
    def _update_noise_estimation(self, energy: float):
        """Update background noise estimation."""
        # Only update during silence periods
        if self.current_state == 'silence':
            self.noise_samples.append(energy)
            if len(self.noise_samples) > 10:
                self.noise_floor = np.percentile(list(self.noise_samples), 75)
    
    def _calculate_speech_probability(self, energy: float, zero_crossings: int, spectral_features: dict) -> float:
        """Calculate probability that frame contains speech."""
        if energy == 0.0:
            return 0.0
        
        # Energy-based probability
        energy_ratio = energy / (self.noise_floor + 1e-7)
        energy_prob = min(1.0, max(0.0, (energy_ratio - 1.0) / 10.0))
        
        # Zero crossing rate probability (speech typically has moderate ZCR)
        zcr_prob = 1.0 - abs(zero_crossings - self.config.zero_crossing_threshold) / 50.0
        zcr_prob = max(0.0, min(1.0, zcr_prob))
        
        # Spectral features probability
        spectral_centroid = spectral_features.get('spectral_centroid', 0.0)
        spec_prob = 1.0 if 300 < spectral_centroid < 3400 else 0.5  # Human speech range
        
        # Weighted combination
        total_prob = (0.6 * energy_prob + 0.3 * zcr_prob + 0.1 * spec_prob)
        
        # Apply sensitivity adjustment - more aggressive for better detection
        adjusted_prob = total_prob * (1.5 - self.config.sensitivity * 0.5)
        
        return max(0.0, min(1.0, adjusted_prob))
    
    def _apply_temporal_logic(self, speech_probability: float, timestamp: float) -> bool:
        """Apply temporal smoothing and hysteresis."""
        is_probable_speech = speech_probability > self.config.sensitivity
        
        if self.current_state == 'silence':
            if is_probable_speech:
                if self.speech_start_time is None:
                    self.speech_start_time = timestamp
                elif (timestamp - self.speech_start_time) * 1000 >= self.config.min_speech_duration:
                    self.current_state = 'speech'
                    self.speech_start_time = None
                    self.last_speech_time = timestamp
                    return True
            else:
                self.speech_start_time = None
        
        elif self.current_state == 'speech':
            if is_probable_speech:
                self.last_speech_time = timestamp
                self.silence_start_time = None
                return True
            else:
                if self.silence_start_time is None:
                    self.silence_start_time = timestamp
                elif (timestamp - self.silence_start_time) * 1000 >= self.config.min_silence_duration:
                    self.current_state = 'silence'
                    self.silence_start_time = None
                else:
                    return True  # Still in speech during short silence
        
        return False
    
    def _update_statistics(self, is_speech: bool):
        """Update processing statistics."""
        self.total_frames += 1
        if is_speech:
            self.speech_frames_count += 1
    
    def reset_state(self):
        """Reset VAD state for new session."""
        self.current_state = 'silence'
        self.speech_start_time = None
        self.silence_start_time = None
        self.last_speech_time = 0
        self.speech_frames.clear()
        self.silence_frames.clear()
        self.noise_samples.clear()
        self.noise_floor = 0.001
        
        logger.info("VAD state reset")
    
    def get_statistics(self) -> dict:
        """Get VAD processing statistics."""
        speech_ratio = self.speech_frames_count / max(1, self.total_frames)
        
        return {
            'total_frames': self.total_frames,
            'speech_frames': self.speech_frames_count,
            'speech_ratio': speech_ratio,
            'current_state': self.current_state,
            'noise_floor': self.noise_floor,
            'false_positives': self.false_positives,
        }
    
    def update_config(self, **kwargs):
        """Update VAD configuration parameters."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated VAD config: {key} = {value}")
            else:
                logger.warning(f"Unknown VAD config parameter: {key}")
    
    def is_currently_speaking(self) -> bool:
        """Check if currently in speech state."""
        return self.current_state == 'speech'
