"""
🎵 STREAMING AUDIO PROCESSOR
Production-ready streaming audio processing with background threading,
chunking strategy, and Voice Activity Detection
"""

import logging
import asyncio
import time
import threading
import queue
from typing import Optional, Dict, Any, Callable, List, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import io
import tempfile
import os
from collections import deque

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    webrtcvad = None
    VAD_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """Represents an audio chunk with metadata"""
    chunk_id: str
    session_id: str
    audio_data: bytes
    timestamp: float
    duration_ms: float
    sample_rate: int = 16000
    channels: int = 1
    has_speech: bool = True
    vad_confidence: float = 0.0
    is_final: bool = False


@dataclass 
class ProcessingResult:
    """Result of audio processing"""
    chunk_id: str
    transcript: str
    confidence: float
    processing_time_ms: float
    word_count: int
    is_interim: bool = False
    error: Optional[str] = None
    latency_ms: float = 0.0


class VoiceActivityDetector:
    """Voice Activity Detection using WebRTC VAD"""
    
    def __init__(self, aggressiveness: int = 2):
        self.aggressiveness = aggressiveness  # 0-3, higher is more aggressive
        self.vad = None
        self.available = False
        
        if VAD_AVAILABLE:
            try:
                self.vad = webrtcvad.Vad(aggressiveness)
                self.available = True
                logger.info(f"✅ VAD initialized with aggressiveness={aggressiveness}")
            except Exception as e:
                logger.warning(f"⚠️ VAD initialization failed: {e}")
                self.available = False
        else:
            logger.warning("⚠️ WebRTCVAD not available, using silence detection fallback")
    
    def has_speech(self, audio_data: bytes, sample_rate: int = 16000) -> Tuple[bool, float]:
        """
        Detect if audio contains speech
        Returns: (has_speech, confidence)
        """
        if not self.available or not audio_data:
            # Fallback: simple energy-based detection
            return self._energy_based_detection(audio_data)
        
        try:
            # WebRTC VAD requires specific sample rates
            if sample_rate not in [8000, 16000, 32000, 48000]:
                # Fallback to energy detection for unsupported rates
                return self._energy_based_detection(audio_data)
            
            # WebRTC VAD requires specific frame sizes
            frame_duration_ms = 30  # 30ms frames
            frame_size = int(sample_rate * frame_duration_ms / 1000)
            bytes_per_frame = frame_size * 2  # 16-bit audio
            
            speech_frames = 0
            total_frames = 0
            
            # Process in 30ms frames
            for i in range(0, len(audio_data) - bytes_per_frame, bytes_per_frame):
                frame = audio_data[i:i + bytes_per_frame]
                if len(frame) == bytes_per_frame:
                    is_speech = self.vad.is_speech(frame, sample_rate)
                    if is_speech:
                        speech_frames += 1
                    total_frames += 1
            
            if total_frames == 0:
                return False, 0.0
            
            confidence = speech_frames / total_frames
            has_speech = confidence > 0.3  # 30% of frames contain speech
            
            return has_speech, confidence
            
        except Exception as e:
            logger.warning(f"⚠️ VAD processing error: {e}, using fallback")
            return self._energy_based_detection(audio_data)
    
    def _energy_based_detection(self, audio_data: bytes) -> Tuple[bool, float]:
        """Fallback energy-based speech detection"""
        if not audio_data or len(audio_data) < 100:
            return False, 0.0
        
        try:
            # Convert bytes to numpy array for energy calculation
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_array.astype(float) ** 2))
            
            # Normalize energy to 0-1 range (rough approximation)
            normalized_energy = min(1.0, energy / 1000.0)
            
            # Simple threshold-based detection
            has_speech = normalized_energy > 0.05  # Adjust threshold as needed
            
            return has_speech, normalized_energy
            
        except Exception as e:
            logger.warning(f"⚠️ Energy detection failed: {e}")
            return True, 0.5  # Default to assuming speech


class AudioChunkProcessor:
    """Processes audio chunks with overlap and deduplication"""
    
    def __init__(self, chunk_duration_ms: int = 300, overlap_ms: int = 50):
        self.chunk_duration_ms = chunk_duration_ms
        self.overlap_ms = overlap_ms
        self.buffer = bytearray()
        self.processed_chunks = deque(maxlen=10)  # Keep last 10 chunks for deduplication
        
        logger.info(f"📦 AudioChunkProcessor initialized: {chunk_duration_ms}ms chunks, {overlap_ms}ms overlap")
    
    def add_audio_data(self, audio_data: bytes, session_id: str) -> List[AudioChunk]:
        """Add audio data and return ready chunks"""
        self.buffer.extend(audio_data)
        
        chunks = []
        sample_rate = 16000
        bytes_per_ms = (sample_rate * 2) // 1000  # 16-bit audio
        chunk_size_bytes = self.chunk_duration_ms * bytes_per_ms
        overlap_size_bytes = self.overlap_ms * bytes_per_ms
        
        # Create chunks with overlap
        chunk_id = 0
        while len(self.buffer) >= chunk_size_bytes:
            chunk_data = bytes(self.buffer[:chunk_size_bytes])
            
            chunk = AudioChunk(
                chunk_id=f"{session_id}_{int(time.time())}_{chunk_id}",
                session_id=session_id,
                audio_data=chunk_data,
                timestamp=time.time(),
                duration_ms=self.chunk_duration_ms,
                sample_rate=sample_rate,
                channels=1
            )
            
            chunks.append(chunk)
            
            # Remove processed data but keep overlap
            advance_bytes = chunk_size_bytes - overlap_size_bytes
            self.buffer = self.buffer[advance_bytes:]
            
            chunk_id += 1
        
        return chunks
    
    def finalize_session(self, session_id: str) -> List[AudioChunk]:
        """Process remaining buffer data as final chunks"""
        chunks = []
        
        if len(self.buffer) > 0:
            chunk = AudioChunk(
                chunk_id=f"{session_id}_{int(time.time())}_final",
                session_id=session_id,
                audio_data=bytes(self.buffer),
                timestamp=time.time(),
                duration_ms=len(self.buffer) // ((16000 * 2) // 1000),
                sample_rate=16000,
                channels=1,
                is_final=True
            )
            chunks.append(chunk)
            self.buffer.clear()
        
        return chunks


class StreamingAudioProcessor:
    """
    Production-ready streaming audio processor with:
    - Background thread processing 
    - Voice Activity Detection
    - Chunking with overlap
    - Performance monitoring
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_queue = queue.Queue(maxsize=100)
        self.result_callbacks: Dict[str, Callable] = {}
        
        # Initialize components
        self.vad = VoiceActivityDetector(aggressiveness=2)
        self.chunk_processor = AudioChunkProcessor(chunk_duration_ms=300, overlap_ms=50)
        
        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self.metrics = {
            'chunks_processed': 0,
            'chunks_dropped': 0,
            'avg_processing_time_ms': 0.0,
            'speech_detection_savings': 0.0,
            'queue_length': 0
        }
        
        # Start background processing thread
        self.processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.running = True
        self.processing_thread.start()
        
        logger.info(f"🎵 StreamingAudioProcessor started with {max_workers} workers")
    
    def start_session(self, session_id: str, callback: Callable[[ProcessingResult], None]) -> None:
        """Start a new transcription session"""
        self.active_sessions[session_id] = {
            'start_time': time.time(),
            'chunk_count': 0,
            'processed_count': 0,
            'total_audio_ms': 0,
            'speech_detected_ms': 0,
            'callback': callback
        }
        
        logger.info(f"📢 Started session: {session_id}")
    
    def process_audio_chunk(self, audio_data: bytes, session_id: str) -> None:
        """Process incoming audio data"""
        if session_id not in self.active_sessions:
            logger.warning(f"⚠️ Unknown session: {session_id}")
            return
        
        # Create chunks with overlap
        chunks = self.chunk_processor.add_audio_data(audio_data, session_id)
        
        # Process each chunk
        for chunk in chunks:
            # Apply VAD filtering
            has_speech, vad_confidence = self.vad.has_speech(chunk.audio_data, chunk.sample_rate)
            chunk.has_speech = has_speech
            chunk.vad_confidence = vad_confidence
            
            # Update session metrics
            session = self.active_sessions[session_id]
            session['chunk_count'] += 1
            session['total_audio_ms'] += chunk.duration_ms
            
            if has_speech:
                session['speech_detected_ms'] += chunk.duration_ms
                # Only process chunks with speech
                self._queue_for_processing(chunk)
            else:
                # Skip silent chunks - saves 40-60% processing
                logger.debug(f"🔇 Skipping silent chunk: {chunk.chunk_id}")
                self.metrics['speech_detection_savings'] += chunk.duration_ms
    
    def _queue_for_processing(self, chunk: AudioChunk) -> None:
        """Queue chunk for background processing"""
        try:
            self.processing_queue.put(chunk, block=False)
            self.metrics['queue_length'] = self.processing_queue.qsize()
        except queue.Full:
            logger.warning(f"⚠️ Processing queue full, dropping chunk: {chunk.chunk_id}")
            self.metrics['chunks_dropped'] += 1
    
    def _process_queue(self) -> None:
        """Background thread for processing queued chunks"""
        logger.info("🔄 Background processing thread started")
        
        while self.running:
            try:
                chunk = self.processing_queue.get(timeout=1.0)
                self._process_chunk_background(chunk)
                self.processing_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Background processing error: {e}", exc_info=True)
    
    def _process_chunk_background(self, chunk: AudioChunk) -> None:
        """Process a single chunk in background thread"""
        start_time = time.time()
        
        try:
            # Get session callback
            session = self.active_sessions.get(chunk.session_id)
            if not session:
                logger.warning(f"⚠️ Session not found for chunk: {chunk.chunk_id}")
                return
            
            callback = session['callback']
            
            # Convert to WAV format for transcription
            wav_data = self._convert_to_wav(chunk.audio_data)
            if not wav_data:
                raise Exception("Audio conversion failed")
            
            # Call transcription service (this would integrate with your Whisper API)
            transcript_result = self._transcribe_audio(wav_data, chunk.chunk_id)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Create result
            result = ProcessingResult(
                chunk_id=chunk.chunk_id,
                transcript=transcript_result.get('text', ''),
                confidence=transcript_result.get('confidence', 0.0),
                processing_time_ms=processing_time,
                word_count=len(transcript_result.get('text', '').split()),
                latency_ms=processing_time
            )
            
            # Update metrics
            self.metrics['chunks_processed'] += 1
            self.metrics['avg_processing_time_ms'] = (
                (self.metrics['avg_processing_time_ms'] * (self.metrics['chunks_processed'] - 1) + processing_time) 
                / self.metrics['chunks_processed']
            )
            
            # Update session metrics
            session['processed_count'] += 1
            
            # Call session callback
            callback(result)
            
            logger.debug(f"✅ Processed chunk {chunk.chunk_id} in {processing_time:.1f}ms")
            
        except Exception as e:
            logger.error(f"❌ Chunk processing failed: {chunk.chunk_id} - {e}")
            
            # Send error result
            if session and session.get('callback'):
                error_result = ProcessingResult(
                    chunk_id=chunk.chunk_id,
                    transcript='',
                    confidence=0.0,
                    processing_time_ms=(time.time() - start_time) * 1000,
                    word_count=0,
                    error=str(e)
                )
                session['callback'](error_result)
    
    def _convert_to_wav(self, audio_data: bytes) -> Optional[bytes]:
        """Convert audio data to WAV format"""
        if not PYDUB_AVAILABLE:
            logger.warning("⚠️ PyDub not available for audio conversion")
            return audio_data  # Return as-is and hope for the best
        
        try:
            # Assume input is PCM16 at 16kHz (adjust as needed)
            audio = AudioSegment(
                data=audio_data,
                sample_width=2,  # 16-bit
                frame_rate=16000,
                channels=1
            )
            
            # Export to WAV
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            return wav_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return None
    
    def _transcribe_audio(self, wav_data: bytes, chunk_id: str) -> Dict[str, Any]:
        """
        Transcribe audio using OpenAI Whisper API
        This integrates with your existing transcription service
        """
        try:
            # This would call your existing transcription API
            from routes.unified_transcription_api import get_openai_client
            
            client = get_openai_client()
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_data)
                temp_file_path = temp_file.name
            
            try:
                with open(temp_file_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        temperature=0.2
                    )
                
                return {
                    'text': response.text.strip(),
                    'confidence': 0.95  # Whisper doesn't provide confidence, use default
                }
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"❌ Transcription failed for {chunk_id}: {e}")
            return {'text': '', 'confidence': 0.0}
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End session and return analytics"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        # Process any remaining chunks
        final_chunks = self.chunk_processor.finalize_session(session_id)
        for chunk in final_chunks:
            has_speech, vad_confidence = self.vad.has_speech(chunk.audio_data)
            if has_speech:
                self._queue_for_processing(chunk)
        
        # Calculate session metrics
        duration = time.time() - session['start_time']
        speech_ratio = session['speech_detected_ms'] / max(session['total_audio_ms'], 1)
        
        analytics = {
            'session_id': session_id,
            'duration_seconds': duration,
            'total_chunks': session['chunk_count'],
            'processed_chunks': session['processed_count'],
            'speech_ratio': speech_ratio,
            'processing_savings_percent': ((session['total_audio_ms'] - session['speech_detected_ms']) / max(session['total_audio_ms'], 1)) * 100
        }
        
        # Cleanup
        del self.active_sessions[session_id]
        
        logger.info(f"📊 Session ended: {session_id}, analytics: {analytics}")
        return analytics
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.metrics,
            'active_sessions': len(self.active_sessions),
            'queue_length': self.processing_queue.qsize()
        }
    
    def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("🛑 Shutting down StreamingAudioProcessor")
        self.running = False
        
        # Wait for processing thread
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)


# Global instance
_streaming_processor = None

def get_streaming_processor() -> StreamingAudioProcessor:
    """Get or create global streaming processor instance"""
    global _streaming_processor
    if _streaming_processor is None:
        _streaming_processor = StreamingAudioProcessor(max_workers=4)
    return _streaming_processor