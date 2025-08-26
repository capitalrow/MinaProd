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
from app import db
from services.session_service import SessionService
from datetime import datetime
import numpy as np

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
    vad_min_speech_duration: int = 10000  # ms
    vad_min_silence_duration: int = 500  # ms
    
    # Audio processing
    sample_rate: int = 16000
    chunk_size: int = 1024
    audio_format: str = "webm"
    
    # Transcription settings
    language: str = "en"
    min_confidence: float = 0.4  # 🔥 CRITICAL FIX: Reduced from 0.7 to 0.4 - less aggressive filtering
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
    
    # 🔥 INT-LIVE-I3: Interim throttling and endpointing
    interim_throttle_ms: int = 400  # Throttle interims to ~400ms
    min_token_diff: int = 5  # Minimum token difference to emit interim
    punctuation_boundary_chars: str = '.!?;:'
    min_tokens_for_punctuation_final: int = 3  # Min tokens before punctuation triggers final
    vad_tail_silence_ms: int = 1500  # VAD silence duration to trigger final

class TranscriptionService:
    """
    High-level transcription service that orchestrates VAD, audio processing, and Whisper streaming.
    Provides a unified interface for real-time meeting transcription with enhanced coordination.
    🔥 INT-LIVE-I3: Enhanced with interim throttling, endpointing, and metrics.
    """
    
    def __init__(self, config: Optional[TranscriptionServiceConfig] = None):
        self.config = config or TranscriptionServiceConfig()
        
        # 🔥 INT-LIVE-I3: Session-level interim throttling and metrics
        self.session_interim_state = {}  # {session_id: {last_interim_time, last_text, metrics}}
        
        # Import and initialize interim throttler
        from interim_throttling import get_interim_throttler
        self.interim_throttler = get_interim_throttler(self.config)
        
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
        
        # 🔥 CRITICAL FIX: Much less aggressive quality control to fix 92.3% WER
        self.dedup_buffer_size = 200  # Characters
        self.min_word_variety_ratio = 0.1  # 🔥 REDUCED: Much less aggressive - was 0.2
        self.max_repetition_threshold = 6  # 🔥 INCREASED: Allow more repetition - was 4
        self.min_meaningful_length = 1  # Allow single words
        
        # 🔥 INT-LIVE-I2: Adaptive confidence gating with hysteresis
        import os
        self.base_confidence = float(os.environ.get('MIN_CONFIDENCE', '0.6'))
        self.hysteresis_window = []  # Track recent confidence decisions
        self.hysteresis_size = 2  # Require 2 consecutive frames for state change
        self.suppression_active = False  # Current suppression state
        
        # 🔥 INT-LIVE-I2: Interim throttling and punctuation boundary detection
        self.interim_throttle_ms = 400  # 300-500ms range per specification
        self.min_interim_diff_chars = 5  # Minimum character difference for interim emit
        self.punctuation_marks = {'.', '!', '?', ';', ':'}  # Marks that trigger boundaries
        
        logger.info(f"Transcription service initialized with config: {asdict(self.config)}")
    
    def _compute_adaptive_confidence(self, vad_result: Optional[Dict[str, Any]]) -> float:
        """
        🔥 INT-LIVE-I2: Compute adaptive confidence threshold based on VAD quality.
        
        Args:
            vad_result: VAD analysis result with confidence/SNR metrics
            
        Returns:
            Adaptive confidence threshold (0.4 to 0.8 range)
        """
        # Start with base confidence from config
        base = self.base_confidence
        
        # Adjust based on VAD confidence if available
        if vad_result and 'confidence' in vad_result:
            vad_conf = vad_result['confidence']
            # If VAD confidence is low (poor signal), raise the threshold
            # If VAD confidence is high (clear signal), lower the threshold
            adjustment = 0.15 * (0.6 - vad_conf)
            adaptive = base + adjustment
        else:
            # No VAD info, use base threshold
            adaptive = base
        
        # Clamp to reasonable range
        return max(0.4, min(0.8, adaptive))
    
    def _apply_hysteresis_gating(self, confidence: float, threshold: float) -> bool:
        """
        🔥 INT-LIVE-I2: Apply hysteresis gating - require 2 consecutive frames for state change.
        
        Args:
            confidence: Current transcription confidence
            threshold: Adaptive confidence threshold
            
        Returns:
            True if should suppress, False if should allow
        """
        # Determine if this frame would be suppressed based on confidence
        would_suppress = confidence < threshold
        
        # Add to hysteresis window
        self.hysteresis_window.append(would_suppress)
        
        # Keep only recent decisions
        if len(self.hysteresis_window) > self.hysteresis_size:
            self.hysteresis_window.pop(0)
        
        # Need at least 2 frames to make a decision
        if len(self.hysteresis_window) < self.hysteresis_size:
            return self.suppression_active  # Use current state
        
        # Check if all recent frames agree on the decision
        all_suppress = all(self.hysteresis_window)
        all_allow = not any(self.hysteresis_window)
        
        if all_suppress and not self.suppression_active:
            # Switch to suppression mode
            self.suppression_active = True
            return True
        elif all_allow and self.suppression_active:
            # Switch to allow mode
            self.suppression_active = False
            return False
        else:
            # No consensus or no change needed, maintain current state
            return self.suppression_active
    
    def _should_emit_interim(self, text: str, now: float, last_emit: float, state: Dict[str, Any]) -> bool:
        """
        🔥 INT-LIVE-I2: Intelligent interim emission with throttling and punctuation boundaries.
        
        Args:
            text: Current transcription text buffer
            now: Current timestamp
            last_emit: Last interim emission timestamp  
            state: Session state
            
        Returns:
            True if should emit interim transcript
        """
        if not text or len(text.strip()) == 0:
            return False
        
        # Get last emitted text for diff comparison
        last_text = state.get('last_interim_text', '')
        
        # Check time-based throttling (300-500ms range)
        time_threshold = (now - last_emit) >= (self.interim_throttle_ms / 1000.0)
        
        # Check if there's meaningful new content (≥5 chars or punctuation)
        char_diff = len(text) - len(last_text)
        has_meaningful_diff = char_diff >= self.min_interim_diff_chars
        
        # Check if punctuation boundary was hit
        has_punctuation = any(p in text[-10:] for p in self.punctuation_marks)  # Check last 10 chars
        
        # Emit if time passed AND (meaningful diff OR punctuation boundary)
        should_emit = time_threshold and (has_meaningful_diff or has_punctuation)
        
        if should_emit:
            state['last_interim_text'] = text  # Update for next diff
            # 🔥 INT-LIVE-I2: Track punctuation boundaries
            if has_punctuation:
                state.get('stats', {})['punctuation_boundaries'] = state.get('stats', {}).get('punctuation_boundaries', 0) + 1
        
        return should_emit
    
    # Sync wrapper methods for Flask routes (avoids asyncio.run() in request handlers)
    def start_session_sync(self, session_id: Optional[str] = None, 
                          user_config: Optional[Dict[str, Any]] = None) -> str:
        """Synchronous wrapper for start_session."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use asyncio.run
                # For now, we'll create the session synchronously
                return self._start_session_sync_impl(session_id, user_config)
            else:
                return asyncio.run(self.start_session(session_id, user_config))
        except RuntimeError:
            # No event loop running
            return asyncio.run(self.start_session(session_id, user_config))
    
    def _start_session_sync_impl(self, session_id: Optional[str] = None, 
                                user_config: Optional[Dict[str, Any]] = None) -> str:
        """Direct synchronous implementation for start_session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if len(self.active_sessions) >= self.config.max_concurrent_sessions:
            raise Exception(f"Maximum concurrent sessions ({self.config.max_concurrent_sessions}) reached")
        
        # Create database session - FIXED model fields
        db_session = Session(
            external_id=session_id,  # FIXED: Use external_id instead of session_id
            title="Transcription Session",
            status='active',  # FIXED: Use 'active' instead of 'created'  
            locale=self.config.language,
            meta={
                'enable_realtime': self.config.enable_realtime,
                'enable_speaker_detection': self.config.enable_speaker_detection,
                'enable_sentiment_analysis': self.config.enable_sentiment_analysis,
                'sample_rate': self.config.sample_rate,
                'min_confidence': self.config.min_confidence,
                'vad_sensitivity': self.config.vad_sensitivity,
                'vad_min_speech_duration': self.config.vad_min_speech_duration,
                'vad_min_silence_duration': self.config.vad_min_silence_duration
            }
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
        # Note: whisper_service.start_session is async, but for sync mode we'll defer this
        
        self.total_sessions += 1
        logger.info(f"Started transcription session (sync): {session_id}")
        
        return session_id
    
    def end_session_sync(self, session_id: str) -> Dict[str, Any]:
        """Synchronous wrapper for end_session."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self._end_session_sync_impl(session_id)
            else:
                return asyncio.run(self.end_session(session_id))
        except RuntimeError:
            return asyncio.run(self.end_session(session_id))
    
    def _end_session_sync_impl(self, session_id: str) -> Dict[str, Any]:
        """Direct synchronous implementation for end_session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        
        # Update database session
        from sqlalchemy import select
        stmt = select(Session).filter_by(external_id=session_id)
        db_session = db.session.execute(stmt).scalar_one_or_none()
        if db_session:
            db_session.status = 'completed'
            db.session.commit()
            
            # Update final statistics
            stats = session_data['stats']
            db_session.total_segments = stats['total_segments']
            db_session.average_confidence = stats['average_confidence']
            db_session.total_duration = stats['total_audio_duration']
            db.session.commit()
        
        # Get final statistics
        final_stats = self._get_session_statistics(session_id)
        
        # Cleanup
        del self.active_sessions[session_id]
        del self.session_callbacks[session_id]
        
        logger.info(f"Ended transcription session (sync): {session_id}")
        return final_stats

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
        
        # Create database session - FIXED model fields
        db_session = Session(
            external_id=session_id,  # FIXED: Use external_id instead of session_id
            title="Transcription Session",
            status='active',  # FIXED: Use 'active' instead of 'created'  
            locale=self.config.language,
            meta={
                'enable_realtime': self.config.enable_realtime,
                'enable_speaker_detection': self.config.enable_speaker_detection,
                'enable_sentiment_analysis': self.config.enable_sentiment_analysis,
                'sample_rate': self.config.sample_rate,
                'min_confidence': self.config.min_confidence,
                'vad_sensitivity': self.config.vad_sensitivity,
                'vad_min_speech_duration': self.config.vad_min_speech_duration,
                'vad_min_silence_duration': self.config.vad_min_silence_duration
            }
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
        from sqlalchemy import select
        stmt = select(Session).filter_by(external_id=session_id)
        db_session = db.session.execute(stmt).scalar_one_or_none()
        if db_session:
            db_session.status = 'completed'
            db.session.commit()
            
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
        
        # Get database session ID from external ID
        from sqlalchemy import select
        from models.session import Session as DbSession
        
        stmt = select(DbSession).filter_by(external_id=session_id)
        db_session_obj = db.session.execute(stmt).scalar_one_or_none()
        
        if not db_session_obj:
            logger.error(f"Database session not found for external_id: {session_id}")
            return
            
        # Create segment using correct database schema
        from models.segment import Segment
        
        segment = Segment(
            session_id=db_session_obj.id,  # Use database ID, not external ID
            kind='final' if transcription_result.is_final else 'interim',
            text=transcription_result.text,
            avg_confidence=transcription_result.confidence,  # Correct field name
            start_ms=int((transcription_result.timestamp - transcription_result.duration) * 1000),
            end_ms=int(transcription_result.timestamp * 1000)
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
        
        # Update database session (using already retrieved db_session_obj)
        if db_session_obj:
            db_session_obj.total_segments = (db_session_obj.total_segments or 0) + 1
            db.session.commit()
        
        logger.debug(f"Stored segment {sequence_number} for session {session_id}")
    
    def _is_repetitive_text(self, text: str) -> bool:
        """
        Enhanced quality filter: Detect repetitive text patterns like 'You You You'.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if text appears to be repetitive garbage
        """
        if not text or len(text.strip()) < 1:
            return True
            
        words = text.strip().lower().split()
        if len(words) < 1:
            return True
            
        # 🔥 CRITICAL FIX: Only block if 3+ consecutive identical words (was blocking after 2)
        consecutive_count = 1
        for i in range(len(words) - 1):
            if words[i] == words[i + 1] and len(words[i]) > 1:
                consecutive_count += 1
                if consecutive_count >= 3:  # 🔥 Changed from 2 to 3 - less aggressive
                    logger.warning(f"BLOCKED excessive repetition: '{text}' ({consecutive_count} consecutive '{words[i]}')")
                    return True
            else:
                consecutive_count = 1
        
        # Enhanced repetition detection for edge cases
        if len(words) >= 2:
            # Check for excessive repetition of same word
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
                
            # 🔥 CRITICAL FIX: Only flag if word appears 3+ times in short texts
            max_word_count = max(word_counts.values())
            if len(words) <= 3 and max_word_count >= 3:  # 🔥 Changed from >1 to >=3
                most_common_word = max(word_counts, key=word_counts.get)
                logger.warning(f"BLOCKED short repetitive text: '{text}' ('{most_common_word}' appears {max_word_count} times)")
                return True
                
            # For longer texts, use threshold
            if len(words) > 3 and max_word_count > getattr(self, 'max_repetition_threshold', 2):
                most_common_word = max(word_counts, key=word_counts.get)
                logger.warning(f"BLOCKED repetitive text: '{text}' ('{most_common_word}' appears {max_word_count} times)")
                return True
                
            # Check word variety ratio for longer texts
            if len(words) > 3:
                unique_words = len(set(words))
                variety_ratio = unique_words / len(words)
                min_variety = getattr(self, 'min_word_variety_ratio', 0.6)
                
                if variety_ratio < min_variety:
                    logger.warning(f"BLOCKED low variety text: '{text}' (variety ratio: {variety_ratio:.2f})")
                    return True
            
        return False
    
    def _is_duplicate_of_recent(self, text: str, session_id: str) -> bool:
        """
        Check if text is substantially similar to recent transcription.
        
        Args:
            text: New text to check
            session_id: Session identifier
            
        Returns:
            True if text is likely a duplicate
        """
        if session_id not in self.active_sessions:
            return False
            
        session_data = self.active_sessions[session_id]
        rolling_text = session_data.get('rolling_text', '')
        
        if not rolling_text or not text:
            return False
            
        # 🔥 INT-LIVE-I2: Rolling Jaccard similarity on last ~80 chars with character n-grams
        WINDOW_SIZE = 80
        JACCARD_THRESHOLD = 0.85
        
        # Take last 80 chars of rolling buffer for comparison
        rolling_window = rolling_text[-WINDOW_SIZE:].lower().strip()
        text_lower = text.lower().strip()
        
        if not rolling_window or not text_lower:
            return False
        
        # Compute Jaccard similarity using character bigrams (more precise than word-level)
        jaccard_sim = self._jaccard_similarity_ngrams(text_lower, rolling_window, n=2)
        
        # Flag as duplicate if >85% similarity  
        if jaccard_sim > JACCARD_THRESHOLD:
            logger.debug(f"Rejected duplicate text: '{text}' (Jaccard similarity: {jaccard_sim:.3f})")
            return True
            
        return False
    
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
    
    def _jaccard_similarity_ngrams(self, text1: str, text2: str, n: int = 2) -> float:
        """
        🔥 INT-LIVE-I2: Compute Jaccard similarity using character n-grams.
        
        Args:
            text1: First text string
            text2: Second text string  
            n: N-gram size (default 2 for bigrams)
            
        Returns:
            Jaccard similarity coefficient (0.0 to 1.0)
        """
        def get_ngrams(text: str, n: int) -> set:
            """Extract character n-grams from text."""
            if len(text) < n:
                return {text}  # If text shorter than n, use whole text
            return {text[i:i+n] for i in range(len(text) - n + 1)}
        
        ngrams1 = get_ngrams(text1, n)
        ngrams2 = get_ngrams(text2, n)
        
        if not ngrams1 and not ngrams2:
            return 1.0  # Both empty
        if not ngrams1 or not ngrams2:
            return 0.0  # One empty
            
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _on_transcription_result(self, result: TranscriptionResult):
        """Handle transcription result callback with critical quality filtering."""
        session_id = result.metadata.get('session_id')
        if not session_id or session_id not in self.active_sessions:
            return
        
        # CRITICAL QUALITY FILTERS: Prevent repetitive garbage transcriptions
        text = result.text.strip()
        
        # Filter 1: Check for repetitive patterns like "You You You"
        if self._is_repetitive_text(text):
            logger.warning(f"QUALITY FILTER: Rejected repetitive transcription for session {session_id}: '{text}'")
            return
        
        # Filter 2: Check for duplicates of recent text
        if self._is_duplicate_of_recent(text, session_id):
            logger.debug(f"QUALITY FILTER: Rejected duplicate transcription for session {session_id}: '{text}'")
            return
        
        # Filter 3: Minimum confidence threshold (already applied by Whisper service)
        if result.confidence < self.config.min_confidence and not result.is_final:
            logger.debug(f"QUALITY FILTER: Rejected low confidence transcription: {result.confidence:.2f} < {self.config.min_confidence}")
            return
        
        # Filter 4: Minimum meaningful length
        if len(text) < 2 and not result.is_final:
            logger.debug(f"QUALITY FILTER: Rejected too short transcription: '{text}'")
            return
        
        # Quality check passed - update deduplication buffer
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]
            rolling_text = session_data.get('rolling_text', '')
            # Keep last N characters for deduplication
            new_rolling_text = (rolling_text + " " + text)[-self.dedup_buffer_size:]
            session_data['rolling_text'] = new_rolling_text
        
        logger.info(f"QUALITY CHECK PASSED: '{text}' (confidence: {result.confidence:.2f}, final: {result.is_final})")
        
        # Call registered callbacks with filtered result
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
    
    def _should_finalize(self, session_id: str, vad_result: Any, now: float, state: Dict[str, Any]) -> bool:
        """
        Determine if current audio chunk should trigger finalization.
        
        Args:
            session_id: Session identifier
            vad_result: VAD processing result
            now: Current timestamp
            state: Session state dictionary
            
        Returns:
            True if should finalize, False for interim
        """
        try:
            # 🔥 INT-LIVE-I2: Proper endpointing logic as specified
            # 1) Explicit finalization signal (is_final_chunk=True from Stop button)
            if state.get('end_of_stream', False):
                logger.debug("🔥 Finalizing on explicit end_of_stream (is_final_chunk=True)")
                return True
                
            # 2) VAD tail - PRIMARY trigger (300-500ms silence)
            if not vad_result.is_speech and len(state.get('rolling_text', '')) > 0:
                # Check if we've had silence for long enough
                last_speech_time = state.get('last_speech_time', now)
                silence_duration = (now - last_speech_time) * 1000  # ms
                VOICE_TAIL_MS = 400  # 300-500ms range, use 400ms as specified
                if silence_duration >= VOICE_TAIL_MS:
                    logger.debug(f"🔥 Finalizing on VAD tail: {silence_duration}ms silence ≥ {VOICE_TAIL_MS}ms")
                    return True
            else:
                # Update last speech time
                state['last_speech_time'] = now
                
            # 3) Punctuation boundary with minimum token count - SECONDARY trigger
            rolling_text = state.get('rolling_text', '')
            if rolling_text:
                tokens = rolling_text.split()
                has_punctuation = any(rolling_text.rstrip().endswith(p) for p in ['.', '!', '?', ';'])
                MIN_TOKENS_FOR_PUNCTUATION = 12  # As specified in requirements
                
                if has_punctuation and len(tokens) >= MIN_TOKENS_FOR_PUNCTUATION:
                    logger.debug(f"🔥 Finalizing on punctuation boundary: {len(tokens)} tokens with punctuation")
                    # Track punctuation boundary metric
                    state.get('stats', {})['punctuation_boundaries'] = state.get('stats', {}).get('punctuation_boundaries', 0) + 1
                    return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error in finalization logic for session {session_id}: {e}")
            return False
    
    def _persist_segment(self, session_id: str, text: str, confidence: float, timestamp: float) -> None:
        """
        Persist final segment to database.
        
        Args:
            session_id: Session identifier
            text: Final transcription text
            confidence: Transcription confidence
            timestamp: Timestamp
        """
        try:
            from models.segment import Segment
            from app import db
            
            # Get database session
            db_session = SessionService.get_session_by_external(session_id)
            if db_session:
                segment = Segment(
                    session_id=db_session.id,
                    text=text,
                    confidence=confidence,
                    start_time=timestamp,
                    end_time=timestamp + 1.0,
                    language='en'
                )
                db.session.add(segment)
                db.session.commit()
                
                logger.info(f"Persisted final segment: '{text}' (confidence: {confidence})")
            else:
                logger.warning(f"Could not find database session for {session_id}")
                
        except Exception as e:
            logger.error(f"Error persisting segment for session {session_id}: {e}")
    
    def _cleanup_stale_sessions(self):
        """Clean up stale sessions that may have been left orphaned."""
        current_time = time.time()
        stale_sessions = []
        
        for session_id, session_data in list(self.active_sessions.items()):
            last_activity = session_data.get('last_activity', 0)
            # Consider sessions stale if no activity for 30 minutes
            if current_time - last_activity > 1800:  # 30 minutes
                stale_sessions.append(session_id)
        
        for session_id in stale_sessions:
            try:
                logger.info(f"Cleaning up stale session: {session_id}")
                self.end_session_sync(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up stale session {session_id}: {e}")
        
        if stale_sessions:
            logger.info(f"Cleaned up {len(stale_sessions)} stale sessions")

    def end_session_sync(self, session_id: str) -> None:
        """
        INT-LIVE-I1: End session with final flush of any remaining buffer.
        """
        try:
            if session_id in self.active_sessions:
                state = self.active_sessions[session_id]
                
                # Flush any remaining rolling text as final
                rolling_text = state.get('rolling_text', '').strip()
                if rolling_text:
                    logger.info(f"Flushing final buffer for session {session_id}: '{rolling_text}'")
                    self._persist_segment(session_id, rolling_text, 0.8, time.time())
                    # Safe dictionary access to prevent AttributeError
                    stats = state.get('stats', {})
                    stats['final_events'] = stats.get('final_events', 0) + 1
                
                # Log session stats
                stats = state.get('stats', {})
                logger.info(f"Session {session_id} ended - Interim events: {stats.get('interim_events', 0)}, Final events: {stats.get('final_events', 0)}")
                
                # Clean up session
                del self.active_sessions[session_id]
                if session_id in self.session_callbacks:
                    del self.session_callbacks[session_id]
                    
        except Exception as e:
            logger.error(f"Error ending session {session_id}: {e}")
    
    def start_session_sync(self, session_id: str, user_config: Optional[Dict[str, Any]] = None) -> None:
        """
        FIXED: Add missing start_session_sync method that was being called everywhere.
        Synchronous session startup for immediate session registration.
        """
        try:
            if session_id in self.active_sessions:
                logger.info(f"Session {session_id} already active")
                return
            
            # Initialize session data structure
            self.active_sessions[session_id] = {
                'state': SessionState.IDLE,
                'created_at': time.time(),
                'last_activity': time.time(),
                'sequence_number': 0,
                'audio_chunks': [],
                'pending_processing': 0,
                'user_config': user_config or {},
                'rolling_text': '',  # Interim text buffer
                'last_interim_emit_ts': 0.0,  # Throttling timestamp
                'last_interim_text': '',  # Last interim text for diff comparison
                'end_of_stream': False,  # Finalization trigger
                'stats': {
                    'total_audio_duration': 0.0,
                    'speech_duration': 0.0,
                    'silence_duration': 0.0,
                    'total_segments': 0,
                    'interim_events': 0,  # Track interim events
                    'final_events': 0,   # Track final events
                    'average_confidence': 0.0,
                    # 🔥 INT-LIVE-I2: Enhanced metrics for quality monitoring
                    'dedupe_hits': 0,  # Count of duplicate text filtered
                    'low_conf_suppressed': 0,  # Count of low confidence rejections
                    'chunks_dropped': 0,  # Count of dropped audio chunks
                    'latency_samples': [],  # Rolling latency measurements (keep last 50)
                    'queue_len_samples': [],  # Queue length for p95 calculation
                    'adaptive_conf_adjustments': 0,  # Count of confidence adjustments
                    'punctuation_boundaries': 0,  # Count of punctuation-triggered boundaries
                    'interim_intervals': []  # Track interim emission intervals (ms)
                }
            }
            
            # Initialize callback list
            if session_id not in self.session_callbacks:
                self.session_callbacks[session_id] = []
            
            logger.info(f"Started transcription session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error starting session {session_id}: {e}")
    
    def process_audio_sync(self, session_id: str, audio_data: bytes, timestamp: Optional[float] = None,
                          mime_type: Optional[str] = None, client_rms: Optional[float] = None, 
                          is_final_signal: bool = False) -> Optional[Dict[str, Any]]:
        """
        INT-LIVE-I1: INTERIM UPDATES - Process audio with interim and final transcription support.
        Implements rolling buffer for interim results and proper finalization logic.
        
        Args:
            session_id: Session identifier
            audio_data: Raw audio bytes
            timestamp: Optional timestamp
            mime_type: MIME type of audio data (e.g., 'audio/webm')
            client_rms: Client-side RMS energy level
            is_final_signal: Whether this is a final chunk signal
            
        Returns:
            Processing result dictionary with interim/final transcription or None
        """
        try:
            if not audio_data or len(audio_data) == 0:
                return None
                
            if session_id not in self.active_sessions:
                logger.warning(f"Session {session_id} not found for audio processing")
                return None
            
            state = self.active_sessions[session_id]
            now = timestamp or time.time()
            
            # 1) Get rolling buffer and timestamps
            buf = state.setdefault('rolling_text', '')
            last_emit = state.setdefault('last_interim_emit_ts', 0.0)
            
            # VAD check for finalization decisions
            vad_result = self.vad_service.process_audio_chunk(audio_data, timestamp)
            logger.debug(f"VAD Result for session {session_id}: is_speech={vad_result.is_speech}, confidence={vad_result.confidence}")
            
            # Process with Whisper API
            logger.debug(f"Sending audio to Whisper API for session {session_id}, chunk size: {len(audio_data)} bytes")
            res = self.whisper_service.transcribe_chunk_sync(
                audio_data=audio_data,
                session_id=session_id
            )
            
            if not res or not res.get('text'):
                return None
                
            # 2) CRITICAL QUALITY FILTERING - Apply before updating buffer
            text = res['text'].strip()
            conf = float(res.get('confidence', 0.8))
            
            if text:
                # Filter 1: Check for repetitive patterns like "You You You" 
                if self._is_repetitive_text(text):
                    # 🔇 REDUCED NOISE: Only log repetitive text warnings for debugging
                    if len(text.split()) > 2:  # Only log significant repetitions
                        logger.debug(f"Quality: Filtered repetitive text ({len(text.split())} words)")
                    return None
                
                # Filter 2: Check for duplicates of recent text
                if self._is_duplicate_of_recent(text, session_id):
                    # 🔥 INT-LIVE-I2: Track deduplication metrics
                    state['stats']['dedupe_hits'] += 1
                    # 🔇 REDUCED NOISE: Minimal duplicate logging
                    return None
                
                # Filter 3: 🔥 INT-LIVE-I2 Adaptive confidence threshold with hysteresis
                adaptive_conf = self._compute_adaptive_confidence(vad_result)
                should_suppress = self._apply_hysteresis_gating(conf, adaptive_conf)
                
                if should_suppress:
                    # 🔥 INT-LIVE-I2: Track suppression metrics
                    state['stats']['low_conf_suppressed'] += 1
                    if adaptive_conf != self.base_confidence:
                        state['stats']['adaptive_conf_adjustments'] += 1
                    
                    # 🔇 REDUCED NOISE: Only log low confidence when significant
                    if conf < 0.3:  # Only log very low confidence
                        logger.debug(f"Quality: Adaptive confidence filter {conf:.2f} < {adaptive_conf:.2f}")
                    return None
                
                # Filter 4: Minimum meaningful length (more permissive)
                if len(text.strip()) < 1:
                    logger.debug(f"SYNC QUALITY FILTER: Rejected empty text for session {session_id}: '{text}'")
                    return None
                
                logger.info(f"SYNC QUALITY CHECK PASSED for session {session_id}: '{text}' (confidence: {conf:.2f})")
                
                # Quality check passed - append to rolling buffer
                buf += (' ' if buf and text else '') + text
                state['rolling_text'] = buf
                
                # 🔥 CRITICAL FIX: Re-check concatenated buffer for quality issues
                if self._is_repetitive_text(buf):
                    logger.warning(f"BUFFER QUALITY FILTER: Rejected concatenated repetitive text for session {session_id}: '{buf}'")
                    # Reset buffer to prevent repetitive patterns from accumulating
                    state['rolling_text'] = text  # Keep only the latest valid chunk
                    buf = text
                
                # 3) 🔥 INT-LIVE-I2: Smart interim vs final decision with punctuation & throttling
                emit_interim = self._should_emit_interim(buf, now, last_emit, state)
                finalize = self._should_finalize(session_id, vad_result, now, state)
                
                if finalize:
                    # FINAL: Additional quality check on final buffer
                    if self._is_repetitive_text(buf):
                        logger.warning(f"FINAL QUALITY FILTER: Blocked repetitive final text for session {session_id}: '{buf}'")
                        state['rolling_text'] = ''
                        return None
                    
                    logger.info(f"FINAL transcription for session {session_id}: '{buf}' (confidence: {conf})")
                    self._persist_segment(session_id, buf, conf, now)
                    state['rolling_text'] = ''
                    state['stats']['final_events'] += 1
                    
                    return {
                        'transcription': {
                            'text': buf,
                            'confidence': conf,
                            'is_final': True
                        },
                        'timestamp': now,
                        'session_id': session_id
                    }
                    
                elif emit_interim:
                    # INTERIM: Additional quality check on interim buffer
                    if self._is_repetitive_text(buf):
                        logger.debug(f"INTERIM QUALITY FILTER: Blocked repetitive interim text for session {session_id}: '{buf}'")
                        return None
                    
                    logger.info(f"INTERIM transcription for session {session_id}: '{buf}' (confidence: {conf})")
                    
                    # 🔥 INT-LIVE-I2: Track interim metrics
                    interval_ms = int((now - state['last_interim_emit_ts']) * 1000)
                    state['stats']['interim_intervals'].append(interval_ms)
                    # Keep only last 50 intervals for rolling average
                    if len(state['stats']['interim_intervals']) > 50:
                        state['stats']['interim_intervals'].pop(0)
                    
                    state['last_interim_emit_ts'] = now
                    state['stats']['interim_events'] += 1
                    
                    return {
                        'transcription': {
                            'text': buf,
                            'confidence': conf,
                            'is_final': False
                        },
                        'timestamp': now,
                        'session_id': session_id
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"CRITICAL ERROR in synchronous audio processing for session {session_id}: {e}", exc_info=True)
            return None
