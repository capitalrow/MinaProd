#!/usr/bin/env python3
# 🎤 Production Feature: Speaker Diarization & Multi-speaker Support
"""
Implements speaker diarization preparation and multi-speaker support
for enterprise meeting transcription requirements.

Addresses: "Speaker Identification & Multi-speaker Support" gap from production assessment.

Key Features:
- Speaker separation and identification
- Multi-speaker audio processing
- Speaker labeling and management
- Timeline-based speaker tracking
- Integration with transcription pipeline
"""

import logging
import time
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class SpeakerIdentificationMode(Enum):
    """Speaker identification modes."""
    AUTOMATIC = "automatic"  # AI-based automatic identification
    MANUAL = "manual"       # User-provided speaker labels
    HYBRID = "hybrid"       # Combination of both

@dataclass
class SpeakerProfile:
    """Speaker profile information."""
    speaker_id: str
    name: Optional[str] = None
    label: Optional[str] = None  # e.g., "Speaker A", "Moderator"
    voice_characteristics: Dict[str, Any] = field(default_factory=dict)
    first_detected: float = field(default_factory=time.time)
    last_detected: float = field(default_factory=time.time)
    total_speaking_time: float = 0.0
    segments_count: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    
    @property
    def average_confidence(self) -> float:
        return sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0.0

@dataclass
class SpeakerSegment:
    """Speaker segment in timeline."""
    segment_id: str
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float
    audio_features: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

@dataclass
class DiarizationConfig:
    """Configuration for speaker diarization."""
    # Detection settings
    min_segment_duration: float = 1.0  # Minimum segment duration in seconds
    max_speakers: int = 10            # Maximum expected speakers
    silence_threshold: float = 0.5    # Silence detection threshold
    
    # Voice characteristics
    enable_voice_features: bool = True
    pitch_analysis: bool = True
    formant_analysis: bool = False
    
    # Speaker tracking
    speaker_switch_penalty: float = 0.1  # Penalty for frequent speaker switches
    min_speaker_confidence: float = 0.6  # Minimum confidence for speaker assignment
    
    # Labeling
    auto_label_speakers: bool = True
    speaker_label_format: str = "Speaker {}"  # Format for auto-generated labels

class SpeakerDiarizationEngine:
    """
    🎤 Production-grade speaker diarization engine.
    
    Handles speaker identification, separation, and tracking for
    multi-speaker meeting transcription scenarios.
    """
    
    def __init__(self, config: Optional[DiarizationConfig] = None):
        self.config = config or DiarizationConfig()
        
        # Speaker tracking
        self.speakers: Dict[str, SpeakerProfile] = {}  # {speaker_id: profile}
        self.segments: List[SpeakerSegment] = []
        self.speaker_sequence = 0
        
        # Session management
        self.session_speakers: Dict[str, Dict[str, SpeakerProfile]] = {}  # {session_id: {speaker_id: profile}}
        self.session_segments: Dict[str, List[SpeakerSegment]] = {}  # {session_id: [segments]}
        
        # Voice feature tracking
        self.voice_features_history: Dict[str, List[Dict[str, Any]]] = {}  # {speaker_id: [features]}
        
        # Metrics
        self.total_segments_processed = 0
        self.speaker_switches_detected = 0
        self.confidence_improvements = 0
        
        logger.info("🎤 Speaker diarization engine initialized")
    
    def initialize_session(self, session_id: str, expected_speakers: Optional[List[str]] = None):
        """
        Initialize speaker diarization for a session.
        
        Args:
            session_id: Session identifier
            expected_speakers: Optional list of expected speaker names
        """
        if session_id not in self.session_speakers:
            self.session_speakers[session_id] = {}
            self.session_segments[session_id] = []
            
            # Pre-register expected speakers if provided
            if expected_speakers:
                for i, speaker_name in enumerate(expected_speakers):
                    speaker_id = f"{session_id}_speaker_{i:02d}"
                    profile = SpeakerProfile(
                        speaker_id=speaker_id,
                        name=speaker_name,
                        label=speaker_name or self.config.speaker_label_format.format(i + 1)
                    )
                    self.session_speakers[session_id][speaker_id] = profile
            
            logger.info(f"Initialized speaker diarization for session {session_id}")
    
    def process_audio_segment(self, session_id: str, audio_data: bytes, 
                            start_time: float, end_time: float,
                            transcription_text: str = "") -> Dict[str, Any]:
        """
        Process audio segment for speaker identification.
        
        Args:
            session_id: Session identifier
            audio_data: Audio data bytes
            start_time: Segment start time
            end_time: Segment end time
            transcription_text: Transcribed text (if available)
            
        Returns:
            Speaker identification result
        """
        try:
            # Extract voice features from audio
            voice_features = self._extract_voice_features(audio_data)
            
            # Identify speaker based on features
            speaker_identification = self._identify_speaker(
                session_id, voice_features, start_time, end_time
            )
            
            speaker_id = speaker_identification['speaker_id']
            confidence = speaker_identification['confidence']
            
            # Create segment
            segment_id = f"{session_id}_seg_{len(self.session_segments[session_id]):06d}"
            segment = SpeakerSegment(
                segment_id=segment_id,
                speaker_id=speaker_id,
                start_time=start_time,
                end_time=end_time,
                text=transcription_text,
                confidence=confidence,
                audio_features=voice_features
            )
            
            # Add to session segments
            self.session_segments[session_id].append(segment)
            
            # Update speaker profile
            self._update_speaker_profile(session_id, speaker_id, segment, voice_features)
            
            # Check for speaker switches
            speaker_switch = self._detect_speaker_switch(session_id, speaker_id)
            if speaker_switch:
                self.speaker_switches_detected += 1
            
            self.total_segments_processed += 1
            
            result = {
                'segment_id': segment_id,
                'speaker_id': speaker_id,
                'speaker_label': self.session_speakers[session_id][speaker_id].label,
                'speaker_name': self.session_speakers[session_id][speaker_id].name,
                'confidence': confidence,
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'is_speaker_switch': speaker_switch,
                'voice_features': voice_features
            }
            
            logger.debug(f"Processed audio segment: {speaker_id} ({confidence:.3f} confidence)")
            return result
            
        except Exception as e:
            logger.error(f"Speaker diarization failed for segment: {e}")
            return {
                'error': str(e),
                'segment_id': None,
                'speaker_id': 'unknown',
                'confidence': 0.0
            }
    
    def _extract_voice_features(self, audio_data: bytes) -> Dict[str, Any]:
        """🎤 Enhanced enterprise-grade voice feature extraction with real audio analysis."""
        # Convert bytes to numpy array
        try:
            # Assume 16-bit PCM audio
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            if len(audio_array) == 0:
                return {}
            
            features = {}
            sample_rate = 16000  # Standard sample rate
            
            # === ENHANCED ENERGY FEATURES ===
            features['rms_energy'] = float(np.sqrt(np.mean(audio_array ** 2)))
            features['peak_amplitude'] = float(np.max(np.abs(audio_array)))
            features['zero_crossing_rate'] = float(np.sum(np.diff(np.sign(audio_array)) != 0) / len(audio_array))
            
            # Dynamic range
            sorted_abs = np.sort(np.abs(audio_array))
            noise_floor = np.mean(sorted_abs[:len(sorted_abs)//10])  # Bottom 10% as noise
            features['dynamic_range'] = float(features['peak_amplitude'] / (noise_floor + 1e-10))
            
            # === ENHANCED SPECTRAL ANALYSIS ===
            # Apply pre-emphasis filter
            pre_emphasized = np.append(audio_array[0], audio_array[1:] - 0.97 * audio_array[:-1])
            
            # Windowed FFT
            windowed = pre_emphasized * np.hanning(len(pre_emphasized))
            fft = np.fft.rfft(windowed)
            magnitude_spectrum = np.abs(fft)
            power_spectrum = magnitude_spectrum ** 2
            frequencies = np.fft.rfftfreq(len(pre_emphasized), 1.0/sample_rate)
            
            # Spectral centroid
            if np.sum(magnitude_spectrum) > 0:
                features['spectral_centroid'] = float(np.sum(frequencies * magnitude_spectrum) / np.sum(magnitude_spectrum))
            else:
                features['spectral_centroid'] = 0.0
            
            # Spectral rolloff (85% of spectral energy)
            cumulative_energy = np.cumsum(power_spectrum)
            total_energy = cumulative_energy[-1]
            if total_energy > 0:
                rolloff_idx = np.where(cumulative_energy >= 0.85 * total_energy)[0]
                features['spectral_rolloff'] = float(frequencies[rolloff_idx[0]]) if len(rolloff_idx) > 0 else 0.0
            else:
                features['spectral_rolloff'] = 0.0
            
            # Spectral bandwidth
            if np.sum(magnitude_spectrum) > 0:
                centroid = features['spectral_centroid']
                bandwidth = np.sqrt(np.sum(((frequencies - centroid) ** 2) * magnitude_spectrum) / np.sum(magnitude_spectrum))
                features['spectral_bandwidth'] = float(bandwidth)
            else:
                features['spectral_bandwidth'] = 0.0
            
            # === ADVANCED FUNDAMENTAL FREQUENCY ESTIMATION ===
            f0_values = self._estimate_f0_advanced(audio_array, sample_rate)
            if len(f0_values) > 0:
                features['fundamental_frequency'] = float(np.median(f0_values))  # Use median for robustness
                features['f0_variance'] = float(np.var(f0_values))
                features['f0_range'] = float(np.max(f0_values) - np.min(f0_values))
            else:
                features['fundamental_frequency'] = 0.0
                features['f0_variance'] = 0.0
                features['f0_range'] = 0.0
            
            # === FORMANT ANALYSIS ===
            formants = self._estimate_formants_advanced(audio_array, sample_rate)
            features['formant_1'] = float(formants[0]) if len(formants) > 0 else 0.0
            features['formant_2'] = float(formants[1]) if len(formants) > 1 else 0.0
            features['formant_3'] = float(formants[2]) if len(formants) > 2 else 0.0
            
            # Formant ratios (distinctive voice characteristics)
            if features['formant_1'] > 0 and features['formant_2'] > 0:
                features['formant_ratio_f2_f1'] = features['formant_2'] / features['formant_1']
            else:
                features['formant_ratio_f2_f1'] = 0.0
            
            # === TEMPORAL FEATURES ===
            features['speaking_rate_estimate'] = self._estimate_speaking_rate(audio_array, sample_rate)
            features['pause_ratio'] = self._calculate_pause_ratio(audio_array, sample_rate)
            
            # === VOICE QUALITY METRICS ===
            features['harmonic_to_noise_ratio'] = self._calculate_hnr(audio_array, sample_rate)
            features['jitter'] = self._calculate_jitter(f0_values) if len(f0_values) > 1 else 0.0
            features['shimmer'] = self._calculate_shimmer(audio_array, sample_rate)
            
            # === MFCC COEFFICIENTS ===
            mfcc_coeffs = self._extract_mfcc_coefficients(magnitude_spectrum, sample_rate)
            features['mfcc_features'] = mfcc_coeffs[:13]  # First 13 MFCC coefficients
            
            # === LEGACY COMPATIBILITY ===
            features['energy'] = features['rms_energy']
            features['duration'] = len(audio_data) / sample_rate
            features['extracted_at'] = time.time()
            
            # === ENHANCED GENDER ESTIMATION ===
            features['estimated_gender'] = self._estimate_gender_advanced(features)
            
            # === OVERALL VOICE QUALITY SCORE ===
            features['voice_quality_score'] = self._calculate_voice_quality_score(features)
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error extracting enhanced voice features: {e}")
            return {}
    
    def _identify_speaker(self, session_id: str, voice_features: Dict[str, Any],
                         start_time: float, end_time: float) -> Dict[str, Any]:
        """
        Identify speaker based on voice features and session context.
        
        Args:
            session_id: Session identifier
            voice_features: Extracted voice features
            start_time: Segment start time
            end_time: Segment end time
            
        Returns:
            Speaker identification result
        """
        session_speakers = self.session_speakers.get(session_id, {})
        
        if not session_speakers:
            # First speaker in session
            speaker_id = self._create_new_speaker(session_id, voice_features)
            return {'speaker_id': speaker_id, 'confidence': 0.8, 'method': 'new_speaker'}
        
        # Find best matching speaker
        best_match = None
        best_score = 0.0
        
        for speaker_id, profile in session_speakers.items():
            similarity_score = self._calculate_voice_similarity(
                voice_features, profile.voice_characteristics
            )
            
            # Consider temporal factors (speaker switch penalty)
            temporal_factor = self._calculate_temporal_factor(session_id, speaker_id, start_time)
            adjusted_score = similarity_score * temporal_factor
            
            if adjusted_score > best_score and adjusted_score > self.config.min_speaker_confidence:
                best_score = adjusted_score
                best_match = speaker_id
        
        if best_match:
            return {'speaker_id': best_match, 'confidence': best_score, 'method': 'voice_match'}
        else:
            # Create new speaker
            new_speaker_id = self._create_new_speaker(session_id, voice_features)
            return {'speaker_id': new_speaker_id, 'confidence': 0.7, 'method': 'new_speaker_threshold'}
    
    def _calculate_voice_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """🎤 Enhanced voice similarity calculation using advanced features."""
        if not features1 or not features2:
            return 0.0
        
        # Calculate similarity based on multiple features
        similarities = []
        
        # === FUNDAMENTAL FREQUENCY ANALYSIS ===
        if 'fundamental_frequency' in features1 and 'fundamental_frequency' in features2:
            f1, f2 = features1['fundamental_frequency'], features2['fundamental_frequency']
            if f1 > 0 and f2 > 0:
                # Use logarithmic scale for F0 comparison (more perceptually relevant)
                log_f1, log_f2 = np.log(f1), np.log(f2)
                f0_diff = abs(log_f1 - log_f2)
                f0_similarity = max(0.0, 1.0 - f0_diff / 1.5)  # Allow ~4x frequency difference
                similarities.append(f0_similarity * 0.25)  # 25% weight
        
        # === FORMANT ANALYSIS ===
        formant_similarities = []
        for i in range(1, 4):  # F1, F2, F3
            f1_key, f2_key = f'formant_{i}', f'formant_{i}'
            if f1_key in features1 and f2_key in features2:
                f1_val, f2_val = features1[f1_key], features2[f2_key]
                if f1_val > 0 and f2_val > 0:
                    formant_diff = abs(f1_val - f2_val)
                    max_diff = 800 if i == 1 else (1000 if i == 2 else 1200)  # Expected variation
                    formant_sim = max(0.0, 1.0 - formant_diff / max_diff)
                    formant_similarities.append(formant_sim)
        
        if formant_similarities:
            avg_formant_similarity = np.mean(formant_similarities)
            similarities.append(avg_formant_similarity * 0.2)  # 20% weight
        
        # === SPECTRAL FEATURES ===
        spectral_similarities = []
        
        # Spectral centroid
        if 'spectral_centroid' in features1 and 'spectral_centroid' in features2:
            s1, s2 = features1['spectral_centroid'], features2['spectral_centroid']
            if s1 > 0 and s2 > 0:
                centroid_diff = abs(s1 - s2)
                centroid_similarity = max(0.0, 1.0 - centroid_diff / 2000.0)
                spectral_similarities.append(centroid_similarity)
        
        # Spectral rolloff
        if 'spectral_rolloff' in features1 and 'spectral_rolloff' in features2:
            r1, r2 = features1['spectral_rolloff'], features2['spectral_rolloff']
            if r1 > 0 and r2 > 0:
                rolloff_diff = abs(r1 - r2)
                rolloff_similarity = max(0.0, 1.0 - rolloff_diff / 3000.0)
                spectral_similarities.append(rolloff_similarity)
        
        # Spectral bandwidth
        if 'spectral_bandwidth' in features1 and 'spectral_bandwidth' in features2:
            b1, b2 = features1['spectral_bandwidth'], features2['spectral_bandwidth']
            if b1 > 0 and b2 > 0:
                bandwidth_diff = abs(b1 - b2)
                bandwidth_similarity = max(0.0, 1.0 - bandwidth_diff / 1500.0)
                spectral_similarities.append(bandwidth_similarity)
        
        if spectral_similarities:
            avg_spectral_similarity = np.mean(spectral_similarities)
            similarities.append(avg_spectral_similarity * 0.15)  # 15% weight
        
        # === MFCC SIMILARITY (Enhanced) ===
        if 'mfcc_features' in features1 and 'mfcc_features' in features2:
            mfcc1 = np.array(features1['mfcc_features'])
            mfcc2 = np.array(features2['mfcc_features'])
            
            if len(mfcc1) > 0 and len(mfcc2) > 0:
                # Ensure same length
                min_len = min(len(mfcc1), len(mfcc2))
                mfcc1_norm = mfcc1[:min_len]
                mfcc2_norm = mfcc2[:min_len]
                
                # Cosine similarity (more robust than Euclidean)
                dot_product = np.dot(mfcc1_norm, mfcc2_norm)
                norms = np.linalg.norm(mfcc1_norm) * np.linalg.norm(mfcc2_norm)
                
                if norms > 0:
                    cosine_similarity = dot_product / norms
                    # Convert to 0-1 range
                    mfcc_similarity = (cosine_similarity + 1) / 2
                    similarities.append(mfcc_similarity * 0.25)  # 25% weight
        
        # === TEMPORAL CHARACTERISTICS ===
        temporal_similarities = []
        
        # Speaking rate similarity
        if 'speaking_rate_estimate' in features1 and 'speaking_rate_estimate' in features2:
            sr1, sr2 = features1['speaking_rate_estimate'], features2['speaking_rate_estimate']
            if sr1 > 0 and sr2 > 0:
                rate_diff = abs(sr1 - sr2)
                rate_similarity = max(0.0, 1.0 - rate_diff / 100.0)  # 100 WPM difference
                temporal_similarities.append(rate_similarity)
        
        # Pause ratio similarity
        if 'pause_ratio' in features1 and 'pause_ratio' in features2:
            pr1, pr2 = features1['pause_ratio'], features2['pause_ratio']
            pause_diff = abs(pr1 - pr2)
            pause_similarity = max(0.0, 1.0 - pause_diff / 0.5)  # 50% difference
            temporal_similarities.append(pause_similarity)
        
        if temporal_similarities:
            avg_temporal_similarity = np.mean(temporal_similarities)
            similarities.append(avg_temporal_similarity * 0.1)  # 10% weight
        
        # === VOICE QUALITY CONSISTENCY ===
        if 'voice_quality_score' in features1 and 'voice_quality_score' in features2:
            vq1, vq2 = features1['voice_quality_score'], features2['voice_quality_score']
            quality_diff = abs(vq1 - vq2)
            quality_similarity = max(0.0, 1.0 - quality_diff / 0.5)  # 50% quality difference
            similarities.append(quality_similarity * 0.05)  # 5% weight
        
        # === ENHANCED SIMILARITY CALCULATION ===
        if similarities:
            # Weighted average
            total_similarity = sum(similarities)
            
            # Apply confidence boost for high-quality features
            if ('voice_quality_score' in features1 and features1['voice_quality_score'] > 0.7 and
                'voice_quality_score' in features2 and features2['voice_quality_score'] > 0.7):
                total_similarity *= 1.1  # 10% boost for high-quality audio
            
            # Apply gender consistency bonus
            if ('estimated_gender' in features1 and 'estimated_gender' in features2 and
                features1['estimated_gender'] == features2['estimated_gender']):
                total_similarity *= 1.05  # 5% bonus for gender match
            
            return min(1.0, total_similarity)  # Cap at 1.0
        
        return 0.0
    
    def _calculate_temporal_factor(self, session_id: str, speaker_id: str, current_time: float) -> float:
        """
        Calculate temporal factor for speaker continuity.
        
        Penalizes frequent speaker switches.
        """
        segments = self.session_segments.get(session_id, [])
        
        if not segments:
            return 1.0
        
        # Check recent segments for speaker switches
        recent_segments = [s for s in segments if current_time - s.end_time < 10.0]  # Last 10 seconds
        
        if not recent_segments:
            return 1.0
        
        # Count speaker switches in recent history
        last_speaker = recent_segments[-1].speaker_id if recent_segments else None
        
        if last_speaker == speaker_id:
            return 1.0  # Same speaker, no penalty
        else:
            # Apply switch penalty
            return 1.0 - self.config.speaker_switch_penalty
    
    def _create_new_speaker(self, session_id: str, voice_features: Dict[str, Any]) -> str:
        """Create a new speaker profile."""
        speaker_count = len(self.session_speakers.get(session_id, {}))
        speaker_id = f"{session_id}_speaker_{speaker_count:02d}"
        
        # Generate label
        if self.config.auto_label_speakers:
            label = self.config.speaker_label_format.format(speaker_count + 1)
        else:
            label = f"Speaker {speaker_count + 1}"
        
        profile = SpeakerProfile(
            speaker_id=speaker_id,
            label=label,
            voice_characteristics=voice_features.copy()
        )
        
        if session_id not in self.session_speakers:
            self.session_speakers[session_id] = {}
        
        self.session_speakers[session_id][speaker_id] = profile
        
        logger.info(f"Created new speaker: {speaker_id} ({label})")
        return speaker_id
    
    # === 🎤 ENTERPRISE-GRADE VOICE ANALYSIS METHODS ===
    
    def _estimate_f0_advanced(self, audio_array: np.ndarray, sample_rate: int) -> np.ndarray:
        """Advanced F0 estimation using multiple methods."""
        # Method 1: Autocorrelation
        autocorr_f0 = self._f0_autocorrelation(audio_array, sample_rate)
        
        # Method 2: Cepstrum (simplified)
        cepstrum_f0 = self._f0_cepstrum(audio_array, sample_rate)
        
        # Combine methods
        f0_candidates = [f for f in [autocorr_f0, cepstrum_f0] if 50 <= f <= 500]
        
        return np.array(f0_candidates) if f0_candidates else np.array([])
    
    def _f0_autocorrelation(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """F0 estimation using autocorrelation method."""
        # Apply window
        windowed = audio_array * np.hanning(len(audio_array))
        
        # Autocorrelation
        autocorr = np.correlate(windowed, windowed, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        # Search in typical speech range: 50-500 Hz
        min_period = int(sample_rate / 500)
        max_period = int(sample_rate / 50)
        
        if max_period >= len(autocorr):
            return 0.0
        
        search_range = autocorr[min_period:max_period]
        if len(search_range) == 0:
            return 0.0
        
        # Find the highest peak
        peak_idx = np.argmax(search_range) + min_period
        f0 = sample_rate / peak_idx
        
        # Validate result
        return f0 if 50 <= f0 <= 500 else 0.0
    
    def _f0_cepstrum(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """F0 estimation using cepstrum method."""
        # Apply window and compute spectrum
        windowed = audio_array * np.hanning(len(audio_array))
        spectrum = np.abs(np.fft.rfft(windowed))
        
        # Log spectrum (avoid log(0))
        log_spectrum = np.log(spectrum + 1e-10)
        
        # Cepstrum
        cepstrum = np.fft.irfft(log_spectrum)
        
        # Search for peak in quefrency domain
        min_quefrency = int(sample_rate / 500)  # 500 Hz
        max_quefrency = int(sample_rate / 50)   # 50 Hz
        
        if max_quefrency >= len(cepstrum):
            return 0.0
        
        search_cepstrum = cepstrum[min_quefrency:max_quefrency]
        if len(search_cepstrum) == 0:
            return 0.0
        
        peak_idx = np.argmax(search_cepstrum) + min_quefrency
        f0 = sample_rate / peak_idx
        
        return f0 if 50 <= f0 <= 500 else 0.0
    
    def _estimate_formants_advanced(self, audio_array: np.ndarray, sample_rate: int) -> List[float]:
        """Advanced formant estimation using LPC analysis (simplified)."""
        if len(audio_array) < 256:
            return []
        
        # Pre-emphasis
        pre_emphasized = np.append(audio_array[0], audio_array[1:] - 0.97 * audio_array[:-1])
        
        # Window
        windowed = pre_emphasized * np.hanning(len(pre_emphasized))
        
        # Compute power spectrum
        spectrum = np.abs(np.fft.rfft(windowed)) ** 2
        frequencies = np.fft.rfftfreq(len(windowed), 1/sample_rate)
        
        # Find peaks in spectrum (simplified formant detection)
        # Smooth spectrum slightly
        spectrum_smooth = np.convolve(spectrum, np.ones(5)/5, mode='same')
        
        # Find peaks
        if len(spectrum_smooth) > 10:
            peak_indices = []
            min_distance = int(200 / (sample_rate / len(spectrum_smooth)))  # Min 200 Hz apart
            
            for i in range(min_distance, len(spectrum_smooth) - min_distance):
                if (spectrum_smooth[i] > spectrum_smooth[i-min_distance] and 
                    spectrum_smooth[i] > spectrum_smooth[i+min_distance] and
                    spectrum_smooth[i] > np.max(spectrum_smooth) * 0.1):
                    peak_indices.append(i)
            
            if peak_indices:
                # Get formant frequencies
                formant_freqs = frequencies[peak_indices]
                
                # Filter to typical formant ranges
                formants = []
                
                # F1 (first formant): 200-1000 Hz
                f1_candidates = [f for f in formant_freqs if 200 <= f <= 1000]
                if f1_candidates:
                    formants.append(min(f1_candidates))
                
                # F2 (second formant): 800-2500 Hz
                f2_candidates = [f for f in formant_freqs if 800 <= f <= 2500 and (not formants or f > formants[0])]
                if f2_candidates:
                    formants.append(min(f2_candidates))
                
                # F3 (third formant): 1500-4000 Hz
                f3_candidates = [f for f in formant_freqs if 1500 <= f <= 4000 and (len(formants) < 2 or f > formants[-1])]
                if f3_candidates:
                    formants.append(min(f3_candidates))
                
                return formants
        
        return []
    
    def _estimate_speaking_rate(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """Estimate speaking rate based on energy peaks."""
        if len(audio_array) == 0:
            return 0.0
        
        # Frame-based energy analysis
        frame_size = int(0.02 * sample_rate)  # 20ms frames
        hop_size = int(0.01 * sample_rate)    # 10ms hop
        
        energy = []
        for i in range(0, len(audio_array) - frame_size, hop_size):
            frame_energy = np.sum(audio_array[i:i+frame_size] ** 2)
            energy.append(frame_energy)
        
        if len(energy) < 10:
            return 0.0
        
        energy = np.array(energy)
        
        # Find energy peaks (potential syllables)
        threshold = np.mean(energy) + 0.5 * np.std(energy)
        peaks = []
        min_distance = 5  # Min 50ms between peaks
        
        for i in range(min_distance, len(energy) - min_distance):
            if (energy[i] > threshold and
                energy[i] > energy[i-min_distance] and
                energy[i] > energy[i+min_distance]):
                peaks.append(i)
        
        # Convert to speaking rate
        duration_seconds = len(audio_array) / sample_rate
        if duration_seconds > 0:
            syllables_per_second = len(peaks) / duration_seconds
            # Approximate: 1.3 syllables per word, convert to words per minute
            words_per_minute = (syllables_per_second / 1.3) * 60
            return min(words_per_minute, 300.0)  # Cap at reasonable maximum
        
        return 0.0
    
    def _calculate_pause_ratio(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """Calculate ratio of pauses/silence in speech."""
        if len(audio_array) == 0:
            return 1.0
        
        # Energy-based silence detection
        frame_size = int(0.02 * sample_rate)  # 20ms frames
        silence_threshold = 0.01 * np.max(np.abs(audio_array))
        
        silence_frames = 0
        total_frames = 0
        
        for i in range(0, len(audio_array) - frame_size, frame_size):
            frame = audio_array[i:i+frame_size]
            if np.max(np.abs(frame)) < silence_threshold:
                silence_frames += 1
            total_frames += 1
        
        return silence_frames / max(total_frames, 1)
    
    def _calculate_hnr(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """Calculate Harmonic-to-Noise Ratio (simplified)."""
        if len(audio_array) < 512:
            return 0.0
        
        # Compute autocorrelation for periodicity
        autocorr = np.correlate(audio_array, audio_array, mode='full')
        autocorr = autocorr[autocorr.size // 2:]
        
        # Estimate periodic and aperiodic components
        max_autocorr = np.max(autocorr[1:])  # Exclude zero-lag
        noise_floor = np.mean(autocorr[len(autocorr)//2:])  # Tail as noise estimate
        
        if noise_floor > 0:
            hnr = 20 * np.log10(max_autocorr / noise_floor)
            return max(0.0, min(40.0, hnr))  # Cap between 0-40 dB
        
        return 0.0
    
    def _calculate_jitter(self, f0_values: np.ndarray) -> float:
        """Calculate F0 jitter (period-to-period variation)."""
        if len(f0_values) < 2:
            return 0.0
        
        # Convert F0 to periods
        periods = 1.0 / (f0_values + 1e-10)
        
        # Calculate period differences
        period_diffs = np.abs(np.diff(periods))
        
        # Jitter as percentage
        mean_period = np.mean(periods)
        if mean_period > 0:
            jitter_percent = (np.mean(period_diffs) / mean_period) * 100
            return min(jitter_percent, 10.0)  # Cap at 10%
        
        return 0.0
    
    def _calculate_shimmer(self, audio_array: np.ndarray, sample_rate: int) -> float:
        """Calculate amplitude shimmer (simplified)."""
        if len(audio_array) < 512:
            return 0.0
        
        # Frame-based amplitude analysis
        frame_size = int(0.02 * sample_rate)  # 20ms frames
        amplitudes = []
        
        for i in range(0, len(audio_array) - frame_size, frame_size):
            frame_amp = np.max(np.abs(audio_array[i:i+frame_size]))
            amplitudes.append(frame_amp)
        
        if len(amplitudes) < 2:
            return 0.0
        
        amplitudes = np.array(amplitudes)
        
        # Calculate amplitude differences
        amp_diffs = np.abs(np.diff(amplitudes))
        
        # Shimmer as percentage
        mean_amplitude = np.mean(amplitudes)
        if mean_amplitude > 0:
            shimmer_percent = (np.mean(amp_diffs) / mean_amplitude) * 100
            return min(shimmer_percent, 20.0)  # Cap at 20%
        
        return 0.0
    
    def _extract_mfcc_coefficients(self, magnitude_spectrum: np.ndarray, sample_rate: int, n_mfcc: int = 13) -> List[float]:
        """Extract MFCC coefficients (simplified implementation)."""
        if len(magnitude_spectrum) < 10:
            return [0.0] * n_mfcc
        
        # Log power spectrum
        log_power = np.log(magnitude_spectrum ** 2 + 1e-10)
        
        # Simple DCT approximation for MFCC
        mfcc_coeffs = []
        
        for m in range(n_mfcc):
            coeff = 0.0
            for k in range(len(log_power)):
                coeff += log_power[k] * np.cos(np.pi * m * (k + 0.5) / len(log_power))
            mfcc_coeffs.append(coeff)
        
        return mfcc_coeffs
    
    def _estimate_gender_advanced(self, features: Dict[str, Any]) -> str:
        """Advanced gender estimation using multiple features."""
        gender_score = 0.0  # Negative = male, Positive = female
        
        # F0-based estimation (primary factor)
        f0 = features.get('fundamental_frequency', 0)
        if f0 > 0:
            if f0 < 130:
                gender_score -= 2.0  # Strong male indicator
            elif f0 < 165:
                gender_score -= 1.0  # Mild male indicator
            elif f0 > 220:
                gender_score += 2.0  # Strong female indicator
            elif f0 > 180:
                gender_score += 1.0  # Mild female indicator
        
        # Formant-based estimation (secondary factor)
        f1 = features.get('formant_1', 0)
        f2 = features.get('formant_2', 0)
        if f1 > 0 and f2 > 0:
            # Female voices typically have higher formants
            if f1 > 500:  # High F1
                gender_score += 0.5
            if f2 > 2000:  # High F2
                gender_score += 0.5
        
        # Spectral centroid (tertiary factor)
        centroid = features.get('spectral_centroid', 0)
        if centroid > 0:
            if centroid > 2500:  # Higher spectral centroid
                gender_score += 0.3
            elif centroid < 1800:  # Lower spectral centroid
                gender_score -= 0.3
        
        return 'female' if gender_score > 0 else 'male'
    
    def _calculate_voice_quality_score(self, features: Dict[str, Any]) -> float:
        """Calculate overall voice quality score based on features."""
        quality_factors = []
        
        # F0 stability (lower jitter = higher quality)
        jitter = features.get('jitter', 10.0)
        f0_quality = max(0.0, 1.0 - jitter / 5.0)  # Normalize by 5% jitter
        quality_factors.append(f0_quality)
        
        # Amplitude stability (lower shimmer = higher quality)
        shimmer = features.get('shimmer', 20.0)
        amp_quality = max(0.0, 1.0 - shimmer / 10.0)  # Normalize by 10% shimmer
        quality_factors.append(amp_quality)
        
        # Harmonic content (higher HNR = higher quality)
        hnr = features.get('harmonic_to_noise_ratio', 0.0)
        harmonic_quality = min(1.0, hnr / 20.0)  # Normalize by 20 dB HNR
        quality_factors.append(harmonic_quality)
        
        # Dynamic range (reasonable range = higher quality)
        dynamic_range = features.get('dynamic_range', 1.0)
        range_quality = min(1.0, max(0.0, (dynamic_range - 5.0) / 20.0))  # 5-25 range
        quality_factors.append(range_quality)
        
        # Overall quality score
        return float(np.mean(quality_factors)) if quality_factors else 0.0
    
    def _update_speaker_profile(self, session_id: str, speaker_id: str, 
                               segment: SpeakerSegment, voice_features: Dict[str, Any]):
        """Update speaker profile with new segment data."""
        if session_id not in self.session_speakers or speaker_id not in self.session_speakers[session_id]:
            return
        
        profile = self.session_speakers[session_id][speaker_id]
        
        # Update timing
        profile.last_detected = segment.end_time
        profile.total_speaking_time += segment.duration
        profile.segments_count += 1
        profile.confidence_scores.append(segment.confidence)
        
        # Update voice characteristics (running average)
        if profile.voice_characteristics:
            # Update fundamental frequency (running average)
            if 'fundamental_frequency' in voice_features and 'fundamental_frequency' in profile.voice_characteristics:
                old_freq = profile.voice_characteristics['fundamental_frequency']
                new_freq = voice_features['fundamental_frequency']
                profile.voice_characteristics['fundamental_frequency'] = (old_freq + new_freq) / 2
            
            # Update other features similarly
            for feature in ['spectral_centroid', 'spectral_rolloff', 'energy']:
                if feature in voice_features and feature in profile.voice_characteristics:
                    old_value = profile.voice_characteristics[feature]
                    new_value = voice_features[feature]
                    profile.voice_characteristics[feature] = (old_value + new_value) / 2
        else:
            profile.voice_characteristics = voice_features.copy()
    
    def _detect_speaker_switch(self, session_id: str, current_speaker_id: str) -> bool:
        """Detect if there was a speaker switch."""
        segments = self.session_segments.get(session_id, [])
        
        if len(segments) < 2:
            return False
        
        previous_speaker_id = segments[-2].speaker_id
        return previous_speaker_id != current_speaker_id
    
    def label_speaker(self, session_id: str, speaker_id: str, name: str, label: Optional[str] = None):
        """
        Manually label a speaker.
        
        Args:
            session_id: Session identifier
            speaker_id: Speaker identifier
            name: Speaker name
            label: Optional custom label
        """
        if session_id in self.session_speakers and speaker_id in self.session_speakers[session_id]:
            profile = self.session_speakers[session_id][speaker_id]
            profile.name = name
            profile.label = label or name
            
            logger.info(f"Labeled speaker {speaker_id} as '{name}'")
    
    def get_session_timeline(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get chronological timeline of speakers for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of timeline entries with speaker information
        """
        segments = self.session_segments.get(session_id, [])
        speakers = self.session_speakers.get(session_id, {})
        
        timeline = []
        for segment in sorted(segments, key=lambda s: s.start_time):
            speaker = speakers.get(segment.speaker_id)
            
            timeline.append({
                'segment_id': segment.segment_id,
                'speaker_id': segment.speaker_id,
                'speaker_name': speaker.name if speaker else None,
                'speaker_label': speaker.label if speaker else f"Speaker {segment.speaker_id}",
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.duration,
                'text': segment.text,
                'confidence': segment.confidence
            })
        
        return timeline
    
    def get_speaker_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get speaker statistics for a session."""
        speakers = self.session_speakers.get(session_id, {})
        segments = self.session_segments.get(session_id, [])
        
        stats = {
            'total_speakers': len(speakers),
            'total_segments': len(segments),
            'session_duration': max([s.end_time for s in segments]) - min([s.start_time for s in segments]) if segments else 0,
            'speakers': {}
        }
        
        for speaker_id, profile in speakers.items():
            speaker_segments = [s for s in segments if s.speaker_id == speaker_id]
            
            stats['speakers'][speaker_id] = {
                'name': profile.name,
                'label': profile.label,
                'speaking_time': profile.total_speaking_time,
                'segments_count': len(speaker_segments),
                'average_confidence': profile.average_confidence,
                'speaking_percentage': (profile.total_speaking_time / stats['session_duration'] * 100) if stats['session_duration'] > 0 else 0
            }
        
        return stats
    
    def cleanup_session(self, session_id: str):
        """Clean up session data."""
        self.session_speakers.pop(session_id, None)
        self.session_segments.pop(session_id, None)
        
        logger.info(f"Cleaned up speaker diarization data for session {session_id}")

# Global diarization engine
_diarization_engine: Optional[SpeakerDiarizationEngine] = None

def get_diarization_engine() -> Optional[SpeakerDiarizationEngine]:
    """Get the global diarization engine."""
    return _diarization_engine

def initialize_diarization_engine(config: Optional[DiarizationConfig] = None) -> SpeakerDiarizationEngine:
    """Initialize the global diarization engine."""
    global _diarization_engine
    _diarization_engine = SpeakerDiarizationEngine(config)
    return _diarization_engine