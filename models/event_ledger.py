"""
EventLedger Model - Unified lifecycle event audit trail for CROWN+ specification compliance.

This model implements the formal EventLedger entity from the CROWN+ spec:
- Logs all events for audit and observability
- Maintains trace_id lineage for complete auditability
- Tracks the critical event chain: record_start → audio_chunk → transcript_partial → 
  record_stop → transcript_final → session_finalized → edit_commit → tasks_update → analytics_update
  
Event Types (Specification-Compliant):
  - record_start: Session recording initiated (maps to join_session)
  - audio_chunk: Audio data received and buffered
  - transcript_partial: Interim transcription result (maps to transcription_result with is_final=false)
  - record_stop: Recording stopped, finalization begins (maps to finalize_session)
  - transcript_final: Final transcription complete (maps to transcription_result with is_final=true)
  - session_finalized: Session processing complete, ready for editing
  - edit_commit: User edit committed with analytics recalc
  - tasks_update: Task list updated/regenerated
  - analytics_update: Analytics metrics recalculated
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, func, Index
from .base import Base

if TYPE_CHECKING:
    from .session import Session

class EventLedger(Base):
    """
    Unified event audit trail for complete session lifecycle tracking.
    
    Every significant event in the system is logged here with:
    - trace_id: unique identifier for the entire event chain
    - session_id: reference to the session
    - event_type: standardized event name from CROWN+ spec
    - payload: event-specific data
    - status: success|error|pending
    - timestamp: when the event occurred
    - latency_ms: processing time for performance tracking
    """
    __tablename__ = "event_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Core identifiers
    trace_id: Mapped[str] = mapped_column(String(64), index=True)  # UUID for complete event chain
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    
    # Event metadata
    event_type: Mapped[str] = mapped_column(String(64), index=True)  # record_start, audio_chunk, transcript_partial, etc.
    event_sequence: Mapped[int] = mapped_column(Integer, default=0)  # Sequence number within trace
    
    # Event data
    payload: Mapped[Optional[dict]] = mapped_column(JSON)  # Event-specific data
    status: Mapped[str] = mapped_column(String(32), default="success")  # success|error|pending
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing and performance
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Integer, nullable=True)  # Event processing time
    
    # Additional context
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    client_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Relationships
    session: Mapped["Session"] = relationship(back_populates="event_ledger")
    
    # Database indexes for query optimization
    __table_args__ = (
        # Composite index for trace analysis
        Index('ix_event_ledger_trace_sequence', 'trace_id', 'event_sequence'),
        # Index for session timeline queries
        Index('ix_event_ledger_session_timestamp', 'session_id', 'timestamp'),
        # Index for event type analysis
        Index('ix_event_ledger_type_status', 'event_type', 'status'),
    )
    
    def __repr__(self):
        return f'<EventLedger {self.event_type} @ {self.timestamp}>'
    
    @property
    def is_success(self):
        """Check if event completed successfully."""
        return self.status == 'success'
    
    @property
    def is_error(self):
        """Check if event encountered an error."""
        return self.status == 'error'
    
    def to_dict(self):
        """Convert event to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'trace_id': self.trace_id,
            'session_id': self.session_id,
            'event_type': self.event_type,
            'event_sequence': self.event_sequence,
            'payload': self.payload,
            'status': self.status,
            'error_message': self.error_message,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'latency_ms': self.latency_ms,
        }
    
    @staticmethod
    def log_event(
        session_id: int,
        trace_id: str,
        event_type: str,
        event_sequence: int = 0,
        payload: Optional[dict] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        latency_ms: Optional[float] = None
    ) -> "EventLedger":
        """
        Create and return a new event ledger entry.
        
        This is a factory method for consistent event logging.
        Caller must add to session and commit.
        """
        from models import db
        
        event = EventLedger()
        event.session_id = session_id
        event.trace_id = trace_id
        event.event_type = event_type
        event.event_sequence = event_sequence
        event.payload = payload or {}
        event.status = status
        event.error_message = error_message
        event.latency_ms = latency_ms
        
        db.session.add(event)
        return event
