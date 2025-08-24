"""
Transcription Service Orchestrator
High-level orchestration service that coordinates VAD, audio processing, and Whisper streaming.
Consolidates superior orchestration logic from real-time transcription improvements.
"""

import logging
import asyncio
import time
import uuid
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum

from .vad_service import VADService, VADConfig
from .whisper_streaming import WhisperStreamingService, TranscriptionConfig, TranscriptionResult
from .audio_processor import AudioProcessor
from models.session import Session
from models.segment import Segment
from app_refactored import db

logger = logging.getLogger(__name__)

class SessionState(Enum):
    """Session state enumeration."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class TranscriptionServiceConfig:
    """Configuration for transcription service."""
    # VAD configuration
    vad_sensitivity: float = 0.5
    vad_min_speech_duration: int = 300  # ms
    vad_min_silence_duration: int = 500  # ms
    
    # Audio processing
    sample_rate: int = 16000
    chunk_size: int = 1024
    audio_format: str = "webm"
    
    # Transcription settings
    language: str = "en"
    min_confidence: float = 0.7
    enable_speaker_detection: bool = True
    enable_sentiment_analysis: bool = False
    
    # Processing limits
    max_chunk_duration: float = 30.0  # seconds
    min_chunk_duration: float = 0.1   # seconds
    max_concurrent_sessions: int = 10
    
    # Real-time settings
    enable_realtime: bool = True
    interim_results: bool = True
    backpressure_threshold: int = 5  # max queued audio chunks

class TranscriptionService:
    """
    High-level transcription service that orchestrates VAD, audio processing, and Whisper streaming.
    Provides a unified interface for real-time meeting transcription with enhanced coordination.
    """
    
    def __init__(self, config: Optional[TranscriptionServiceConfig] = None):
        self.config = config or TranscriptionServiceConfig()
        
        # Initialize sub-services
        vad_config = VADConfig(
            sensitivity=self.config.vad_sensitivity,
            min_speech_duration=self.config.vad_min_speech_duration,
            min_silence_duration=self.config.vad_min_silence_duration,
            sample_rate=self.config.sample_rate
        )
        self.vad_service = VADService(vad_config)
        
        transcription_config = TranscriptionConfig(
            language=self.config.language,
            max_chunk_duration=self.config.max_chunk_duration,
            min_chunk_duration=self.config.min_chunk_duration,
            confidence_threshold=self.config.min_confidence
        )
        self.whisper_service = WhisperStreamingService(transcription_config)
        
        self.audio_processor = AudioProcessor()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_callbacks: Dict[str, List[Callable]] = {}
        
        # Processing queues and stats
        self.processing_queue_size = 0
        self.total_sessions = 0
        self.total_segments = 0
        self.average_processing_time = 0.0
        
        # Set up Whisper service callback
        self.whisper_service.set_result_callback(self._on_transcription_result)
        
        logger.info(f"Transcription service initialized with config: {asdict(self.config)}")
    
    async def start_session(self, session_id: Optional[str] = None, 
                           user_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new transcription session.
        
        Args:
            session_id: Optional session ID, will generate if None
            user_config: Optional user-specific configuration overrides
            
        Returns:
            Session ID
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if len(self.active_sessions) >= self.config.max_concurrent_sessions:
            raise Exception(f"Maximum concurrent sessions ({self.config.max_concurrent_sessions}) reached")
        
        # Create database session
        db_session = Session(
            session_id=session_id,
            status='created',
            language=self.config.language,
            enable_realtime=self.config.enable_realtime,
            enable_speaker_detection=self.config.enable_speaker_detection,
            enable_sentiment_analysis=self.config.enable_sentiment_analysis,
            sample_rate=self.config.sample_rate,
            min_confidence=self.config.min_confidence,
            vad_sensitivity=self.config.vad_sensitivity,
            vad_min_speech_duration=self.config.vad_min_speech_duration,
            vad_min_silence_duration=self.config.vad_min_silence_duration
        )
        
        # Apply user configuration overrides
        if user_config:
            for key, value in user_config.items():
                if hasattr(db_session, key):
                    setattr(db_session, key, value)
        
        db.session.add(db_session)
        db.session.commit()
        
        # Initialize session state
        self.active_sessions[session_id] = {
            'state': SessionState.IDLE,
            'created_at': time.time(),
            'last_activity': time.time(),
            'sequence_number': 0,
            'audio_chunks': [],
            'pending_processing': 0,
            'stats': {
                'total_audio_duration': 0.0,
                'speech_duration': 0.0,
                'silence_duration': 0.0,
                'total_segments': 0,
                'average_confidence': 0.0
            }
        }
        
        self.session_callbacks[session_id] = []
        
        # Initialize sub-services for this session
        self.vad_service.reset_state()
        self.whisper_service.start_session(session_id)
        
        self.total_sessions += 1
        logger.info(f"Started transcription session: {session_id}")
        
        return session_id
    
    async def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a transcription session and return statistics.
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Session statistics and metadata
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        
        # Process any remaining audio
        if session_data['audio_chunks']:
            await self._process_pending_audio(session_id, final=True)
        
        # Update database session
        db_session = Session.query.filter_by(session_id=session_id).first()
        if db_session:
            db_session.end_session()
            
            # Update final statistics
            stats = session_data['stats']
            db_session.total_segments = stats['total_segments']
            db_session.average_confidence = stats['average_confidence']
            db_session.total_duration = stats['total_audio_duration']
            db.session.commit()
        
        # End Whisper service session
        self.whisper_service.end_session()
        
        # Get final statistics
        final_stats = self._get_session_statistics(session_id)
        
        # Cleanup
        del self.active_sessions[session_id]
        del self.session_callbacks[session_id]
        
        logger.info(f"Ended transcription session: {session_id}")
        return final_stats
    
    async def process_audio(self, session_id: str, audio_data: bytes, 
                           timestamp: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Process audio chunk for real-time transcription.
        
        Args:
            session_id: Session ID
            audio_data: Raw audio bytes
            timestamp: Optional timestamp
            
        Returns:
            Processing result with interim/final transcription if available
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        if timestamp is None:
            timestamp = time.time()
        
        session_data = self.active_sessions[session_id]
        
        # Check backpressure
        if session_data['pending_processing'] >= self.config.backpressure_threshold:
            logger.warning(f"Backpressure limit reached for session {session_id}")
            return None
        
        # Update session activity
        session_data['last_activity'] = timestamp
        session_data['state'] = SessionState.RECORDING
        
        # Process audio through pipeline
        result = await self._process_audio_pipeline(session_id, audio_data, timestamp)
        
        return result
    
    async def _process_audio_pipeline(self, session_id: str, audio_data: bytes, 
                                     timestamp: float) -> Optional[Dict[str, Any]]:
        """Process audio through the complete pipeline."""
        session_data = self.active_sessions[session_id]
        
        try:
            # Step 1: Audio preprocessing
            processed_audio = self.audio_processor.normalize_audio(audio_data)
            processed_audio = self.audio_processor.apply_noise_gate(processed_audio, threshold=0.005)
            
            # Convert back to bytes for further processing
            audio_bytes = (processed_audio * 32767).astype(np.int16).tobytes()
            
            # Step 2: Voice Activity Detection
            vad_result = self.vad_service.process_audio_chunk(audio_bytes, timestamp)
            
            # Update statistics
            audio_duration = len(audio_data) / (self.config.sample_rate * 2)  # 16-bit audio
            session_data['stats']['total_audio_duration'] += audio_duration
            
            if vad_result.is_speech:
                session_data['stats']['speech_duration'] += audio_duration
            else:
                session_data['stats']['silence_duration'] += audio_duration
            
            # Step 3: Conditional transcription (only if speech detected or buffer full)
            transcription_result = None
            if self.config.enable_realtime and (vad_result.is_speech or vad_result.confidence > 0.3):
                session_data['pending_processing'] += 1
                try:
                    transcription_result = await self.whisper_service.process_audio_chunk(
                        audio_bytes, timestamp, is_final=False
                    )
                finally:
                    session_data['pending_processing'] -= 1
            
            # Prepare result
            result = {
                'session_id': session_id,
                'timestamp': timestamp,
                'vad': {
                    'is_speech': vad_result.is_speech,
                    'confidence': vad_result.confidence,
                    'energy': vad_result.energy
                },
                'audio_duration': audio_duration,
                'transcription': None
            }
            
            if transcription_result:
                result['transcription'] = self._format_transcription_result(transcription_result)
                
                # Store in database if final
                if transcription_result.is_final:
                    await self._store_segment(session_id, transcription_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in audio pipeline for session {session_id}: {e}")
            session_data['state'] = SessionState.ERROR
            return None
    
    async def _store_segment(self, session_id: str, transcription_result: TranscriptionResult):
        """Store transcription segment in database."""
        session_data = self.active_sessions[session_id]
        sequence_number = session_data['sequence_number']
        session_data['sequence_number'] += 1
        
        # Create segment
        segment = Segment(
            session_id=session_id,
            segment_id=f"{session_id}_{sequence_number}",
            sequence_number=sequence_number,
            start_time=transcription_result.timestamp - transcription_result.duration,
            end_time=transcription_result.timestamp,
            text=transcription_result.text,
            confidence=transcription_result.confidence,
            is_final=transcription_result.is_final,
            language=transcription_result.language,
            audio_duration=transcription_result.duration,
            sample_rate=self.config.sample_rate,
            metadata=transcription_result.metadata
        )
        
        db.session.add(segment)
        db.session.commit()
        
        # Update session statistics
        self.total_segments += 1
        session_data['stats']['total_segments'] += 1
        
        # Update average confidence
        total_segments = session_data['stats']['total_segments']
        current_avg = session_data['stats']['average_confidence']
        new_avg = (current_avg * (total_segments - 1) + transcription_result.confidence) / total_segments
        session_data['stats']['average_confidence'] = new_avg
        
        # Update database session
        db_session = Session.query.filter_by(session_id=session_id).first()
        if db_session:
            db_session.add_segment()
            db_session.update_stats(confidence=transcription_result.confidence)
        
        logger.debug(f"Stored segment {sequence_number} for session {session_id}")
    
    def _format_transcription_result(self, result: TranscriptionResult) -> Dict[str, Any]:
        """Format transcription result for API response."""
        return {
            'text': result.text,
            'confidence': result.confidence,
            'is_final': result.is_final,
            'language': result.language,
            'duration': result.duration,
            'timestamp': result.timestamp,
            'words': result.words,
            'metadata': result.metadata
        }
    
    def _on_transcription_result(self, result: TranscriptionResult):
        """Handle transcription result callback."""
        session_id = result.metadata.get('session_id')
        if not session_id or session_id not in self.active_sessions:
            return
        
        # Call registered callbacks
        callbacks = self.session_callbacks.get(session_id, [])
        for callback in callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error in transcription callback: {e}")
    
    def add_session_callback(self, session_id: str, callback: Callable[[TranscriptionResult], None]):
        """Add callback for transcription results."""
        if session_id in self.session_callbacks:
            self.session_callbacks[session_id].append(callback)
    
    def remove_session_callback(self, session_id: str, callback: Callable[[TranscriptionResult], None]):
        """Remove callback for transcription results."""
        if session_id in self.session_callbacks:
            try:
                self.session_callbacks[session_id].remove(callback)
            except ValueError:
                pass
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status and statistics."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self._get_session_statistics(session_id)
    
    def _get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        session_data = self.active_sessions[session_id]
        vad_stats = self.vad_service.get_statistics()
        whisper_stats = self.whisper_service.get_statistics()
        
        return {
            'session_id': session_id,
            'state': session_data['state'].value,
            'created_at': session_data['created_at'],
            'last_activity': session_data['last_activity'],
            'duration': time.time() - session_data['created_at'],
            'stats': session_data['stats'],
            'vad_stats': vad_stats,
            'whisper_stats': whisper_stats,
            'pending_processing': session_data['pending_processing']
        }
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global service statistics."""
        return {
            'total_sessions': self.total_sessions,
            'active_sessions': len(self.active_sessions),
            'total_segments': self.total_segments,
            'average_processing_time': self.average_processing_time,
            'processing_queue_size': self.processing_queue_size,
            'max_concurrent_sessions': self.config.max_concurrent_sessions,
            'config': asdict(self.config)
        }
    
    def update_config(self, **kwargs):
        """Update service configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated transcription service config: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
    
    async def shutdown(self):
        """Shutdown service and cleanup all sessions."""
        logger.info("Shutting down transcription service")
        
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            try:
                await self.end_session(session_id)
            except Exception as e:
                logger.error(f"Error ending session {session_id}: {e}")
        
        # Shutdown sub-services
        self.whisper_service.shutdown()
        
        logger.info("Transcription service shutdown complete")
