#!/usr/bin/env python3
# 🎤 Production Feature: Adaptive VAD with Environmental Noise Estimation
"""
Enterprise-grade Voice Activity Detection (VAD) service with adaptive algorithms.
Enhanced VAD processing with superior buffer management, noise reduction, 
and dynamic environmental adaptation.

Addresses: "Adaptive VAD algorithms with environmental noise estimation" for Fix Pack 4.

Key Features:
- Adaptive thresholds based on environmental noise
- Multi-band spectral analysis
- Dynamic sensitivity adjustment
- Environmental noise profiling and adaptation
- Advanced temporal logic with hysteresis
- Real-time quality metrics and performance monitoring
"""

import logging
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import time
from scipy import signal
from scipy.stats import entropy

logger = logging.getLogger(__name__)

class NoiseEnvironment(Enum):
    """Environmental noise classification."""
    QUIET = "quiet"              # Library, studio
    OFFICE = "office"           # Office environment
    CAFE = "cafe"              # Restaurant, cafe
    STREET = "street"          # Street, traffic
    CONSTRUCTION = "construction" # Construction, machinery
    UNKNOWN = "unknown"        # Unknown/unclassified

@dataclass
class VADConfig:
    """Enhanced configuration for adaptive Voice Activity Detection."""
    # Basic VAD settings
    sensitivity: float = 0.5
    min_speech_duration: int = 10000  # ms
    min_silence_duration: int = 500  # ms
    sample_rate: int = 16000
    frame_duration: int = 20  # ms
    
    # Adaptive settings
    adaptive_mode: bool = True
    adaptation_rate: float = 0.1          # Speed of adaptation (0-1)
    noise_estimation_window: int = 50     # Frames for noise estimation
    
    # Thresholds (will be adaptive)
    energy_threshold: float = 0.01
    zero_crossing_threshold: int = 10
    noise_gate_threshold: float = 0.005
    spectral_threshold: float = 0.3
    
    # Environmental adaptation
    environment_detection: bool = True
    min_environment_confidence: float = 0.7
    environment_adaptation_factor: float = 1.5
    
    # Quality control
    min_snr_threshold: float = 6.0        # dB
    max_noise_variance: float = 0.1
    quality_check_enabled: bool = True
    
    # Performance settings
    multi_band_analysis: bool = True
    spectral_smoothing: bool = True
    temporal_smoothing_factor: float = 0.3

@dataclass
class NoiseProfile:
    """Environmental noise profile."""
    environment: NoiseEnvironment = NoiseEnvironment.UNKNOWN
    average_noise_level: float = 0.0
    noise_spectrum: np.ndarray = field(default_factory=lambda: np.array([]))
    spectral_characteristics: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0
    last_updated: float = field(default_factory=time.time)

class VADResult:
    """Result of VAD processing."""
    def __init__(self, is_speech: bool, confidence: float, energy: float, timestamp: float):
        self.is_speech = is_speech
        self.confidence = confidence
        self.energy = energy
        self.timestamp = timestamp

class VADService:
    """
    🎤 Enterprise-grade adaptive Voice Activity Detection service.
    
    Provides advanced VAD processing with environmental adaptation,
    multi-band spectral analysis, and dynamic threshold adjustment.
    """
    
    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self.frame_size = int(self.config.sample_rate * self.config.frame_duration / 1000)
        
        # Enhanced buffer management
        self.speech_frames = deque(maxlen=200)    # Extended for better analysis
        self.silence_frames = deque(maxlen=100)   # Enhanced silence tracking
        self.spectral_history = deque(maxlen=50)  # Spectral analysis history
        
        # Adaptive state tracking
        self.current_state = 'silence'  # 'silence', 'speech', 'transition'
        self.speech_start_time = None
        self.silence_start_time = None
        self.last_speech_time = 0
        
        # Enhanced noise estimation and environmental adaptation
        self.noise_profile = NoiseProfile()
        self.noise_samples = deque(maxlen=self.config.noise_estimation_window)
        self.spectral_noise_samples = deque(maxlen=30)
        self.adaptive_thresholds = self._initialize_adaptive_thresholds()
        
        # Multi-band analysis
        self.frequency_bands = self._initialize_frequency_bands()
        self.band_energies_history = deque(maxlen=20)
        
        # Performance statistics
        self.statistics = {
            'total_frames': 0,
            'speech_frames': 0,
            'false_positives': 0,
            'environment_switches': 0,
            'adaptation_events': 0,
            'snr_measurements': deque(maxlen=100),
            'quality_scores': deque(maxlen=50)
        }
        
        # Advanced features
        self.last_voice_time = 0
        self.voice_tail_ms = 300
        self.spectral_smoothing_buffer = deque(maxlen=5)
        
        logger.info(f"🎤 Enhanced VAD Service initialized with adaptive mode: {self.config.adaptive_mode}")
    
    def _initialize_adaptive_thresholds(self) -> Dict[str, float]:
        """Initialize adaptive threshold values."""
        return {
            'energy': self.config.energy_threshold,
            'spectral': self.config.spectral_threshold,
            'zero_crossing': float(self.config.zero_crossing_threshold),
            'noise_gate': self.config.noise_gate_threshold
        }
    
    def _initialize_frequency_bands(self) -> List[Tuple[float, float]]:
        """Initialize frequency bands for multi-band analysis."""
        # Define frequency bands optimized for speech analysis
        return [
            (80, 250),     # Low frequency (fundamental F0)
            (250, 500),    # Low-mid (first formant region)
            (500, 2000),   # Mid (second formant region) 
            (2000, 4000),  # High-mid (consonants, clarity)
            (4000, 8000)   # High (fricatives, sibilants)
        ]
    
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
        🎤 Enhanced audio chunk processing with adaptive algorithms.
        
        Args:
            audio_data: Raw audio bytes
            timestamp: Optional timestamp, uses current time if None
            
        Returns:
            VADResult with comprehensive speech detection information
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
            
            # === ENHANCED FEATURE EXTRACTION ===
            # Basic features
            energy = self._calculate_energy(audio_array)
            zero_crossings = self._calculate_zero_crossings(audio_array)
            
            # Advanced spectral features
            spectral_features = self._calculate_enhanced_spectral_features(audio_array)
            
            # Multi-band analysis
            band_features = self._analyze_frequency_bands(audio_array) if self.config.multi_band_analysis else {}
            
            # Environmental noise analysis
            noise_features = self._analyze_environmental_noise(audio_array)
            
            # === ADAPTIVE PROCESSING ===
            # Update environmental profile
            if self.config.environment_detection:
                self._update_environmental_profile(spectral_features, noise_features)
            
            # Adaptive threshold adjustment
            if self.config.adaptive_mode:
                self._adapt_thresholds(energy, spectral_features, noise_features)
            
            # === SPEECH DETECTION ===
            # Calculate comprehensive speech probability
            speech_probability = self._calculate_enhanced_speech_probability(
                energy, zero_crossings, spectral_features, band_features, noise_features
            )
            
            # Apply temporal smoothing and hysteresis
            is_speech = self._apply_enhanced_temporal_logic(speech_probability, timestamp)
            
            # Quality assessment
            quality_score = self._assess_audio_quality(audio_array, spectral_features, noise_features)
            
            # === STATE UPDATES ===
            # Update voice timing for gating
            if is_speech:
                self.last_voice_time = timestamp
            
            # Update comprehensive statistics
            self._update_enhanced_statistics(is_speech, speech_probability, quality_score)
            
            # Create enhanced VAD result
            result = VADResult(is_speech, float(speech_probability), float(energy), timestamp)
            result.spectral_features = spectral_features
            result.band_features = band_features
            result.noise_features = noise_features
            result.quality_score = quality_score
            result.environment = self.noise_profile.environment.value
            result.adaptive_thresholds = self.adaptive_thresholds.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing enhanced audio chunk: {e}")
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
    
    def _calculate_enhanced_spectral_features(self, audio_array: np.ndarray) -> Dict[str, float]:
        """🎤 Calculate enhanced spectral features with advanced analysis."""
        if len(audio_array) < 64:  # Minimum for FFT
            return {'spectral_centroid': 0.0, 'spectral_rolloff': 0.0, 'spectral_bandwidth': 0.0, 'spectral_flatness': 0.0}
        
        # Pre-emphasis filter for speech enhancement
        pre_emphasized = np.append(audio_array[0], audio_array[1:] - 0.97 * audio_array[:-1])
        
        # Apply windowing
        windowed = pre_emphasized * np.hanning(len(pre_emphasized))
        
        # FFT with zero padding for better frequency resolution
        n_fft = max(512, len(windowed))
        fft = np.fft.rfft(windowed, n=n_fft)
        magnitude = np.abs(fft)
        power_spectrum = magnitude ** 2
        
        # Frequency array
        freqs = np.fft.rfftfreq(n_fft, 1/self.config.sample_rate)
        
        # Enhanced spectral features
        features = {}
        
        # Spectral centroid (center of mass of spectrum)
        if np.sum(magnitude) > 0:
            features['spectral_centroid'] = float(np.sum(freqs * magnitude) / np.sum(magnitude))
        else:
            features['spectral_centroid'] = 0.0
        
        # Spectral rolloff (85% of spectral energy)
        cumsum = np.cumsum(power_spectrum)
        total_energy = cumsum[-1]
        if total_energy > 0:
            rolloff_idx = np.where(cumsum >= 0.85 * total_energy)[0]
            features['spectral_rolloff'] = float(freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else freqs[-1])
        else:
            features['spectral_rolloff'] = 0.0
        
        # Spectral bandwidth (spread around centroid)
        if np.sum(magnitude) > 0 and features['spectral_centroid'] > 0:
            centroid = features['spectral_centroid']
            bandwidth = np.sqrt(np.sum(((freqs - centroid) ** 2) * magnitude) / np.sum(magnitude))
            features['spectral_bandwidth'] = float(bandwidth)
        else:
            features['spectral_bandwidth'] = 0.0
        
        # Spectral flatness (measure of how noise-like vs tonal)
        if len(magnitude) > 0 and np.all(magnitude > 1e-10):
            geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10)))
            arithmetic_mean = np.mean(magnitude)
            features['spectral_flatness'] = float(geometric_mean / arithmetic_mean) if arithmetic_mean > 0 else 0.0
        else:
            features['spectral_flatness'] = 0.0
        
        # Spectral flux (change from previous frame)
        if len(self.spectral_history) > 0:
            prev_spectrum = self.spectral_history[-1]
            if len(prev_spectrum) == len(magnitude):
                spectral_flux = np.sum((magnitude - prev_spectrum) ** 2)
                features['spectral_flux'] = float(spectral_flux)
            else:
                features['spectral_flux'] = 0.0
        else:
            features['spectral_flux'] = 0.0
        
        # Store current spectrum for next frame
        self.spectral_history.append(magnitude.copy())
        
        # Speech-specific features
        features['formant_activity'] = self._detect_formant_activity(magnitude, freqs)
        features['harmonic_strength'] = self._calculate_harmonic_strength(magnitude, freqs)
        
        return features
    
    def _detect_formant_activity(self, magnitude: np.ndarray, freqs: np.ndarray) -> float:
        """Detect formant activity in typical speech ranges."""
        # Check for peaks in formant regions
        f1_region = (freqs >= 300) & (freqs <= 1000)  # F1 region
        f2_region = (freqs >= 800) & (freqs <= 2500)  # F2 region
        
        f1_energy = np.sum(magnitude[f1_region]) if np.any(f1_region) else 0
        f2_energy = np.sum(magnitude[f2_region]) if np.any(f2_region) else 0
        total_energy = np.sum(magnitude)
        
        formant_ratio = (f1_energy + f2_energy) / (total_energy + 1e-10)
        return float(min(1.0, formant_ratio * 2))  # Normalize to 0-1
    
    def _calculate_harmonic_strength(self, magnitude: np.ndarray, freqs: np.ndarray) -> float:
        """Calculate strength of harmonic structure."""
        # Look for harmonic peaks
        if len(magnitude) < 10:
            return 0.0
        
        # Smooth spectrum to find peaks
        smoothed = signal.medfilt(magnitude, kernel_size=5)
        
        # Find peaks
        peaks = signal.find_peaks(smoothed, height=np.max(smoothed) * 0.1)[0]
        
        if len(peaks) < 2:
            return 0.0
        
        # Check for harmonic relationships
        peak_freqs = freqs[peaks]
        harmonic_score = 0.0
        
        for i, f1 in enumerate(peak_freqs[:-1]):
            for f2 in peak_freqs[i+1:]:
                if f1 > 0 and 1.8 <= f2/f1 <= 2.2:  # Approximately 2:1 ratio
                    harmonic_score += 1.0
                elif f1 > 0 and 2.8 <= f2/f1 <= 3.2:  # Approximately 3:1 ratio
                    harmonic_score += 0.5
        
        return float(min(1.0, harmonic_score / max(1, len(peaks))))
    
    def _analyze_frequency_bands(self, audio_array: np.ndarray) -> Dict[str, float]:
        """🎤 Multi-band frequency analysis for enhanced speech detection."""
        if len(audio_array) < 64:
            return {f'band_{i}_energy': 0.0 for i in range(len(self.frequency_bands))}
        
        # FFT for frequency domain analysis
        windowed = audio_array * np.hanning(len(audio_array))
        fft = np.fft.rfft(windowed)
        magnitude = np.abs(fft) ** 2
        freqs = np.fft.rfftfreq(len(audio_array), 1/self.config.sample_rate)
        
        band_features = {}
        total_energy = np.sum(magnitude)
        
        for i, (low_freq, high_freq) in enumerate(self.frequency_bands):
            # Find frequency indices for this band
            band_mask = (freqs >= low_freq) & (freqs <= high_freq)
            band_energy = np.sum(magnitude[band_mask]) if np.any(band_mask) else 0.0
            
            # Normalize by total energy
            band_ratio = band_energy / (total_energy + 1e-10)
            band_features[f'band_{i}_energy'] = float(band_ratio)
            
            # Band-specific features
            if i == 0:  # Low frequency (F0 region)
                band_features['f0_strength'] = float(min(1.0, band_ratio * 5))  # Amplify F0 contribution
            elif i == 1 or i == 2:  # Formant regions
                band_features[f'formant_{i}_strength'] = float(min(1.0, band_ratio * 3))
            elif i == 3 or i == 4:  # High frequency (consonants)
                band_features[f'consonant_{i-3}_strength'] = float(min(1.0, band_ratio * 4))
        
        # Calculate band energy ratios for speech characteristics
        low_energy = sum(band_features.get(f'band_{i}_energy', 0) for i in range(2))
        high_energy = sum(band_features.get(f'band_{i}_energy', 0) for i in range(2, 5))
        
        band_features['speech_balance'] = float(low_energy / (high_energy + 1e-10))
        band_features['total_speech_energy'] = float(low_energy + high_energy)
        
        # Store for trend analysis
        self.band_energies_history.append(band_features.copy())
        
        return band_features
    
    def _analyze_environmental_noise(self, audio_array: np.ndarray) -> Dict[str, float]:
        """🎤 Analyze environmental noise characteristics."""
        if len(audio_array) < 64:
            return {'noise_level': 0.0, 'noise_type': 'unknown'}
        
        # Basic noise level
        rms_energy = np.sqrt(np.mean(audio_array ** 2))
        
        # Spectral analysis for noise characterization
        windowed = audio_array * np.hanning(len(audio_array))
        fft = np.fft.rfft(windowed)
        magnitude = np.abs(fft)
        freqs = np.fft.rfftfreq(len(audio_array), 1/self.config.sample_rate)
        
        noise_features = {
            'noise_level': float(rms_energy),
            'spectral_peak': float(freqs[np.argmax(magnitude)] if len(magnitude) > 0 else 0),
            'high_freq_noise': float(np.sum(magnitude[freqs > 4000]) / (np.sum(magnitude) + 1e-10)),
            'low_freq_noise': float(np.sum(magnitude[freqs < 300]) / (np.sum(magnitude) + 1e-10)),
        }
        
        # Noise type classification (simplified)
        if noise_features['high_freq_noise'] > 0.3:
            noise_features['noise_type'] = 'hiss'  # Air conditioning, electronics
        elif noise_features['low_freq_noise'] > 0.4:
            noise_features['noise_type'] = 'rumble'  # Traffic, machinery
        elif noise_features['spectral_peak'] > 1000:
            noise_features['noise_type'] = 'tonal'  # Electronic interference
        else:
            noise_features['noise_type'] = 'broadband'  # General ambient noise
        
        # Signal-to-noise ratio estimation
        if len(self.noise_samples) > 5:
            noise_floor = np.percentile(list(self.noise_samples), 25)  # Use 25th percentile as noise floor
            snr_db = 20 * np.log10((rms_energy + 1e-10) / (noise_floor + 1e-10))
            noise_features['estimated_snr'] = float(max(-10, min(40, snr_db)))  # Clip to reasonable range
        else:
            noise_features['estimated_snr'] = 0.0
        
        return noise_features
    
    def _update_environmental_profile(self, spectral_features: Dict[str, float], noise_features: Dict[str, float]):
        """🌍 Update environmental noise profile for adaptive thresholds."""
        current_noise = noise_features.get('noise_level', 0.0)
        noise_type = noise_features.get('noise_type', 'unknown')
        
        # Update noise profile
        if self.current_state == 'silence' and current_noise > 0:
            self.noise_samples.append(current_noise)
            
            # Update average noise level with exponential moving average
            alpha = 0.1  # Learning rate
            self.noise_profile.average_noise_level = (
                alpha * current_noise + (1 - alpha) * self.noise_profile.average_noise_level
            )
        
        # Environment classification
        snr = noise_features.get('estimated_snr', 0.0)
        
        if current_noise < 0.005 and snr > 25:
            detected_env = NoiseEnvironment.QUIET
        elif 0.005 <= current_noise < 0.02 and snr > 15:
            detected_env = NoiseEnvironment.OFFICE
        elif 0.02 <= current_noise < 0.05 and snr > 10:
            detected_env = NoiseEnvironment.CAFE
        elif 0.05 <= current_noise < 0.1 and snr > 5:
            detected_env = NoiseEnvironment.STREET
        elif current_noise >= 0.1:
            detected_env = NoiseEnvironment.CONSTRUCTION
        else:
            detected_env = NoiseEnvironment.UNKNOWN
        
        # Update environment with confidence
        if detected_env != self.noise_profile.environment:
            # Require consistent detection before switching
            if not hasattr(self, '_env_transition_count'):
                self._env_transition_count = {}
            
            self._env_transition_count[detected_env] = self._env_transition_count.get(detected_env, 0) + 1
            
            if self._env_transition_count[detected_env] >= 5:  # Require 5 consistent detections
                logger.info(f"🌍 Environment changed: {self.noise_profile.environment.value} → {detected_env.value}")
                self.noise_profile.environment = detected_env
                self.noise_profile.confidence = 0.8
                self.noise_profile.last_updated = time.time()
                self.statistics['environment_switches'] += 1
                self._env_transition_count.clear()
    
    def _adapt_thresholds(self, energy: float, spectral_features: Dict[str, float], noise_features: Dict[str, float]):
        """🎯 Dynamically adapt detection thresholds based on environment."""
        if not self.config.adaptive_mode:
            return
        
        # Base adaptation on noise level and environment
        noise_level = noise_features.get('noise_level', 0.0)
        snr = noise_features.get('estimated_snr', 0.0)
        
        # Environment-specific adaptation factors
        env_factors = {
            NoiseEnvironment.QUIET: 0.8,      # Lower thresholds in quiet
            NoiseEnvironment.OFFICE: 1.0,     # Standard thresholds
            NoiseEnvironment.CAFE: 1.3,       # Higher thresholds in noisy cafe
            NoiseEnvironment.STREET: 1.6,     # Much higher for street noise
            NoiseEnvironment.CONSTRUCTION: 2.0, # Highest for construction
            NoiseEnvironment.UNKNOWN: 1.0     # Default
        }
        
        env_factor = env_factors.get(self.noise_profile.environment, 1.0)
        
        # Adaptive energy threshold
        base_energy_threshold = self.config.energy_threshold
        noise_adaptation = 1 + (noise_level * 10)  # Scale with noise level
        snr_adaptation = max(0.5, 1 - (snr - 15) / 30)  # Adjust based on SNR
        
        new_energy_threshold = base_energy_threshold * env_factor * noise_adaptation * snr_adaptation
        
        # Smooth threshold changes to prevent oscillation
        adaptation_rate = self.config.adaptation_rate
        self.adaptive_thresholds['energy'] = (
            adaptation_rate * new_energy_threshold + 
            (1 - adaptation_rate) * self.adaptive_thresholds['energy']
        )
        
        # Adaptive spectral threshold
        spectral_centroid = spectral_features.get('spectral_centroid', 1000)
        if spectral_centroid > 3000:  # High spectral centroid suggests noise
            spectral_adaptation = 1.4
        elif spectral_centroid < 500:  # Very low suggests poor quality
            spectral_adaptation = 1.2
        else:
            spectral_adaptation = 1.0
        
        new_spectral_threshold = self.config.spectral_threshold * env_factor * spectral_adaptation
        self.adaptive_thresholds['spectral'] = (
            adaptation_rate * new_spectral_threshold +
            (1 - adaptation_rate) * self.adaptive_thresholds['spectral']
        )
        
        # Log significant adaptations
        if abs(new_energy_threshold - self.config.energy_threshold) > 0.005:
            logger.debug(f"🎯 Threshold adapted - Energy: {self.adaptive_thresholds['energy']:.4f}, "
                        f"Spectral: {self.adaptive_thresholds['spectral']:.3f}, Env: {self.noise_profile.environment.value}")
            self.statistics['adaptation_events'] += 1
    
    def _calculate_enhanced_speech_probability(self, energy: float, zero_crossings: int, 
                                             spectral_features: Dict[str, float], 
                                             band_features: Dict[str, float],
                                             noise_features: Dict[str, float]) -> float:
        """🎤 Calculate enhanced speech probability using multiple features."""
        if energy == 0.0:
            return 0.0
        
        probabilities = []
        
        # === ADAPTIVE ENERGY-BASED PROBABILITY ===
        adaptive_energy_threshold = self.adaptive_thresholds['energy']
        noise_level = self.noise_profile.average_noise_level
        
        # Use adaptive threshold instead of fixed noise floor
        energy_ratio = energy / (adaptive_energy_threshold + 1e-7)
        energy_prob = min(1.0, max(0.0, (energy_ratio - 1.0) / 5.0))  # More responsive
        probabilities.append(('energy', energy_prob, 0.25))
        
        # === ENHANCED ZERO CROSSING RATE ===
        # Adaptive ZCR threshold based on environment
        expected_zcr = {
            NoiseEnvironment.QUIET: 15,
            NoiseEnvironment.OFFICE: 12,
            NoiseEnvironment.CAFE: 10,
            NoiseEnvironment.STREET: 8,
            NoiseEnvironment.CONSTRUCTION: 6
        }.get(self.noise_profile.environment, 10)
        
        zcr_prob = 1.0 - abs(zero_crossings - expected_zcr) / 30.0
        zcr_prob = max(0.0, min(1.0, zcr_prob))
        probabilities.append(('zcr', zcr_prob, 0.15))
        
        # === SPECTRAL ANALYSIS ===
        spectral_centroid = spectral_features.get('spectral_centroid', 0.0)
        spectral_bandwidth = spectral_features.get('spectral_bandwidth', 0.0)
        spectral_flatness = spectral_features.get('spectral_flatness', 0.0)
        
        # Speech has characteristic spectral shape
        centroid_prob = 1.0 if 300 < spectral_centroid < 3400 else 0.3
        
        # Speech has moderate bandwidth (not too narrow, not too wide)
        bandwidth_prob = 1.0 if 800 < spectral_bandwidth < 2500 else 0.5
        
        # Speech is less flat (more structured) than noise
        flatness_prob = 1.0 - spectral_flatness  # Less flatness = more structured
        
        spectral_prob = (centroid_prob + bandwidth_prob + flatness_prob) / 3
        probabilities.append(('spectral', spectral_prob, 0.2))
        
        # === FORMANT AND HARMONIC FEATURES ===
        formant_activity = spectral_features.get('formant_activity', 0.0)
        harmonic_strength = spectral_features.get('harmonic_strength', 0.0)
        
        formant_prob = formant_activity  # Already normalized 0-1
        harmonic_prob = harmonic_strength  # Already normalized 0-1
        
        speech_structure_prob = (formant_prob + harmonic_prob) / 2
        probabilities.append(('speech_structure', speech_structure_prob, 0.15))
        
        # === MULTI-BAND ANALYSIS ===
        if band_features:
            f0_strength = band_features.get('f0_strength', 0.0)
            formant_1_strength = band_features.get('formant_1_strength', 0.0)
            formant_2_strength = band_features.get('formant_2_strength', 0.0)
            speech_balance = band_features.get('speech_balance', 1.0)
            
            # Good speech has balanced energy across bands
            balance_prob = min(1.0, speech_balance) if speech_balance > 0.3 else 0.2
            
            # F0 and formant presence
            fundamental_prob = (f0_strength + formant_1_strength + formant_2_strength) / 3
            
            multiband_prob = (balance_prob + fundamental_prob) / 2
            probabilities.append(('multiband', multiband_prob, 0.15))
        
        # === NOISE CONTEXT ADAPTATION ===
        snr = noise_features.get('estimated_snr', 0.0)
        noise_type = noise_features.get('noise_type', 'unknown')
        
        # Adjust based on SNR
        if snr > 15:  # Good SNR
            snr_factor = 1.0
        elif snr > 6:  # Acceptable SNR
            snr_factor = 0.8
        elif snr > 0:  # Poor SNR
            snr_factor = 0.6
        else:  # Very poor or unknown SNR
            snr_factor = 0.4
        
        # Noise type adaptation
        noise_factors = {
            'hiss': 0.9,        # High freq noise - moderate impact
            'rumble': 0.8,      # Low freq noise - more impact on speech
            'tonal': 0.7,       # Tonal interference - significant impact
            'broadband': 0.85,  # General noise - moderate impact
            'unknown': 0.8      # Default
        }
        noise_factor = noise_factors.get(noise_type, 0.8)
        
        # === COMBINE PROBABILITIES ===
        # Weighted average of all probability components
        weighted_sum = sum(prob * weight for _, prob, weight in probabilities)
        total_weight = sum(weight for _, _, weight in probabilities)
        
        base_probability = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Apply environmental adaptations
        adapted_probability = base_probability * snr_factor * noise_factor
        
        # Apply sensitivity adjustment with adaptive scaling
        sensitivity_factor = 1.0 + (self.config.sensitivity - 0.5) * 0.6  # Scale around 0.7-1.3
        final_probability = adapted_probability * sensitivity_factor
        
        return max(0.0, min(1.0, final_probability))
    
    def _apply_enhanced_temporal_logic(self, speech_probability: float, timestamp: float) -> bool:
        """🎤 Apply enhanced temporal smoothing and hysteresis."""
        # Adaptive threshold based on current environment
        env_thresholds = {
            NoiseEnvironment.QUIET: 0.4,
            NoiseEnvironment.OFFICE: 0.5,
            NoiseEnvironment.CAFE: 0.6,
            NoiseEnvironment.STREET: 0.7,
            NoiseEnvironment.CONSTRUCTION: 0.8,
            NoiseEnvironment.UNKNOWN: 0.5
        }
        
        base_threshold = env_thresholds.get(self.noise_profile.environment, 0.5)
        
        # Apply sensitivity adjustment
        threshold = base_threshold * (1.5 - self.config.sensitivity)
        
        # Hysteresis: different thresholds for switching on/off
        switch_on_threshold = threshold
        switch_off_threshold = threshold * 0.7  # Easier to stay in speech mode
        
        is_probable_speech = speech_probability > switch_on_threshold
        is_still_speech = speech_probability > switch_off_threshold
        
        # Enhanced state machine with transition states
        if self.current_state == 'silence':
            if is_probable_speech:
                if self.speech_start_time is None:
                    self.speech_start_time = timestamp
                    self.current_state = 'transition'  # Enter transition state
                    return False  # Don't report speech yet
                elif (timestamp - self.speech_start_time) * 1000 >= self.config.min_speech_duration:
                    self.current_state = 'speech'
                    self.speech_start_time = None
                    self.last_speech_time = timestamp
                    return True
            else:
                self.speech_start_time = None
                self.current_state = 'silence'
        
        elif self.current_state == 'transition':
            if is_probable_speech:
                if (timestamp - self.speech_start_time) * 1000 >= self.config.min_speech_duration:
                    self.current_state = 'speech'
                    self.speech_start_time = None
                    self.last_speech_time = timestamp
                    return True
            else:
                # Fell back to silence during transition
                self.current_state = 'silence'
                self.speech_start_time = None
        
        elif self.current_state == 'speech':
            if is_still_speech:  # Use lower threshold to stay in speech
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
    
    def _assess_audio_quality(self, audio_array: np.ndarray, spectral_features: Dict[str, float], 
                            noise_features: Dict[str, float]) -> float:
        """🎤 Assess overall audio quality for the current frame."""
        quality_factors = []
        
        # === SNR-based quality ===
        snr = noise_features.get('estimated_snr', 0.0)
        if snr > 20:  # Excellent
            snr_quality = 1.0
        elif snr > 15:  # Good
            snr_quality = 0.8
        elif snr > 10:  # Fair
            snr_quality = 0.6
        elif snr > 5:   # Poor
            snr_quality = 0.4
        else:           # Very poor
            snr_quality = 0.2
        
        quality_factors.append(('snr', snr_quality, 0.4))
        
        # === Spectral quality ===
        spectral_centroid = spectral_features.get('spectral_centroid', 0.0)
        spectral_bandwidth = spectral_features.get('spectral_bandwidth', 0.0)
        
        # Good audio has reasonable spectral characteristics
        if 500 <= spectral_centroid <= 2500:  # Good for speech
            centroid_quality = 1.0
        elif 300 <= spectral_centroid <= 3500:  # Acceptable
            centroid_quality = 0.7
        else:  # Poor
            centroid_quality = 0.3
        
        if 800 <= spectral_bandwidth <= 2000:  # Good bandwidth
            bandwidth_quality = 1.0
        elif 500 <= spectral_bandwidth <= 3000:  # Acceptable
            bandwidth_quality = 0.7
        else:  # Poor
            bandwidth_quality = 0.4
        
        spectral_quality = (centroid_quality + bandwidth_quality) / 2
        quality_factors.append(('spectral', spectral_quality, 0.3))
        
        # === Dynamic range quality ===
        peak_amplitude = np.max(np.abs(audio_array))
        rms_amplitude = np.sqrt(np.mean(audio_array ** 2))
        
        if peak_amplitude > 0 and rms_amplitude > 0:
            dynamic_range = peak_amplitude / rms_amplitude
            if 2.0 <= dynamic_range <= 10.0:  # Good range
                range_quality = 1.0
            elif 1.5 <= dynamic_range <= 15.0:  # Acceptable
                range_quality = 0.7
            else:  # Poor (too compressed or too dynamic)
                range_quality = 0.4
        else:
            range_quality = 0.0
        
        quality_factors.append(('dynamic_range', range_quality, 0.2))
        
        # === Clipping detection ===
        clipping_ratio = np.sum(np.abs(audio_array) > 0.95) / len(audio_array)
        if clipping_ratio < 0.001:  # No clipping
            clipping_quality = 1.0
        elif clipping_ratio < 0.01:  # Minimal clipping
            clipping_quality = 0.8
        elif clipping_ratio < 0.05:  # Some clipping
            clipping_quality = 0.5
        else:  # Heavy clipping
            clipping_quality = 0.2
        
        quality_factors.append(('clipping', clipping_quality, 0.1))
        
        # === COMBINE QUALITY SCORES ===
        weighted_sum = sum(score * weight for _, score, weight in quality_factors)
        total_weight = sum(weight for _, _, weight in quality_factors)
        
        overall_quality = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Store quality measurements
        self.statistics['quality_scores'].append(overall_quality)
        
        return overall_quality
    
    def _update_enhanced_statistics(self, is_speech: bool, speech_probability: float, quality_score: float):
        """🎤 Update comprehensive processing statistics."""
        self.statistics['total_frames'] += 1
        
        if is_speech:
            self.statistics['speech_frames'] += 1
        
        # Track speech probability distribution
        if not hasattr(self, '_probability_histogram'):
            self._probability_histogram = {'high': 0, 'medium': 0, 'low': 0}
        
        if speech_probability > 0.7:
            self._probability_histogram['high'] += 1
        elif speech_probability > 0.3:
            self._probability_histogram['medium'] += 1
        else:
            self._probability_histogram['low'] += 1
        
        # Detection accuracy estimation (simplified)
        if hasattr(self, '_last_detection_confidence'):
            confidence_change = abs(speech_probability - self._last_detection_confidence)
            if confidence_change > 0.3:  # Significant change might indicate instability
                self.statistics['false_positives'] += 0.1  # Fractional increment
        
        self._last_detection_confidence = speech_probability
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """🎤 Get comprehensive VAD processing statistics."""
        base_stats = self.get_statistics()
        
        # Add enhanced statistics
        enhanced_stats = {
            **base_stats,
            'adaptive_mode': self.config.adaptive_mode,
            'current_environment': self.noise_profile.environment.value,
            'environment_confidence': self.noise_profile.confidence,
            'adaptive_thresholds': self.adaptive_thresholds.copy(),
            'average_noise_level': self.noise_profile.average_noise_level,
            'environment_switches': self.statistics['environment_switches'],
            'adaptation_events': self.statistics['adaptation_events']
        }
        
        # Quality statistics
        if self.statistics['quality_scores']:
            quality_scores = list(self.statistics['quality_scores'])
            enhanced_stats['average_quality'] = np.mean(quality_scores)
            enhanced_stats['min_quality'] = np.min(quality_scores)
            enhanced_stats['max_quality'] = np.max(quality_scores)
        
        # SNR statistics
        if self.statistics['snr_measurements']:
            snr_values = list(self.statistics['snr_measurements'])
            enhanced_stats['average_snr'] = np.mean(snr_values)
            enhanced_stats['snr_trend'] = 'improving' if len(snr_values) > 10 and snr_values[-5:] > snr_values[:5] else 'stable'
        
        # Speech detection distribution
        if hasattr(self, '_probability_histogram'):
            total_frames = sum(self._probability_histogram.values())
            if total_frames > 0:
                enhanced_stats['detection_distribution'] = {
                    'high_confidence': self._probability_histogram['high'] / total_frames,
                    'medium_confidence': self._probability_histogram['medium'] / total_frames,
                    'low_confidence': self._probability_histogram['low'] / total_frames
                }
        
        return enhanced_stats
    
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
        """Get basic VAD processing statistics."""
        total_frames = self.statistics['total_frames']
        speech_frames = self.statistics['speech_frames']
        speech_ratio = speech_frames / max(1, total_frames)
        
        return {
            'total_frames': total_frames,
            'speech_frames': speech_frames,
            'speech_ratio': speech_ratio,
            'current_state': self.current_state,
            'noise_floor': self.noise_profile.average_noise_level,
            'false_positives': self.statistics['false_positives'],
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
