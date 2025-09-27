"""
Advanced Audio Processor - Google Recorder Level Quality
Enhanced audio preprocessing pipeline for enterprise-grade transcription accuracy.
Implements advanced spectral enhancement, adaptive noise reduction, and intelligent chunking.
"""

import logging
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import time
import threading
from collections import deque
from scipy import signal
import librosa

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Enhanced audio chunk with context and metadata."""
    data: np.ndarray
    timestamp: float
    duration: float
    chunk_id: int
    session_id: str
    overlap_start: Optional[np.ndarray] = None
    overlap_end: Optional[np.ndarray] = None
    quality_score: float = 0.0
    speech_probability: float = 0.0
    noise_level: float = 0.0
    context_hash: str = ""

@dataclass 
class AudioEnhancementConfig:
    """Configuration for advanced audio enhancement."""
    # Spectral enhancement
    enable_spectral_enhancement: bool = True
    spectral_subtraction_alpha: float = 2.0
    wiener_filter_strength: float = 0.8
    
    # Adaptive noise reduction
    enable_adaptive_noise_reduction: bool = True
    noise_estimation_frames: int = 10
    adaptation_rate: float = 0.1
    
    # Speech enhancement
    enable_speech_enhancement: bool = True
    formant_enhancement: bool = True
    harmonic_enhancement: bool = True
    
    # Context correlation
    overlap_duration_ms: int = 500  # 500ms overlap between chunks
    context_window_chunks: int = 3   # Consider 3 previous chunks for context
    
    # Quality control
    min_quality_threshold: float = 0.7
    auto_gain_control: bool = True
    dynamic_range_compression: bool = True

class AdvancedAudioProcessor:
    """
    🎯 Google Recorder-level audio processing pipeline.
    
    Implements advanced preprocessing, intelligent chunking with context correlation,
    and adaptive enhancement for optimal transcription accuracy.
    """
    
    def __init__(self, config: Optional[AudioEnhancementConfig] = None):
        self.config = config or AudioEnhancementConfig()
        self.sample_rate = 16000
        
        # Context correlation system
        self.chunk_history = deque(maxlen=self.config.context_window_chunks)
        self.noise_profile = None
        self.adaptive_gain = 1.0
        
        # Performance tracking
        self.processing_times = deque(maxlen=100)
        self.quality_scores = deque(maxlen=100)
        
        # Initialize spectral analysis components
        self._init_spectral_components()
        
        logger.info("🎯 Advanced Audio Processor initialized with Google Recorder-level enhancement")
    
    def _init_spectral_components(self):
        """Initialize spectral analysis and enhancement components."""
        # FFT parameters for optimal speech analysis
        self.fft_size = 1024
        self.hop_length = 256
        self.window = np.hanning(self.fft_size)
        
        # Frequency bands for speech enhancement
        self.speech_bands = {
            'fundamental': (80, 300),    # F0 range
            'formant1': (300, 1000),     # First formant
            'formant2': (1000, 2500),    # Second formant  
            'consonants': (2500, 6000),  # Consonant clarity
            'sibilants': (6000, 8000)    # Sibilant sounds
        }
        
        # Adaptive filters
        self.noise_spectrum = None
        self.speech_spectrum = None
        
    def process_audio_chunk_advanced(self, audio_data: bytes, 
                                   session_id: str, 
                                   chunk_id: int, 
                                   timestamp: Optional[float] = None) -> AudioChunk:
        """
        🚀 Process audio chunk with Google Recorder-level enhancement.
        
        Args:
            audio_data: Raw audio bytes
            session_id: Session identifier for context
            chunk_id: Chunk sequence number
            timestamp: Chunk timestamp
            
        Returns:
            Enhanced AudioChunk with context and quality metadata
        """
        start_time = time.time()
        
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Convert audio to numpy array
            audio_array = self._convert_audio_to_array(audio_data)
            
            if len(audio_array) == 0:
                return self._create_empty_chunk(session_id, chunk_id, timestamp)
            
            # === PHASE 1: ADVANCED PREPROCESSING ===
            
            # 1. Adaptive Gain Control
            if self.config.auto_gain_control:
                audio_array = self._apply_adaptive_gain_control(audio_array)
            
            # 2. Advanced Noise Reduction
            if self.config.enable_adaptive_noise_reduction:
                audio_array = self._apply_adaptive_noise_reduction(audio_array)
            
            # 3. Spectral Enhancement
            if self.config.enable_spectral_enhancement:
                audio_array = self._apply_spectral_enhancement(audio_array)
            
            # 4. Speech-Optimized Enhancement
            if self.config.enable_speech_enhancement:
                audio_array = self._apply_speech_enhancement(audio_array)
            
            # === PHASE 2: QUALITY ASSESSMENT ===
            
            quality_score = self._assess_audio_quality_advanced(audio_array)
            speech_probability = self._calculate_speech_probability(audio_array)
            noise_level = self._estimate_noise_level(audio_array)
            
            # === PHASE 3: CONTEXT CORRELATION ===
            
            # Create overlaps for context correlation
            overlap_start, overlap_end = self._create_context_overlaps(audio_array)
            context_hash = self._generate_context_hash(audio_array, chunk_id)
            
            # === PHASE 4: CHUNK CREATION ===
            
            chunk = AudioChunk(
                data=audio_array,
                timestamp=timestamp,
                duration=len(audio_array) / self.sample_rate,
                chunk_id=chunk_id,
                session_id=session_id,
                overlap_start=overlap_start,
                overlap_end=overlap_end,
                quality_score=quality_score,
                speech_probability=speech_probability,
                noise_level=noise_level,
                context_hash=context_hash
            )
            
            # Add to history for context correlation
            self.chunk_history.append(chunk)
            
            # Update performance metrics
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            self.quality_scores.append(quality_score)
            
            logger.debug(f"🎯 Enhanced chunk {chunk_id}: quality={quality_score:.2f}, "
                        f"speech_prob={speech_probability:.2f}, processing_time={processing_time:.3f}s")
            
            return chunk
            
        except Exception as e:
            logger.error(f"❌ Advanced audio processing failed for chunk {chunk_id}: {e}")
            return self._create_empty_chunk(session_id, chunk_id, timestamp)
    
    def _apply_adaptive_gain_control(self, audio: np.ndarray) -> np.ndarray:
        """🎚️ Apply adaptive gain control for optimal transcription levels."""
        try:
            # Calculate RMS energy
            rms = np.sqrt(np.mean(audio ** 2))
            
            if rms < 1e-6:  # Very quiet audio
                return audio
            
            # Target RMS level for optimal transcription (around -20dB)
            target_rms = 0.1
            
            # Calculate adaptive gain with smoothing
            current_gain = target_rms / rms
            
            # Smooth gain changes to prevent artifacts
            alpha = 0.1  # Smoothing factor
            self.adaptive_gain = alpha * current_gain + (1 - alpha) * self.adaptive_gain
            
            # Apply gain with limiting to prevent clipping
            gained_audio = audio * self.adaptive_gain
            gained_audio = np.clip(gained_audio, -0.95, 0.95)
            
            return gained_audio
            
        except Exception as e:
            logger.warning(f"⚠️ AGC failed: {e}")
            return audio
    
    def _apply_adaptive_noise_reduction(self, audio: np.ndarray) -> np.ndarray:
        """🔇 Apply adaptive noise reduction based on environmental analysis."""
        try:
            # Compute STFT
            stft = librosa.stft(audio, n_fft=self.fft_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Update noise profile adaptively
            self._update_noise_profile(magnitude)
            
            if self.noise_spectrum is not None:
                # Spectral subtraction with over-subtraction factor
                alpha = self.config.spectral_subtraction_alpha
                enhanced_magnitude = magnitude - alpha * self.noise_spectrum
                
                # Apply floor to prevent over-subtraction artifacts
                floor_factor = 0.1
                enhanced_magnitude = np.maximum(enhanced_magnitude, 
                                               floor_factor * magnitude)
                
                # Reconstruct audio
                enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
                enhanced_audio = librosa.istft(enhanced_stft, hop_length=self.hop_length)
                
                # Ensure output length matches input
                if len(enhanced_audio) > len(audio):
                    enhanced_audio = enhanced_audio[:len(audio)]
                elif len(enhanced_audio) < len(audio):
                    enhanced_audio = np.pad(enhanced_audio, (0, len(audio) - len(enhanced_audio)))
                
                return enhanced_audio
            
            return audio
            
        except Exception as e:
            logger.warning(f"⚠️ Noise reduction failed: {e}")
            return audio
    
    def _apply_spectral_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """🌟 Apply spectral enhancement for speech clarity."""
        try:
            # Compute STFT
            stft = librosa.stft(audio, n_fft=self.fft_size, hop_length=self.hop_length)
            magnitude = np.abs(stft)
            phase = np.angle(stft)
            
            # Frequency array
            freqs = librosa.fft_frequencies(sr=self.sample_rate, n_fft=self.fft_size)
            
            # Apply frequency-dependent enhancement
            enhanced_magnitude = magnitude.copy()
            
            for band_name, (low_freq, high_freq) in self.speech_bands.items():
                # Find frequency indices for this band
                band_mask = (freqs >= low_freq) & (freqs <= high_freq)
                
                if np.any(band_mask):
                    # Enhancement factors for different speech bands
                    if band_name in ['formant1', 'formant2']:
                        enhancement_factor = 1.2  # Boost formants
                    elif band_name == 'consonants':
                        enhancement_factor = 1.1  # Moderate consonant boost
                    else:
                        enhancement_factor = 1.0  # No change for other bands
                    
                    enhanced_magnitude[band_mask] *= enhancement_factor
            
            # Reconstruct audio
            enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_audio = librosa.istft(enhanced_stft, hop_length=self.hop_length)
            
            # Match length
            if len(enhanced_audio) > len(audio):
                enhanced_audio = enhanced_audio[:len(audio)]
            elif len(enhanced_audio) < len(audio):
                enhanced_audio = np.pad(enhanced_audio, (0, len(audio) - len(enhanced_audio)))
            
            return enhanced_audio
            
        except Exception as e:
            logger.warning(f"⚠️ Spectral enhancement failed: {e}")
            return audio
    
    def _apply_speech_enhancement(self, audio: np.ndarray) -> np.ndarray:
        """🗣️ Apply speech-specific enhancement algorithms."""
        try:
            # Pre-emphasis filter to balance spectrum
            pre_emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])
            
            # Dynamic range compression for consistent levels
            if self.config.dynamic_range_compression:
                compressed = self._apply_dynamic_range_compression(pre_emphasized)
            else:
                compressed = pre_emphasized
            
            # High-pass filter to remove low-frequency noise
            sos = signal.butter(4, 80, btype='high', fs=self.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, compressed)
            
            # Low-pass filter to remove high-frequency noise
            sos = signal.butter(4, 7000, btype='low', fs=self.sample_rate, output='sos')
            filtered = signal.sosfilt(sos, filtered)
            
            return filtered
            
        except Exception as e:
            logger.warning(f"⚠️ Speech enhancement failed: {e}")
            return audio
    
    def _apply_dynamic_range_compression(self, audio: np.ndarray) -> np.ndarray:
        """🎛️ Apply dynamic range compression for consistent speech levels."""
        try:
            # Simple compressor implementation
            threshold = 0.3
            ratio = 3.0
            attack = 0.01
            release = 0.1
            
            # Calculate envelope
            envelope = np.abs(audio)
            
            # Smooth envelope
            smoothed_env = signal.filtfilt([attack], [1, attack - 1], envelope)
            
            # Apply compression
            compressed_env = np.where(
                smoothed_env > threshold,
                threshold + (smoothed_env - threshold) / ratio,
                smoothed_env
            )
            
            # Apply to audio
            gain = np.where(smoothed_env > 1e-6, compressed_env / smoothed_env, 1.0)
            compressed_audio = audio * gain
            
            return compressed_audio
            
        except Exception as e:
            logger.warning(f"⚠️ Dynamic range compression failed: {e}")
            return audio
    
    def _assess_audio_quality_advanced(self, audio: np.ndarray) -> float:
        """🔍 Advanced audio quality assessment for transcription."""
        try:
            # Multiple quality metrics
            scores = {}
            
            # 1. RMS Energy Score
            rms = np.sqrt(np.mean(audio ** 2))
            scores['energy'] = min(1.0, max(0.0, (rms - 0.01) / 0.1))
            
            # 2. Dynamic Range Score
            peak = np.max(np.abs(audio))
            if peak > 0:
                dynamic_range_db = 20 * np.log10(peak / (rms + 1e-10))
                scores['dynamic_range'] = min(1.0, max(0.0, (dynamic_range_db - 10) / 30))
            else:
                scores['dynamic_range'] = 0.0
            
            # 3. Spectral Quality Score
            scores['spectral'] = self._calculate_spectral_quality(audio)
            
            # 4. Speech Characteristics Score
            scores['speech_characteristics'] = self._calculate_speech_characteristics_score(audio)
            
            # 5. SNR Estimation Score
            scores['snr'] = self._estimate_snr_score(audio)
            
            # Weighted combination
            weights = {
                'energy': 0.2,
                'dynamic_range': 0.15,
                'spectral': 0.25,
                'speech_characteristics': 0.25,
                'snr': 0.15
            }
            
            overall_score = sum(scores[metric] * weights[metric] for metric in scores)
            
            return float(overall_score)
            
        except Exception as e:
            logger.warning(f"⚠️ Quality assessment failed: {e}")
            return 0.5
    
    def _calculate_spectral_quality(self, audio: np.ndarray) -> float:
        """Calculate spectral quality metrics."""
        try:
            # Compute power spectrum
            freqs, psd = signal.welch(audio, self.sample_rate, nperseg=1024)
            
            # Speech frequency energy ratio
            speech_mask = (freqs >= 300) & (freqs <= 3400)  # Speech band
            speech_energy = np.sum(psd[speech_mask])
            total_energy = np.sum(psd)
            
            speech_ratio = speech_energy / (total_energy + 1e-10)
            
            # Spectral flatness (measure of noise-like vs tonal)
            geometric_mean = np.exp(np.mean(np.log(psd + 1e-10)))
            arithmetic_mean = np.mean(psd)
            spectral_flatness = geometric_mean / (arithmetic_mean + 1e-10)
            
            # Combine metrics
            quality_score = 0.7 * min(1.0, speech_ratio * 3) + 0.3 * (1 - spectral_flatness)
            
            return float(quality_score)
            
        except Exception:
            return 0.5
    
    def _calculate_speech_characteristics_score(self, audio: np.ndarray) -> float:
        """Calculate speech-specific quality characteristics."""
        try:
            # Zero crossing rate (speech has moderate ZCR)
            zcr = np.sum(np.diff(np.sign(audio)) != 0) / len(audio)
            zcr_score = 1.0 - abs(zcr - 0.05) / 0.05  # Optimal around 0.05
            zcr_score = max(0.0, min(1.0, zcr_score))
            
            # Formant analysis
            formant_score = self._analyze_formant_presence(audio)
            
            # Periodicity (speech has some periodicity)
            periodicity_score = self._calculate_periodicity_score(audio)
            
            # Combine scores
            overall_score = 0.4 * zcr_score + 0.4 * formant_score + 0.2 * periodicity_score
            
            return float(overall_score)
            
        except Exception:
            return 0.5
    
    def _analyze_formant_presence(self, audio: np.ndarray) -> float:
        """Analyze presence of speech formants."""
        try:
            # Simple formant detection using peak finding in spectrum
            freqs, psd = signal.welch(audio, self.sample_rate, nperseg=512)
            
            # Look for peaks in typical formant regions
            f1_region = (freqs >= 300) & (freqs <= 1000)
            f2_region = (freqs >= 1000) & (freqs <= 2500)
            
            f1_energy = np.max(psd[f1_region]) if np.any(f1_region) else 0
            f2_energy = np.max(psd[f2_region]) if np.any(f2_region) else 0
            total_max = np.max(psd)
            
            formant_score = (f1_energy + f2_energy) / (2 * total_max + 1e-10)
            
            return float(min(1.0, formant_score * 2))
            
        except Exception:
            return 0.5
    
    def _calculate_periodicity_score(self, audio: np.ndarray) -> float:
        """Calculate periodicity score (speech has some periodicity)."""
        try:
            # Autocorrelation for periodicity detection
            autocorr = np.correlate(audio, audio, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Normalize
            autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr
            
            # Find peaks in typical F0 range (80-400 Hz)
            min_period = int(self.sample_rate / 400)  # 400 Hz
            max_period = int(self.sample_rate / 80)   # 80 Hz
            
            if max_period < len(autocorr):
                period_range = autocorr[min_period:max_period]
                max_autocorr = np.max(period_range) if len(period_range) > 0 else 0
                
                return float(max(0.0, min(1.0, max_autocorr)))
            
            return 0.5
            
        except Exception:
            return 0.5
    
    def _estimate_snr_score(self, audio: np.ndarray) -> float:
        """Estimate signal-to-noise ratio score."""
        try:
            # Use percentile-based estimation
            sorted_abs = np.sort(np.abs(audio))
            noise_floor = np.mean(sorted_abs[:len(sorted_abs)//10])  # Bottom 10%
            signal_level = np.mean(sorted_abs[-len(sorted_abs)//10:])  # Top 10%
            
            if noise_floor > 0:
                snr_db = 20 * np.log10(signal_level / noise_floor)
                # Map SNR to 0-1 score (0dB=0.0, 30dB=1.0)
                snr_score = max(0.0, min(1.0, snr_db / 30))
                return float(snr_score)
            
            return 0.5
            
        except Exception:
            return 0.5
    
    def _calculate_speech_probability(self, audio: np.ndarray) -> float:
        """Calculate probability that audio contains speech."""
        try:
            # Combine multiple speech indicators
            energy_score = min(1.0, np.sqrt(np.mean(audio ** 2)) / 0.1)
            spectral_score = self._calculate_spectral_quality(audio)
            characteristics_score = self._calculate_speech_characteristics_score(audio)
            
            # Weighted combination
            speech_prob = 0.3 * energy_score + 0.4 * spectral_score + 0.3 * characteristics_score
            
            return float(max(0.0, min(1.0, speech_prob)))
            
        except Exception:
            return 0.0
    
    def _estimate_noise_level(self, audio: np.ndarray) -> float:
        """Estimate environmental noise level."""
        try:
            # Use lower percentile as noise floor estimate
            sorted_abs = np.sort(np.abs(audio))
            noise_level = np.mean(sorted_abs[:len(sorted_abs)//4])  # Bottom 25%
            
            return float(noise_level)
            
        except Exception:
            return 0.0
    
    def _create_context_overlaps(self, audio: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Create overlap segments for context correlation."""
        try:
            overlap_samples = int(self.config.overlap_duration_ms * self.sample_rate / 1000)
            
            if len(audio) > overlap_samples:
                overlap_start = audio[:overlap_samples]
                overlap_end = audio[-overlap_samples:]
                return overlap_start, overlap_end
            
            return None, None
            
        except Exception:
            return None, None
    
    def _generate_context_hash(self, audio: np.ndarray, chunk_id: int) -> str:
        """Generate hash for context correlation."""
        try:
            # Simple hash based on spectral characteristics
            freqs, psd = signal.welch(audio, self.sample_rate, nperseg=256)
            spectral_centroid = np.sum(freqs * psd) / np.sum(psd)
            
            hash_value = f"{chunk_id}_{spectral_centroid:.2f}_{len(audio)}"
            return hash_value
            
        except Exception:
            return f"chunk_{chunk_id}"
    
    def _update_noise_profile(self, magnitude: np.ndarray):
        """Update adaptive noise profile."""
        try:
            # Estimate noise from quiet regions
            energy_per_frame = np.mean(magnitude, axis=0)
            quiet_frames = energy_per_frame < np.percentile(energy_per_frame, 30)
            
            if np.any(quiet_frames):
                current_noise = np.mean(magnitude[:, quiet_frames], axis=1)
                
                if self.noise_spectrum is None:
                    self.noise_spectrum = current_noise
                else:
                    # Exponential moving average update
                    alpha = self.config.adaptation_rate
                    self.noise_spectrum = alpha * current_noise + (1 - alpha) * self.noise_spectrum
                    
        except Exception as e:
            logger.warning(f"⚠️ Noise profile update failed: {e}")
    
    def _convert_audio_to_array(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array."""
        try:
            if isinstance(audio_data, bytes):
                # Assume 16-bit PCM
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            return audio_array
            
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return np.array([])
    
    def _create_empty_chunk(self, session_id: str, chunk_id: int, timestamp: float) -> AudioChunk:
        """Create empty chunk for error cases."""
        return AudioChunk(
            data=np.array([]),
            timestamp=timestamp,
            duration=0.0,
            chunk_id=chunk_id,
            session_id=session_id,
            quality_score=0.0,
            speech_probability=0.0,
            noise_level=0.0,
            context_hash=f"empty_{chunk_id}"
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        return {
            'avg_processing_time': np.mean(self.processing_times) if self.processing_times else 0,
            'avg_quality_score': np.mean(self.quality_scores) if self.quality_scores else 0,
            'chunks_processed': len(self.chunk_history),
            'current_noise_level': np.mean(self.noise_spectrum) if self.noise_spectrum is not None else 0
        }

# Global processor instance
_advanced_processor = None
_processor_lock = threading.Lock()

def get_advanced_audio_processor() -> AdvancedAudioProcessor:
    """Get global advanced audio processor instance"""
    global _advanced_processor
    
    with _processor_lock:
        if _advanced_processor is None:
            _advanced_processor = AdvancedAudioProcessor()
        return _advanced_processor

logger.info("✅ Advanced Audio Processor module initialized")