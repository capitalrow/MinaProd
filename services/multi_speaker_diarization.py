# services/multi_speaker_diarization.py
"""
ADVANCED MULTI-SPEAKER DIARIZATION SYSTEM
Comprehensive speaker identification, tracking, and voice characteristic analysis
for enhanced transcription processing with speaker attribution.
"""

import logging
import numpy as np
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from scipy import signal
from scipy.spatial.distance import cosine
from sklearn.cluster import DBSCAN
import uuid

logger = logging.getLogger(__name__)

@dataclass
class SpeakerProfile:
    """Comprehensive speaker profile with voice characteristics"""
    speaker_id: str
    voice_features: np.ndarray
    pitch_range: Tuple[float, float]
    formant_characteristics: Dict[str, float]
    speaking_rate: float
    energy_profile: float
    spectral_signature: np.ndarray
    confidence_score: float = 0.0
    first_seen: float = 0.0
    last_seen: float = 0.0
    total_speech_time: float = 0.0
    segment_count: int = 0
    
    def update_profile(self, new_features: np.ndarray, timestamp: float):
        """Update speaker profile with new voice features"""
        try:
            # Weighted average for continuous learning
            alpha = 0.2  # Learning rate
            self.voice_features = (1 - alpha) * self.voice_features + alpha * new_features
            
            self.last_seen = timestamp
            self.segment_count += 1
            
            # Update confidence based on consistency
            feature_similarity = 1 - cosine(self.voice_features, new_features)
            self.confidence_score = 0.9 * self.confidence_score + 0.1 * feature_similarity
            
        except Exception as e:
            logger.warning(f"⚠️ Speaker profile update failed: {e}")

@dataclass
class SpeakerSegment:
    """Enhanced speaker segment with detailed attribution"""
    segment_id: str
    speaker_id: str
    start_time: float
    end_time: float
    audio_data: bytes
    transcript: str = ""
    confidence: float = 0.0
    voice_features: Optional[np.ndarray] = None
    speaker_confidence: float = 0.0
    overlap_detected: bool = False
    background_speakers: List[str] = field(default_factory=list)

class AdvancedVoiceFeatureExtractor:
    """Advanced voice feature extraction for speaker identification"""
    
    def __init__(self):
        self.sample_rate = 16000
        self.frame_length = 1024
        self.hop_length = 512
        
        # Feature extraction parameters
        self.mfcc_coeffs = 13
        self.pitch_min = 50
        self.pitch_max = 500
        
        logger.info("🎤 Advanced Voice Feature Extractor initialized")
    
    def extract_comprehensive_features(self, audio_samples: np.ndarray) -> np.ndarray:
        """Extract comprehensive voice features for speaker identification"""
        try:
            if len(audio_samples) == 0:
                return np.zeros(39)  # Return zero vector for empty audio
            
            features = []
            
            # 1. MFCC Features (13 coefficients)
            mfcc_features = self._extract_mfcc_features(audio_samples)
            features.extend(mfcc_features)
            
            # 2. Pitch-related features (5 features)
            pitch_features = self._extract_pitch_features(audio_samples)
            features.extend(pitch_features)
            
            # 3. Formant features (6 features)
            formant_features = self._extract_formant_features(audio_samples)
            features.extend(formant_features)
            
            # 4. Spectral features (8 features)
            spectral_features = self._extract_spectral_features(audio_samples)
            features.extend(spectral_features)
            
            # 5. Prosodic features (7 features)
            prosodic_features = self._extract_prosodic_features(audio_samples)
            features.extend(prosodic_features)
            
            # Ensure consistent feature vector length
            feature_vector = np.array(features)
            if len(feature_vector) != 39:
                # Pad or truncate to ensure consistent length
                if len(feature_vector) < 39:
                    feature_vector = np.pad(feature_vector, (0, 39 - len(feature_vector)))
                else:
                    feature_vector = feature_vector[:39]
            
            # Normalize features
            feature_vector = self._normalize_features(feature_vector)
            
            return feature_vector
            
        except Exception as e:
            logger.warning(f"⚠️ Feature extraction failed: {e}")
            return np.zeros(39)
    
    def _extract_mfcc_features(self, audio_samples: np.ndarray) -> List[float]:
        """Extract MFCC features"""
        try:
            # Simple MFCC approximation using spectral analysis
            # Compute power spectrum
            freqs, psd = signal.welch(audio_samples, self.sample_rate, nperseg=512)
            
            # Mel-scale approximation
            mel_features = []
            mel_bands = np.logspace(np.log10(300), np.log10(8000), self.mfcc_coeffs)
            
            for i, mel_freq in enumerate(mel_bands):
                # Find closest frequency bin
                freq_idx = np.argmin(np.abs(freqs - mel_freq))
                if freq_idx < len(psd):
                    mel_features.append(float(np.log(psd[freq_idx] + 1e-10)))
                else:
                    mel_features.append(0.0)
            
            return mel_features
            
        except Exception:
            return [0.0] * self.mfcc_coeffs
    
    def _extract_pitch_features(self, audio_samples: np.ndarray) -> List[float]:
        """Extract pitch-related features"""
        try:
            # Autocorrelation-based pitch detection
            pitch_values = []
            frame_size = 1024
            
            for i in range(0, len(audio_samples) - frame_size, frame_size // 2):
                frame = audio_samples[i:i + frame_size]
                pitch = self._estimate_frame_pitch(frame)
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                mean_pitch = np.mean(pitch_values)
                pitch_std = np.std(pitch_values)
                min_pitch = np.min(pitch_values)
                max_pitch = np.max(pitch_values)
                pitch_range = max_pitch - min_pitch
            else:
                mean_pitch = pitch_std = min_pitch = max_pitch = pitch_range = 0.0
            
            return [
                float(mean_pitch),
                float(pitch_std),
                float(min_pitch),
                float(max_pitch),
                float(pitch_range)
            ]
            
        except Exception:
            return [0.0] * 5
    
    def _estimate_frame_pitch(self, frame: np.ndarray) -> float:
        """Estimate pitch for a single frame"""
        try:
            # Autocorrelation method
            autocorr = np.correlate(frame, frame, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Normalize
            if autocorr[0] > 0:
                autocorr = autocorr / autocorr[0]
            
            # Find peak in pitch range
            min_period = int(self.sample_rate / self.pitch_max)
            max_period = int(self.sample_rate / self.pitch_min)
            
            if max_period < len(autocorr):
                search_range = autocorr[min_period:max_period]
                if len(search_range) > 0:
                    peak_idx = np.argmax(search_range) + min_period
                    if autocorr[peak_idx] > 0.3:  # Threshold for pitch detection
                        return self.sample_rate / peak_idx
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _extract_formant_features(self, audio_samples: np.ndarray) -> List[float]:
        """Extract formant-related features"""
        try:
            # Simplified formant estimation using spectral peaks
            freqs, psd = signal.welch(audio_samples, self.sample_rate, nperseg=1024)
            
            # Find peaks in formant regions
            f1_region = (freqs >= 200) & (freqs <= 1200)  # F1 region
            f2_region = (freqs >= 800) & (freqs <= 3000)  # F2 region
            f3_region = (freqs >= 1500) & (freqs <= 4000) # F3 region
            
            f1_peak = 0.0
            f2_peak = 0.0
            f3_peak = 0.0
            
            if np.any(f1_region):
                f1_peak_idx = np.argmax(psd[f1_region])
                f1_peak = freqs[f1_region][f1_peak_idx]
            
            if np.any(f2_region):
                f2_peak_idx = np.argmax(psd[f2_region])
                f2_peak = freqs[f2_region][f2_peak_idx]
            
            if np.any(f3_region):
                f3_peak_idx = np.argmax(psd[f3_region])
                f3_peak = freqs[f3_region][f3_peak_idx]
            
            # Formant bandwidths (approximated)
            f1_bandwidth = self._estimate_bandwidth(psd, f1_region, freqs)
            f2_bandwidth = self._estimate_bandwidth(psd, f2_region, freqs)
            f3_bandwidth = self._estimate_bandwidth(psd, f3_region, freqs)
            
            return [
                float(f1_peak),
                float(f2_peak),
                float(f3_peak),
                float(f1_bandwidth),
                float(f2_bandwidth),
                float(f3_bandwidth)
            ]
            
        except Exception:
            return [0.0] * 6
    
    def _estimate_bandwidth(self, psd: np.ndarray, region_mask: np.ndarray, freqs: np.ndarray) -> float:
        """Estimate bandwidth for a formant region"""
        try:
            if not np.any(region_mask):
                return 0.0
            
            region_psd = psd[region_mask]
            region_freqs = freqs[region_mask]
            
            if len(region_psd) == 0:
                return 0.0
            
            # Find -3dB bandwidth
            max_power = np.max(region_psd)
            half_power = max_power / 2
            
            above_half_power = region_psd >= half_power
            if np.any(above_half_power):
                bandwidth_freqs = region_freqs[above_half_power]
                bandwidth = np.max(bandwidth_freqs) - np.min(bandwidth_freqs)
                return float(bandwidth)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _extract_spectral_features(self, audio_samples: np.ndarray) -> List[float]:
        """Extract spectral characteristics"""
        try:
            freqs, psd = signal.welch(audio_samples, self.sample_rate, nperseg=512)
            
            # Spectral centroid
            if np.sum(psd) > 0:
                spectral_centroid = np.sum(freqs * psd) / np.sum(psd)
            else:
                spectral_centroid = 0.0
            
            # Spectral rolloff
            cumulative_energy = np.cumsum(psd)
            if cumulative_energy[-1] > 0:
                rolloff_threshold = 0.85 * cumulative_energy[-1]
                rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
                spectral_rolloff = freqs[rolloff_idx[0]] if len(rolloff_idx) > 0 else 0.0
            else:
                spectral_rolloff = 0.0
            
            # Spectral flux
            spectral_flux = np.sum(np.diff(psd) ** 2)
            
            # Spectral flatness
            if np.all(psd > 0):
                geometric_mean = np.exp(np.mean(np.log(psd)))
                arithmetic_mean = np.mean(psd)
                spectral_flatness = geometric_mean / arithmetic_mean
            else:
                spectral_flatness = 0.0
            
            # Zero crossing rate
            zcr = np.sum(np.diff(np.sign(audio_samples)) != 0) / len(audio_samples)
            
            # Spectral slope
            if len(freqs) > 1 and np.std(freqs) > 0:
                spectral_slope = np.corrcoef(freqs, psd)[0, 1]
                if np.isnan(spectral_slope):
                    spectral_slope = 0.0
            else:
                spectral_slope = 0.0
            
            # Energy in different bands
            low_energy = np.sum(psd[(freqs >= 0) & (freqs <= 500)])
            mid_energy = np.sum(psd[(freqs > 500) & (freqs <= 2000)])
            high_energy = np.sum(psd[(freqs > 2000) & (freqs <= 8000)])
            
            total_energy = low_energy + mid_energy + high_energy
            if total_energy > 0:
                low_ratio = low_energy / total_energy
                high_ratio = high_energy / total_energy
            else:
                low_ratio = high_ratio = 0.0
            
            return [
                float(spectral_centroid),
                float(spectral_rolloff),
                float(spectral_flux),
                float(spectral_flatness),
                float(zcr),
                float(spectral_slope),
                float(low_ratio),
                float(high_ratio)
            ]
            
        except Exception:
            return [0.0] * 8
    
    def _extract_prosodic_features(self, audio_samples: np.ndarray) -> List[float]:
        """Extract prosodic features"""
        try:
            # Energy envelope
            energy = audio_samples ** 2
            
            # Energy statistics
            mean_energy = np.mean(energy)
            energy_std = np.std(energy)
            max_energy = np.max(energy)
            
            # Energy dynamics
            energy_slope = 0.0
            if len(energy) > 1:
                x = np.arange(len(energy))
                if np.std(x) > 0:
                    energy_slope = np.corrcoef(x, energy)[0, 1]
                    if np.isnan(energy_slope):
                        energy_slope = 0.0
            
            # Rhythm features
            # Simple rhythm estimation using energy peaks
            energy_smooth = signal.savgol_filter(energy, min(51, len(energy)), 3) if len(energy) > 51 else energy
            
            # Find energy peaks
            if len(energy_smooth) > 3:
                peaks, _ = signal.find_peaks(energy_smooth, height=np.mean(energy_smooth))
                rhythm_rate = len(peaks) / (len(audio_samples) / self.sample_rate)
                
                # Peak intervals
                if len(peaks) > 1:
                    peak_intervals = np.diff(peaks) / self.sample_rate
                    rhythm_regularity = 1.0 / (np.std(peak_intervals) + 0.001)
                else:
                    rhythm_regularity = 0.0
            else:
                rhythm_rate = 0.0
                rhythm_regularity = 0.0
            
            # Pause detection (very simple)
            silence_threshold = 0.01 * max_energy
            silent_frames = np.sum(energy < silence_threshold)
            pause_ratio = silent_frames / len(energy)
            
            return [
                float(mean_energy),
                float(energy_std),
                float(max_energy),
                float(energy_slope),
                float(rhythm_rate),
                float(rhythm_regularity),
                float(pause_ratio)
            ]
            
        except Exception:
            return [0.0] * 7
    
    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize feature vector"""
        try:
            # Z-score normalization with clipping
            mean_val = np.mean(features)
            std_val = np.std(features)
            
            if std_val > 0:
                normalized = (features - mean_val) / std_val
                # Clip to reasonable range
                normalized = np.clip(normalized, -3, 3)
            else:
                normalized = features
            
            return normalized
            
        except Exception:
            return features

class MultiSpeakerDiarization:
    """Advanced multi-speaker diarization system"""
    
    def __init__(self, max_speakers: int = 10):
        self.max_speakers = max_speakers
        self.feature_extractor = AdvancedVoiceFeatureExtractor()
        
        # Speaker tracking
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
        self.active_speakers: Dict[str, float] = {}  # speaker_id -> last_activity_time
        
        # Clustering parameters
        self.clustering_threshold = 0.3
        self.min_segment_duration = 0.5  # seconds
        
        # Speaker overlap detection
        self.overlap_threshold = 0.7
        self.overlap_window_ms = 200
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance tracking
        self.diarization_history = deque(maxlen=1000)
        
        logger.info("🎭 Multi-Speaker Diarization system initialized")
    
    def process_audio_segment(
        self, 
        audio_samples: np.ndarray, 
        timestamp: float, 
        segment_id: str,
        existing_transcript: str = ""
    ) -> SpeakerSegment:
        """Process audio segment for speaker identification"""
        
        try:
            with self._lock:
                # Extract voice features
                voice_features = self.feature_extractor.extract_comprehensive_features(audio_samples)
                
                # Identify speaker
                speaker_id, speaker_confidence = self._identify_speaker(voice_features, timestamp)
                
                # Detect overlapping speakers
                overlap_detected, background_speakers = self._detect_speaker_overlap(
                    voice_features, speaker_id, timestamp
                )
                
                # Create speaker segment
                segment = SpeakerSegment(
                    segment_id=segment_id,
                    speaker_id=speaker_id,
                    start_time=timestamp,
                    end_time=timestamp + len(audio_samples) / self.feature_extractor.sample_rate,
                    audio_data=audio_samples.tobytes(),
                    transcript=existing_transcript,
                    voice_features=voice_features,
                    speaker_confidence=speaker_confidence,
                    overlap_detected=overlap_detected,
                    background_speakers=background_speakers
                )
                
                # Update speaker tracking
                self._update_speaker_tracking(speaker_id, voice_features, timestamp)
                
                # Record diarization result
                self.diarization_history.append({
                    'timestamp': timestamp,
                    'speaker_id': speaker_id,
                    'confidence': speaker_confidence,
                    'overlap': overlap_detected,
                    'segment_id': segment_id
                })
                
                logger.debug(f"🎭 Diarized segment {segment_id}: speaker={speaker_id}, "
                           f"confidence={speaker_confidence:.2f}, overlap={overlap_detected}")
                
                return segment
                
        except Exception as e:
            logger.error(f"❌ Speaker diarization failed for segment {segment_id}: {e}")
            return self._create_default_segment(segment_id, timestamp, audio_samples, existing_transcript)
    
    def _identify_speaker(self, voice_features: np.ndarray, timestamp: float) -> Tuple[str, float]:
        """Identify speaker from voice features"""
        try:
            if len(self.speaker_profiles) == 0:
                # First speaker
                speaker_id = self._create_new_speaker(voice_features, timestamp)
                return speaker_id, 1.0
            
            # Compare with existing speakers
            best_match_id = None
            best_similarity = 0.0
            
            for speaker_id, profile in self.speaker_profiles.items():
                try:
                    similarity = 1 - cosine(voice_features, profile.voice_features)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_match_id = speaker_id
                except Exception as e:
                    logger.warning(f"⚠️ Similarity calculation failed: {e}")
                    continue
            
            # Decision threshold
            if best_similarity > self.clustering_threshold:
                return best_match_id, best_similarity
            else:
                # Create new speaker if we haven't reached max speakers
                if len(self.speaker_profiles) < self.max_speakers:
                    new_speaker_id = self._create_new_speaker(voice_features, timestamp)
                    return new_speaker_id, 1.0
                else:
                    # Assign to best match even if below threshold
                    return best_match_id, best_similarity
                    
        except Exception as e:
            logger.warning(f"⚠️ Speaker identification failed: {e}")
            # Default to first speaker or create new one
            if self.speaker_profiles:
                return list(self.speaker_profiles.keys())[0], 0.5
            else:
                speaker_id = self._create_new_speaker(voice_features, timestamp)
                return speaker_id, 0.5
    
    def _create_new_speaker(self, voice_features: np.ndarray, timestamp: float) -> str:
        """Create new speaker profile"""
        try:
            speaker_id = f"speaker_{len(self.speaker_profiles) + 1}"
            
            # Extract initial characteristics
            pitch_range = self._extract_pitch_range(voice_features)
            formant_chars = self._extract_formant_characteristics(voice_features)
            
            profile = SpeakerProfile(
                speaker_id=speaker_id,
                voice_features=voice_features.copy(),
                pitch_range=pitch_range,
                formant_characteristics=formant_chars,
                speaking_rate=0.0,  # Will be updated over time
                energy_profile=float(np.mean(voice_features[:5])),  # Energy-related features
                spectral_signature=voice_features[13:21].copy(),  # Spectral features
                confidence_score=1.0,
                first_seen=timestamp,
                last_seen=timestamp,
                total_speech_time=0.0,
                segment_count=1
            )
            
            self.speaker_profiles[speaker_id] = profile
            self.active_speakers[speaker_id] = timestamp
            
            logger.info(f"🆕 Created new speaker profile: {speaker_id}")
            return speaker_id
            
        except Exception as e:
            logger.error(f"❌ Speaker creation failed: {e}")
            return "speaker_unknown"
    
    def _extract_pitch_range(self, voice_features: np.ndarray) -> Tuple[float, float]:
        """Extract pitch range from voice features"""
        try:
            # Pitch features are at indices 13-17
            if len(voice_features) > 17:
                min_pitch = float(voice_features[15])  # min_pitch feature
                max_pitch = float(voice_features[16])  # max_pitch feature
                return (min_pitch, max_pitch)
            return (0.0, 0.0)
        except Exception:
            return (0.0, 0.0)
    
    def _extract_formant_characteristics(self, voice_features: np.ndarray) -> Dict[str, float]:
        """Extract formant characteristics from voice features"""
        try:
            # Formant features are at indices 18-23
            if len(voice_features) > 23:
                return {
                    'f1': float(voice_features[18]),
                    'f2': float(voice_features[19]),
                    'f3': float(voice_features[20]),
                    'f1_bandwidth': float(voice_features[21]),
                    'f2_bandwidth': float(voice_features[22]),
                    'f3_bandwidth': float(voice_features[23])
                }
            return {}
        except Exception:
            return {}
    
    def _detect_speaker_overlap(
        self, 
        voice_features: np.ndarray, 
        primary_speaker: str, 
        timestamp: float
    ) -> Tuple[bool, List[str]]:
        """Detect overlapping speakers in the audio"""
        try:
            # Simple overlap detection based on energy distribution
            background_speakers = []
            
            # Check if multiple speakers might be present
            # This is a simplified approach - real overlap detection would be more complex
            energy_features = voice_features[:5]  # Energy-related features
            energy_variance = np.var(energy_features)
            
            # High variance might indicate multiple speakers
            if energy_variance > 0.5:  # Threshold for overlap detection
                # Find potential background speakers
                for speaker_id, profile in self.speaker_profiles.items():
                    if speaker_id != primary_speaker:
                        try:
                            similarity = 1 - cosine(voice_features, profile.voice_features)
                            if similarity > 0.4:  # Lower threshold for background detection
                                background_speakers.append(speaker_id)
                        except Exception:
                            continue
            
            overlap_detected = len(background_speakers) > 0
            
            return overlap_detected, background_speakers
            
        except Exception as e:
            logger.warning(f"⚠️ Overlap detection failed: {e}")
            return False, []
    
    def _update_speaker_tracking(self, speaker_id: str, voice_features: np.ndarray, timestamp: float):
        """Update speaker tracking information"""
        try:
            if speaker_id in self.speaker_profiles:
                profile = self.speaker_profiles[speaker_id]
                profile.update_profile(voice_features, timestamp)
                
                # Update active speakers
                self.active_speakers[speaker_id] = timestamp
                
                # Clean up inactive speakers
                self._cleanup_inactive_speakers(timestamp)
                
        except Exception as e:
            logger.warning(f"⚠️ Speaker tracking update failed: {e}")
    
    def _cleanup_inactive_speakers(self, current_time: float, inactive_threshold: float = 300.0):
        """Remove speakers that haven't been active for a while"""
        try:
            inactive_speakers = []
            
            for speaker_id, last_activity in self.active_speakers.items():
                if current_time - last_activity > inactive_threshold:
                    inactive_speakers.append(speaker_id)
            
            for speaker_id in inactive_speakers:
                del self.active_speakers[speaker_id]
                # Keep profile but mark as inactive
                if speaker_id in self.speaker_profiles:
                    logger.debug(f"📋 Speaker {speaker_id} marked as inactive")
                    
        except Exception as e:
            logger.warning(f"⚠️ Speaker cleanup failed: {e}")
    
    def _create_default_segment(
        self, 
        segment_id: str, 
        timestamp: float, 
        audio_samples: np.ndarray, 
        transcript: str
    ) -> SpeakerSegment:
        """Create default speaker segment for error cases"""
        return SpeakerSegment(
            segment_id=segment_id,
            speaker_id="speaker_unknown",
            start_time=timestamp,
            end_time=timestamp + len(audio_samples) / self.feature_extractor.sample_rate,
            audio_data=audio_samples.tobytes(),
            transcript=transcript,
            confidence=0.0,
            speaker_confidence=0.0,
            overlap_detected=False,
            background_speakers=[]
        )
    
    def get_speaker_summary(self) -> Dict[str, Any]:
        """Get comprehensive speaker analysis summary"""
        try:
            with self._lock:
                summary = {
                    'total_speakers': len(self.speaker_profiles),
                    'active_speakers': len(self.active_speakers),
                    'speaker_profiles': {},
                    'recent_activity': [],
                    'overlap_statistics': self._get_overlap_statistics()
                }
                
                # Speaker profile summaries
                for speaker_id, profile in self.speaker_profiles.items():
                    summary['speaker_profiles'][speaker_id] = {
                        'confidence_score': profile.confidence_score,
                        'total_speech_time': profile.total_speech_time,
                        'segment_count': profile.segment_count,
                        'pitch_range': profile.pitch_range,
                        'voice_category': self._categorize_voice(profile),
                        'is_active': speaker_id in self.active_speakers,
                        'last_seen': profile.last_seen
                    }
                
                # Recent activity (last 10 diarization results)
                summary['recent_activity'] = list(self.diarization_history)[-10:]
                
                return summary
                
        except Exception as e:
            logger.error(f"❌ Speaker summary generation failed: {e}")
            return {'total_speakers': 0, 'active_speakers': 0}
    
    def _categorize_voice(self, profile: SpeakerProfile) -> str:
        """Categorize voice based on characteristics"""
        try:
            pitch_range = profile.pitch_range
            avg_pitch = (pitch_range[0] + pitch_range[1]) / 2
            
            if avg_pitch > 200:
                return "high_voice"  # Likely female or child
            elif avg_pitch > 120:
                return "medium_voice"  # Could be either
            elif avg_pitch > 0:
                return "low_voice"  # Likely male
            else:
                return "unknown"
                
        except Exception:
            return "unknown"
    
    def _get_overlap_statistics(self) -> Dict[str, Any]:
        """Get speaker overlap statistics"""
        try:
            recent_history = list(self.diarization_history)[-100:]  # Last 100 segments
            
            total_segments = len(recent_history)
            overlap_segments = sum(1 for h in recent_history if h.get('overlap', False))
            
            overlap_rate = overlap_segments / total_segments if total_segments > 0 else 0.0
            
            return {
                'total_segments_analyzed': total_segments,
                'overlap_segments': overlap_segments,
                'overlap_rate': overlap_rate,
                'average_confidence': np.mean([h.get('confidence', 0) for h in recent_history]) if recent_history else 0.0
            }
            
        except Exception:
            return {'overlap_rate': 0.0, 'total_segments_analyzed': 0}

# Global diarization instance
_diarization_system = None
_diarization_lock = threading.Lock()

def get_multi_speaker_diarization() -> MultiSpeakerDiarization:
    """Get global multi-speaker diarization instance"""
    global _diarization_system
    
    with _diarization_lock:
        if _diarization_system is None:
            _diarization_system = MultiSpeakerDiarization()
        return _diarization_system

logger.info("✅ Multi-Speaker Diarization module initialized")