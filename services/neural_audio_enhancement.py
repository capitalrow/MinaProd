# services/neural_audio_enhancement.py
"""
Neural Audio Enhancement Pipeline
Advanced audio processing with acoustic scene analysis, voice fingerprinting,
emotion detection, and neural enhancement algorithms.
"""

import logging
import time
import threading
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from scipy import signal
import json

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    
try:
    import webrtcvad
    WEBRTC_VAD_AVAILABLE = True
except ImportError:
    WEBRTC_VAD_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class AudioFeatures:
    """Advanced audio feature representation"""
    mfcc: np.ndarray = field(default_factory=lambda: np.array([]))
    spectral_centroid: float = 0.0
    spectral_bandwidth: float = 0.0
    spectral_rolloff: float = 0.0
    zero_crossing_rate: float = 0.0
    rms_energy: float = 0.0
    tempo: float = 0.0
    pitch_mean: float = 0.0
    pitch_std: float = 0.0
    harmonics: np.ndarray = field(default_factory=lambda: np.array([]))
    formants: List[float] = field(default_factory=list)
    voice_activity: float = 0.0
    emotion_features: Dict[str, float] = field(default_factory=dict)
    
    def to_vector(self) -> np.ndarray:
        """Convert features to flat vector"""
        vector_parts = [
            self.mfcc.flatten() if self.mfcc.size > 0 else np.zeros(13),
            np.array([
                self.spectral_centroid,
                self.spectral_bandwidth, 
                self.spectral_rolloff,
                self.zero_crossing_rate,
                self.rms_energy,
                self.tempo,
                self.pitch_mean,
                self.pitch_std,
                self.voice_activity
            ])
        ]
        
        if self.harmonics.size > 0:
            vector_parts.append(self.harmonics[:5])  # Take first 5 harmonics
        else:
            vector_parts.append(np.zeros(5))
            
        return np.concatenate(vector_parts)

@dataclass
class VoiceProfile:
    """Speaker voice profile for identification"""
    speaker_id: str
    features: List[AudioFeatures] = field(default_factory=list)
    avg_pitch: float = 0.0
    pitch_range: Tuple[float, float] = (0.0, 0.0)
    formant_pattern: List[float] = field(default_factory=list)
    speaking_rate: float = 0.0
    voice_quality: Dict[str, float] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    confidence: float = 0.0
    
    def update_profile(self, features: AudioFeatures):
        """Update voice profile with new features"""
        self.features.append(features)
        
        # Keep only recent features (sliding window)
        if len(self.features) > 50:
            self.features = self.features[-50:]
        
        # Update statistical measures
        if len(self.features) >= 3:
            self._calculate_averages()
            self.confidence = min(1.0, len(self.features) / 20.0)
        
        self.last_updated = time.time()
    
    def _calculate_averages(self):
        """Calculate average characteristics"""
        pitches = [f.pitch_mean for f in self.features if f.pitch_mean > 0]
        if pitches:
            self.avg_pitch = np.mean(pitches)
            self.pitch_range = (np.min(pitches), np.max(pitches))
        
        # Calculate average formants
        all_formants = [f.formants for f in self.features if f.formants]
        if all_formants and len(all_formants[0]) > 0:
            max_formants = max(len(f) for f in all_formants)
            formant_matrix = np.zeros((len(all_formants), max_formants))
            
            for i, formants in enumerate(all_formants):
                formant_matrix[i, :len(formants)] = formants
            
            self.formant_pattern = np.mean(formant_matrix, axis=0).tolist()
    
    def similarity(self, other_features: AudioFeatures) -> float:
        """Calculate similarity to given features"""
        if not self.features:
            return 0.0
        
        # Compare with recent profile features
        recent_features = self.features[-10:]
        similarities = []
        
        for profile_feature in recent_features:
            # Pitch similarity
            if other_features.pitch_mean > 0 and profile_feature.pitch_mean > 0:
                pitch_sim = 1.0 - abs(other_features.pitch_mean - profile_feature.pitch_mean) / max(other_features.pitch_mean, profile_feature.pitch_mean)
                similarities.append(pitch_sim * 0.4)
            
            # Spectral similarity
            if other_features.spectral_centroid > 0 and profile_feature.spectral_centroid > 0:
                spectral_sim = 1.0 - abs(other_features.spectral_centroid - profile_feature.spectral_centroid) / max(other_features.spectral_centroid, profile_feature.spectral_centroid)
                similarities.append(spectral_sim * 0.3)
            
            # MFCC similarity
            if other_features.mfcc.size > 0 and profile_feature.mfcc.size > 0:
                mfcc_sim = np.corrcoef(other_features.mfcc.flatten(), profile_feature.mfcc.flatten())[0, 1]
                if not np.isnan(mfcc_sim):
                    similarities.append(abs(mfcc_sim) * 0.3)
        
        return np.mean(similarities) if similarities else 0.0

class AcousticSceneAnalyzer:
    """Analyze acoustic environment and scene characteristics"""
    
    def __init__(self):
        self.noise_profile = None
        self.scene_history = deque(maxlen=100)
        self.environment_type = "unknown"
        
    def analyze_scene(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Analyze acoustic scene characteristics"""
        try:
            if not LIBROSA_AVAILABLE:
                return self._basic_scene_analysis(audio, sample_rate)
            
            # Advanced acoustic analysis
            scene_info = {
                'timestamp': time.time(),
                'noise_level': self._estimate_noise_level(audio),
                'reverberation': self._estimate_reverberation(audio, sample_rate),
                'environment_type': self._classify_environment(audio, sample_rate),
                'acoustic_complexity': self._calculate_complexity(audio),
                'dynamic_range': self._calculate_dynamic_range(audio),
                'spectral_density': self._analyze_spectral_density(audio, sample_rate)
            }
            
            self.scene_history.append(scene_info)
            self._update_environment_classification()
            
            return scene_info
            
        except Exception as e:
            logger.warning(f"⚠️ Scene analysis failed: {e}")
            return self._basic_scene_analysis(audio, sample_rate)
    
    def _basic_scene_analysis(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """Basic scene analysis without advanced libraries"""
        energy = np.mean(audio ** 2)
        dynamic_range = np.max(audio) - np.min(audio)
        
        return {
            'timestamp': time.time(),
            'noise_level': float(energy),
            'reverberation': 0.0,
            'environment_type': 'unknown',
            'acoustic_complexity': float(dynamic_range),
            'dynamic_range': float(dynamic_range),
            'spectral_density': {}
        }
    
    def _estimate_noise_level(self, audio: np.ndarray) -> float:
        """Estimate background noise level"""
        # Use quieter segments to estimate noise
        frame_size = 512
        frames = [audio[i:i+frame_size] for i in range(0, len(audio)-frame_size, frame_size)]
        frame_energies = [np.mean(frame**2) for frame in frames]
        
        # Assume bottom 30% represents noise
        noise_frames = sorted(frame_energies)[:int(len(frame_energies) * 0.3)]
        return float(np.mean(noise_frames)) if noise_frames else 0.0
    
    def _estimate_reverberation(self, audio: np.ndarray, sample_rate: int) -> float:
        """Estimate reverberation time (RT60 approximation)"""
        try:
            # Simple energy decay analysis
            frame_size = int(sample_rate * 0.1)  # 100ms frames
            frames = [audio[i:i+frame_size] for i in range(0, len(audio)-frame_size, frame_size)]
            
            energy_decay = [np.mean(frame**2) for frame in frames]
            if len(energy_decay) < 3:
                return 0.0
            
            # Look for exponential decay pattern
            decay_rate = 0.0
            for i in range(1, len(energy_decay)):
                if energy_decay[i] > 0 and energy_decay[i-1] > 0:
                    decay_rate += np.log(energy_decay[i] / energy_decay[i-1])
            
            return abs(decay_rate / len(energy_decay)) if len(energy_decay) > 1 else 0.0
            
        except Exception:
            return 0.0
    
    def _classify_environment(self, audio: np.ndarray, sample_rate: int) -> str:
        """Classify acoustic environment type"""
        try:
            # Simple classification based on spectral characteristics
            fft = np.fft.fft(audio)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            magnitude = np.abs(fft)
            
            # Analyze frequency distribution
            low_freq = np.sum(magnitude[(freqs >= 0) & (freqs < 500)])
            mid_freq = np.sum(magnitude[(freqs >= 500) & (freqs < 2000)])
            high_freq = np.sum(magnitude[(freqs >= 2000) & (freqs < 8000)])
            
            total_energy = low_freq + mid_freq + high_freq
            if total_energy == 0:
                return "quiet"
            
            low_ratio = low_freq / total_energy
            high_ratio = high_freq / total_energy
            
            if low_ratio > 0.6:
                return "indoor"
            elif high_ratio > 0.4:
                return "outdoor"
            else:
                return "office"
                
        except Exception:
            return "unknown"
    
    def _calculate_complexity(self, audio: np.ndarray) -> float:
        """Calculate acoustic complexity"""
        try:
            # Use spectral entropy as complexity measure
            fft = np.fft.fft(audio)
            magnitude = np.abs(fft)
            magnitude = magnitude / np.sum(magnitude)  # Normalize
            
            # Calculate entropy
            entropy = -np.sum(magnitude * np.log2(magnitude + 1e-10))
            return float(entropy / np.log2(len(magnitude)))  # Normalize
            
        except Exception:
            return 0.0
    
    def _calculate_dynamic_range(self, audio: np.ndarray) -> float:
        """Calculate dynamic range of audio"""
        if len(audio) == 0:
            return 0.0
        
        rms = np.sqrt(np.mean(audio**2))
        peak = np.max(np.abs(audio))
        
        if rms > 0:
            return float(20 * np.log10(peak / rms))
        return 0.0
    
    def _analyze_spectral_density(self, audio: np.ndarray, sample_rate: int) -> Dict[str, float]:
        """Analyze spectral power density"""
        try:
            freqs, psd = signal.welch(audio, sample_rate, nperseg=1024)
            
            # Define frequency bands
            bands = {
                'sub_bass': (20, 60),
                'bass': (60, 250),
                'low_mid': (250, 500),
                'mid': (500, 2000),
                'high_mid': (2000, 4000),
                'high': (4000, 8000)
            }
            
            band_powers = {}
            for band_name, (low, high) in bands.items():
                mask = (freqs >= low) & (freqs <= high)
                band_powers[band_name] = float(np.sum(psd[mask]))
            
            return band_powers
            
        except Exception:
            return {}
    
    def _update_environment_classification(self):
        """Update overall environment classification based on history"""
        if len(self.scene_history) < 5:
            return
        
        recent_scenes = list(self.scene_history)[-10:]
        env_types = [scene['environment_type'] for scene in recent_scenes]
        
        # Most common environment type
        env_counts = defaultdict(int)
        for env_type in env_types:
            env_counts[env_type] += 1
        
        if env_counts:
            self.environment_type = max(env_counts.items(), key=lambda x: x[1])[0]

class VoiceFingerprinting:
    """Advanced voice fingerprinting and speaker identification"""
    
    def __init__(self):
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self.feature_cache = {}
        self.lock = threading.Lock()
        
    def extract_voice_features(self, audio: np.ndarray, sample_rate: int = 16000) -> AudioFeatures:
        """Extract comprehensive voice features"""
        try:
            features = AudioFeatures()
            
            if LIBROSA_AVAILABLE:
                features = self._extract_advanced_features(audio, sample_rate)
            else:
                features = self._extract_basic_features(audio, sample_rate)
            
            return features
            
        except Exception as e:
            logger.warning(f"⚠️ Feature extraction failed: {e}")
            return AudioFeatures()
    
    def _extract_advanced_features(self, audio: np.ndarray, sample_rate: int) -> AudioFeatures:
        """Extract advanced audio features using librosa"""
        features = AudioFeatures()
        
        # MFCC features
        features.mfcc = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)
        features.spectral_centroid = float(np.mean(spectral_centroids))
        
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sample_rate)
        features.spectral_bandwidth = float(np.mean(spectral_bandwidth))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sample_rate)
        features.spectral_rolloff = float(np.mean(spectral_rolloff))
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        features.zero_crossing_rate = float(np.mean(zcr))
        
        # RMS energy
        rms = librosa.feature.rms(y=audio)
        features.rms_energy = float(np.mean(rms))
        
        # Tempo
        tempo, _ = librosa.beat.beat_track(y=audio, sr=sample_rate)
        features.tempo = float(tempo)
        
        # Pitch features
        f0 = librosa.yin(audio, fmin=50, fmax=400, sr=sample_rate)
        f0_clean = f0[f0 > 0]  # Remove unvoiced frames
        if len(f0_clean) > 0:
            features.pitch_mean = float(np.mean(f0_clean))
            features.pitch_std = float(np.std(f0_clean))
        
        # Harmonic analysis
        harmonic, percussive = librosa.effects.hpss(audio)
        if len(harmonic) > 0:
            features.harmonics = np.abs(np.fft.fft(harmonic))[:10]  # First 10 harmonics
        
        # Voice activity detection
        features.voice_activity = self._calculate_voice_activity(audio, sample_rate)
        
        return features
    
    def _extract_basic_features(self, audio: np.ndarray, sample_rate: int) -> AudioFeatures:
        """Extract basic audio features without advanced libraries"""
        features = AudioFeatures()
        
        # Basic energy and spectral features
        features.rms_energy = float(np.sqrt(np.mean(audio**2)))
        
        # Zero crossing rate
        zero_crossings = np.where(np.diff(np.sign(audio)))[0]
        features.zero_crossing_rate = float(len(zero_crossings) / len(audio))
        
        # Basic spectral analysis
        fft = np.fft.fft(audio)
        freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
        magnitude = np.abs(fft)
        
        # Spectral centroid (basic)
        if np.sum(magnitude) > 0:
            features.spectral_centroid = float(np.sum(freqs[:len(freqs)//2] * magnitude[:len(magnitude)//2]) / np.sum(magnitude[:len(magnitude)//2]))
        
        # Voice activity (energy-based)
        features.voice_activity = self._calculate_voice_activity_basic(audio)
        
        return features
    
    def _calculate_voice_activity(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate voice activity using advanced methods"""
        if WEBRTC_VAD_AVAILABLE:
            try:
                vad = webrtcvad.Vad(2)  # Aggressiveness level 2
                
                # Process in 30ms frames
                frame_duration = 30  # ms
                frame_size = int(sample_rate * frame_duration / 1000)
                
                voiced_frames = 0
                total_frames = 0
                
                for i in range(0, len(audio) - frame_size, frame_size):
                    frame = audio[i:i + frame_size]
                    
                    # Convert to 16-bit PCM
                    frame_bytes = (frame * 32767).astype(np.int16).tobytes()
                    
                    if vad.is_speech(frame_bytes, sample_rate):
                        voiced_frames += 1
                    total_frames += 1
                
                return float(voiced_frames / max(total_frames, 1))
                
            except Exception:
                pass
        
        return self._calculate_voice_activity_basic(audio)
    
    def _calculate_voice_activity_basic(self, audio: np.ndarray) -> float:
        """Basic voice activity detection using energy"""
        # Simple energy-based VAD
        frame_size = 512
        frames = [audio[i:i+frame_size] for i in range(0, len(audio)-frame_size, frame_size)]
        frame_energies = [np.mean(frame**2) for frame in frames]
        
        if not frame_energies:
            return 0.0
        
        # Threshold-based detection
        threshold = np.mean(frame_energies) * 0.1
        voiced_frames = sum(1 for energy in frame_energies if energy > threshold)
        
        return float(voiced_frames / len(frame_energies))
    
    def identify_speaker(self, features: AudioFeatures) -> Tuple[Optional[str], float]:
        """Identify speaker based on voice features"""
        with self.lock:
            if not self.voice_profiles:
                return None, 0.0
            
            best_match = None
            best_similarity = 0.0
            
            for speaker_id, profile in self.voice_profiles.items():
                similarity = profile.similarity(features)
                
                if similarity > best_similarity and similarity > 0.5:  # Minimum threshold
                    best_similarity = similarity
                    best_match = speaker_id
            
            return best_match, best_similarity
    
    def register_speaker(self, speaker_id: str, features: AudioFeatures) -> VoiceProfile:
        """Register or update speaker profile"""
        with self.lock:
            if speaker_id not in self.voice_profiles:
                self.voice_profiles[speaker_id] = VoiceProfile(speaker_id=speaker_id)
            
            profile = self.voice_profiles[speaker_id]
            profile.update_profile(features)
            
            logger.info(f"🎤 Updated voice profile for speaker {speaker_id} (confidence: {profile.confidence:.2f})")
            return profile
    
    def get_speaker_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all speaker profiles summary"""
        with self.lock:
            profiles_summary = {}
            
            for speaker_id, profile in self.voice_profiles.items():
                profiles_summary[speaker_id] = {
                    'avg_pitch': profile.avg_pitch,
                    'pitch_range': profile.pitch_range,
                    'confidence': profile.confidence,
                    'last_updated': profile.last_updated,
                    'sample_count': len(profile.features)
                }
            
            return profiles_summary

class EmotionDetector:
    """Detect emotions from audio characteristics"""
    
    def __init__(self):
        self.emotion_models = self._initialize_emotion_models()
        
    def _initialize_emotion_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize simple emotion detection models"""
        return {
            'happy': {
                'pitch_range': (150, 300),
                'pitch_variation_high': True,
                'energy_high': True,
                'spectral_brightness': 'high'
            },
            'sad': {
                'pitch_range': (80, 150),
                'pitch_variation_low': True,
                'energy_low': True,
                'spectral_brightness': 'low'
            },
            'angry': {
                'pitch_range': (100, 250),
                'pitch_variation_high': True,
                'energy_high': True,
                'harsh_harmonics': True
            },
            'calm': {
                'pitch_range': (100, 200),
                'pitch_variation_low': True,
                'energy_medium': True,
                'spectral_balance': True
            }
        }
    
    def detect_emotion(self, features: AudioFeatures) -> Dict[str, float]:
        """Detect emotions from audio features"""
        emotions = {}
        
        try:
            # Analyze acoustic characteristics
            pitch = features.pitch_mean
            pitch_variation = features.pitch_std
            energy = features.rms_energy
            spectral_centroid = features.spectral_centroid
            
            # Happy detection
            if pitch > 150 and pitch_variation > 20 and energy > 0.1:
                emotions['happy'] = min(1.0, (pitch - 150) / 150 + pitch_variation / 50 + energy * 2)
            
            # Sad detection  
            if pitch < 150 and pitch_variation < 15 and energy < 0.05:
                emotions['sad'] = min(1.0, (150 - pitch) / 100 + (15 - pitch_variation) / 15 + (0.05 - energy) * 10)
            
            # Angry detection
            if pitch_variation > 30 and energy > 0.15:
                emotions['angry'] = min(1.0, pitch_variation / 50 + energy * 3)
            
            # Calm detection
            if 100 <= pitch <= 200 and pitch_variation < 20 and 0.02 <= energy <= 0.1:
                emotions['calm'] = min(1.0, 1.0 - abs(pitch - 150) / 150 + (20 - pitch_variation) / 20)
            
            # Normalize emotions
            total_emotion = sum(emotions.values())
            if total_emotion > 0:
                emotions = {k: v / total_emotion for k, v in emotions.items()}
            
            return emotions
            
        except Exception as e:
            logger.warning(f"⚠️ Emotion detection failed: {e}")
            return {}

class NeuralAudioEnhancer:
    """Main neural audio enhancement pipeline"""
    
    def __init__(self):
        self.scene_analyzer = AcousticSceneAnalyzer()
        self.voice_fingerprinting = VoiceFingerprinting()
        self.emotion_detector = EmotionDetector()
        self.enhancement_history = deque(maxlen=1000)
        
        logger.info("🧠 Neural Audio Enhancer initialized with advanced capabilities")
    
    def process_audio(self, audio: np.ndarray, sample_rate: int = 16000, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process audio through neural enhancement pipeline"""
        try:
            start_time = time.time()
            
            # Extract voice features
            voice_features = self.voice_fingerprinting.extract_voice_features(audio, sample_rate)
            
            # Analyze acoustic scene
            scene_info = self.scene_analyzer.analyze_scene(audio, sample_rate)
            
            # Detect emotions
            emotions = self.emotion_detector.detect_emotion(voice_features)
            
            # Speaker identification
            speaker_id, speaker_confidence = self.voice_fingerprinting.identify_speaker(voice_features)
            
            # If no speaker identified, create new profile
            if speaker_id is None and speaker_confidence < 0.5:
                speaker_id = f"speaker_{len(self.voice_fingerprinting.voice_profiles) + 1}"
                self.voice_fingerprinting.register_speaker(speaker_id, voice_features)
                speaker_confidence = 0.7  # New speaker
            elif speaker_id:
                # Update existing profile
                self.voice_fingerprinting.register_speaker(speaker_id, voice_features)
            
            # Compile enhancement results
            enhancement_result = {
                'timestamp': time.time(),
                'session_id': session_id,
                'processing_time_ms': (time.time() - start_time) * 1000,
                'voice_features': {
                    'pitch_mean': voice_features.pitch_mean,
                    'pitch_std': voice_features.pitch_std,
                    'spectral_centroid': voice_features.spectral_centroid,
                    'spectral_bandwidth': voice_features.spectral_bandwidth,
                    'voice_activity': voice_features.voice_activity,
                    'rms_energy': voice_features.rms_energy
                },
                'speaker_identification': {
                    'speaker_id': speaker_id,
                    'confidence': speaker_confidence,
                    'is_new_speaker': speaker_confidence == 0.7
                },
                'acoustic_scene': scene_info,
                'emotions': emotions,
                'enhancement_quality': self._calculate_enhancement_quality(voice_features, scene_info)
            }
            
            # Store in history
            self.enhancement_history.append(enhancement_result)
            
            logger.debug(f"🎯 Audio enhanced: speaker={speaker_id}, emotions={list(emotions.keys())}, scene={scene_info.get('environment_type')}")
            
            return enhancement_result
            
        except Exception as e:
            logger.error(f"❌ Neural enhancement failed: {e}")
            return {
                'timestamp': time.time(),
                'session_id': session_id,
                'error': str(e)
            }
    
    def _calculate_enhancement_quality(self, voice_features: AudioFeatures, scene_info: Dict[str, Any]) -> float:
        """Calculate overall enhancement quality score"""
        quality_factors = []
        
        # Voice activity quality
        if voice_features.voice_activity > 0.5:
            quality_factors.append(voice_features.voice_activity)
        
        # Signal-to-noise ratio estimate
        noise_level = scene_info.get('noise_level', 0.5)
        if noise_level < 0.1:  # Low noise is good
            quality_factors.append(0.9)
        elif noise_level < 0.3:
            quality_factors.append(0.7)
        else:
            quality_factors.append(0.4)
        
        # Feature extraction success
        if voice_features.pitch_mean > 0:
            quality_factors.append(0.8)
        
        if voice_features.spectral_centroid > 0:
            quality_factors.append(0.7)
        
        return float(np.mean(quality_factors)) if quality_factors else 0.0
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session enhancement summary"""
        session_enhancements = [e for e in self.enhancement_history if e.get('session_id') == session_id]
        
        if not session_enhancements:
            return {}
        
        # Aggregate statistics
        speakers = set()
        all_emotions = defaultdict(list)
        quality_scores = []
        environments = []
        
        for enhancement in session_enhancements:
            if enhancement.get('speaker_identification', {}).get('speaker_id'):
                speakers.add(enhancement['speaker_identification']['speaker_id'])
            
            for emotion, score in enhancement.get('emotions', {}).items():
                all_emotions[emotion].append(score)
            
            quality_scores.append(enhancement.get('enhancement_quality', 0))
            
            env_type = enhancement.get('acoustic_scene', {}).get('environment_type')
            if env_type:
                environments.append(env_type)
        
        # Calculate summary statistics
        emotion_summary = {}
        for emotion, scores in all_emotions.items():
            emotion_summary[emotion] = {
                'mean': float(np.mean(scores)),
                'max': float(np.max(scores)),
                'frequency': len(scores)
            }
        
        # Most common environment
        env_counts = defaultdict(int)
        for env in environments:
            env_counts[env] += 1
        dominant_environment = max(env_counts.items(), key=lambda x: x[1])[0] if env_counts else "unknown"
        
        return {
            'session_id': session_id,
            'total_enhancements': len(session_enhancements),
            'unique_speakers': len(speakers),
            'speaker_list': list(speakers),
            'avg_quality': float(np.mean(quality_scores)) if quality_scores else 0.0,
            'emotion_profile': emotion_summary,
            'dominant_environment': dominant_environment,
            'speaker_profiles': self.voice_fingerprinting.get_speaker_profiles()
        }

# Global enhancer instance
_neural_enhancer = None
_enhancer_lock = threading.Lock()

def get_neural_audio_enhancer() -> NeuralAudioEnhancer:
    """Get global neural audio enhancer instance"""
    global _neural_enhancer
    
    with _enhancer_lock:
        if _neural_enhancer is None:
            _neural_enhancer = NeuralAudioEnhancer()
        return _neural_enhancer

logger.info("✅ Neural Audio Enhancement module initialized")