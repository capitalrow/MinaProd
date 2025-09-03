"""
Enhanced VAD Service - Google Recorder Level Voice Activity Detection
Advanced voice activity detection with environmental adaptation and multi-level analysis.
Optimized for real-time transcription accuracy and noise robustness.
"""

import logging
import numpy as np
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
import time
from collections import deque
import webrtcvad
from scipy import signal
from scipy.stats import entropy

logger = logging.getLogger(__name__)

@dataclass
class VADResult:
    """Enhanced VAD result with detailed analysis."""
    is_speech: bool
    confidence: float
    energy_level: float
    spectral_features: Dict[str, float]
    noise_level: float
    quality_score: float
    timestamp: float
    frame_duration: float

@dataclass
class EnvironmentalProfile:
    """Environmental audio profile for adaptive VAD."""
    noise_floor: float
    speech_threshold: float
    adaptation_rate: float
    ambient_characteristics: Dict[str, float]
    last_update: float

class EnhancedVADService:
    """
    🎤 Google Recorder-level Voice Activity Detection.
    
    Implements advanced VAD with environmental adaptation, multi-algorithm fusion,
    and intelligent noise robustness for optimal transcription triggering.
    """
    
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 2):
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        
        # Core VAD engines
        self.webrtc_vad = webrtcvad.Vad(aggressiveness)
        
        # Environmental adaptation
        self.environmental_profile = EnvironmentalProfile(
            noise_floor=0.01,
            speech_threshold=0.05,
            adaptation_rate=0.1,
            ambient_characteristics={},
            last_update=time.time()
        )
        
        # Performance tracking
        self.vad_history = deque(maxlen=100)
        self.energy_history = deque(maxlen=50)
        self.spectral_history = deque(maxlen=30)
        
        # Analysis windows
        self.analysis_window_ms = 30  # 30ms analysis window
        self.samples_per_window = int(sample_rate * self.analysis_window_ms / 1000)
        
        # Feature extractors
        self._init_feature_extractors()
        
        logger.info(f"🎤 Enhanced VAD Service initialized (SR: {sample_rate}, Aggressiveness: {aggressiveness})")
    
    def _init_feature_extractors(self):
        """Initialize advanced feature extraction components."""
        # Frequency bands for analysis
        self.frequency_bands = {
            'low': (80, 300),      # Fundamental frequency range
            'mid_low': (300, 1000), # First formant region
            'mid_high': (1000, 2500), # Second formant region
            'high': (2500, 4000),   # Consonant clarity
            'very_high': (4000, 8000) # Fricatives and sibilants
        }
        
        # Pre-computed filter banks
        self.filter_bank = self._create_mel_filter_bank()
        
        # Spectral analysis parameters
        self.fft_size = 512
        self.hop_length = 160  # 10ms hop at 16kHz
        
    def _create_mel_filter_bank(self, n_filters: int = 13) -> np.ndarray:
        """Create mel-scale filter bank for spectral analysis."""
        try:
            # Mel scale boundaries
            low_freq_mel = 0
            high_freq_mel = 2595 * np.log10(1 + (self.sample_rate / 2) / 700)
            
            # Equal spaced in mel scale
            mel_points = np.linspace(low_freq_mel, high_freq_mel, n_filters + 2)
            hz_points = 700 * (10**(mel_points / 2595) - 1)
            
            # Convert to FFT bin numbers
            bin_points = np.floor((self.fft_size + 1) * hz_points / self.sample_rate)
            
            # Create filter bank
            filter_bank = np.zeros((n_filters, int(np.floor(self.fft_size / 2 + 1))))
            
            for i in range(1, n_filters + 1):
                left = int(bin_points[i - 1])
                center = int(bin_points[i])
                right = int(bin_points[i + 1])
                
                for j in range(left, center):
                    filter_bank[i - 1, j] = (j - left) / (center - left)
                for j in range(center, right):
                    filter_bank[i - 1, j] = (right - j) / (right - center)
            
            return filter_bank
            
        except Exception as e:
            logger.warning(f"⚠️ Filter bank creation failed: {e}")
            return np.ones((13, 257))  # Fallback uniform filters
    
    def analyze_voice_activity(self, audio_data: bytes, timestamp: Optional[float] = None) -> VADResult:
        """
        🔍 Analyze voice activity with Google Recorder-level accuracy.
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM)
            timestamp: Optional timestamp for the audio frame
            
        Returns:
            Comprehensive VAD analysis result
        """
        if timestamp is None:
            timestamp = time.time()
        
        try:
            # Convert audio to numpy array
            audio_array = self._convert_audio_to_array(audio_data)
            
            if len(audio_array) < self.samples_per_window:
                return self._create_silence_result(timestamp)
            
            # === MULTI-ALGORITHM VAD ANALYSIS ===
            
            # 1. WebRTC VAD (baseline)
            webrtc_result = self._webrtc_vad_analysis(audio_data)
            
            # 2. Energy-based VAD
            energy_result = self._energy_based_vad(audio_array)
            
            # 3. Spectral VAD
            spectral_result = self._spectral_vad_analysis(audio_array)
            
            # 4. Advanced feature-based VAD
            feature_result = self._feature_based_vad(audio_array)
            
            # === FUSION AND DECISION ===
            
            # Combine results with adaptive weighting
            final_result = self._fuse_vad_results(
                webrtc_result, energy_result, spectral_result, feature_result
            )
            
            # Apply environmental adaptation
            adapted_result = self._apply_environmental_adaptation(final_result, audio_array)
            
            # Update environmental profile
            self._update_environmental_profile(audio_array, adapted_result)
            
            # Track performance
            self.vad_history.append(adapted_result)
            
            frame_duration = len(audio_array) / self.sample_rate
            
            return VADResult(
                is_speech=adapted_result['is_speech'],
                confidence=adapted_result['confidence'],
                energy_level=adapted_result['energy_level'],
                spectral_features=adapted_result['spectral_features'],
                noise_level=adapted_result['noise_level'],
                quality_score=adapted_result['quality_score'],
                timestamp=timestamp,
                frame_duration=frame_duration
            )
            
        except Exception as e:
            logger.error(f"❌ VAD analysis failed: {e}")
            return self._create_error_result(timestamp)
    
    def _webrtc_vad_analysis(self, audio_data: bytes) -> Dict[str, Any]:
        """🌐 WebRTC VAD baseline analysis."""
        try:
            # WebRTC VAD requires specific frame sizes (10, 20, or 30ms)
            frame_length = len(audio_data)
            
            # Check if frame length is compatible
            valid_lengths = [320, 640, 960]  # 10ms, 20ms, 30ms at 16kHz
            
            if frame_length in valid_lengths:
                is_speech = self.webrtc_vad.is_speech(audio_data, self.sample_rate)
                confidence = 0.8 if is_speech else 0.2
            else:
                # Resample to compatible length
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                target_length = min(valid_lengths, key=lambda x: abs(x - frame_length))
                
                if len(audio_array) > target_length:
                    resampled = audio_array[:target_length]
                else:
                    resampled = np.pad(audio_array, (0, target_length - len(audio_array)))
                
                resampled_bytes = resampled.astype(np.int16).tobytes()
                is_speech = self.webrtc_vad.is_speech(resampled_bytes, self.sample_rate)
                confidence = 0.6 if is_speech else 0.3  # Lower confidence for resampled
            
            return {
                'is_speech': is_speech,
                'confidence': confidence,
                'method': 'webrtc'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ WebRTC VAD failed: {e}")
            return {
                'is_speech': False,
                'confidence': 0.0,
                'method': 'webrtc_error'
            }
    
    def _energy_based_vad(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """⚡ Energy-based voice activity detection."""
        try:
            # Calculate RMS energy
            rms_energy = np.sqrt(np.mean(audio_array ** 2))
            
            # Adaptive threshold based on environmental profile
            base_threshold = self.environmental_profile.speech_threshold
            adaptive_threshold = base_threshold * (1 + self.environmental_profile.noise_floor)
            
            # Zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
            zcr = zero_crossings / len(audio_array)
            
            # Speech typically has moderate ZCR and sufficient energy
            energy_score = min(1.0, rms_energy / adaptive_threshold)
            zcr_score = 1.0 - abs(zcr - 0.05) / 0.1  # Optimal around 0.05
            zcr_score = max(0.0, zcr_score)
            
            # Combined energy-based decision
            combined_score = 0.7 * energy_score + 0.3 * zcr_score
            is_speech = combined_score > 0.5
            
            return {
                'is_speech': is_speech,
                'confidence': combined_score,
                'energy_level': rms_energy,
                'zcr': zcr,
                'method': 'energy'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Energy VAD failed: {e}")
            return {
                'is_speech': False,
                'confidence': 0.0,
                'energy_level': 0.0,
                'zcr': 0.0,
                'method': 'energy_error'
            }
    
    def _spectral_vad_analysis(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """🌈 Spectral-based voice activity detection."""
        try:
            # Compute power spectral density
            freqs, psd = signal.welch(audio_array, self.sample_rate, nperseg=min(256, len(audio_array)))
            
            # Speech frequency band analysis
            speech_band_energy = {}
            total_energy = np.sum(psd)
            
            for band_name, (low_freq, high_freq) in self.frequency_bands.items():
                band_mask = (freqs >= low_freq) & (freqs <= high_freq)
                band_energy = np.sum(psd[band_mask])
                speech_band_energy[band_name] = band_energy / (total_energy + 1e-10)
            
            # Speech characteristic indicators
            formant_energy = speech_band_energy['mid_low'] + speech_band_energy['mid_high']
            consonant_energy = speech_band_energy['high']
            fundamental_energy = speech_band_energy['low']
            
            # Spectral centroid
            spectral_centroid = np.sum(freqs * psd) / (np.sum(psd) + 1e-10)
            
            # Spectral rolloff (frequency below which 85% of energy is contained)
            cumulative_energy = np.cumsum(psd)
            rolloff_threshold = 0.85 * cumulative_energy[-1]
            rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
            spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else freqs[-1]
            
            # Speech likelihood based on spectral features
            speech_indicators = {
                'formant_prominence': min(1.0, formant_energy * 3),
                'spectral_balance': 1.0 - abs(0.5 - (consonant_energy / (formant_energy + 1e-10))),
                'fundamental_presence': min(1.0, fundamental_energy * 5),
                'centroid_position': 1.0 - abs(spectral_centroid - 1000) / 2000,
                'rolloff_position': 1.0 - abs(spectral_rolloff - 2000) / 3000
            }
            
            # Combined spectral score
            spectral_score = np.mean(list(speech_indicators.values()))
            is_speech = spectral_score > 0.4
            
            return {
                'is_speech': is_speech,
                'confidence': spectral_score,
                'spectral_features': speech_indicators,
                'spectral_centroid': spectral_centroid,
                'spectral_rolloff': spectral_rolloff,
                'band_energies': speech_band_energy,
                'method': 'spectral'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Spectral VAD failed: {e}")
            return {
                'is_speech': False,
                'confidence': 0.0,
                'spectral_features': {},
                'method': 'spectral_error'
            }
    
    def _feature_based_vad(self, audio_array: np.ndarray) -> Dict[str, Any]:
        """🔬 Advanced feature-based VAD using MFCC and other features."""
        try:
            # Mel-frequency cepstral coefficients (MFCC)
            mfcc_features = self._extract_mfcc_features(audio_array)
            
            # Spectral features
            spectral_features = self._extract_spectral_features(audio_array)
            
            # Temporal features
            temporal_features = self._extract_temporal_features(audio_array)
            
            # Combine all features for classification
            feature_vector = np.concatenate([
                mfcc_features,
                list(spectral_features.values()),
                list(temporal_features.values())
            ])
            
            # Simple decision tree based on feature analysis
            speech_probability = self._classify_speech_features(feature_vector)
            
            is_speech = speech_probability > 0.5
            
            return {
                'is_speech': is_speech,
                'confidence': speech_probability,
                'mfcc_features': mfcc_features,
                'spectral_features': spectral_features,
                'temporal_features': temporal_features,
                'method': 'feature_based'
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Feature-based VAD failed: {e}")
            return {
                'is_speech': False,
                'confidence': 0.0,
                'method': 'feature_error'
            }
    
    def _extract_mfcc_features(self, audio_array: np.ndarray, n_mfcc: int = 8) -> np.ndarray:
        """Extract MFCC features."""
        try:
            # Compute FFT
            fft = np.fft.rfft(audio_array * np.hanning(len(audio_array)))
            magnitude = np.abs(fft)
            
            # Apply mel filter bank
            mel_energies = np.dot(self.filter_bank, magnitude)
            
            # Log mel energies
            log_mel_energies = np.log(mel_energies + 1e-10)
            
            # DCT to get MFCC
            mfcc = np.zeros(n_mfcc)
            N = len(log_mel_energies)
            
            for i in range(n_mfcc):
                for j in range(N):
                    mfcc[i] += log_mel_energies[j] * np.cos(np.pi * i * (j + 0.5) / N)
            
            return mfcc
            
        except Exception:
            return np.zeros(8)
    
    def _extract_spectral_features(self, audio_array: np.ndarray) -> Dict[str, float]:
        """Extract additional spectral features."""
        try:
            # FFT
            fft = np.fft.rfft(audio_array)
            magnitude = np.abs(fft)
            freqs = np.fft.rfftfreq(len(audio_array), 1/self.sample_rate)
            
            # Spectral centroid
            centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-10)
            
            # Spectral bandwidth
            bandwidth = np.sqrt(np.sum(((freqs - centroid) ** 2) * magnitude) / (np.sum(magnitude) + 1e-10))
            
            # Spectral flatness
            geometric_mean = np.exp(np.mean(np.log(magnitude + 1e-10)))
            arithmetic_mean = np.mean(magnitude)
            flatness = geometric_mean / (arithmetic_mean + 1e-10)
            
            # Spectral entropy
            normalized_magnitude = magnitude / (np.sum(magnitude) + 1e-10)
            spectral_entropy = entropy(normalized_magnitude + 1e-10)
            
            return {
                'centroid': centroid,
                'bandwidth': bandwidth,
                'flatness': flatness,
                'entropy': spectral_entropy
            }
            
        except Exception:
            return {'centroid': 0, 'bandwidth': 0, 'flatness': 0, 'entropy': 0}
    
    def _extract_temporal_features(self, audio_array: np.ndarray) -> Dict[str, float]:
        """Extract temporal domain features."""
        try:
            # RMS energy
            rms = np.sqrt(np.mean(audio_array ** 2))
            
            # Peak energy
            peak = np.max(np.abs(audio_array))
            
            # Dynamic range
            dynamic_range = peak / (rms + 1e-10)
            
            # Autocorrelation features
            autocorr = np.correlate(audio_array, audio_array, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            autocorr = autocorr / autocorr[0] if autocorr[0] != 0 else autocorr
            
            # Pitch estimation from autocorrelation
            min_period = int(self.sample_rate / 500)  # 500 Hz max
            max_period = int(self.sample_rate / 50)   # 50 Hz min
            
            if max_period < len(autocorr):
                pitch_candidates = autocorr[min_period:max_period]
                pitch_strength = np.max(pitch_candidates) if len(pitch_candidates) > 0 else 0
            else:
                pitch_strength = 0
            
            return {
                'rms_energy': rms,
                'peak_energy': peak,
                'dynamic_range': dynamic_range,
                'pitch_strength': pitch_strength
            }
            
        except Exception:
            return {'rms_energy': 0, 'peak_energy': 0, 'dynamic_range': 1, 'pitch_strength': 0}
    
    def _classify_speech_features(self, feature_vector: np.ndarray) -> float:
        """Simple feature-based speech classification."""
        try:
            # Normalize features
            normalized_features = feature_vector / (np.linalg.norm(feature_vector) + 1e-10)
            
            # Simple decision rules based on typical speech characteristics
            speech_indicators = []
            
            # MFCC-based indicators
            if len(normalized_features) >= 8:
                mfcc_energy = np.sum(normalized_features[:8] ** 2)
                speech_indicators.append(min(1.0, mfcc_energy * 2))
            
            # Energy-based indicators
            if len(normalized_features) >= 12:
                energy_features = normalized_features[8:12]
                energy_score = np.mean(energy_features)
                speech_indicators.append(min(1.0, max(0.0, energy_score)))
            
            # Overall feature consistency
            feature_variance = np.var(normalized_features)
            consistency_score = 1.0 - min(1.0, feature_variance * 10)
            speech_indicators.append(consistency_score)
            
            # Combine indicators
            speech_probability = np.mean(speech_indicators) if speech_indicators else 0.0
            
            return float(speech_probability)
            
        except Exception:
            return 0.0
    
    def _fuse_vad_results(self, webrtc_result: Dict, energy_result: Dict, 
                         spectral_result: Dict, feature_result: Dict) -> Dict[str, Any]:
        """🔗 Fuse multiple VAD results with adaptive weighting."""
        try:
            # Extract individual decisions and confidences
            decisions = [
                webrtc_result.get('is_speech', False),
                energy_result.get('is_speech', False),
                spectral_result.get('is_speech', False),
                feature_result.get('is_speech', False)
            ]
            
            confidences = [
                webrtc_result.get('confidence', 0.0),
                energy_result.get('confidence', 0.0),
                spectral_result.get('confidence', 0.0),
                feature_result.get('confidence', 0.0)
            ]
            
            # Adaptive weighting based on environmental conditions
            weights = self._calculate_adaptive_weights()
            
            # Weighted confidence fusion
            weighted_confidence = sum(w * c for w, c in zip(weights, confidences))
            
            # Majority voting with confidence weighting
            weighted_votes = sum(w * d for w, d in zip(weights, decisions))
            final_decision = weighted_votes > 0.5
            
            # Combine spectral features
            combined_spectral = spectral_result.get('spectral_features', {})
            
            return {
                'is_speech': final_decision,
                'confidence': weighted_confidence,
                'energy_level': energy_result.get('energy_level', 0.0),
                'spectral_features': combined_spectral,
                'individual_results': {
                    'webrtc': webrtc_result,
                    'energy': energy_result,
                    'spectral': spectral_result,
                    'feature': feature_result
                },
                'fusion_weights': weights
            }
            
        except Exception as e:
            logger.warning(f"⚠️ VAD fusion failed: {e}")
            return {
                'is_speech': False,
                'confidence': 0.0,
                'energy_level': 0.0,
                'spectral_features': {},
                'individual_results': {},
                'fusion_weights': [0.25, 0.25, 0.25, 0.25]
            }
    
    def _calculate_adaptive_weights(self) -> List[float]:
        """🎯 Calculate adaptive weights based on environmental conditions."""
        try:
            # Base weights
            base_weights = [0.3, 0.25, 0.25, 0.2]  # WebRTC, Energy, Spectral, Feature
            
            # Adjust based on noise level
            noise_level = self.environmental_profile.noise_floor
            
            if noise_level > 0.1:  # High noise environment
                # Favor spectral and feature-based methods
                adjusted_weights = [0.2, 0.2, 0.35, 0.25]
            elif noise_level < 0.01:  # Very quiet environment
                # Favor energy-based methods
                adjusted_weights = [0.3, 0.35, 0.2, 0.15]
            else:
                adjusted_weights = base_weights
            
            return adjusted_weights
            
        except Exception:
            return [0.25, 0.25, 0.25, 0.25]
    
    def _apply_environmental_adaptation(self, result: Dict[str, Any], 
                                      audio_array: np.ndarray) -> Dict[str, Any]:
        """🌍 Apply environmental adaptation to VAD result."""
        try:
            # Calculate current noise level
            current_noise = self._estimate_noise_level(audio_array)
            
            # Adaptive threshold adjustment
            base_confidence = result['confidence']
            noise_adaptation = 1.0 - min(0.5, current_noise * 5)  # Reduce confidence in noisy conditions
            
            adapted_confidence = base_confidence * noise_adaptation
            
            # Quality score based on various factors
            quality_factors = {
                'noise_level': 1.0 - min(1.0, current_noise * 10),
                'energy_consistency': self._calculate_energy_consistency(audio_array),
                'spectral_quality': self._calculate_spectral_quality_score(result.get('spectral_features', {}))
            }
            
            quality_score = np.mean(list(quality_factors.values()))
            
            # Update result
            result['confidence'] = adapted_confidence
            result['noise_level'] = current_noise
            result['quality_score'] = quality_score
            result['quality_factors'] = quality_factors
            
            return result
            
        except Exception as e:
            logger.warning(f"⚠️ Environmental adaptation failed: {e}")
            result['noise_level'] = 0.0
            result['quality_score'] = 0.5
            return result
    
    def _estimate_noise_level(self, audio_array: np.ndarray) -> float:
        """📊 Estimate current noise level."""
        try:
            # Use lower percentile as noise floor estimate
            sorted_abs = np.sort(np.abs(audio_array))
            noise_level = np.mean(sorted_abs[:len(sorted_abs)//4])  # Bottom 25%
            return float(noise_level)
        except Exception:
            return 0.0
    
    def _calculate_energy_consistency(self, audio_array: np.ndarray) -> float:
        """⚡ Calculate energy consistency score."""
        try:
            # Split into overlapping windows
            window_size = len(audio_array) // 4
            if window_size < 10:
                return 0.5
            
            energies = []
            for i in range(0, len(audio_array) - window_size, window_size // 2):
                window = audio_array[i:i + window_size]
                energy = np.sqrt(np.mean(window ** 2))
                energies.append(energy)
            
            if len(energies) < 2:
                return 0.5
            
            # Calculate consistency (inverse of coefficient of variation)
            mean_energy = np.mean(energies)
            std_energy = np.std(energies)
            
            if mean_energy > 0:
                cv = std_energy / mean_energy
                consistency = 1.0 / (1.0 + cv)  # Higher consistency = lower variation
            else:
                consistency = 0.0
            
            return float(consistency)
            
        except Exception:
            return 0.5
    
    def _calculate_spectral_quality_score(self, spectral_features: Dict[str, float]) -> float:
        """🌈 Calculate spectral quality score."""
        try:
            if not spectral_features:
                return 0.5
            
            scores = []
            
            # Formant prominence indicates speech
            if 'formant_prominence' in spectral_features:
                scores.append(spectral_features['formant_prominence'])
            
            # Spectral balance
            if 'spectral_balance' in spectral_features:
                scores.append(spectral_features['spectral_balance'])
            
            # Overall spectral quality
            quality_score = np.mean(scores) if scores else 0.5
            
            return float(quality_score)
            
        except Exception:
            return 0.5
    
    def _update_environmental_profile(self, audio_array: np.ndarray, vad_result: Dict[str, Any]):
        """🌍 Update environmental profile based on current analysis."""
        try:
            current_time = time.time()
            time_since_update = current_time - self.environmental_profile.last_update
            
            if time_since_update > 1.0:  # Update every second
                # Update noise floor
                current_noise = vad_result.get('noise_level', 0.0)
                alpha = self.environmental_profile.adaptation_rate
                
                self.environmental_profile.noise_floor = (
                    alpha * current_noise + 
                    (1 - alpha) * self.environmental_profile.noise_floor
                )
                
                # Update speech threshold
                if vad_result.get('is_speech', False):
                    current_energy = vad_result.get('energy_level', 0.0)
                    self.environmental_profile.speech_threshold = (
                        alpha * current_energy + 
                        (1 - alpha) * self.environmental_profile.speech_threshold
                    )
                
                self.environmental_profile.last_update = current_time
                
        except Exception as e:
            logger.warning(f"⚠️ Environmental profile update failed: {e}")
    
    def _convert_audio_to_array(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array."""
        try:
            return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            return np.array([])
    
    def _create_silence_result(self, timestamp: float) -> VADResult:
        """Create result for silence/insufficient audio."""
        return VADResult(
            is_speech=False,
            confidence=0.0,
            energy_level=0.0,
            spectral_features={},
            noise_level=0.0,
            quality_score=0.0,
            timestamp=timestamp,
            frame_duration=0.0
        )
    
    def _create_error_result(self, timestamp: float) -> VADResult:
        """Create result for error cases."""
        return VADResult(
            is_speech=False,
            confidence=0.0,
            energy_level=0.0,
            spectral_features={},
            noise_level=0.0,
            quality_score=0.0,
            timestamp=timestamp,
            frame_duration=0.0
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """📊 Get VAD performance statistics."""
        try:
            if not self.vad_history:
                return {'status': 'no_data'}
            
            recent_results = list(self.vad_history)
            
            speech_ratio = np.mean([r.is_speech for r in recent_results])
            avg_confidence = np.mean([r.confidence for r in recent_results])
            avg_quality = np.mean([r.quality_score for r in recent_results])
            avg_noise_level = np.mean([r.noise_level for r in recent_results])
            
            return {
                'speech_ratio': speech_ratio,
                'avg_confidence': avg_confidence,
                'avg_quality_score': avg_quality,
                'avg_noise_level': avg_noise_level,
                'environmental_noise_floor': self.environmental_profile.noise_floor,
                'speech_threshold': self.environmental_profile.speech_threshold,
                'total_frames_analyzed': len(recent_results)
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Performance stats calculation failed: {e}")
            return {'status': 'error', 'error': str(e)}