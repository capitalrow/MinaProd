"""
Session Event Coordinator - CROWN+ Event Pipeline
Unified event emission layer that integrates EventLogger with session lifecycle.
Provides backward-compatible dual event emission during migration.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from flask_socketio import emit as socketio_emit
from models import db, Session
from services.event_logger import get_event_logger

# Import socketio for direct emission
try:
    from app import socketio
except ImportError:
    socketio = None

logger = logging.getLogger(__name__)

# Feature flag for dual event emission (backward compatibility)
ENABLE_LEGACY_EVENTS = True


class SessionEventCoordinator:
    """
    Coordinates all session-related events with EventLogger integration.
    
    Responsibilities:
    - Emit events to Socket.IO clients
    - Log all events to EventLedger via EventLogger
    - Provide backward compatibility with legacy event names
    - Maintain trace_id propagation through event chain
    """
    
    def __init__(self):
        self.event_logger = get_event_logger()
    
    def emit_record_start(
        self, 
        session: Session, 
        room: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit record_start event when transcription session begins.
        
        Args:
            session: Session database object with trace_id
            room: Socket.IO room to broadcast to
            metadata: Additional context (user agent, IP, etc.)
        """
        payload = {
            'session_id': session.external_id,
            'trace_id': str(session.trace_id),
            'started_at': session.started_at.isoformat(),
            'title': session.title,
            'status': 'recording'
        }
        
        # Log to EventLedger and emit to Socket.IO
        success = self.event_logger.emit_event(
            event_type='record_start',
            trace_id=session.trace_id,
            session_id=session.id,
            payload=payload,
            metadata=metadata or {})
        
        # Backward compatibility: Also emit legacy event name
        if ENABLE_LEGACY_EVENTS:
            try:
                legacy_payload = {
                    'status': 'started',
                    'session_id': session.external_id,
                    'message': 'Transcription session started'
                }
                if room:
                    socketio_emit('session_started', legacy_payload)
                else:
                    socketio_emit('session_started', legacy_payload)
            except Exception as e:
                logger.warning(f"Legacy event emission failed: {e}")
        
        return success
    
    def emit_transcript_partial(
        self,
        session: Session,
        text: str,
        confidence: float,
        room: Optional[str] = None,
        segments: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit transcript_partial event for interim transcription results.
        
        Args:
            session: Session database object
            text: Transcribed text
            confidence: Confidence score (0-1)
            room: Socket.IO room
            segments: Optional segment data
            metadata: Additional context
        """
        payload = {
            'session_id': session.external_id,
            'trace_id': str(session.trace_id),
            'text': text,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'partial',
            'segments': segments or []
        }
        
        # Log and emit
        success = self.event_logger.emit_event(
            event_type='transcript_partial',
            trace_id=session.trace_id,
            session_id=session.id,
            payload=payload,
            metadata=metadata or {})
        
        # Backward compatibility
        if ENABLE_LEGACY_EVENTS and confidence > 0.1:
            try:
                legacy_payload = {
                    'text': text,
                    'confidence': confidence,
                    'session_id': session.external_id,
                    'type': 'success' if text else 'partial',
                    'segments': segments or []
                }
                if room:
                    socketio_emit('transcription_result', legacy_payload)
                else:
                    socketio_emit('transcription_result', legacy_payload)
            except Exception as e:
                logger.warning(f"Legacy event emission failed: {e}")
        
        return success
    
    def emit_transcript_final(
        self,
        session: Session,
        text: str,
        confidence: float,
        room: Optional[str] = None,
        segments: Optional[list] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit transcript_final event for finalized segment after silence/punctuation.
        
        Args:
            session: Session database object
            text: Final transcribed text
            confidence: Confidence score
            room: Socket.IO room
            segments: Segment data
            metadata: Additional context
        """
        payload = {
            'session_id': session.external_id,
            'trace_id': str(session.trace_id),
            'text': text,
            'confidence': confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'type': 'final',
            'segments': segments or []
        }
        
        success = self.event_logger.emit_event(
            event_type='transcript_final',
            trace_id=session.trace_id,
            session_id=session.id,
            payload=payload,
            metadata=metadata or {})
        
        return success
    
    def emit_session_finalized(
        self,
        session: Session,
        room: Optional[str] = None,
        final_stats: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit session_finalized event when recording stops and session is complete.
        
        This triggers the PostTranscriptionOrchestrator to begin processing.
        
        Args:
            session: Session database object
            room: Socket.IO room
            final_stats: Session statistics (duration, segments, etc.)
            metadata: Additional context
        """
        payload = {
            'session_id': session.external_id,
            'trace_id': str(session.trace_id),
            'status': 'finalized',
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'stats': final_stats or {
                'total_segments': session.total_segments,
                'total_duration': session.total_duration,
                'average_confidence': session.average_confidence
            }
        }
        
        # Log to EventLedger
        success = self.event_logger.emit_event(
            event_type='session_finalized',
            trace_id=session.trace_id,
            session_id=session.id,
            payload=payload,
            metadata=metadata or {}
        )
        
        # Emit to Socket.IO separately (only if socketio available and in proper context)
        if room and socketio:
            try:
                socketio.emit('session_finalized', payload, to=room)
            except RuntimeError as e:
                # Ignore "working outside of request context" errors from background tasks
                logger.debug(f"Socket.IO emit skipped (background context): {e}")
        
        # Backward compatibility
        if ENABLE_LEGACY_EVENTS:
            try:
                legacy_payload = {
                    'status': 'ended',
                    'session_id': session.external_id,
                    'message': 'Transcription session ended'
                }
                if room:
                    socketio_emit('session_ended', legacy_payload)
                else:
                    socketio_emit('session_ended', legacy_payload)
            except Exception as e:
                logger.warning(f"Legacy event emission failed: {e}")
        
        return success
    
    def emit_processing_event(
        self,
        session: Session,
        task_type: str,
        status: str,
        room: Optional[str] = None,
        payload_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit post-transcription processing events (analytics, tasks, summary, refinement).
        
        Args:
            session: Session database object
            task_type: Type of task (analytics, tasks, summary, refinement)
            status: Status (started, ready, failed)
            room: Socket.IO room
            payload_data: Task-specific data
            metadata: Additional context
        """
        event_name = f"{task_type}_{status}"
        
        payload = {
            'session_id': session.external_id,
            'trace_id': str(session.trace_id),
            'task_type': task_type,
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            **(payload_data or {})
        }
        
        success = self.event_logger.emit_event(
            event_type=event_name,
            trace_id=session.trace_id,
            session_id=session.id,
            payload=payload,
            metadata=metadata or {})
        
        return success


# Singleton instance
_coordinator = None

def get_session_event_coordinator() -> SessionEventCoordinator:
    """Get or create the singleton SessionEventCoordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = SessionEventCoordinator()
    return _coordinator
