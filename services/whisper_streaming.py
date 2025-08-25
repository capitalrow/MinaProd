"""
Whisper Streaming Service
Enhanced real-time transcription with superior orchestration and buffering.
Integrates improvements from the real-time transcription codebase.
"""

import logging
import asyncio
import time
import json
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
    confidence_threshold: float = 0.6
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
        """Get all buffered audio as single chunk."""
        if not self.buffer:
            return None
        
        if len(self.buffer) == 1:
            return self.buffer[0]
        
        # Concatenate all chunks
        return b''.join(self.buffer)
    
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
                self.client = openai.Client(api_key=api_key)
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
                self._process_buffered_audio(final=True)
            
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
        
        # Decide whether to process now
        should_process = (
            is_final or 
            self.audio_buffer.is_full() or
            self.audio_buffer.total_duration >= self.config.min_chunk_duration
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
    
    def _transcribe_audio(self, audio_data: bytes, is_final: bool) -> Optional[TranscriptionResult]:
        """Perform actual transcription using OpenAI Whisper API or mock."""
        if not self.client:
            return self._mock_transcription(audio_data, is_final)
        
        try:
            # Convert audio data to file-like object
            import io
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Required for OpenAI API
            
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
            response = self.client.audio.transcriptions.create(
                model=self.config.model,
                file=audio_file,
                language=self.config.language if self.config.language != 'auto' else None,
                response_format='verbose_json',
                timestamp_granularities=['word'] if self.config.enable_word_timestamps else ['segment']
            )
            
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
    
    def transcribe_chunk_sync(self, audio_data: bytes, session_id: str) -> Optional[Dict[str, Any]]:
        """
        SIMPLIFIED: Synchronous transcription to fix server stability.
        Direct OpenAI API call without complex async/threading.
        
        Args:
            audio_data: Raw audio bytes
            session_id: Session identifier
            
        Returns:
            Transcription result dictionary or None
        """
        try:
            if not self.client or not audio_data:
                return None
            
            # Save audio to temporary file for OpenAI API
            import tempfile
            import os
            
            # CRITICAL FIX: Convert webm to WAV for Whisper API compatibility
            try:
                from .audio_processor import AudioProcessor
                audio_processor = AudioProcessor()
                wav_audio = audio_processor.convert_to_wav(audio_data, 'webm', 16000, 1)
                logger.info(f"Audio format conversion: {len(audio_data)} webm -> {len(wav_audio)} wav bytes")
            except Exception as e:
                logger.warning(f"Audio conversion failed: {e}, using raw data")
                wav_audio = audio_data
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_audio)
                temp_file.flush()
                temp_path = temp_file.name
            
            try:
                # Direct synchronous OpenAI transcription call
                with open(temp_path, 'rb') as audio_file:
                    # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
                    # do not change this unless explicitly requested by the user
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                
                text = response.text.strip() if response.text else ""
                
                if text:
                    logger.info(f"Whisper transcription: '{text}'")
                    return {
                        'text': text,
                        'confidence': 0.8,  # Whisper doesn't provide confidence, use default
                        'language': 'en'
                    }
                
                return None
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error in synchronous Whisper transcription: {e}")
            return None
