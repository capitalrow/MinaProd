"""
Event Logger Service - CROWN+ Event Infrastructure
Atomic event logging with trace_id propagation and EventLedger persistence.
"""

import uuid
import time
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from contextlib import contextmanager
from models import db, EventLedger, Session

logger = logging.getLogger(__name__)


class EventLogger:
    """
    Central event logging service for CROWN+ traceability.
    
    Provides:
    - Atomic event emission with database logging
    - trace_id propagation across all events
    - Event sequencing within traces
    - Transaction safety with automatic rollback
    """
    
    def __init__(self):
        self._event_sequences: Dict[str, int] = {}  # trace_id -> sequence counter
    
    def emit_event(
        self,
        event_type: str,
        trace_id: uuid.UUID,
        session_id: Optional[int] = None,
        payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Emit an event with atomic logging to EventLedger.
        
        NOTE: This only logs to database. Socket.IO emission is handled by SessionEventCoordinator.
        
        Args:
            event_type: Internal event type for ledger (e.g., "record_start", "session_finalized")
            trace_id: UUID trace identifier for event correlation
            session_id: Database session ID for linkage
            payload: Event-specific data to log
            metadata: Contextual metadata (user agent, IP, etc.)
            
        Returns:
            True if event logged successfully, False otherwise
        """
        start_time = time.time()
        trace_id_str = str(trace_id)
        
        try:
            # Get next sequence number for this trace
            sequence = self._get_next_sequence(trace_id_str)
            
            # Create EventLedger entry
            event_entry = EventLedger(
                trace_id=trace_id,
                event_type=event_type,
                event_sequence=sequence,
                session_id=session_id,
                event_payload=payload or {},
                event_metadata=metadata or {},
                status="success",
                created_at=datetime.utcnow()
            )
            
            db.session.add(event_entry)
            db.session.commit()
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            event_entry.duration_ms = duration_ms
            db.session.commit()
            
            logger.info(
                f"✅ Event logged: {event_type} "
                f"[trace={trace_id_str[:8]}...seq={sequence}] "
                f"duration={duration_ms}ms"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Event logging failed: {event_type} [trace={trace_id_str[:8]}] - {e}")
            db.session.rollback()
            
            # Try to log the failure itself
            try:
                failure_entry = EventLedger(
                    trace_id=trace_id,
                    event_type=event_type,
                    event_sequence=self._get_next_sequence(trace_id_str),
                    session_id=session_id,
                    event_payload=payload or {},
                    status="failed",
                    error_message=str(e),
                    created_at=datetime.utcnow()
                )
                db.session.add(failure_entry)
                db.session.commit()
            except:
                pass  # Best effort
            
            return False
    
    @contextmanager
    def transaction(self, trace_id: uuid.UUID, event_type: str, session_id: Optional[int] = None):
        """
        Context manager for atomic event logging with automatic rollback on error.
        
        Usage:
            with event_logger.transaction(trace_id, "processing_task", session_id=1) as log:
                # Do work
                result = process_data()
                log(payload={"result": result})  # Commits on success
        """
        start_time = time.time()
        payload_holder = {}
        
        def log_payload(payload: Dict[str, Any]):
            payload_holder.update(payload)
        
        try:
            yield log_payload
            
            # Success - emit event
            duration_ms = int((time.time() - start_time) * 1000)
            self.emit_event(
                event_type=event_type,
                trace_id=trace_id,
                session_id=session_id,
                payload=payload_holder,
                metadata={"duration_ms": duration_ms}
            )
            
        except Exception as e:
            # Failure - log error
            logger.error(f"❌ Transaction failed: {event_type} - {e}")
            self.emit_event(
                event_type=f"{event_type}_failed",
                trace_id=trace_id,
                session_id=session_id,
                payload=payload_holder,
                metadata={"error": str(e), "duration_ms": int((time.time() - start_time) * 1000)}
            )
            raise
    
    def get_event_history(
        self, 
        trace_id: Optional[uuid.UUID] = None,
        session_id: Optional[int] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve event history from EventLedger.
        
        Args:
            trace_id: Filter by trace ID
            session_id: Filter by session ID
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        query = db.session.query(EventLedger)
        
        if trace_id:
            query = query.filter_by(trace_id=trace_id)
        if session_id:
            query = query.filter_by(session_id=session_id)
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        events = query.order_by(EventLedger.created_at.desc()).limit(limit).all()
        return [event.to_dict() for event in events]
    
    def get_trace_timeline(self, trace_id: uuid.UUID) -> list:
        """
        Get complete event timeline for a trace, ordered by sequence.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Ordered list of events in the trace
        """
        events = db.session.query(EventLedger).filter_by(
            trace_id=trace_id
        ).order_by(EventLedger.event_sequence).all()
        
        return [event.to_dict() for event in events]
    
    def _get_next_sequence(self, trace_id_str: str) -> int:
        """Get and increment sequence number for a trace."""
        if trace_id_str not in self._event_sequences:
            self._event_sequences[trace_id_str] = 0
        
        self._event_sequences[trace_id_str] += 1
        return self._event_sequences[trace_id_str]
    
    @staticmethod
    def generate_trace_id() -> uuid.UUID:
        """Generate a new trace ID for a recording session."""
        return uuid.uuid4()


# Singleton instance
_event_logger = None

def get_event_logger() -> EventLogger:
    """Get or create the singleton EventLogger instance."""
    global _event_logger
    if _event_logger is None:
        _event_logger = EventLogger()
    return _event_logger
