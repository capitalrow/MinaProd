"""
EventLedger Model - Atomic event tracking for CROWN+ Event Sequencing

Every event in Mina is tracked for auditability, replay, and debugging.
Ensures atomic, idempotent, and traceable event history.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, JSON, Enum as SQLEnum, Index, ForeignKey, Text, func
import enum
from .base import Base


class EventStatus(enum.Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EventType(enum.Enum):
    """CROWN+ Event Types - matches event sequencing spec"""
    # Recording Phase
    RECORD_START = "record_start"
    AUDIO_CHUNK_SENT = "audio_chunk_sent"
    TRANSCRIPT_PARTIAL = "transcript_partial"
    RECORD_STOP = "record_stop"
    
    # Post-Transcription Phase
    TRANSCRIPT_FINALIZED = "transcript_finalized"
    TRANSCRIPT_REFINED = "transcript_refined"
    INSIGHTS_GENERATE = "insights_generate"
    POST_TRANSCRIPTION_REVEAL = "post_transcription_reveal"
    
    # Reflection Phase
    SESSION_REFINED_READY = "session_refined_ready"
    ANALYTICS_UPDATE = "analytics_update"
    TASKS_GENERATION = "tasks_generation"
    SESSION_FINALIZED = "session_finalized"
    
    # User Interactions
    EDIT_COMMIT = "edit_commit"
    DASHBOARD_REFRESH = "dashboard_refresh"
    REPLAY_ENGAGE = "replay_engage"
    TASK_COMPLETE = "task_complete"
    
    # System Events
    ERROR_OCCURRED = "error_occurred"
    RECOVERY_ATTEMPTED = "recovery_attempted"


class EventLedger(Base):
    """
    Event Ledger for tracking all system events.
    
    Implements CROWN+ philosophy:
    - Atomic: Each event is a single unit of truth
    - Idempotent: Can be replayed safely
    - Traceable: Full audit trail for debugging and compliance
    """
    __tablename__ = "event_ledger"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event identification
    event_type: Mapped[EventType] = mapped_column(SQLEnum(EventType), nullable=False, index=True)
    event_name: Mapped[str] = mapped_column(String(128), nullable=False)  # Human-readable name
    
    # Session linkage
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('sessions.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    external_session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Event metadata
    status: Mapped[EventStatus] = mapped_column(
        SQLEnum(EventStatus),
        default=EventStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Event data and context
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Event input data
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)   # Event output data
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Tracing and correlation
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)  # For distributed tracing
    parent_event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('event_ledger.id'),
        nullable=True
    )
    
    # Performance tracking
    duration_ms: Mapped[Optional[float]] = mapped_column(nullable=True)  # Event processing time
    
    # Versioning for idempotency
    event_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_event_ledger_session_created', 'session_id', 'created_at'),
        Index('ix_event_ledger_type_status', 'event_type', 'status'),
        Index('ix_event_ledger_trace_created', 'trace_id', 'created_at'),
    )
    
    def __repr__(self):
        return f'<EventLedger {self.event_type.value} session={self.external_session_id} status={self.status.value}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'event_name': self.event_name,
            'session_id': self.session_id,
            'external_session_id': self.external_session_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'payload': self.payload,
            'result': self.result,
            'error_message': self.error_message,
            'trace_id': self.trace_id,
            'duration_ms': self.duration_ms,
            'event_version': self.event_version
        }
    
    @property
    def is_completed(self) -> bool:
        """Check if event completed successfully"""
        return self.status == EventStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if event failed"""
        return self.status == EventStatus.FAILED
    
    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Get processing time in seconds"""
        return self.duration_ms / 1000.0 if self.duration_ms else None
