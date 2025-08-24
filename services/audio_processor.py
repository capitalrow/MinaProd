"""
Audio Processing Service
Utility functions for audio manipulation, format conversion, and processing.
Consolidates audio processing logic from multiple codebases.
"""

import logging
import numpy as np
from typing import Optional, Tuple, Union
import io
import wave
import struct

logger = logging.getLogger(__name__)

class AudioProcessor:
    """
    Audio processing utilities for format conversion and signal processing.
    """
    
    def __init__(self):
        """Initialize audio processor."""
        self.supported_formats = ['wav', 'webm', 'mp3', 'ogg']
        self.default_sample_rate = 16000
        self.default_channels = 1
        self.default_bit_depth = 16
    
    def convert_to_wav(self, audio_data: bytes, input_format: str = 'webm',
                       sample_rate: int = 16000, channels: int = 1) -> bytes:
        """
        Convert audio data to WAV format.
        
        Args:
            audio_data: Raw audio bytes
            input_format: Input audio format
            sample_rate: Target sample rate
            channels: Number of audio channels
            
        Returns:
            WAV formatted audio bytes
        """
        try:
            if input_format.lower() == 'wav':
                return audio_data
            
            # For WebM/other formats, we'll create a basic WAV wrapper
            # In a real implementation, you'd use ffmpeg or similar
            return self._create_wav_header(audio_data, sample_rate, channels)
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            raise
    
    def _create_wav_header(self, audio_data: bytes, sample_rate: int, channels: int) -> bytes:
        """Create WAV file with proper header."""
        # WAV header parameters
        byte_rate = sample_rate * channels * 2  # 16-bit = 2 bytes per sample
        block_align = channels * 2
        data_size = len(audio_data)
        file_size = 36 + data_size
        
        # Create WAV header
        header = struct.pack(
            '<4sL4s4sLHHLLHH4sL',
            b'RIFF',           # Chunk ID
            file_size,         # Chunk size
            b'WAVE',           # Format
            b'fmt ',           # Subchunk 1 ID
            16,                # Subchunk 1 size (PCM)
            1,                 # Audio format (PCM)
            channels,          # Number of channels
            sample_rate,       # Sample rate
            byte_rate,         # Byte rate
            block_align,       # Block align
            16,                # Bits per sample
            b'data',           # Subchunk 2 ID
            data_size          # Subchunk 2 size
        )
        
        return header + audio_data
    
    def resample_audio(self, audio_data: Union[bytes, np.ndarray], 
                      original_rate: int, target_rate: int) -> np.ndarray:
        """
        Resample audio to target sample rate.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            original_rate: Original sample rate
            target_rate: Target sample rate
            
        Returns:
            Resampled audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if original_rate == target_rate:
                return audio_array
            
            # Simple linear interpolation resampling
            # In production, use scipy.signal.resample or librosa
            ratio = target_rate / original_rate
            new_length = int(len(audio_array) * ratio)
            
            # Create new time indices
            old_indices = np.linspace(0, len(audio_array) - 1, len(audio_array))
            new_indices = np.linspace(0, len(audio_array) - 1, new_length)
            
            # Interpolate
            resampled = np.interp(new_indices, old_indices, audio_array)
            
            return resampled
            
        except Exception as e:
            logger.error(f"Error resampling audio: {e}")
            raise
    
    def normalize_audio(self, audio_data: Union[bytes, np.ndarray]) -> np.ndarray:
        """
        Normalize audio amplitude to [-1, 1] range.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            
        Returns:
            Normalized audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # Find peak amplitude
            peak = np.max(np.abs(audio_array))
            
            if peak > 0:
                # Normalize to 95% to avoid clipping
                audio_array = audio_array * (0.95 / peak)
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            raise
    
    def apply_noise_gate(self, audio_data: Union[bytes, np.ndarray], 
                        threshold: float = 0.01) -> np.ndarray:
        """
        Apply noise gate to suppress low-level noise.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            threshold: Noise gate threshold (0.0 to 1.0)
            
        Returns:
            Processed audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # Apply noise gate
            mask = np.abs(audio_array) > threshold
            audio_array = audio_array * mask
            
            return audio_array
            
        except Exception as e:
            logger.error(f"Error applying noise gate: {e}")
            raise
    
    def chunk_audio(self, audio_data: Union[bytes, np.ndarray], 
                   chunk_duration: float, sample_rate: int = 16000,
                   overlap: float = 0.0) -> list:
        """
        Split audio into chunks of specified duration.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            chunk_duration: Duration of each chunk in seconds
            sample_rate: Audio sample rate
            overlap: Overlap between chunks (0.0 to 1.0)
            
        Returns:
            List of audio chunks as numpy arrays
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            chunk_samples = int(chunk_duration * sample_rate)
            overlap_samples = int(chunk_samples * overlap)
            step_samples = chunk_samples - overlap_samples
            
            chunks = []
            start = 0
            
            while start < len(audio_array):
                end = min(start + chunk_samples, len(audio_array))
                chunk = audio_array[start:end]
                
                # Pad last chunk if necessary
                if len(chunk) < chunk_samples:
                    chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), mode='constant')
                
                chunks.append(chunk)
                start += step_samples
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking audio: {e}")
            raise
    
    def merge_chunks(self, chunks: list, overlap: float = 0.0) -> np.ndarray:
        """
        Merge audio chunks back into continuous audio.
        
        Args:
            chunks: List of audio chunks as numpy arrays
            overlap: Overlap between chunks used during chunking
            
        Returns:
            Merged audio as numpy array
        """
        try:
            if not chunks:
                return np.array([])
            
            if len(chunks) == 1:
                return chunks[0]
            
            chunk_samples = len(chunks[0])
            overlap_samples = int(chunk_samples * overlap)
            step_samples = chunk_samples - overlap_samples
            
            # Calculate total length
            total_samples = (len(chunks) - 1) * step_samples + chunk_samples
            merged = np.zeros(total_samples)
            
            # Merge chunks with overlap handling
            for i, chunk in enumerate(chunks):
                start = i * step_samples
                end = start + len(chunk)
                
                if i == 0:
                    # First chunk - no overlap
                    merged[start:end] = chunk
                else:
                    # Apply fade-in/fade-out for smooth overlap
                    if overlap_samples > 0:
                        # Fade out previous chunk
                        fade_start = start
                        fade_end = start + overlap_samples
                        fade_weights = np.linspace(1, 0, overlap_samples)
                        merged[fade_start:fade_end] *= fade_weights
                        
                        # Fade in current chunk
                        fade_weights = np.linspace(0, 1, overlap_samples)
                        chunk_fade = chunk[:overlap_samples] * fade_weights
                        merged[fade_start:fade_end] += chunk_fade
                        
                        # Add remainder of chunk
                        merged[fade_end:end] = chunk[overlap_samples:]
                    else:
                        merged[start:end] = chunk
            
            return merged
            
        except Exception as e:
            logger.error(f"Error merging audio chunks: {e}")
            raise
    
    def calculate_rms_energy(self, audio_data: Union[bytes, np.ndarray]) -> float:
        """
        Calculate RMS (Root Mean Square) energy of audio signal.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            
        Returns:
            RMS energy value
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if len(audio_array) == 0:
                return 0.0
            
            # Calculate RMS
            rms = np.sqrt(np.mean(audio_array ** 2))
            return float(rms)
            
        except Exception as e:
            logger.error(f"Error calculating RMS energy: {e}")
            return 0.0
    
    def detect_silence(self, audio_data: Union[bytes, np.ndarray], 
                      threshold: float = 0.01, min_duration: float = 0.5,
                      sample_rate: int = 16000) -> list:
        """
        Detect silent regions in audio.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            threshold: Silence threshold (0.0 to 1.0)
            min_duration: Minimum duration for silence detection in seconds
            sample_rate: Audio sample rate
            
        Returns:
            List of (start_time, end_time) tuples for silent regions
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # Calculate frame-based energy
            frame_size = int(0.02 * sample_rate)  # 20ms frames
            frames = self.chunk_audio(audio_array, 0.02, sample_rate)
            
            # Detect silent frames
            silent_frames = []
            for i, frame in enumerate(frames):
                energy = self.calculate_rms_energy(frame)
                silent_frames.append(energy < threshold)
            
            # Find continuous silent regions
            silent_regions = []
            min_frames = int(min_duration / 0.02)  # Convert to frame count
            
            start_frame = None
            for i, is_silent in enumerate(silent_frames):
                if is_silent and start_frame is None:
                    start_frame = i
                elif not is_silent and start_frame is not None:
                    if i - start_frame >= min_frames:
                        start_time = start_frame * 0.02
                        end_time = i * 0.02
                        silent_regions.append((start_time, end_time))
                    start_frame = None
            
            # Handle case where audio ends with silence
            if start_frame is not None and len(silent_frames) - start_frame >= min_frames:
                start_time = start_frame * 0.02
                end_time = len(silent_frames) * 0.02
                silent_regions.append((start_time, end_time))
            
            return silent_regions
            
        except Exception as e:
            logger.error(f"Error detecting silence: {e}")
            return []
    
    def trim_silence(self, audio_data: Union[bytes, np.ndarray], 
                    threshold: float = 0.01) -> np.ndarray:
        """
        Trim leading and trailing silence from audio.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            threshold: Silence threshold (0.0 to 1.0)
            
        Returns:
            Trimmed audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if len(audio_array) == 0:
                return audio_array
            
            # Find first non-silent sample
            start_idx = 0
            for i, sample in enumerate(audio_array):
                if abs(sample) > threshold:
                    start_idx = i
                    break
            
            # Find last non-silent sample
            end_idx = len(audio_array) - 1
            for i in range(len(audio_array) - 1, -1, -1):
                if abs(audio_array[i]) > threshold:
                    end_idx = i + 1
                    break
            
            return audio_array[start_idx:end_idx]
            
        except Exception as e:
            logger.error(f"Error trimming silence: {e}")
            return audio_array if isinstance(audio_data, np.ndarray) else np.array([])
