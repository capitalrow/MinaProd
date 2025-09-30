"""
Enhanced Speech Detection System
Addresses the "No speech detected" issue by improving audio analysis
"""

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False
    import array
import struct
import logging
from typing import Tuple, Dict, Any, Union, List

logger = logging.getLogger(__name__)

class SpeechDetectionEnhancer:
    def __init__(self):
        self.sample_rate = 16000
        self.frame_duration_ms = 30  # 30ms frames
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)
        self.voice_activity_threshold = 0.3
        self.energy_threshold = 0.01
        
    def analyze_audio_for_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Enhanced speech detection analysis
        """
        try:
            analysis = {
                'has_speech': False,
                'confidence': 0.0,
                'energy_level': 0.0,
                'voice_activity': 0.0,
                'audio_quality': 'unknown',
                'duration_ms': 0.0,
                'issues': []
            }
            
            # Convert audio data to samples
            samples = self.extract_audio_samples(audio_data)
            if samples is None or len(samples) == 0:
                analysis['issues'].append('No audio samples extracted')
                return analysis
                
            # Calculate duration
            analysis['duration_ms'] = (len(samples) / self.sample_rate) * 1000
            
            # Energy analysis
            analysis['energy_level'] = self.calculate_energy_level(samples)
            
            # Voice activity detection
            analysis['voice_activity'] = self.detect_voice_activity(samples)
            
            # Speech confidence calculation
            analysis['confidence'] = self.calculate_speech_confidence(
                analysis['energy_level'], 
                analysis['voice_activity']
            )
            
            # Determine if speech is present
            analysis['has_speech'] = (
                analysis['confidence'] > self.voice_activity_threshold and
                analysis['energy_level'] > self.energy_threshold
            )
            
            # Audio quality assessment
            analysis['audio_quality'] = self.assess_audio_quality(samples)
            
            logger.info(f"🔍 Speech Analysis: {analysis['confidence']:.2f} confidence, "
                       f"{analysis['energy_level']:.3f} energy, speech: {analysis['has_speech']}")
                       
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Speech detection analysis error: {e}")
            return {
                'has_speech': False,
                'confidence': 0.0,
                'energy_level': 0.0,
                'voice_activity': 0.0,
                'audio_quality': 'error',
                'duration_ms': 0.0,
                'issues': [str(e)]
            }
    
    def extract_audio_samples(self, audio_data: bytes) -> Union[List[float], None]:
        """
        Extract audio samples from various formats
        """
        try:
            # Try WAV format first
            if self.is_wav_format(audio_data):
                return self.extract_wav_samples(audio_data)
            
            # Try raw 16-bit PCM
            return self.extract_raw_samples(audio_data)
            
        except Exception as e:
            logger.error(f"❌ Sample extraction error: {e}")
            return None
    
    def is_wav_format(self, audio_data: bytes) -> bool:
        """Check if data has WAV header"""
        return (len(audio_data) >= 12 and 
                audio_data[:4] == b'RIFF' and 
                audio_data[8:12] == b'WAVE')
    
    def extract_wav_samples(self, audio_data: bytes) -> Union[List[float], None]:
        """Extract samples from WAV data"""
        try:
            # Skip WAV header (44 bytes)
            audio_samples = audio_data[44:]
            
            if NUMPY_AVAILABLE and np is not None:
                # Convert to 16-bit integers
                samples = np.frombuffer(audio_samples, dtype=np.int16)
                # Normalize to [-1, 1] and convert to list
                normalized = samples.astype(np.float32) / 32768.0
                return normalized.tolist()
            else:
                # Fallback without numpy
                samples = []
                for i in range(0, len(audio_samples) - 1, 2):
                    sample = struct.unpack('<h', audio_samples[i:i+2])[0]
                    samples.append(sample / 32768.0)
                return samples
            
        except Exception as e:
            logger.error(f"❌ WAV extraction error: {e}")
            return None
    
    def extract_raw_samples(self, audio_data: bytes) -> Union[List[float], None]:
        """Extract samples treating data as raw 16-bit PCM"""
        try:
            # Skip potential headers by finding audio-like content
            start_offset = self.find_audio_data_offset(audio_data)
            audio_samples = audio_data[start_offset:]
            
            # Ensure even number of bytes
            if len(audio_samples) % 2 != 0:
                audio_samples = audio_samples[:-1]
            
            # Convert to 16-bit integers
            samples = np.frombuffer(audio_samples, dtype=np.int16)
            
            # Normalize to [-1, 1]
            return samples.astype(np.float32) / 32768.0
            
        except Exception as e:
            logger.error(f"❌ Raw extraction error: {e}")
            return None
    
    def find_audio_data_offset(self, audio_data: bytes) -> int:
        """Find where actual audio data starts"""
        # Look for high-entropy regions that suggest audio content
        chunk_size = 1000
        best_offset = 0
        max_variance = 0
        
        for offset in range(0, min(len(audio_data) - chunk_size, 5000), 100):
            chunk = audio_data[offset:offset + chunk_size]
            if len(chunk) >= chunk_size:
                # Calculate variance as a measure of audio-like content
                try:
                    samples = np.frombuffer(chunk, dtype=np.uint8)
                    variance = np.var(samples)
                    if variance > max_variance:
                        max_variance = variance
                        best_offset = offset
                except:
                    continue
        
        return best_offset
    
    def calculate_energy_level(self, samples: np.ndarray) -> float:
        """Calculate RMS energy level"""
        try:
            rms = np.sqrt(np.mean(samples ** 2))
            return float(rms)
        except Exception:
            return 0.0
    
    def detect_voice_activity(self, samples: np.ndarray) -> float:
        """Detect voice activity using frame-based analysis"""
        try:
            if len(samples) < self.frame_size:
                return 0.0
            
            # Split into frames
            num_frames = len(samples) // self.frame_size
            frames = samples[:num_frames * self.frame_size].reshape(num_frames, self.frame_size)
            
            voice_frames = 0
            total_frames = num_frames
            
            for frame in frames:
                # Calculate frame energy
                frame_energy = np.sqrt(np.mean(frame ** 2))
                
                # Calculate zero crossing rate
                zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
                
                # Voice activity criteria
                if frame_energy > 0.01 and 0.01 < zcr < 0.3:
                    voice_frames += 1
            
            return voice_frames / total_frames if total_frames > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Voice activity detection error: {e}")
            return 0.0
    
    def calculate_speech_confidence(self, energy: float, voice_activity: float) -> float:
        """Calculate overall speech confidence score"""
        try:
            # Weighted combination of energy and voice activity
            energy_score = min(1.0, energy * 10)  # Scale energy
            voice_score = voice_activity
            
            # Combine scores with weights
            confidence = (energy_score * 0.6) + (voice_score * 0.4)
            
            return min(1.0, max(0.0, confidence))
            
        except Exception:
            return 0.0
    
    def assess_audio_quality(self, samples: np.ndarray) -> str:
        """Assess overall audio quality"""
        try:
            if len(samples) == 0:
                return 'empty'
            
            # Calculate quality metrics
            rms = np.sqrt(np.mean(samples ** 2))
            dynamic_range = np.max(samples) - np.min(samples)
            
            if rms < 0.001:
                return 'too_quiet'
            elif rms > 0.8:
                return 'too_loud'
            elif dynamic_range < 0.1:
                return 'low_dynamic_range'
            else:
                return 'acceptable'
                
        except Exception:
            return 'error'

# Global speech detector instance
speech_detector = SpeechDetectionEnhancer()

def enhanced_speech_detection(audio_data: bytes) -> Dict[str, Any]:
    """
    Enhanced speech detection wrapper function
    """
    return speech_detector.analyze_audio_for_speech(audio_data)

def should_process_audio(audio_data: bytes, min_confidence: float = 0.2) -> Tuple[bool, Dict[str, Any]]:
    """
    Determine if audio should be sent to transcription service
    """
    analysis = enhanced_speech_detection(audio_data)
    should_process = (
        analysis['has_speech'] or 
        analysis['confidence'] > min_confidence or
        analysis['energy_level'] > 0.005  # Lower threshold for quiet speech
    )
    
    return should_process, analysis