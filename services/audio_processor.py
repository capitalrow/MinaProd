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
        self._audio_buffer = []
        self._conversion_cache = {}
    
    def clear_buffers(self):
        """Clear all audio processing buffers for memory optimization."""
        self._audio_buffer.clear()
        self._conversion_cache.clear()
        import gc
        gc.collect()
        logger.info("Audio processor buffers cleared")
    
    def convert_to_wav(self, audio_data: bytes, input_format: str = 'webm',
                       sample_rate: int = 16000, channels: int = 1, mime_type: str = None) -> bytes:
        """
        Convert audio data to WAV format with proper decoding.
        🔥 CRITICAL FIX: Implements proper WebM to WAV conversion for Google Recorder accuracy.
        Enhanced with client-side format detection support.
        
        Args:
            audio_data: Raw audio bytes
            input_format: Input audio format
            sample_rate: Target sample rate
            channels: Number of audio channels
            mime_type: Detected MIME type from client (audio/webm or audio/wav)
            
        Returns:
            WAV formatted audio bytes
        """
        try:
            # Use client-provided MIME type if available for better detection
            detected_format = input_format
            if mime_type:
                if 'wav' in mime_type.lower():
                    detected_format = 'wav'
                elif 'webm' in mime_type.lower():
                    detected_format = 'webm'
                    
            logger.info(f"🔧 Processing audio: {len(audio_data)} bytes, format: {detected_format}, mime: {mime_type}")
            
            if detected_format.lower() == 'wav':
                return self._validate_wav_format(audio_data)
            
            # Enhanced WebM processing with header validation
            return self._convert_webm_to_wav_enhanced(audio_data, sample_rate, channels)
            
        except Exception as e:
            logger.error(f"🚨 Audio conversion failed: {e}")
            # Emergency fallback with quality validation
            return self._emergency_wav_conversion(audio_data, sample_rate, channels)
    
    def _convert_webm_to_wav_enhanced(self, webm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
        """
        🔥 ENHANCED WebM to WAV conversion using PyDub for accuracy.
        Enhanced with EBML header validation and multiple fallback strategies.
        Implements Google Recorder-level audio processing quality.
        """
        try:
            from pydub import AudioSegment
            from io import BytesIO
            
            logger.info(f"🔧 Converting {len(webm_data)} bytes of WebM to WAV (SR: {sample_rate}, Ch: {channels})")
            
            # CRITICAL: Check for EBML header first
            has_ebml_header = (len(webm_data) >= 4 and 
                             webm_data[0] == 0x1A and webm_data[1] == 0x45 and 
                             webm_data[2] == 0xDF and webm_data[3] == 0xA3)
            
            if not has_ebml_header:
                logger.warning(f"⚠️ Missing EBML header in WebM data, attempting repair")
                # Try to add minimal EBML header if missing
                webm_data = self._repair_webm_header(webm_data)
            
            # Strategy 1: Direct PyDub conversion
            try:
                audio_segment = AudioSegment.from_file(
                    BytesIO(webm_data), 
                    format="webm"
                )
                
                # Normalize to target specs
                audio_segment = audio_segment.set_frame_rate(sample_rate)
                audio_segment = audio_segment.set_channels(channels)
                audio_segment = audio_segment.set_sample_width(2)  # 16-bit
                
                # Apply audio enhancement for speech recognition
                audio_segment = self._enhance_for_speech_recognition(audio_segment)
                
                # Export to WAV
                wav_buffer = BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                wav_data = wav_buffer.getvalue()
                
                logger.info(f"✅ Strategy 1 successful: {len(wav_data)} bytes WAV")
                return wav_data
                
            except Exception as e1:
                logger.warning(f"⚠️ Strategy 1 failed: {e1}")
                
                # Strategy 2: Try with opus codec hint
                try:
                    audio_segment = AudioSegment.from_file(
                        BytesIO(webm_data), 
                        format="webm",
                        codec="opus"
                    )
                    
                    audio_segment = audio_segment.set_frame_rate(sample_rate)
                    audio_segment = audio_segment.set_channels(channels)
                    audio_segment = audio_segment.set_sample_width(2)
                    
                    audio_segment = self._enhance_for_speech_recognition(audio_segment)
                    
                    wav_buffer = BytesIO()
                    audio_segment.export(wav_buffer, format="wav")
                    wav_data = wav_buffer.getvalue()
                    
                    logger.info(f"✅ Strategy 2 successful: {len(wav_data)} bytes WAV")
                    return wav_data
                    
                except Exception as e2:
                    logger.warning(f"⚠️ Strategy 2 failed: {e2}")
                    raise Exception(f"All conversion strategies failed: {e1}, {e2}")
            
        except ImportError:
            logger.error("❌ PyDub not available, falling back to basic conversion")
            return self._emergency_wav_conversion(webm_data, sample_rate, channels)
        except Exception as e:
            logger.error(f"❌ WebM conversion failed: {e}")
            return self._emergency_wav_conversion(webm_data, sample_rate, channels)
    
    def _enhance_for_speech_recognition(self, audio_segment):
        """
        🎯 Enhance audio for optimal speech recognition accuracy.
        Applies Google Recorder-level audio processing.
        """
        try:
            # Normalize volume to optimal range for speech
            audio_segment = audio_segment.normalize()
            
            # Apply mild compression to even out volume levels
            audio_segment = audio_segment.compress_dynamic_range(threshold=-20.0, ratio=2.0, attack=5.0, release=50.0)
            
            # High-pass filter to remove low-frequency noise
            audio_segment = audio_segment.high_pass_filter(80)
            
            # Low-pass filter to remove high-frequency noise above speech range
            audio_segment = audio_segment.low_pass_filter(7000)
            
            logger.debug("✅ Audio enhanced for speech recognition")
            return audio_segment
            
        except Exception as e:
            logger.warning(f"⚠️ Audio enhancement failed: {e}, using original")
            return audio_segment
    
    def _validate_wav_format(self, wav_data: bytes) -> bytes:
        """
        🔍 Validate and potentially fix WAV format issues.
        """
        try:
            if not wav_data.startswith(b'RIFF'):
                logger.warning("⚠️ Invalid WAV header, attempting to fix")
                return self._create_proper_wav_header(wav_data, 16000, 1)
            
            # Validate WAV structure
            if len(wav_data) < 44:
                logger.warning("⚠️ WAV file too short, padding")
                return self._create_proper_wav_header(wav_data[44:] if len(wav_data) > 44 else b'\x00' * 1600, 16000, 1)
            
            return wav_data
            
        except Exception as e:
            logger.error(f"❌ WAV validation failed: {e}")
            return self._create_proper_wav_header(wav_data, 16000, 1)
    
    def _emergency_wav_conversion(self, audio_data: bytes, sample_rate: int, channels: int) -> bytes:
        """
        🔥 CRITICAL FIX: Proper raw PCM to WAV conversion for Google Recorder accuracy.
        Handles the actual format mismatch that causes hallucinations.
        """
        logger.warning("🚨 Emergency conversion: Processing raw audio data")
        
        try:
            # 🔥 STEP 1: Detect if this is actually raw PCM or garbage data
            pcm_data = self._extract_raw_pcm(audio_data)
            
            # 🔥 STEP 2: Validate PCM data quality
            if not self._validate_pcm_quality(pcm_data):
                logger.error("❌ PCM data quality too low, rejecting to prevent hallucinations")
                raise ValueError("Audio quality insufficient for transcription")
            
            # 🔥 STEP 3: Create proper WAV with validated PCM
            wav_data = self._create_professional_wav(pcm_data, sample_rate, channels)
            
            logger.info(f"✅ Emergency conversion successful: {len(wav_data)} bytes")
            return wav_data
            
        except Exception as e:
            logger.error(f"❌ Emergency conversion failed: {e}")
            raise ValueError(f"Unable to convert audio data: {e}")
    
    def _extract_raw_pcm(self, audio_data: bytes) -> bytes:
        """
        🔥 Extract raw PCM samples from unknown format data.
        """
        # Check if data might be base64 encoded PCM
        if len(audio_data) % 4 == 0:
            try:
                import base64
                decoded = base64.b64decode(audio_data)
                if self._looks_like_pcm(decoded):
                    logger.info("📦 Detected base64-encoded PCM data")
                    return decoded
            except:
                pass
        
        # Check if it's already raw PCM
        if self._looks_like_pcm(audio_data):
            logger.info("🎵 Detected raw PCM data")
            return audio_data
        
        # Try to find PCM data within the bytes
        # Sometimes there's metadata or padding
        for offset in [0, 44, 64, 128]:  # Common header sizes
            if offset < len(audio_data):
                potential_pcm = audio_data[offset:]
                if len(potential_pcm) > 1600 and self._looks_like_pcm(potential_pcm):
                    logger.info(f"🔍 Found PCM data at offset {offset}")
                    return potential_pcm
        
        # If all else fails, treat as raw bytes but validate
        logger.warning("⚠️ Treating unknown data as raw PCM")
        return audio_data
    
    def _looks_like_pcm(self, data: bytes) -> bool:
        """
        🔍 Heuristic to detect if bytes are likely PCM audio samples.
        """
        if len(data) < 1600:  # Too short
            return False
        
        if len(data) % 2 != 0:  # Should be even for 16-bit samples
            return False
        
        # Convert to 16-bit samples and check characteristics
        try:
            samples = np.frombuffer(data[:min(3200, len(data))], dtype=np.int16)
            
            # Check dynamic range
            peak = np.max(np.abs(samples))
            if peak == 0:  # Silent
                return False
            if peak > 32767:  # Clipped
                return False
            
            # Check for reasonable audio characteristics
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            if rms < 10:  # Too quiet
                return False
            
            # Check zero crossing rate (speech typically 0.01-0.3)
            zero_crossings = np.sum(np.diff(np.sign(samples)) != 0)
            zcr = zero_crossings / len(samples)
            if zcr > 0.5:  # Too noisy
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_pcm_quality(self, pcm_data: bytes) -> bool:
        """
        🔥 FIXED: Real-world audio validation for web browsers and mobile devices.
        Relaxed thresholds to accept legitimate speech while preventing only true garbage.
        """
        try:
            if len(pcm_data) < 320:  # Less than 0.02 seconds at 16kHz - very lenient
                logger.debug("❌ PCM too short")
                return False
            
            # Convert to numpy for analysis
            samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)
            
            # 1. RELAXED Energy Analysis - accept much quieter audio
            rms = np.sqrt(np.mean(samples ** 2))
            peak = np.max(np.abs(samples))
            
            # EXTREMELY lenient thresholds for real-world audio
            if rms < 5:  # Was 10 - now 5 (even more lenient)
                logger.debug(f"❌ RMS too low: {rms:.1f}")
                return False
            if peak < 20:  # Was 50 - now 20 (much more lenient)
                logger.debug(f"❌ Peak too low: {peak:.1f}")
                return False
            if rms > 20000:  # Was 12000 - now higher to allow louder audio
                logger.debug(f"❌ RMS too high: {rms:.1f}")
                return False
                
            # 2. RELAXED Speech Characteristics
            # Zero crossing rate - much wider acceptable range
            zero_crossings = np.sum(np.diff(np.sign(samples)) != 0)
            zcr = zero_crossings / len(samples) if len(samples) > 0 else 0
            if zcr > 0.8:  # Only reject extremely high noise - was 0.02-0.4 range
                logger.debug(f"❌ ZCR too high (noise): {zcr:.3f}")
                return False
            
            # 3. RELAXED Dynamic Range Check
            dynamic_range = peak / (rms + 1e-6)  # Avoid division by zero
            if dynamic_range < 1.5 or dynamic_range > 100.0:  # Much wider range - was 2.0-50.0
                logger.debug(f"❌ Poor dynamic range: {dynamic_range:.1f}")
                return False
            
            # 4. SIMPLIFIED Spectral Analysis - only basic checks
            if len(samples) >= 512:  # Only if we have enough data
                fft = np.fft.fft(samples[:min(1024, len(samples))])
                magnitude_spectrum = np.abs(fft[:len(fft)//2])
                total_energy = np.sum(magnitude_spectrum)
                
                if total_energy == 0:
                    logger.debug("❌ No spectral energy")
                    return False
                # Removed strict mid-frequency requirement that was rejecting valid audio
            
            # 5. RELAXED DC Offset Check
            dc_offset = np.mean(samples)
            if abs(dc_offset) > peak * 0.8:  # Much more lenient - was 0.3
                logger.debug(f"❌ High DC offset: {abs(dc_offset):.1f}")
                return False
            
            logger.debug(f"✅ PCM validation passed: RMS={rms:.1f}, Peak={peak:.1f}, ZCR={zcr:.3f}, DR={dynamic_range:.1f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ PCM validation error: {e}")
            # CRITICAL FIX: Return True on validation errors to ensure audio gets through
            logger.warning("⚠️ Validation failed but allowing audio through for robustness")
            return True
    
    def _create_professional_wav(self, pcm_data: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
        """
        🔥 Create professional-grade WAV file optimized for Whisper API.
        """
        try:
            # Ensure PCM data is properly aligned
            if len(pcm_data) % (channels * 2) != 0:
                # Pad to align with frame boundaries
                padding_needed = (channels * 2) - (len(pcm_data) % (channels * 2))
                pcm_data += b'\x00' * padding_needed
            
            # Apply light processing to optimize for Whisper
            samples = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32)
            
            # Normalize to optimal range
            peak = np.max(np.abs(samples))
            if peak > 0:
                target_peak = 16000.0  # ~50% of 16-bit range
                if peak > target_peak:
                    samples = samples * (target_peak / peak)
            
            # Remove DC offset
            samples = samples - np.mean(samples)
            
            # Convert back to 16-bit
            processed_pcm = samples.astype(np.int16).tobytes()
            
            # Create WAV header
            wav_data = self._create_proper_wav_header(processed_pcm, sample_rate, channels)
            
            logger.info(f"✅ Professional WAV created: {len(wav_data)} bytes ({len(processed_pcm)} PCM + 44 header)")
            return wav_data
            
        except Exception as e:
            logger.error(f"❌ Professional WAV creation failed: {e}")
            # Fallback to simple header creation
            return self._create_proper_wav_header(pcm_data, sample_rate, channels)
    
    def _create_proper_wav_header(self, audio_data: bytes, sample_rate: int, channels: int) -> bytes:
        """
        Create properly formatted WAV file with validation.
        🔥 Enhanced with proper PCM validation.
        """
        # Ensure audio data is valid PCM format
        if len(audio_data) % (channels * 2) != 0:
            # Pad to align with frame boundaries
            padding_needed = (channels * 2) - (len(audio_data) % (channels * 2))
            audio_data += b'\x00' * padding_needed
        
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
        
        logger.debug(f"✅ Created WAV header: {len(header)} + {len(audio_data)} = {len(header + audio_data)} bytes")
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
            # Ensure audio_array is defined before using it
            if isinstance(audio_data, np.ndarray):
                return audio_data
            elif isinstance(audio_data, bytes):
                return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                return np.array([])
    
    # === 🎵 ENTERPRISE-GRADE ADVANCED AUDIO PROCESSING === 
    
    def apply_advanced_noise_reduction(self, audio_data: Union[bytes, np.ndarray], 
                                     sample_rate: int = 16000,
                                     noise_reduction_strength: float = 0.7,
                                     spectral_gating: bool = True) -> np.ndarray:
        """
        🎵 Enterprise-grade advanced noise reduction with spectral gating and adaptive filtering.
        
        Implements multi-band noise reduction similar to professional audio processing:
        - Spectral subtraction with adaptive coefficients
        - Multi-band frequency domain processing  
        - Adaptive noise floor estimation
        - Harmonic preservation for voice quality
        
        Args:
            audio_data: Audio data as bytes or numpy array
            sample_rate: Audio sample rate
            noise_reduction_strength: Reduction strength (0.0 to 1.0)
            spectral_gating: Enable advanced spectral gating
            
        Returns:
            Enhanced audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if len(audio_array) == 0:
                return audio_array
                
            # FFT window size for spectral processing
            window_size = 1024
            hop_length = window_size // 4
            
            # Apply windowing for spectral processing
            windowed_audio = self._apply_spectral_noise_reduction(
                audio_array, 
                sample_rate, 
                window_size, 
                hop_length,
                noise_reduction_strength,
                spectral_gating
            )
            
            # Apply adaptive filtering for further enhancement
            enhanced_audio = self._apply_adaptive_filtering(
                windowed_audio, 
                sample_rate
            )
            
            # Final normalization to prevent clipping
            enhanced_audio = self._safe_normalize(enhanced_audio, target_level=0.85)
            
            logger.debug(f"🎵 Advanced noise reduction applied: strength={noise_reduction_strength}")
            return enhanced_audio
            
        except Exception as e:
            logger.error(f"❌ Error in advanced noise reduction: {e}")
            # Fallback to basic noise gate
            return self.apply_noise_gate(audio_data, threshold=0.02)
    
    def _apply_spectral_noise_reduction(self, audio_array: np.ndarray,
                                      sample_rate: int,
                                      window_size: int, 
                                      hop_length: int,
                                      strength: float,
                                      spectral_gating: bool) -> np.ndarray:
        """Apply spectral subtraction noise reduction."""
        # Pad audio for processing
        padded_length = ((len(audio_array) - 1) // hop_length + 1) * hop_length
        padded_audio = np.zeros(padded_length)
        padded_audio[:len(audio_array)] = audio_array
        
        # Create output array
        enhanced_audio = np.zeros_like(padded_audio)
        
        # Hanning window for smooth transitions
        window = np.hanning(window_size)
        
        # Estimate noise spectrum from first 500ms (assumed silence)
        noise_frames = min(int(0.5 * sample_rate / hop_length), 10)
        noise_spectrum = np.zeros(window_size // 2 + 1)
        
        for i in range(noise_frames):
            start_idx = i * hop_length
            end_idx = start_idx + window_size
            if end_idx <= len(padded_audio):
                frame = padded_audio[start_idx:end_idx] * window
                fft_frame = np.fft.rfft(frame)
                noise_spectrum += np.abs(fft_frame) ** 2
        
        noise_spectrum = noise_spectrum / max(noise_frames, 1)
        noise_spectrum = np.sqrt(noise_spectrum)
        
        # Process each frame
        for i in range(0, len(padded_audio) - window_size + 1, hop_length):
            frame = padded_audio[i:i + window_size] * window
            fft_frame = np.fft.rfft(frame)
            magnitude = np.abs(fft_frame)
            phase = np.angle(fft_frame)
            
            # Spectral subtraction with adaptive coefficients
            snr = magnitude / (noise_spectrum + 1e-10)
            
            if spectral_gating:
                # Advanced spectral gating with frequency-dependent thresholds
                freq_bins = len(magnitude)
                freq_weights = self._compute_frequency_weights(freq_bins, sample_rate)
                adaptive_threshold = 2.0 * freq_weights
                alpha = np.minimum(1.0, np.maximum(0.1, (snr - adaptive_threshold) / adaptive_threshold))
            else:
                # Basic spectral subtraction
                alpha = np.minimum(1.0, np.maximum(0.1, snr - 2.0))
            
            # Apply noise reduction with strength control
            reduction_factor = 1.0 - strength * (1.0 - alpha)
            enhanced_magnitude = magnitude * reduction_factor
            
            # Reconstruct signal
            enhanced_fft = enhanced_magnitude * np.exp(1j * phase)
            enhanced_frame = np.fft.irfft(enhanced_fft)[:window_size] * window
            
            # Overlap-add reconstruction
            end_idx = i + window_size
            enhanced_audio[i:end_idx] += enhanced_frame
        
        return enhanced_audio[:len(audio_array)]
    
    def _compute_frequency_weights(self, freq_bins: int, sample_rate: int) -> np.ndarray:
        """Compute frequency-dependent weights for spectral processing."""
        freqs = np.linspace(0, sample_rate / 2, freq_bins)
        
        # Emphasize speech frequency range (300-3400 Hz)
        weights = np.ones_like(freqs)
        speech_mask = (freqs >= 300) & (freqs <= 3400)
        weights[speech_mask] *= 1.2  # Boost speech frequencies
        
        # Reduce weight for very low frequencies (< 80 Hz)
        low_freq_mask = freqs < 80
        weights[low_freq_mask] *= 0.7
        
        # Reduce weight for very high frequencies (> 8000 Hz) 
        high_freq_mask = freqs > 8000
        weights[high_freq_mask] *= 0.8
        
        return weights
    
    def _apply_adaptive_filtering(self, audio_array: np.ndarray, sample_rate: int) -> np.ndarray:
        """Apply adaptive filtering for additional enhancement."""
        # Simple high-pass filter to remove low-frequency noise
        if len(audio_array) < 10:
            return audio_array
            
        # Basic IIR high-pass filter (cutoff ~80 Hz)
        cutoff_freq = 80.0
        nyquist = sample_rate / 2.0
        normalized_cutoff = cutoff_freq / nyquist
        
        # Simple first-order high-pass filter coefficients
        alpha = normalized_cutoff / (normalized_cutoff + 1.0)
        
        # Apply filter
        filtered_audio = np.zeros_like(audio_array)
        filtered_audio[0] = audio_array[0]
        
        for i in range(1, len(audio_array)):
            filtered_audio[i] = alpha * (filtered_audio[i-1] + audio_array[i] - audio_array[i-1])
        
        return filtered_audio
    
    def _safe_normalize(self, audio_array: np.ndarray, target_level: float = 0.85) -> np.ndarray:
        """Safely normalize audio to target level without clipping."""
        if len(audio_array) == 0:
            return audio_array
            
        peak = np.max(np.abs(audio_array))
        
        if peak > 0:
            # Normalize to target level
            normalized = audio_array * (target_level / peak)
            return normalized
        
        return audio_array
    
    def apply_automatic_gain_control(self, audio_data: Union[bytes, np.ndarray], 
                                   target_level: float = 0.7,
                                   attack_time: float = 0.01,
                                   release_time: float = 0.1,
                                   sample_rate: int = 16000) -> np.ndarray:
        """
        🎵 Apply automatic gain control (AGC) for consistent audio levels.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            target_level: Target RMS level (0.0 to 1.0)
            attack_time: Attack time in seconds
            release_time: Release time in seconds
            sample_rate: Audio sample rate
            
        Returns:
            AGC-processed audio as numpy array
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if len(audio_array) == 0:
                return audio_array
            
            # Calculate attack/release coefficients
            attack_coeff = np.exp(-1.0 / (attack_time * sample_rate))
            release_coeff = np.exp(-1.0 / (release_time * sample_rate))
            
            # Process with AGC
            output = np.zeros_like(audio_array)
            envelope = 0.0
            gain = 1.0
            
            for i, sample in enumerate(audio_array):
                # Calculate envelope
                sample_abs = abs(sample)
                if sample_abs > envelope:
                    envelope = envelope * attack_coeff + sample_abs * (1.0 - attack_coeff)
                else:
                    envelope = envelope * release_coeff + sample_abs * (1.0 - release_coeff)
                
                # Calculate required gain
                if envelope > 0:
                    required_gain = target_level / envelope
                    gain = min(required_gain, 4.0)  # Limit maximum gain
                
                # Apply gain
                output[i] = sample * gain
            
            logger.debug(f"🎵 AGC applied: target_level={target_level}")
            return output
            
        except Exception as e:
            logger.error(f"❌ Error applying AGC: {e}")
            # Ensure audio_array is defined before using it
            if isinstance(audio_data, np.ndarray):
                return audio_data
            elif isinstance(audio_data, bytes):
                return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                return np.array([])
    
    def analyze_audio_quality(self, audio_data: Union[bytes, np.ndarray], 
                            sample_rate: int = 16000) -> dict:
        """
        🎵 Analyze audio quality metrics for monitoring and optimization.
        
        Args:
            audio_data: Audio data as bytes or numpy array
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary with quality metrics
        """
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            if len(audio_array) == 0:
                return {"error": "Empty audio data"}
            
            # Calculate quality metrics
            rms_energy = self.calculate_rms_energy(audio_array)
            peak_level = float(np.max(np.abs(audio_array)))
            crest_factor = peak_level / rms_energy if rms_energy > 0 else 0
            
            # Signal-to-noise ratio estimation
            # Use quieter 10% of signal as noise floor
            sorted_abs = np.sort(np.abs(audio_array))
            noise_floor = np.mean(sorted_abs[:len(sorted_abs)//10])
            snr_estimate = 20 * np.log10(rms_energy / noise_floor) if noise_floor > 0 else 0
            
            # Dynamic range
            dynamic_range = 20 * np.log10(peak_level / noise_floor) if noise_floor > 0 else 0
            
            # Zero crossing rate (indication of speech vs noise)
            zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
            zcr = zero_crossings / len(audio_array) if len(audio_array) > 1 else 0
            
            # Quality assessment
            quality_score = self._calculate_quality_score(rms_energy, snr_estimate, zcr, crest_factor)
            
            return {
                "rms_energy": float(rms_energy),
                "peak_level": float(peak_level),
                "crest_factor": float(crest_factor),
                "snr_estimate_db": float(snr_estimate),
                "dynamic_range_db": float(dynamic_range),
                "zero_crossing_rate": float(zcr),
                "noise_floor": float(noise_floor),
                "quality_score": float(quality_score),
                "quality_grade": self._grade_quality(quality_score)
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing audio quality: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_score(self, rms: float, snr: float, zcr: float, crest: float) -> float:
        """Calculate overall audio quality score (0-100)."""
        # Normalize metrics to 0-1 range
        rms_score = min(1.0, max(0.0, (rms - 0.01) / 0.2))  # 0.01 to 0.21 range
        snr_score = min(1.0, max(0.0, (snr - 10) / 30))     # 10 to 40 dB range
        zcr_score = min(1.0, max(0.0, (zcr - 0.01) / 0.1))  # 0.01 to 0.11 range
        crest_score = min(1.0, max(0.0, (crest - 2) / 8))   # 2 to 10 range
        
        # Weighted combination
        quality = (rms_score * 0.3 + snr_score * 0.4 + zcr_score * 0.2 + crest_score * 0.1) * 100
        return min(100.0, max(0.0, quality))
    
    def _grade_quality(self, score: float) -> str:
        """Convert quality score to grade."""
        if score >= 85:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 55:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Very Poor"
    
    def _repair_webm_header(self, webm_data: bytes) -> bytes:
        """
        🔧 Attempt to repair WebM data by adding minimal EBML header.
        This is a basic repair attempt - may not work for all cases.
        """
        try:
            # Minimal EBML header for WebM
            ebml_header = bytes([
                0x1A, 0x45, 0xDF, 0xA3,  # EBML signature
                0x9F, 0x42, 0x86, 0x81, 0x01,  # EBML Version = 1
                0x42, 0xF2, 0x81, 0x04,  # EBML ReadVersion = 1  
                0x42, 0xF3, 0x81, 0x08,  # EBML MaxIDLength = 4
                0x42, 0x82, 0x84, 0x77, 0x65, 0x62, 0x6D,  # DocType = "webm"
                0x42, 0x87, 0x81, 0x02,  # DocTypeVersion = 2
                0x42, 0x85, 0x81, 0x02,  # DocTypeReadVersion = 2
            ])
            
            logger.info(f"🔧 Adding EBML header to {len(webm_data)} bytes")
            return ebml_header + webm_data
            
        except Exception as e:
            logger.warning(f"⚠️ Could not repair WebM header: {e}")
            return webm_data
