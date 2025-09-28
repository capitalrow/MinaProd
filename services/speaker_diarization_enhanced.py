"""
👥 ENHANCED SPEAKER DIARIZATION: Advanced speaker identification and voice profiling
Provides sophisticated speaker separation, voice characteristics analysis, and speaker tracking
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
import numpy as np
import hashlib
import json
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class VoiceProfile:
    """Comprehensive voice profile for speaker identification"""
    speaker_id: str
    voice_signature: np.ndarray = None
    pitch_range: Tuple[float, float] = (0.0, 0.0)
    speaking_rate: float = 0.0  # words per minute
    energy_level: float = 0.0
    formant_characteristics: Dict[str, float] = field(default_factory=dict)
    accent_markers: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    first_appearance: float = 0.0
    last_appearance: float = 0.0
    total_speaking_time: float = 0.0
    segment_count: int = 0
    speaker_name: Optional[str] = None
    speaker_role: Optional[str] = None

@dataclass
class SpeakerSegment:
    """Individual speaker segment with enhanced metadata"""
    segment_id: str
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float
    voice_characteristics: Dict[str, float] = field(default_factory=dict)
    emotion_indicators: Dict[str, float] = field(default_factory=dict)
    speech_quality: float = 0.0
    interruption_type: Optional[str] = None  # 'overlap', 'interruption', 'pause'

@dataclass 
class DiarizationResult:
    """Comprehensive diarization result"""
    session_id: str
    total_speakers: int
    speaker_profiles: Dict[str, VoiceProfile]
    speaker_segments: List[SpeakerSegment]
    speaker_timeline: List[Tuple[float, float, str]]  # (start, end, speaker_id)
    interaction_patterns: Dict[str, Any]
    meeting_dynamics: Dict[str, Any]
    processing_time_ms: float = 0.0

class EnhancedSpeakerDiarization:
    """
    Advanced speaker diarization with voice profiling and interaction analysis
    """
    
    def __init__(self):
        self.session_speakers: Dict[str, Dict[str, VoiceProfile]] = {}
        self.speaker_counter = 0
        self.voice_signatures_cache = {}
        self.session_lock = threading.RLock()
        
        # Advanced analysis parameters
        self.similarity_threshold = 0.85
        self.min_segment_duration = 0.5  # seconds
        self.overlap_tolerance = 0.1  # seconds
        
        logger.info("👥 Enhanced Speaker Diarization initialized")
    
    def analyze_speaker_segment(self, 
                              session_id: str,
                              audio_data: bytes,
                              transcription_result: Dict[str, Any],
                              timestamp: float) -> SpeakerSegment:
        """Analyze audio segment for speaker identification and characteristics"""
        start_time = time.time()
        
        try:
            # Extract voice characteristics from audio
            voice_features = self._extract_voice_features(audio_data)
            
            # Identify or create speaker profile
            speaker_id = self._identify_speaker(session_id, voice_features, timestamp)
            
            # Analyze speech characteristics
            speech_characteristics = self._analyze_speech_characteristics(
                audio_data, transcription_result
            )
            
            # Detect emotion indicators
            emotion_indicators = self._detect_emotion_indicators(
                voice_features, transcription_result
            )
            
            # Create speaker segment
            segment = SpeakerSegment(
                segment_id=f"{session_id}_{int(timestamp)}_{speaker_id}",
                speaker_id=speaker_id,
                start_time=timestamp,
                end_time=timestamp + len(audio_data) / (16000 * 2),  # Approximate duration
                text=transcription_result.get('text', ''),
                confidence=transcription_result.get('confidence', 0.0),
                voice_characteristics=speech_characteristics,
                emotion_indicators=emotion_indicators,
                speech_quality=voice_features.get('quality_score', 0.5)
            )
            
            # Update speaker profile
            self._update_speaker_profile(session_id, speaker_id, voice_features, segment)
            
            logger.debug(f"👤 Analyzed segment for speaker {speaker_id}: "
                        f"quality={segment.speech_quality:.2f}")
            
            return segment
            
        except Exception as e:
            logger.error(f"❌ Speaker analysis failed: {e}")
            # Return fallback segment
            return SpeakerSegment(
                segment_id=f"{session_id}_{int(timestamp)}_unknown",
                speaker_id="unknown",
                start_time=timestamp,
                end_time=timestamp + 1.0,
                text=transcription_result.get('text', ''),
                confidence=0.5
            )
    
    def _extract_voice_features(self, audio_data: bytes) -> Dict[str, Any]:
        """Extract comprehensive voice features for speaker identification"""
        try:
            # Convert audio data to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            if len(audio_array) == 0:
                return {'quality_score': 0.0}
            
            # Basic acoustic features
            features = {}
            
            # 1. Fundamental frequency (pitch) analysis
            features['pitch_mean'], features['pitch_std'] = self._analyze_pitch(audio_array)
            
            # 2. Spectral characteristics
            features['spectral_centroid'] = self._calculate_spectral_centroid(audio_array)
            features['spectral_rolloff'] = self._calculate_spectral_rolloff(audio_array)
            features['mfcc'] = self._extract_mfcc_features(audio_array)
            
            # 3. Energy and dynamics
            features['energy_mean'] = np.mean(audio_array ** 2)
            features['energy_std'] = np.std(audio_array ** 2)
            features['zero_crossing_rate'] = self._calculate_zcr(audio_array)
            
            # 4. Voice quality indicators
            features['jitter'] = self._calculate_jitter(audio_array)
            features['shimmer'] = self._calculate_shimmer(audio_array)
            
            # 5. Formant analysis (simplified)
            features['formants'] = self._estimate_formants(audio_array)
            
            # 6. Overall quality score
            features['quality_score'] = self._calculate_voice_quality(features)
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Voice feature extraction failed: {e}")
            return {'quality_score': 0.0}
    
    def _analyze_pitch(self, audio: np.ndarray, sr: int = 16000) -> Tuple[float, float]:
        """Analyze pitch characteristics"""
        try:
            # Simple autocorrelation-based pitch detection
            autocorr = np.correlate(audio, audio, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            # Find peaks in expected pitch range (50-400 Hz)
            min_period = sr // 400  # 400 Hz
            max_period = sr // 50   # 50 Hz
            
            if max_period < len(autocorr):
                pitch_autocorr = autocorr[min_period:min_period + max_period]
                if len(pitch_autocorr) > 0:
                    peak_idx = np.argmax(pitch_autocorr)
                    period = min_period + peak_idx
                    pitch = sr / period if period > 0 else 0
                    
                    return float(pitch), float(np.std(pitch_autocorr))
            
            return 0.0, 0.0
            
        except Exception:
            return 0.0, 0.0
    
    def _calculate_spectral_centroid(self, audio: np.ndarray, sr: int = 16000) -> float:
        """Calculate spectral centroid"""
        try:
            # Compute magnitude spectrum
            fft = np.fft.fft(audio)
            magnitude = np.abs(fft[:len(fft)//2])
            freqs = np.fft.fftfreq(len(audio), 1/sr)[:len(fft)//2]
            
            # Calculate centroid
            if np.sum(magnitude) > 0:
                centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
                return float(centroid)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_spectral_rolloff(self, audio: np.ndarray, sr: int = 16000) -> float:
        """Calculate spectral rolloff (85% energy point)"""
        try:
            fft = np.fft.fft(audio)
            magnitude = np.abs(fft[:len(fft)//2])
            freqs = np.fft.fftfreq(len(audio), 1/sr)[:len(fft)//2]
            
            # Calculate cumulative energy
            energy = magnitude ** 2
            cumulative_energy = np.cumsum(energy)
            total_energy = cumulative_energy[-1]
            
            # Find 85% rolloff point
            rolloff_idx = np.where(cumulative_energy >= 0.85 * total_energy)[0]
            if len(rolloff_idx) > 0:
                return float(freqs[rolloff_idx[0]])
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _extract_mfcc_features(self, audio: np.ndarray) -> List[float]:
        """Extract simplified MFCC-like features"""
        try:
            # Simplified mel-frequency cepstral coefficients
            # This is a basic implementation for demonstration
            
            # Pre-emphasis
            pre_emphasized = np.append(audio[0], audio[1:] - 0.97 * audio[:-1])
            
            # Windowing and FFT
            windowed = pre_emphasized * np.hanning(len(pre_emphasized))
            fft = np.fft.fft(windowed)
            magnitude = np.abs(fft[:len(fft)//2])
            
            # Mel filter bank (simplified)
            mel_filters = self._create_mel_filterbank(len(magnitude))
            mel_energies = np.dot(mel_filters, magnitude)
            
            # Log and DCT (simplified)
            log_mel = np.log(mel_energies + 1e-10)
            mfcc = np.fft.dct(log_mel)[:13]  # First 13 coefficients
            
            return mfcc.tolist()
            
        except Exception:
            return [0.0] * 13
    
    def _create_mel_filterbank(self, n_fft: int, n_mels: int = 26) -> np.ndarray:
        """Create simplified mel filterbank"""
        try:
            # Simplified mel filterbank creation
            filterbank = np.zeros((n_mels, n_fft))
            
            # Create triangular filters
            for i in range(n_mels):
                start = i * n_fft // (n_mels + 1)
                center = (i + 1) * n_fft // (n_mels + 1)
                end = (i + 2) * n_fft // (n_mels + 1)
                
                if end < n_fft:
                    # Rising edge
                    filterbank[i, start:center] = np.linspace(0, 1, center - start)
                    # Falling edge
                    filterbank[i, center:end] = np.linspace(1, 0, end - center)
            
            return filterbank
            
        except Exception:
            return np.zeros((26, n_fft))
    
    def _calculate_zcr(self, audio: np.ndarray) -> float:
        """Calculate zero crossing rate"""
        try:
            zero_crossings = np.sum(np.diff(np.sign(audio)) != 0)
            return float(zero_crossings / len(audio))
        except Exception:
            return 0.0
    
    def _calculate_jitter(self, audio: np.ndarray) -> float:
        """Calculate jitter (pitch variation)"""
        try:
            # Simplified jitter calculation
            if len(audio) < 100:
                return 0.0
            
            # Find period-to-period variations
            periods = []
            for i in range(0, len(audio) - 100, 50):
                segment = audio[i:i+100]
                autocorr = np.correlate(segment, segment, mode='full')
                autocorr = autocorr[autocorr.size // 2:]
                
                if len(autocorr) > 20:
                    peak_idx = np.argmax(autocorr[10:50]) + 10
                    periods.append(peak_idx)
            
            if len(periods) > 1:
                period_diffs = np.diff(periods)
                return float(np.std(period_diffs) / np.mean(periods) if np.mean(periods) > 0 else 0)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_shimmer(self, audio: np.ndarray) -> float:
        """Calculate shimmer (amplitude variation)"""
        try:
            # Simplified shimmer calculation
            if len(audio) < 100:
                return 0.0
            
            # Calculate amplitude variations
            amplitudes = []
            for i in range(0, len(audio) - 100, 50):
                segment = audio[i:i+100]
                amplitude = np.max(np.abs(segment))
                amplitudes.append(amplitude)
            
            if len(amplitudes) > 1:
                amp_diffs = np.diff(amplitudes)
                return float(np.std(amp_diffs) / np.mean(amplitudes) if np.mean(amplitudes) > 0 else 0)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _estimate_formants(self, audio: np.ndarray) -> Dict[str, float]:
        """Estimate formant frequencies"""
        try:
            # Simplified formant estimation using peak detection
            fft = np.fft.fft(audio)
            magnitude = np.abs(fft[:len(fft)//2])
            freqs = np.fft.fftfreq(len(audio), 1/16000)[:len(fft)//2]
            
            # Find peaks in typical formant ranges
            f1_range = (200, 1000)  # F1 range
            f2_range = (1000, 3000)  # F2 range
            
            f1_mask = (freqs >= f1_range[0]) & (freqs <= f1_range[1])
            f2_mask = (freqs >= f2_range[0]) & (freqs <= f2_range[1])
            
            f1_freq = 0.0
            f2_freq = 0.0
            
            if np.any(f1_mask):
                f1_idx = np.argmax(magnitude[f1_mask])
                f1_freq = freqs[f1_mask][f1_idx]
            
            if np.any(f2_mask):
                f2_idx = np.argmax(magnitude[f2_mask])
                f2_freq = freqs[f2_mask][f2_idx]
            
            return {
                'f1': float(f1_freq),
                'f2': float(f2_freq),
                'f1_f2_ratio': float(f2_freq / f1_freq if f1_freq > 0 else 0)
            }
            
        except Exception:
            return {'f1': 0.0, 'f2': 0.0, 'f1_f2_ratio': 0.0}
    
    def _calculate_voice_quality(self, features: Dict[str, Any]) -> float:
        """Calculate overall voice quality score"""
        try:
            score = 0.0
            weights = {
                'pitch_stability': 0.2,
                'spectral_quality': 0.3,
                'energy_consistency': 0.2,
                'formant_clarity': 0.2,
                'noise_level': 0.1
            }
            
            # Pitch stability (lower jitter is better)
            jitter = features.get('jitter', 1.0)
            pitch_stability = max(0, 1 - jitter * 10)
            score += weights['pitch_stability'] * pitch_stability
            
            # Spectral quality
            spectral_centroid = features.get('spectral_centroid', 0)
            spectral_quality = min(1.0, spectral_centroid / 2000) if spectral_centroid > 0 else 0
            score += weights['spectral_quality'] * spectral_quality
            
            # Energy consistency (lower shimmer is better)
            shimmer = features.get('shimmer', 1.0)
            energy_consistency = max(0, 1 - shimmer * 5)
            score += weights['energy_consistency'] * energy_consistency
            
            # Formant clarity
            formants = features.get('formants', {})
            f1_f2_ratio = formants.get('f1_f2_ratio', 0)
            formant_clarity = min(1.0, f1_f2_ratio / 3) if f1_f2_ratio > 0 else 0
            score += weights['formant_clarity'] * formant_clarity
            
            # Noise level (inverse of ZCR deviation from speech norm)
            zcr = features.get('zero_crossing_rate', 0.1)
            optimal_zcr = 0.05  # Typical for speech
            noise_score = max(0, 1 - abs(zcr - optimal_zcr) / optimal_zcr)
            score += weights['noise_level'] * noise_score
            
            return float(max(0.0, min(1.0, score)))
            
        except Exception:
            return 0.5
    
    def _identify_speaker(self, session_id: str, voice_features: Dict[str, Any], timestamp: float) -> str:
        """Identify speaker or create new speaker profile"""
        with self.session_lock:
            if session_id not in self.session_speakers:
                self.session_speakers[session_id] = {}
            
            session_speakers = self.session_speakers[session_id]
            
            # Compare with existing speakers
            best_match_id = None
            best_similarity = 0.0
            
            for speaker_id, profile in session_speakers.items():
                similarity = self._calculate_speaker_similarity(voice_features, profile)
                if similarity > best_similarity and similarity > self.similarity_threshold:
                    best_similarity = similarity
                    best_match_id = speaker_id
            
            # Return existing speaker or create new one
            if best_match_id:
                return best_match_id
            else:
                # Create new speaker
                new_speaker_id = f"speaker_{len(session_speakers) + 1}"
                
                new_profile = VoiceProfile(
                    speaker_id=new_speaker_id,
                    voice_signature=self._create_voice_signature(voice_features),
                    pitch_range=(voice_features.get('pitch_mean', 0), voice_features.get('pitch_std', 0)),
                    energy_level=voice_features.get('energy_mean', 0),
                    formant_characteristics=voice_features.get('formants', {}),
                    confidence_score=voice_features.get('quality_score', 0.5),
                    first_appearance=timestamp
                )
                
                session_speakers[new_speaker_id] = new_profile
                
                logger.info(f"👤 Created new speaker profile: {new_speaker_id}")
                return new_speaker_id
    
    def _calculate_speaker_similarity(self, features: Dict[str, Any], profile: VoiceProfile) -> float:
        """Calculate similarity between voice features and speaker profile"""
        try:
            similarities = []
            
            # Pitch similarity
            pitch_mean = features.get('pitch_mean', 0)
            if pitch_mean > 0 and profile.pitch_range[0] > 0:
                pitch_diff = abs(pitch_mean - profile.pitch_range[0]) / profile.pitch_range[0]
                pitch_similarity = max(0, 1 - pitch_diff)
                similarities.append(pitch_similarity * 0.3)
            
            # Spectral centroid similarity
            spectral_centroid = features.get('spectral_centroid', 0)
            if hasattr(profile, 'spectral_centroid') and spectral_centroid > 0:
                centroid_diff = abs(spectral_centroid - profile.spectral_centroid) / profile.spectral_centroid
                centroid_similarity = max(0, 1 - centroid_diff)
                similarities.append(centroid_similarity * 0.2)
            
            # Formant similarity
            formants = features.get('formants', {})
            if formants and profile.formant_characteristics:
                f1_sim = self._compare_formants(formants.get('f1', 0), profile.formant_characteristics.get('f1', 0))
                f2_sim = self._compare_formants(formants.get('f2', 0), profile.formant_characteristics.get('f2', 0))
                formant_similarity = (f1_sim + f2_sim) / 2
                similarities.append(formant_similarity * 0.3)
            
            # Energy level similarity
            energy = features.get('energy_mean', 0)
            if energy > 0 and profile.energy_level > 0:
                energy_diff = abs(energy - profile.energy_level) / profile.energy_level
                energy_similarity = max(0, 1 - energy_diff)
                similarities.append(energy_similarity * 0.2)
            
            return sum(similarities) if similarities else 0.0
            
        except Exception:
            return 0.0
    
    def _compare_formants(self, f1: float, f2: float) -> float:
        """Compare formant frequencies"""
        if f1 == 0 or f2 == 0:
            return 0.0
        
        diff = abs(f1 - f2) / max(f1, f2)
        return max(0, 1 - diff)
    
    def _create_voice_signature(self, features: Dict[str, Any]) -> np.ndarray:
        """Create voice signature for speaker identification"""
        try:
            # Create feature vector from key characteristics
            signature_features = [
                features.get('pitch_mean', 0),
                features.get('pitch_std', 0),
                features.get('spectral_centroid', 0),
                features.get('spectral_rolloff', 0),
                features.get('energy_mean', 0),
                features.get('energy_std', 0),
                features.get('zero_crossing_rate', 0),
                features.get('jitter', 0),
                features.get('shimmer', 0)
            ]
            
            # Add MFCC features
            mfcc = features.get('mfcc', [0] * 13)
            signature_features.extend(mfcc[:13])
            
            # Add formant features
            formants = features.get('formants', {})
            signature_features.extend([
                formants.get('f1', 0),
                formants.get('f2', 0),
                formants.get('f1_f2_ratio', 0)
            ])
            
            return np.array(signature_features, dtype=np.float32)
            
        except Exception:
            return np.zeros(25, dtype=np.float32)
    
    def _analyze_speech_characteristics(self, audio_data: bytes, transcription: Dict[str, Any]) -> Dict[str, float]:
        """Analyze speech-specific characteristics"""
        try:
            text = transcription.get('text', '')
            
            characteristics = {}
            
            # Speaking rate (words per minute)
            word_count = len(text.split()) if text else 0
            duration = len(audio_data) / (16000 * 2)  # Approximate duration
            if duration > 0:
                characteristics['speaking_rate'] = (word_count / duration) * 60
            else:
                characteristics['speaking_rate'] = 0
            
            # Pause patterns (simplified)
            characteristics['pause_frequency'] = text.count(',') + text.count('.') if text else 0
            
            # Confidence indicators
            characteristics['transcription_confidence'] = transcription.get('confidence', 0.0)
            
            return characteristics
            
        except Exception:
            return {}
    
    def _detect_emotion_indicators(self, voice_features: Dict[str, Any], transcription: Dict[str, Any]) -> Dict[str, float]:
        """Detect emotion indicators from voice and text"""
        try:
            emotions = {}
            
            # Voice-based emotion indicators
            pitch = voice_features.get('pitch_mean', 0)
            energy = voice_features.get('energy_mean', 0)
            jitter = voice_features.get('jitter', 0)
            
            # High pitch + high energy = excitement/arousal
            if pitch > 200 and energy > 0.1:
                emotions['excitement'] = min(1.0, (pitch - 200) / 100 + energy * 5)
            
            # High jitter = stress/nervousness
            if jitter > 0.02:
                emotions['stress'] = min(1.0, jitter * 50)
            
            # Low energy = calm/tired
            if energy < 0.05:
                emotions['calm'] = 1.0 - energy * 20
            
            # Text-based emotion indicators (basic)
            text = transcription.get('text', '').lower()
            
            # Positive indicators
            positive_words = ['good', 'great', 'excellent', 'happy', 'love', 'amazing']
            positive_count = sum(1 for word in positive_words if word in text)
            if positive_count > 0:
                emotions['positive'] = min(1.0, positive_count / 10)
            
            # Negative indicators
            negative_words = ['bad', 'terrible', 'hate', 'angry', 'frustrated', 'awful']
            negative_count = sum(1 for word in negative_words if word in text)
            if negative_count > 0:
                emotions['negative'] = min(1.0, negative_count / 10)
            
            return emotions
            
        except Exception:
            return {}
    
    def _update_speaker_profile(self, session_id: str, speaker_id: str, 
                              voice_features: Dict[str, Any], segment: SpeakerSegment):
        """Update speaker profile with new information"""
        with self.session_lock:
            if session_id in self.session_speakers and speaker_id in self.session_speakers[session_id]:
                profile = self.session_speakers[session_id][speaker_id]
                
                # Update speaking time
                segment_duration = segment.end_time - segment.start_time
                profile.total_speaking_time += segment_duration
                profile.segment_count += 1
                profile.last_appearance = segment.end_time
                
                # Update speaking rate
                if segment.voice_characteristics.get('speaking_rate', 0) > 0:
                    current_rate = profile.speaking_rate or 0
                    new_rate = segment.voice_characteristics['speaking_rate']
                    # Exponential moving average
                    profile.speaking_rate = 0.8 * current_rate + 0.2 * new_rate
                
                # Update confidence score
                if segment.confidence > 0:
                    current_confidence = profile.confidence_score
                    profile.confidence_score = 0.8 * current_confidence + 0.2 * segment.confidence
    
    def generate_diarization_report(self, session_id: str) -> DiarizationResult:
        """Generate comprehensive diarization report for a session"""
        start_time = time.time()
        
        try:
            with self.session_lock:
                if session_id not in self.session_speakers:
                    return DiarizationResult(
                        session_id=session_id,
                        total_speakers=0,
                        speaker_profiles={},
                        speaker_segments=[],
                        speaker_timeline=[],
                        interaction_patterns={},
                        meeting_dynamics={}
                    )
                
                session_speakers = self.session_speakers[session_id]
                
                # Analyze interaction patterns
                interaction_patterns = self._analyze_interaction_patterns(session_speakers)
                
                # Analyze meeting dynamics
                meeting_dynamics = self._analyze_meeting_dynamics(session_speakers)
                
                # Create timeline (simplified)
                timeline = []
                for speaker_id, profile in session_speakers.items():
                    timeline.append((
                        profile.first_appearance,
                        profile.last_appearance,
                        speaker_id
                    ))
                
                timeline.sort(key=lambda x: x[0])
                
                processing_time = (time.time() - start_time) * 1000
                
                return DiarizationResult(
                    session_id=session_id,
                    total_speakers=len(session_speakers),
                    speaker_profiles=session_speakers.copy(),
                    speaker_segments=[],  # Would be populated from actual segments
                    speaker_timeline=timeline,
                    interaction_patterns=interaction_patterns,
                    meeting_dynamics=meeting_dynamics,
                    processing_time_ms=processing_time
                )
                
        except Exception as e:
            logger.error(f"❌ Diarization report generation failed: {e}")
            return DiarizationResult(
                session_id=session_id,
                total_speakers=0,
                speaker_profiles={},
                speaker_segments=[],
                speaker_timeline=[],
                interaction_patterns={},
                meeting_dynamics={}
            )
    
    def _analyze_interaction_patterns(self, speakers: Dict[str, VoiceProfile]) -> Dict[str, Any]:
        """Analyze speaker interaction patterns"""
        try:
            patterns = {
                'dominant_speaker': None,
                'speaking_time_distribution': {},
                'average_segment_duration': {},
                'interaction_frequency': {}
            }
            
            # Find dominant speaker
            max_speaking_time = 0
            for speaker_id, profile in speakers.items():
                if profile.total_speaking_time > max_speaking_time:
                    max_speaking_time = profile.total_speaking_time
                    patterns['dominant_speaker'] = speaker_id
            
            # Speaking time distribution
            total_time = sum(profile.total_speaking_time for profile in speakers.values())
            if total_time > 0:
                for speaker_id, profile in speakers.items():
                    patterns['speaking_time_distribution'][speaker_id] = profile.total_speaking_time / total_time
            
            # Average segment duration
            for speaker_id, profile in speakers.items():
                if profile.segment_count > 0:
                    patterns['average_segment_duration'][speaker_id] = profile.total_speaking_time / profile.segment_count
            
            return patterns
            
        except Exception:
            return {}
    
    def _analyze_meeting_dynamics(self, speakers: Dict[str, VoiceProfile]) -> Dict[str, Any]:
        """Analyze overall meeting dynamics"""
        try:
            dynamics = {
                'participation_balance': 0.0,
                'energy_level': 'medium',
                'speaking_rate_variance': 0.0,
                'confidence_levels': {}
            }
            
            if not speakers:
                return dynamics
            
            # Participation balance (entropy-based)
            speaking_times = [profile.total_speaking_time for profile in speakers.values()]
            total_time = sum(speaking_times)
            
            if total_time > 0:
                proportions = [t / total_time for t in speaking_times]
                entropy = -sum(p * np.log(p) for p in proportions if p > 0)
                max_entropy = np.log(len(speakers))
                dynamics['participation_balance'] = entropy / max_entropy if max_entropy > 0 else 0
            
            # Energy level
            avg_energy = np.mean([profile.energy_level for profile in speakers.values()])
            if avg_energy > 0.15:
                dynamics['energy_level'] = 'high'
            elif avg_energy < 0.05:
                dynamics['energy_level'] = 'low'
            else:
                dynamics['energy_level'] = 'medium'
            
            # Speaking rate variance
            speaking_rates = [profile.speaking_rate for profile in speakers.values() if profile.speaking_rate > 0]
            if speaking_rates:
                dynamics['speaking_rate_variance'] = float(np.std(speaking_rates))
            
            # Confidence levels
            for speaker_id, profile in speakers.items():
                dynamics['confidence_levels'][speaker_id] = profile.confidence_score
            
            return dynamics
            
        except Exception:
            return {}
    
    def clear_session(self, session_id: str):
        """Clear speaker data for a session"""
        with self.session_lock:
            if session_id in self.session_speakers:
                del self.session_speakers[session_id]
                logger.info(f"🗑️ Cleared speaker data for session {session_id}")

# Global diarization service
_global_diarization = None
_diarization_lock = threading.Lock()

def get_speaker_diarization() -> EnhancedSpeakerDiarization:
    """Get global speaker diarization service"""
    global _global_diarization
    
    if _global_diarization is None:
        with _diarization_lock:
            if _global_diarization is None:
                _global_diarization = EnhancedSpeakerDiarization()
    
    return _global_diarization

logger.info("👥 Enhanced Speaker Diarization service initialized")