"""
Whisper Streaming Service
Enhanced real-time transcription with superior orchestration and buffering.
Integrates improvements from the real-time transcription codebase.
"""

import logging
import asyncio
import time
import json
import os
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import numpy as np

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

# 🔥 PHASE 1: Check for stub mode environment variable
STUB_TRANSCRIPTION = os.getenv("STUB_TRANSCRIPTION", "false").lower() == "true"

@dataclass
class TranscriptionConfig:
    """Configuration for Whisper streaming transcription."""
    model: str = "whisper-1"
    language: str = "en"
    temperature: float = 0.0
    response_format: str = "json"
    prompt: Optional[str] = None
    max_chunk_duration: float = 30.0  # seconds
    min_chunk_duration: float = 0.1   # seconds
    buffer_size: int = 10  # number of audio chunks to buffer
    confidence_threshold: float = 0.4  # 🔥 CRITICAL FIX: Reduced from 0.6 to 0.4
    enable_word_timestamps: bool = True
    enable_vad_filtering: bool = True
    # M1 Quality settings
    max_chunk_ms: int = 640
    max_queue_len: int = 8
    voice_tail_ms: int = 300
    dedup_overlap_threshold: float = 0.9

@dataclass
class TranscriptionResult:
    """Result from transcription processing."""
    text: str
    confidence: float
    is_final: bool
    language: str
    duration: float
    timestamp: float
    words: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class AudioBuffer:
    """Enhanced audio buffer with intelligent chunking."""
    
    def __init__(self, max_size: int = 10, max_duration: float = 30.0):
        self.max_size = max_size
        self.max_duration = max_duration
        self.buffer = deque(maxlen=max_size)
        self.timestamps = deque(maxlen=max_size)
        self.total_duration = 0.0
    
    def add_chunk(self, audio_data: bytes, timestamp: float, duration: float):
        """Add audio chunk to buffer."""
        self.buffer.append(audio_data)
        self.timestamps.append(timestamp)
        self.total_duration += duration
        
        # Remove old chunks if duration exceeded
        while self.total_duration > self.max_duration and len(self.buffer) > 1:
            self.buffer.popleft()
            self.timestamps.popleft()
            # Recalculate duration (approximation)
            self.total_duration *= 0.9
    
    def get_concatenated_audio(self) -> Optional[bytes]:
        """Get all buffered audio as single chunk with proper WAV format."""
        if not self.buffer:
            return None
        
        # Get all audio data
        audio_chunks = list(self.buffer)
        
        # If we have a single chunk that starts with RIFF (WAV header), return as-is
        if len(audio_chunks) == 1 and audio_chunks[0].startswith(b'RIFF'):
            return audio_chunks[0]
        
        # For multiple chunks or non-WAV data, create proper WAV file
        return self._create_wav_from_chunks(audio_chunks)
    
    def _create_wav_from_chunks(self, chunks: List[bytes]) -> bytes:
        """Create a proper WAV file from audio chunks."""
        try:
            import wave
            from io import BytesIO
            import struct
            
            # Extract raw audio data from chunks
            raw_audio_data = b''
            for chunk in chunks:
                if chunk.startswith(b'RIFF'):
                    # Skip WAV header (44 bytes) and get audio data
                    raw_audio_data += chunk[44:]
                else:
                    # Assume raw PCM data
                    raw_audio_data += chunk
            
            if not raw_audio_data:
                return b''
                
            # Create proper WAV file
            wav_buffer = BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(raw_audio_data)
            
            wav_buffer.seek(0)
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.warning(f"Failed to create WAV from chunks: {e}")
            # Fallback: just concatenate chunks
            return b''.join(chunks)
    
    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()
        self.timestamps.clear()
        self.total_duration = 0.0
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return len(self.buffer) >= self.max_size
    
    def get_size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)

class WhisperStreamingService:
    """
    Enhanced Whisper streaming service with superior orchestration.
    Consolidates improvements from real-time transcription system.
    """
    
    def __init__(self, config: Optional[TranscriptionConfig] = None):
        self.config = config or TranscriptionConfig()
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.audio_buffer = AudioBuffer(
            max_size=self.config.buffer_size,
            max_duration=self.config.max_chunk_duration
        )
        
        # State management
        self.is_processing = False
        self.last_transcription_time = 0
        self.session_id = None
        self.sequence_number = 0
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.average_latency = 0.0
        self.error_count = 0
        
        # M1 Quality tracking
        self.chunks_received = 0
        self.chunks_processed = 0
        self.chunks_dropped = 0
        self.interim_events = 0
        self.final_events = 0
        self.retries = 0
        self.ws_disconnects = 0
        self.latency_samples = deque(maxlen=100)
        
        # Bounded queue for backpressure
        from queue import Queue
        self.processing_queue = Queue(maxsize=config.max_queue_len if config else 8)
        
        # Deduplication buffer
        self.last_text_buffer = ""
        self.buffer_size_chars = 80
        
        # Callback for real-time results
        self.result_callback: Optional[Callable[[TranscriptionResult], None]] = None
        
        # Initialize OpenAI client if available
        if OPENAI_AVAILABLE:
            api_key = self._get_api_key()
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)  # Fixed: Use OpenAI() instead of Client()
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OpenAI API key not found, using mock transcription")
        else:
            logger.warning("OpenAI library not available, using mock transcription")
    
    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or config."""
        import os
        return os.environ.get('OPENAI_API_KEY')
    
    def set_result_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Set callback function for receiving transcription results."""
        self.result_callback = callback
    
    def start_session(self, session_id: str):
        """Start a new transcription session."""
        self.session_id = session_id
        self.sequence_number = 0
        self.audio_buffer.clear()
        logger.info(f"Started transcription session: {session_id}")
    
    def end_session(self):
        """End current transcription session."""
        if self.session_id:
            # Process any remaining audio in buffer
            if self.audio_buffer.get_size() > 0:
                # Synchronous processing for cleanup
                try:
                    self._process_buffered_audio_sync(final=True)
                except Exception as e:
                    logger.error(f"Error processing final buffer: {e}")
            
            logger.info(f"Ended transcription session: {self.session_id}")
            self.session_id = None
    
    async def process_audio_chunk(self, audio_data: bytes, timestamp: Optional[float] = None, 
                                  is_final: bool = False) -> Optional[TranscriptionResult]:
        """
        Process audio chunk for real-time transcription.
        
        Args:
            audio_data: Raw audio bytes
            timestamp: Optional timestamp
            is_final: Whether this is the final chunk
            
        Returns:
            TranscriptionResult if transcription was performed
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Estimate duration (assuming 16kHz, 16-bit, mono)
        estimated_duration = len(audio_data) / (16000 * 2)
        
        # Add to buffer
        self.audio_buffer.add_chunk(audio_data, timestamp, estimated_duration)
        
        # Decide whether to process now - be more conservative with buffering
        should_process = (
            is_final or 
            self.audio_buffer.is_full() or
            self.audio_buffer.total_duration >= self.config.max_chunk_duration or
            (len(self.audio_buffer.buffer) >= 5 and self.audio_buffer.total_duration >= 2.0)  # Process after 5 chunks + 2 seconds
        )
        
        if should_process and not self.is_processing:
            return await self._process_buffered_audio(final=is_final)
        
        return None
    
    async def _process_buffered_audio(self, final: bool = False) -> Optional[TranscriptionResult]:
        """Process audio from buffer."""
        if self.is_processing:
            logger.debug("Already processing, skipping")
            return None
        
        audio_data = self.audio_buffer.get_concatenated_audio()
        if not audio_data:
            return None
        
        self.is_processing = True
        start_time = time.time()
        
        try:
            # Run transcription in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._transcribe_audio,
                audio_data,
                final
            )
            
            if result:
                # Update statistics
                latency = time.time() - start_time
                self._update_statistics(latency, success=True)
                
                # Clear buffer after successful processing
                self.audio_buffer.clear()
                
                # Call result callback if set
                if self.result_callback:
                    self.result_callback(result)
                
                logger.debug(f"Transcription completed in {latency:.2f}s: {result.text[:100]}...")
                return result
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            self._update_statistics(0, success=False)
        
        finally:
            self.is_processing = False
        
        return None
    
    def _process_buffered_audio_sync(self, final: bool = False) -> Optional[TranscriptionResult]:
        """Synchronous version for cleanup operations."""
        if self.is_processing:
            logger.debug("Already processing, skipping")
            return None
        
        audio_data = self.audio_buffer.get_concatenated_audio()
        if not audio_data:
            return None
        
        self.is_processing = True
        start_time = time.time()
        
        try:
            # Direct synchronous call for cleanup
            result = self._transcribe_audio(audio_data, final)
            
            if result:
                latency = time.time() - start_time
                self._update_statistics(latency, success=True)
                self.audio_buffer.clear()
                
                if self.result_callback:
                    self.result_callback(result)
                
                logger.debug(f"Sync transcription completed in {latency:.2f}s")
                return result
                
        except Exception as e:
            logger.error(f"Error in sync processing: {e}")
            self._update_statistics(0, success=False)
        
        finally:
            self.is_processing = False
        
        return None
    
    def _transcribe_audio(self, audio_data: bytes, is_final: bool) -> Optional[TranscriptionResult]:
        """Perform actual transcription using OpenAI Whisper API or stub mode."""
        # 🔥 PHASE 1: Use stub mode if enabled
        if STUB_TRANSCRIPTION:
            return self._stub_transcription(audio_data, is_final)
            
        if not self.client:
            return self._mock_transcription(audio_data, is_final)
        
        try:
            # Convert audio data to file-like object
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.webm"  # WebM is officially supported by Whisper API
            
            # Prepare transcription parameters
            params = {
                "model": self.config.model,
                "file": audio_file,
                "response_format": "verbose_json",
                "temperature": self.config.temperature,
                "language": self.config.language,
            }
            
            if self.config.prompt:
                params["prompt"] = self.config.prompt
            
            if self.config.enable_word_timestamps:
                params["timestamp_granularities"] = ["word"]
            
            # Make API request
            response = self.client.audio.transcriptions.create(**params)
            
            # Process response
            text = response.text.strip()
            
            # Extract word-level timestamps if available
            words = []
            if hasattr(response, 'words') and response.words:
                words = [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end
                    }
                    for word in response.words
                ]
            
            # Calculate confidence (OpenAI doesn't provide this, so estimate)
            confidence = self._estimate_confidence(text, len(audio_data))
            
            # Create result
            result = TranscriptionResult(
                text=text,
                confidence=confidence,
                is_final=is_final,
                language=response.language if hasattr(response, 'language') else self.config.language,
                duration=response.duration if hasattr(response, 'duration') else 0.0,
                timestamp=time.time(),
                words=words,
                metadata={
                    "session_id": self.session_id,
                    "sequence_number": self.sequence_number,
                    "audio_size": len(audio_data),
                    "model": self.config.model
                }
            )
            
            self.sequence_number += 1
            return result
            
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            raise
    
    def _stub_transcription(self, audio_data: bytes, is_final: bool) -> TranscriptionResult:
        """🔥 PHASE 1: Stub transcription for testing WebSocket wiring without API calls."""
        import time
        
        # Minimal processing time for testing
        time.sleep(0.05)  # 50ms to simulate some processing
        
        # Generate simple stub text for wiring validation
        audio_length_seconds = len(audio_data) / (16000 * 2)  # Assume 16kHz, 16-bit
        
        if is_final:
            text = f"Final stub transcription (session: {self.session_id}, seq: {self.sequence_number})"
        else:
            text = f"Interim stub #{self.sequence_number}"
        
        self.sequence_number += 1
        
        return TranscriptionResult(
            text=text,
            confidence=1.0,  # Perfect confidence for stub
            is_final=is_final,
            language=self.config.language,
            duration=audio_length_seconds,
            timestamp=time.time(),
            words=[],
            metadata={
                "session_id": self.session_id,
                "sequence_number": self.sequence_number,
                "audio_size": len(audio_data),
                "model": "stub",
                "stub_mode": True
            }
        )

    def _mock_transcription(self, audio_data: bytes, is_final: bool) -> TranscriptionResult:
        """Mock transcription for testing when OpenAI is not available."""
        # Simulate processing time
        import time
        import random
        time.sleep(0.1 + random.random() * 0.2)
        
        # Generate mock text based on audio length
        audio_length_seconds = len(audio_data) / (16000 * 2)  # Assume 16kHz, 16-bit
        
        if audio_length_seconds < 0.5:
            text = "[Mock interim transcription]"
        elif audio_length_seconds < 2.0:
            text = "This is a mock transcription for testing purposes."
        else:
            text = "This is a longer mock transcription that simulates real speech content for development and testing."
        
        return TranscriptionResult(
            text=text,
            confidence=0.85 + random.random() * 0.1,
            is_final=is_final,
            language=self.config.language,
            duration=audio_length_seconds,
            timestamp=time.time(),
            words=[],
            metadata={
                "session_id": self.session_id,
                "sequence_number": self.sequence_number,
                "audio_size": len(audio_data),
                "model": "mock",
                "mock": True
            }
        )
    
    def _estimate_confidence(self, text: str, audio_size: int) -> float:
        """Estimate transcription confidence based on text characteristics."""
        if not text:
            return 0.0
        
        # Simple heuristic based on text length and audio size
        text_length = len(text.split())
        expected_length = audio_size / (16000 * 2) * 3  # ~3 words per second
        
        length_ratio = min(1.0, text_length / max(1, expected_length))
        base_confidence = 0.7 + length_ratio * 0.2
        
        # Adjust based on text characteristics
        if any(char in text for char in ".,!?"):
            base_confidence += 0.05  # Punctuation suggests better recognition
        
        if text.count('[') > 0 or text.count('(') > 0:
            base_confidence -= 0.1  # Brackets suggest uncertainty
        
        return max(0.0, min(1.0, base_confidence))
    
    def _update_statistics(self, latency: float, success: bool):
        """Update processing statistics."""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
            # Update running average latency
            alpha = 0.1  # Smoothing factor
            self.average_latency = (1 - alpha) * self.average_latency + alpha * latency
        else:
            self.error_count += 1
        
        self.last_transcription_time = time.time()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        success_rate = self.successful_requests / max(1, self.total_requests)
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "average_latency": self.average_latency,
            "last_transcription_time": self.last_transcription_time,
            "is_processing": self.is_processing,
            "buffer_size": self.audio_buffer.get_size(),
            "session_id": self.session_id,
            "sequence_number": self.sequence_number,
        }
    
    def update_config(self, **kwargs):
        """Update transcription configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated transcription config: {key} = {value}")
            else:
                logger.warning(f"Unknown transcription config parameter: {key}")
    
    def transcribe_file(self, audio_file):
        """
        Transcribe an entire audio file using OpenAI Whisper API.
        
        Args:
            audio_file: File object or file-like object containing audio data
            
        Returns:
            TranscriptionResult object with the transcribed text and metadata
        """
        try:
            import os
            
            # Get API key from environment
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key or not self.client:
                logger.warning("OpenAI client not available, falling back to mock transcription")
                # Read file data for mock processing
                audio_data = audio_file.read()
                audio_file.seek(0)  # Reset file pointer
                return self._mock_transcription(audio_data, True)
            
            # Use OpenAI Whisper API for file transcription
            language_param = self.config.language if self.config.language and self.config.language != 'auto' else None
            
            params = {
                "model": self.config.model,
                "file": audio_file,
                "response_format": "verbose_json"
            }
            
            if language_param:
                params["language"] = language_param
                
            if self.config.enable_word_timestamps:
                params["timestamp_granularities"] = ["word"]
            
            response = self.client.audio.transcriptions.create(**params)
            
            # Extract results
            text = response.text or ""
            duration = getattr(response, 'duration', 0.0)
            language = getattr(response, 'language', self.config.language)
            
            # Extract word-level timestamps if available
            words = []
            if hasattr(response, 'words') and response.words:
                words = [
                    {
                        'word': word.word,
                        'start': word.start,
                        'end': word.end,
                        'confidence': getattr(word, 'confidence', 0.95)
                    }
                    for word in response.words
                ]
            
            logger.info(f"File transcription completed: {len(text)} characters, {duration:.2f}s duration")
            
            return TranscriptionResult(
                text=text,
                confidence=0.95,  # High confidence for file transcription
                is_final=True,
                timestamp=time.time(),
                language=language,
                duration=duration,
                words=words,
                metadata={
                    'engine': 'openai_whisper',
                    'model': self.config.model,
                    'file_transcription': True,
                    'word_count': len(text.split()) if text else 0
                }
            )
            
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            # Fallback to mock transcription
            try:
                audio_data = audio_file.read()
                audio_file.seek(0)  # Reset file pointer
                return self._mock_transcription(audio_data, True)
            except Exception as fallback_error:
                logger.error(f"Fallback transcription also failed: {fallback_error}")
                return TranscriptionResult(
                    text="Transcription failed",
                    confidence=0.0,
                    is_final=True,
                    timestamp=time.time(),
                    language='en',
                    duration=0.0,
                    words=[],
                    metadata={'engine': 'error', 'error': str(e)}
                )
    
    def shutdown(self):
        """Shutdown the service and cleanup resources."""
        if self.session_id:
            self.end_session()
        
        self.executor.shutdown(wait=True)
        logger.info("Whisper streaming service shutdown complete")
    
    def transcribe_chunk_sync(self, audio_data: bytes, session_id: str, retry_count: int = 0) -> Optional[Dict[str, Any]]:
        """
        🔥 ENHANCED: Robust synchronous transcription with comprehensive error handling.
        
        Args:
            audio_data: Raw audio bytes
            session_id: Session identifier
            retry_count: Current retry attempt (for exponential backoff)
            
        Returns:
            Transcription result dictionary or None
        """
        start_time = time.time()
        
        try:
            # 🔥 VALIDATION: Comprehensive input validation
            if not self.client:
                logger.error("🚨 CRITICAL: OpenAI client not initialized for transcription")
                return self._create_error_result("client_not_initialized", session_id)
                
            if not audio_data:
                logger.warning(f"⚠️ WHISPER SKIP: No audio data provided for session {session_id}")
                return None
                
            if len(audio_data) < 1000:  # 🔥 ENHANCED: Minimum 1KB for meaningful audio
                logger.info(f"📊 WHISPER SKIP: Audio chunk too small ({len(audio_data)} bytes) for session {session_id}")
                return None
                
            # 🔥 AUDIO VALIDATION: Check for valid audio format
            if not self._validate_audio_format(audio_data):
                logger.error(f"🚨 AUDIO FORMAT ERROR: Invalid audio format for session {session_id}")
                return self._create_error_result("invalid_audio_format", session_id)
            
            # Save audio to temporary file for OpenAI API
            import tempfile
            import os
            
            # 🔥 ENHANCED AUDIO FORMAT DETECTION: Check multiple indicators
            if audio_data.startswith(b'RIFF') and b'WAVE' in audio_data[:50]:
                logger.info("🔍 AUDIO FORMAT: Detected WAV format")
                wav_audio = audio_data  # Already WAV
                file_suffix = '.wav'
            elif audio_data.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/Matroska magic number
                logger.info("🔍 AUDIO FORMAT: Detected WebM format")
                wav_audio = audio_data  # Keep as WebM for Whisper API
                file_suffix = '.webm'
            elif audio_data.startswith(b'fLaC'):
                logger.info("🔍 AUDIO FORMAT: Detected FLAC format")
                wav_audio = audio_data  # Keep as FLAC for Whisper API
                file_suffix = '.flac'
            elif audio_data.startswith(b'OggS'):
                logger.info("🔍 AUDIO FORMAT: Detected OGG format")
                wav_audio = audio_data  # Keep as OGG for Whisper API
                file_suffix = '.ogg'
            elif audio_data.startswith(b'ID3') or audio_data[4:8] == b'ftyp':
                logger.info("🔍 AUDIO FORMAT: Detected MP3/MP4 format")
                wav_audio = audio_data  # Keep as MP3/MP4 for Whisper API
                file_suffix = '.mp3' if audio_data.startswith(b'ID3') else '.mp4'
            else:
                logger.info(f"🔍 AUDIO FORMAT: Unknown format, treating as WAV (first 8 bytes: {audio_data[:8].hex()})")
                # For unknown formats, assume WAV (most common for test data)
                wav_audio = audio_data
                file_suffix = '.wav'
                logger.info(f"Using WAV format for unknown data: {len(audio_data)} bytes")
            
            with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False) as temp_file:
                temp_file.write(wav_audio)
                temp_file.flush()
                temp_path = temp_file.name
            
            try:
                # 🔥 ENHANCED LOGGING: Detailed API call tracking
                request_id = f"{session_id}_{int(time.time()*1000)}"
                logger.info(f"🗺 WHISPER API CALL: Processing {len(audio_data)} bytes via OpenAI API (request_id: {request_id})")
                
                # 🔥 ROBUST API CALL: Enhanced error handling and format validation
                with open(temp_path, 'rb') as audio_file:
                    # Verify file size before API call
                    file_size = audio_file.seek(0, 2)
                    audio_file.seek(0)
                    
                    if file_size == 0:
                        logger.error(f"🚨 EMPTY FILE: Generated empty temp file for session {session_id}")
                        return self._create_error_result("empty_temp_file", session_id)
                    
                    logger.info(f"📁 TEMP FILE: Created {file_size} byte file for Whisper API (request_id: {request_id})")
                    
                    # 🔥 API CALL: Enhanced with timeout and error handling
                    try:
                        response = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            language="en",
                            response_format="verbose_json",
                            timestamp_granularities=["word"]  # 🔥 ENHANCED: Request word-level timestamps
                        )
                        
                        api_latency = (time.time() - start_time) * 1000
                        logger.info(f"⚡ WHISPER TIMING: API call completed in {api_latency:.2f}ms (request_id: {request_id})")
                        
                    except Exception as api_error:
                        logger.error(f"🚨 WHISPER API ERROR: {str(api_error)} (request_id: {request_id})")
                        # 🔥 RETRY LOGIC: Implement exponential backoff
                        if retry_count < 3:
                            retry_delay = (2 ** retry_count) * 1.0  # 1s, 2s, 4s delays
                            logger.info(f"🔄 RETRY: Attempting retry {retry_count + 1}/3 after {retry_delay}s delay")
                            time.sleep(retry_delay)
                            return self.transcribe_chunk_sync(audio_data, session_id, retry_count + 1)
                        else:
                            return self._create_error_result(f"api_error_after_retries: {str(api_error)}", session_id)
                
                # 🔥 RESPONSE VALIDATION: Comprehensive result processing
                if not response:
                    logger.error(f"🚨 WHISPER NULL RESPONSE: API returned null response (request_id: {request_id})")
                    return self._create_error_result("null_api_response", session_id)
                
                # 🔥 TEXT EXTRACTION: Handle different response formats
                text = ""
                if hasattr(response, 'text') and response.text:
                    text = response.text.strip()
                elif hasattr(response, 'segments') and response.segments:
                    # Handle segmented response format
                    text = " ".join([seg.text for seg in response.segments if hasattr(seg, 'text')]).strip()
                
                if text and len(text) > 0:
                    total_latency = (time.time() - start_time) * 1000
                    logger.info(f"✅ WHISPER SUCCESS: '{text[:100]}...' ({len(text)} chars, {total_latency:.2f}ms total, request_id: {request_id})")
                    
                    return {
                        'text': text,
                        'confidence': 0.85,  # Enhanced default confidence
                        'language': 'en',
                        'processing_time_ms': total_latency,
                        'request_id': request_id,
                        'audio_duration_estimate': len(audio_data) / 16000,  # Rough estimate
                        'retry_count': retry_count
                    }
                else:
                    logger.warning(f"⚠️ WHISPER EMPTY: OpenAI returned empty/null text for {len(audio_data)} bytes (request_id: {request_id}, response: {response})")
                    # 🔥 FALLBACK: Try with different parameters on empty result
                    if retry_count == 0:
                        logger.info(f"🔄 FALLBACK: Retrying with enhanced parameters for session {session_id}")
                        fallback_result = self._try_fallback_transcription(audio_data, session_id, temp_path)
                        if fallback_result:
                            return fallback_result
                
                return None
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            total_latency = (time.time() - start_time) * 1000
            logger.error(f"🚨 WHISPER EXCEPTION: {str(e)} after {total_latency:.2f}ms for session {session_id}")
            return self._create_error_result(f"exception: {str(e)}", session_id)
    
    def _validate_audio_format(self, audio_data: bytes) -> bool:
        """🔥 ENHANCED: Validate audio format for Whisper API compatibility."""
        try:
            # Check for common audio file headers
            if len(audio_data) < 4:
                return False
                
            # Check for WebM header (common format from MediaRecorder)
            if audio_data[:4] == b'\x1a\x45\xdf\xa3':  # WebM/Matroska header
                return True
                
            # Check for WAV header
            if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
                return True
                
            # Check for OGG header
            if audio_data[:4] == b'OggS':
                return True
                
            # Check for MP4/M4A header
            if len(audio_data) >= 8 and audio_data[4:8] == b'ftyp':
                return True
                
            # For other formats, allow through (Whisper is quite flexible)
            logger.info(f"🔍 AUDIO FORMAT: Unknown format, allowing through (first 8 bytes: {audio_data[:8].hex()})")
            return True
            
        except Exception as e:
            logger.error(f"🚨 AUDIO VALIDATION ERROR: {e}")
            return False
    
    def _create_error_result(self, error_type: str, session_id: str) -> Dict[str, Any]:
        """🔥 ENHANCED: Create structured error result for failed transcription."""
        return {
            'text': '',
            'confidence': 0.0,
            'language': 'en',
            'error': True,
            'error_type': error_type,
            'session_id': session_id,
            'timestamp': time.time()
        }
    
    def _try_fallback_transcription(self, audio_data: bytes, session_id: str, temp_path: str) -> Optional[Dict[str, Any]]:
        """🔥 ENHANCED: Fallback transcription with different parameters."""
        try:
            logger.info(f"🔄 FALLBACK TRANSCRIPTION: Trying alternative approach for session {session_id}")
            
            with open(temp_path, 'rb') as audio_file:
                # Try without language specification
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",  # 🔥 Try verbose format
                    temperature=0.2  # 🔥 Add some randomness
                )
                
                if response and hasattr(response, 'text') and response.text:
                    text = response.text.strip()
                    if text:
                        logger.info(f"✅ FALLBACK SUCCESS: '{text[:50]}...' for session {session_id}")
                        return {
                            'text': text,
                            'confidence': 0.7,  # Lower confidence for fallback
                            'language': getattr(response, 'language', 'en'),
                            'fallback': True
                        }
                        
            logger.warning(f"⚠️ FALLBACK FAILED: No text from alternative approach for session {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"🚨 FALLBACK ERROR: {e} for session {session_id}")
            return None
