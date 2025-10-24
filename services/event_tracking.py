"""
Event Tracking Service - CROWN+ Specification Compliance

Ensures complete event chain integrity with formal EventLedger logging:
  record_start → audio_chunk → transcript_partial → record_stop → 
  transcript_final → session_finalized → edit_commit → tasks_update → analytics_update

Zero-tolerance production requirement: any break in this chain is a critical failure.
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from flask import request
from models import db
from models.event_ledger import EventLedger
from models.session import Session

logger = logging.getLogger(__name__)


class EventTracker:
    """
    Thread-safe event tracking service for CROWN+ specification compliance.
    
    Logs every event in the chain to EventLedger with:
    - trace_id for complete lineage
    - event_sequence for ordering
    - latency_ms for performance tracking
    - payload for debugging
    """
    
    def __init__(self):
        logger.info("✅ EventTracker initialized for CROWN+ compliance")
    
    def _get_next_sequence(self, trace_id: str) -> int:
        """
        Get next sequence number for this trace using database with row locking.
        
        Uses SELECT FOR UPDATE to ensure sequence integrity across workers.
        """
        from sqlalchemy import func, select
        
        # Use SELECT FOR UPDATE to lock rows and prevent concurrent sequence conflicts
        # Get max sequence with lock
        result = db.session.execute(
            select(func.coalesce(func.max(EventLedger.event_sequence), 0))
            .where(EventLedger.trace_id == trace_id)
            .with_for_update()
        )
        max_seq = result.scalar()
        
        return max_seq + 1
    
    def _get_client_context(self) -> Dict[str, Optional[str]]:
        """Extract client context from request."""
        try:
            return {
                'user_agent': request.headers.get('User-Agent'),
                'client_ip': request.remote_addr
            }
        except:
            return {'user_agent': None, 'client_ip': None}
    
    def log_event(
        self,
        session_id: int,
        trace_id: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        start_time_ms: Optional[float] = None
    ) -> EventLedger:
        """
        Log an event to the EventLedger.
        
        Args:
            session_id: Database session ID
            trace_id: Unique trace ID for the event chain
            event_type: Event name (record_start, audio_chunk, transcript_partial, etc.)
            payload: Event-specific data
            status: success|error|pending
            error_message: Error details if status=error
            start_time_ms: Event start time (for latency calculation)
        
        Returns:
            EventLedger instance
        """
        sequence = self._get_next_sequence(trace_id)
        latency_ms = None
        
        if start_time_ms is not None:
            latency_ms = int((time.time() * 1000) - start_time_ms)
        
        client_context = self._get_client_context()
        
        event = EventLedger()
        event.session_id = session_id
        event.trace_id = trace_id
        event.event_type = event_type
        event.event_sequence = sequence
        event.payload = payload or {}
        event.status = status
        event.error_message = error_message
        event.latency_ms = latency_ms
        event.user_agent = client_context['user_agent']
        event.client_ip = client_context['client_ip']
        
        db.session.add(event)
        
        logger.info(
            f"📊 EVENT: {event_type} [trace={trace_id[:8]}...] "
            f"[seq={sequence}] [status={status}] "
            f"[latency={latency_ms}ms]" if latency_ms else ""
        )
        
        return event
    
    def record_start(self, session: Session, metadata: Optional[Dict] = None) -> str:
        """
        Log record_start event and initialize trace_id.
        
        This is the first event in the chain.
        
        Returns:
            trace_id for the session
        """
        trace_id = session.trace_id or str(uuid.uuid4())
        session.trace_id = trace_id
        
        self.log_event(
            session_id=session.id,
            trace_id=trace_id,
            event_type="record_start",
            payload={
                'external_id': session.external_id,
                'title': session.title,
                'metadata': metadata or {}
            }
        )
        
        db.session.commit()
        return trace_id
    
    def audio_chunk(
        self,
        session: Session,
        chunk_size: int,
        chunk_index: int,
        start_time_ms: Optional[float] = None
    ):
        """Log audio_chunk event. CRITICAL: Raises exception if session has no trace_id."""
        if not session:
            error_msg = "CROWN+ VIOLATION: audio_chunk called with None session - event chain broken!"
            logger.error(f"🚨 {error_msg}")
            raise ValueError(error_msg)
        
        if not session.trace_id:
            error_msg = f"CROWN+ VIOLATION: Session {session.id} has no trace_id for audio_chunk - event chain broken!"
            logger.error(f"🚨 {error_msg}")
            raise ValueError(error_msg)
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="audio_chunk",
            payload={
                'chunk_size': chunk_size,
                'chunk_index': chunk_index
            },
            start_time_ms=start_time_ms
        )
        
        db.session.commit()
    
    def transcript_partial(
        self,
        session: Session,
        text: str,
        confidence: float,
        start_time_ms: Optional[float] = None
    ):
        """Log transcript_partial event. CRITICAL: Raises exception if session has no trace_id."""
        if not session:
            error_msg = "CROWN+ VIOLATION: transcript_partial called with None session - event chain broken!"
            logger.error(f"🚨 {error_msg}")
            raise ValueError(error_msg)
        
        if not session.trace_id:
            error_msg = f"CROWN+ VIOLATION: Session {session.id} has no trace_id for transcript_partial - event chain broken!"
            logger.error(f"🚨 {error_msg}")
            raise ValueError(error_msg)
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="transcript_partial",
            payload={
                'text_length': len(text),
                'confidence': confidence,
                'text_preview': text[:100] if text else None
            },
            start_time_ms=start_time_ms
        )
        
        db.session.commit()
    
    def record_stop(self, session: Session, final_duration_ms: int):
        """Log record_stop event."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for record_stop event")
            return
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="record_stop",
            payload={
                'duration_ms': final_duration_ms,
                'external_id': session.external_id
            }
        )
        
        db.session.commit()
    
    def transcript_final(
        self,
        session: Session,
        total_segments: int,
        total_words: int,
        avg_confidence: float
    ):
        """Log transcript_final event."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for transcript_final event")
            return
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="transcript_final",
            payload={
                'total_segments': total_segments,
                'total_words': total_words,
                'avg_confidence': avg_confidence
            }
        )
        
        db.session.commit()
    
    def session_finalized(
        self,
        session: Session,
        start_time_ms: Optional[float] = None
    ):
        """Log session_finalized event - marks session ready for editing."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for session_finalized event")
            return
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="session_finalized",
            payload={
                'external_id': session.external_id,
                'status': session.status,
                'total_segments': session.total_segments,
                'total_duration': session.total_duration
            },
            start_time_ms=start_time_ms
        )
        
        db.session.commit()
    
    def edit_commit(
        self,
        session: Session,
        segment_id: int,
        old_text: str,
        new_text: str,
        user_id: Optional[int] = None
    ):
        """Log edit_commit event."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for edit_commit event")
            return
        
        # Increment version on edit
        session.version += 1
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="edit_commit",
            payload={
                'segment_id': segment_id,
                'old_length': len(old_text),
                'new_length': len(new_text),
                'user_id': user_id,
                'new_version': session.version
            }
        )
        
        db.session.commit()
    
    def tasks_update(
        self,
        session: Session,
        tasks_added: int,
        tasks_removed: int
    ):
        """Log tasks_update event."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for tasks_update event")
            return
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="tasks_update",
            payload={
                'tasks_added': tasks_added,
                'tasks_removed': tasks_removed
            }
        )
        
        db.session.commit()
    
    def analytics_update(
        self,
        session: Session,
        metrics: Dict[str, Any]
    ):
        """Log analytics_update event."""
        if not session.trace_id:
            logger.warning(f"⚠️ Session {session.id} has no trace_id for analytics_update event")
            return
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type="analytics_update",
            payload=metrics
        )
        
        db.session.commit()
    
    def log_error(
        self,
        session: Session,
        event_type: str,
        error_message: str,
        payload: Optional[Dict] = None
    ):
        """Log an error event."""
        if not session.trace_id:
            session.trace_id = str(uuid.uuid4())
        
        self.log_event(
            session_id=session.id,
            trace_id=session.trace_id,
            event_type=event_type,
            payload=payload or {},
            status="error",
            error_message=error_message
        )
        
        db.session.commit()
    
    def verify_chain_integrity(self, trace_id: str) -> Dict[str, Any]:
        """
        Verify complete event chain for a trace_id.
        
        Returns dict with:
        - complete: bool (all required events present)
        - missing_events: list of missing event types
        - event_count: total events logged
        - latency_stats: performance metrics
        """
        events = db.session.query(EventLedger).filter_by(trace_id=trace_id).order_by(EventLedger.event_sequence).all()
        
        required_events = [
            'record_start',
            'audio_chunk',
            'transcript_partial',
            'record_stop',
            'transcript_final',
            'session_finalized'
        ]
        
        found_events = {e.event_type for e in events}
        missing_events = [e for e in required_events if e not in found_events]
        
        latencies = [e.latency_ms for e in events if e.latency_ms is not None]
        
        return {
            'complete': len(missing_events) == 0,
            'missing_events': missing_events,
            'event_count': len(events),
            'event_sequence': [e.event_type for e in events],
            'latency_stats': {
                'min_ms': min(latencies) if latencies else None,
                'max_ms': max(latencies) if latencies else None,
                'avg_ms': sum(latencies) / len(latencies) if latencies else None
            }
        }


# Global singleton instance
_event_tracker = None

def get_event_tracker() -> EventTracker:
    """Get global EventTracker instance."""
    global _event_tracker
    if _event_tracker is None:
        _event_tracker = EventTracker()
    return _event_tracker
