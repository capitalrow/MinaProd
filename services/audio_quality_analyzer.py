"""
🔥 PHASE 3: Advanced Audio Quality Analysis
Real-time audio quality monitoring and enhancement features.
"""

import numpy as np
import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class AudioQualityMetrics:
    """Audio quality measurement results."""
    snr_db: float
    volume_level: float
    frequency_balance: float
    clarity_score: float
    stability_score: float
    noise_level: float
    dynamic_range: float
    spectral_centroid: float
    zero_crossing_rate: float
    overall_quality: float
    timestamp: float

@dataclass
class QualityEnhancementConfig:
    """Configuration for audio quality enhancement."""
    enable_noise_reduction: bool = True
    enable_dynamic_range_compression: bool = True
    enable_spectral_enhancement: bool = True
    target_snr_db: float = 20.0
    volume_normalization: bool = True
    adaptive_filtering: bool = True
    quality_threshold: float = 0.7
    measurement_window_size: int = 100

class AudioQualityAnalyzer:
    """
    🔥 PHASE 3: Advanced audio quality analysis and enhancement.
    Provides real-time audio quality monitoring, noise reduction, and adaptive enhancement.
    """
    
    def __init__(self, config: Optional[QualityEnhancementConfig] = None):
        self.config = config or QualityEnhancementConfig()
        
        # Quality measurement history
        self.quality_history = deque(maxlen=self.config.measurement_window_size)
        self.noise_profile = None
        self.baseline_established = False
        
        # Enhancement state
        self.enhancement_filters = {}
        self.adaptation_state = {
            'noise_reduction_strength': 0.5,
            'compression_ratio': 2.0,
            'enhancement_level': 0.3,
            'last_adaptation': 0
        }
        
        # Statistics
        self.stats = {
            'total_analyses': 0,
            'quality_improvements': 0,
            'noise_reduction_applications': 0,
            'enhancement_adaptations': 0,
            'average_quality': 0.0
        }
        
        logger.info("Advanced Audio Quality Analyzer initialized")
    
    def analyze_audio_quality(self, audio_data: np.ndarray, sample_rate: int = 16000) -> AudioQualityMetrics:
        """
        Comprehensive audio quality analysis.
        
        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            
        Returns:
            Detailed quality metrics
        """
        if len(audio_data) == 0:
            return self._create_empty_metrics()
        
        # Ensure audio is normalized
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
        
        # Calculate individual quality metrics
        snr_db = self._calculate_snr(audio_data)
        volume_level = self._calculate_volume_level(audio_data)
        frequency_balance = self._calculate_frequency_balance(audio_data, sample_rate)
        clarity_score = self._calculate_clarity_score(audio_data, sample_rate)
        stability_score = self._calculate_stability_score(audio_data)
        noise_level = self._calculate_noise_level(audio_data)
        dynamic_range = self._calculate_dynamic_range(audio_data)
        spectral_centroid = self._calculate_spectral_centroid(audio_data, sample_rate)
        zero_crossing_rate = self._calculate_zero_crossing_rate(audio_data)
        
        # Calculate overall quality score
        overall_quality = self._calculate_overall_quality(
            snr_db, volume_level, frequency_balance, clarity_score, 
            stability_score, noise_level, dynamic_range
        )
        
        metrics = AudioQualityMetrics(
            snr_db=snr_db,
            volume_level=volume_level,
            frequency_balance=frequency_balance,
            clarity_score=clarity_score,
            stability_score=stability_score,
            noise_level=noise_level,
            dynamic_range=dynamic_range,
            spectral_centroid=spectral_centroid,
            zero_crossing_rate=zero_crossing_rate,
            overall_quality=overall_quality,
            timestamp=time.time()
        )
        
        # Update quality history
        self.quality_history.append(metrics)
        
        # Update statistics
        self.stats['total_analyses'] += 1
        self.stats['average_quality'] = (
            self.stats['average_quality'] * 0.95 + overall_quality * 0.05
        )
        
        return metrics
    
    def enhance_audio_quality(self, audio_data: np.ndarray, 
                            quality_metrics: AudioQualityMetrics) -> np.ndarray:
        """
        Apply adaptive audio quality enhancement.
        
        Args:
            audio_data: Input audio samples
            quality_metrics: Current quality assessment
            
        Returns:
            Enhanced audio samples
        """
        enhanced_audio = audio_data.copy()
        
        if quality_metrics.overall_quality >= self.config.quality_threshold:
            return enhanced_audio  # Already good quality
        
        # Apply noise reduction if needed
        if (self.config.enable_noise_reduction and 
            quality_metrics.noise_level > 0.3):
            enhanced_audio = self._apply_noise_reduction(enhanced_audio)
            self.stats['noise_reduction_applications'] += 1
        
        # Apply dynamic range compression if needed
        if (self.config.enable_dynamic_range_compression and 
            quality_metrics.dynamic_range < 0.3):
            enhanced_audio = self._apply_dynamic_range_compression(enhanced_audio)
        
        # Apply spectral enhancement if needed
        if (self.config.enable_spectral_enhancement and 
            quality_metrics.clarity_score < 0.6):
            enhanced_audio = self._apply_spectral_enhancement(enhanced_audio)
        
        # Volume normalization if needed
        if (self.config.volume_normalization and 
            (quality_metrics.volume_level < 0.1 or quality_metrics.volume_level > 0.9)):
            enhanced_audio = self._normalize_volume(enhanced_audio)
        
        # Adaptive filter tuning
        if self.config.adaptive_filtering:
            self._adapt_enhancement_parameters(quality_metrics)
        
        self.stats['quality_improvements'] += 1
        return enhanced_audio
    
    def _calculate_snr(self, audio_data: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio in dB."""
        if len(audio_data) == 0:
            return 0.0
        
        # Estimate signal and noise power
        signal_power = np.mean(audio_data ** 2)
        noise_power = np.var(audio_data) * 0.1  # Rough noise estimate
        
        if noise_power == 0:
            return 60.0  # Very high SNR
        
        snr = 10 * np.log10(signal_power / noise_power)
        return max(0, min(60, snr))  # Clamp to reasonable range
    
    def _calculate_volume_level(self, audio_data: np.ndarray) -> float:
        """Calculate normalized volume level (0-1)."""
        if len(audio_data) == 0:
            return 0.0
        return np.sqrt(np.mean(audio_data ** 2))
    
    def _calculate_frequency_balance(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate frequency balance score (0-1)."""
        if len(audio_data) < 256:
            return 0.5  # Not enough data
        
        # Simple FFT-based frequency analysis
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        # Divide into frequency bands
        low_band = np.mean(magnitude[:len(magnitude)//4])
        mid_band = np.mean(magnitude[len(magnitude)//4:3*len(magnitude)//4])
        high_band = np.mean(magnitude[3*len(magnitude)//4:])
        
        # Calculate balance (ideal is roughly equal distribution)
        total_energy = low_band + mid_band + high_band
        if total_energy == 0:
            return 0.5
        
        # Penalize extreme imbalances
        balance_score = 1.0 - np.std([low_band, mid_band, high_band]) / total_energy
        return max(0, min(1, balance_score))
    
    def _calculate_clarity_score(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate audio clarity score based on spectral characteristics."""
        if len(audio_data) < 256:
            return 0.5
        
        # Calculate spectral sharpness
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        
        # Spectral centroid indicates clarity
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        centroid = np.sum(freqs * magnitude) / np.sum(magnitude) if np.sum(magnitude) > 0 else 0
        
        # Normalize to 0-1 range (assume speech is around 1000-4000 Hz)
        clarity = min(1.0, centroid / 4000.0) if centroid > 0 else 0.0
        return clarity
    
    def _calculate_stability_score(self, audio_data: np.ndarray) -> float:
        """Calculate temporal stability of the audio."""
        if len(audio_data) < 100:
            return 0.5
        
        # Calculate frame-to-frame variation
        frame_size = len(audio_data) // 10
        frame_energies = []
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame_energy = np.mean(audio_data[i:i+frame_size] ** 2)
            frame_energies.append(frame_energy)
        
        if len(frame_energies) < 2:
            return 0.5
        
        # Lower variation = higher stability
        variation = np.std(frame_energies) / (np.mean(frame_energies) + 1e-10)
        stability = 1.0 / (1.0 + variation)
        return max(0, min(1, stability))
    
    def _calculate_noise_level(self, audio_data: np.ndarray) -> float:
        """Estimate noise level in the audio."""
        if len(audio_data) == 0:
            return 0.0
        
        # Use minimum energy periods as noise estimate
        frame_size = max(1, len(audio_data) // 20)
        frame_energies = []
        
        for i in range(0, len(audio_data) - frame_size, frame_size):
            frame_energy = np.mean(audio_data[i:i+frame_size] ** 2)
            frame_energies.append(frame_energy)
        
        if not frame_energies:
            return 0.0
        
        # Noise level is estimated from lowest energy frames
        noise_level = np.percentile(frame_energies, 10)  # Bottom 10%
        return min(1.0, noise_level * 10)  # Scale to 0-1
    
    def _calculate_dynamic_range(self, audio_data: np.ndarray) -> float:
        """Calculate dynamic range of the audio."""
        if len(audio_data) == 0:
            return 0.0
        
        max_amplitude = np.max(np.abs(audio_data))
        min_amplitude = np.mean(np.abs(audio_data)) + 1e-10
        
        dynamic_range = max_amplitude / min_amplitude
        return min(1.0, dynamic_range / 100.0)  # Normalize to 0-1
    
    def _calculate_spectral_centroid(self, audio_data: np.ndarray, sample_rate: int) -> float:
        """Calculate spectral centroid frequency."""
        if len(audio_data) < 256:
            return 0.0
        
        fft = np.fft.rfft(audio_data)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio_data), 1/sample_rate)
        
        if np.sum(magnitude) == 0:
            return 0.0
        
        centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
        return centroid
    
    def _calculate_zero_crossing_rate(self, audio_data: np.ndarray) -> float:
        """Calculate zero crossing rate."""
        if len(audio_data) < 2:
            return 0.0
        
        zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
        zcr = zero_crossings / len(audio_data)
        return zcr
    
    def _calculate_overall_quality(self, snr_db: float, volume_level: float, 
                                 frequency_balance: float, clarity_score: float,
                                 stability_score: float, noise_level: float,
                                 dynamic_range: float) -> float:
        """Calculate weighted overall quality score."""
        # Normalize SNR to 0-1 scale
        snr_normalized = min(1.0, snr_db / 30.0)
        
        # Normalize volume level (penalize too low or too high)
        volume_score = 1.0 - abs(volume_level - 0.5) * 2
        volume_score = max(0, volume_score)
        
        # Invert noise level (lower noise = higher score)
        noise_score = 1.0 - noise_level
        
        # Weighted combination
        weights = {
            'snr': 0.25,
            'volume': 0.15,
            'frequency_balance': 0.15,
            'clarity': 0.20,
            'stability': 0.10,
            'noise': 0.10,
            'dynamic_range': 0.05
        }
        
        quality_score = (
            weights['snr'] * snr_normalized +
            weights['volume'] * volume_score +
            weights['frequency_balance'] * frequency_balance +
            weights['clarity'] * clarity_score +
            weights['stability'] * stability_score +
            weights['noise'] * noise_score +
            weights['dynamic_range'] * dynamic_range
        )
        
        return max(0, min(1, quality_score))
    
    def _apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply adaptive noise reduction."""
        # Simple spectral subtraction noise reduction
        if len(audio_data) < 256:
            return audio_data
        
        # FFT
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Estimate noise floor
        noise_floor = np.percentile(magnitude, 10)
        
        # Apply spectral subtraction
        strength = self.adaptation_state['noise_reduction_strength']
        enhanced_magnitude = magnitude - strength * noise_floor
        enhanced_magnitude = np.maximum(enhanced_magnitude, 0.1 * magnitude)
        
        # Reconstruct signal
        enhanced_fft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = np.real(np.fft.ifft(enhanced_fft))
        
        return enhanced_audio.astype(audio_data.dtype)
    
    def _apply_dynamic_range_compression(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply dynamic range compression."""
        if len(audio_data) == 0:
            return audio_data
        
        # Simple compressor
        threshold = 0.7
        ratio = self.adaptation_state['compression_ratio']
        
        compressed = np.copy(audio_data)
        above_threshold = np.abs(compressed) > threshold
        
        # Apply compression to samples above threshold
        compressed[above_threshold] = (
            np.sign(compressed[above_threshold]) * 
            (threshold + (np.abs(compressed[above_threshold]) - threshold) / ratio)
        )
        
        return compressed
    
    def _apply_spectral_enhancement(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply spectral enhancement for clarity."""
        if len(audio_data) < 256:
            return audio_data
        
        # FFT-based enhancement
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft)
        phase = np.angle(fft)
        
        # Enhance mid-frequencies (speech clarity)
        enhancement_level = self.adaptation_state['enhancement_level']
        freq_bins = len(magnitude)
        
        # Create enhancement filter (boost 1-4 kHz range)
        enhancement_filter = np.ones(freq_bins)
        mid_start = int(0.1 * freq_bins)  # ~1 kHz for 16kHz sample rate
        mid_end = int(0.4 * freq_bins)    # ~4 kHz for 16kHz sample rate
        
        enhancement_filter[mid_start:mid_end] *= (1.0 + enhancement_level)
        
        # Apply enhancement
        enhanced_magnitude = magnitude * enhancement_filter
        enhanced_fft = enhanced_magnitude * np.exp(1j * phase)
        enhanced_audio = np.real(np.fft.ifft(enhanced_fft))
        
        return enhanced_audio.astype(audio_data.dtype)
    
    def _normalize_volume(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio volume to target level."""
        if len(audio_data) == 0:
            return audio_data
        
        current_rms = np.sqrt(np.mean(audio_data ** 2))
        if current_rms == 0:
            return audio_data
        
        target_rms = 0.5  # Target RMS level
        gain = target_rms / current_rms
        
        # Limit gain to prevent excessive amplification
        gain = min(gain, 10.0)
        
        normalized = audio_data * gain
        
        # Prevent clipping
        max_val = np.max(np.abs(normalized))
        if max_val > 1.0:
            normalized = normalized / max_val
        
        return normalized
    
    def _adapt_enhancement_parameters(self, quality_metrics: AudioQualityMetrics):
        """Adapt enhancement parameters based on quality feedback."""
        current_time = time.time()
        if current_time - self.adaptation_state['last_adaptation'] < 5.0:
            return  # Don't adapt too frequently
        
        # Adjust noise reduction strength
        if quality_metrics.noise_level > 0.5:
            self.adaptation_state['noise_reduction_strength'] = min(0.8, 
                self.adaptation_state['noise_reduction_strength'] + 0.1)
        elif quality_metrics.noise_level < 0.2:
            self.adaptation_state['noise_reduction_strength'] = max(0.2,
                self.adaptation_state['noise_reduction_strength'] - 0.1)
        
        # Adjust enhancement level
        if quality_metrics.clarity_score < 0.5:
            self.adaptation_state['enhancement_level'] = min(0.5,
                self.adaptation_state['enhancement_level'] + 0.05)
        elif quality_metrics.clarity_score > 0.8:
            self.adaptation_state['enhancement_level'] = max(0.1,
                self.adaptation_state['enhancement_level'] - 0.05)
        
        self.adaptation_state['last_adaptation'] = current_time
        self.stats['enhancement_adaptations'] += 1
    
    def _create_empty_metrics(self) -> AudioQualityMetrics:
        """Create empty quality metrics for invalid input."""
        return AudioQualityMetrics(
            snr_db=0.0, volume_level=0.0, frequency_balance=0.5,
            clarity_score=0.0, stability_score=0.0, noise_level=0.0,
            dynamic_range=0.0, spectral_centroid=0.0, zero_crossing_rate=0.0,
            overall_quality=0.0, timestamp=time.time()
        )
    
    def get_quality_statistics(self) -> Dict[str, Any]:
        """Get comprehensive quality analysis statistics."""
        recent_quality = 0.0
        if self.quality_history:
            recent_quality = np.mean([m.overall_quality for m in self.quality_history])
        
        return {
            'total_analyses': self.stats['total_analyses'],
            'quality_improvements': self.stats['quality_improvements'],
            'noise_reduction_applications': self.stats['noise_reduction_applications'],
            'enhancement_adaptations': self.stats['enhancement_adaptations'],
            'average_quality': self.stats['average_quality'],
            'recent_quality': recent_quality,
            'current_adaptation_state': self.adaptation_state.copy()
        }