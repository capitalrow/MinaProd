"""
EventLedger Model - CROWN+ Traceability
Append-only audit log for all state transitions and events in the system.
Provides complete event lineage with trace_id correlation.
"""

import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, JSON, ForeignKey, func, Index
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

if TYPE_CHECKING:
    from .session import Session


class EventLedger(Base):
    """
    Append-only event ledger for complete system traceability.
    
    Every significant state transition emits an event that is logged here.
    This enables:
    - Complete audit trail per session
    - Event correlation via trace_id
    - Debugging and observability
    - Compliance and data integrity
    """
    __tablename__ = "event_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event identification
    trace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Order within trace
    
    # Session linkage
    session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), 
        nullable=True, 
        index=True
    )
    
    # Event payload and context
    event_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    event_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # User agent, IP, etc.
    
    # Status and error tracking
    status: Mapped[str] = mapped_column(String(32), default="success")  # success|failed|pending
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Event processing time
    
    # Relationships
    session: Mapped[Optional["Session"]] = relationship(back_populates="event_ledger_entries")
    
    # Database indexes for query optimization
    __table_args__ = (
        # Composite indexes for common queries
        Index('ix_event_ledger_trace_sequence', 'trace_id', 'event_sequence'),
        Index('ix_event_ledger_session_type', 'session_id', 'event_type'),
        Index('ix_event_ledger_type_created', 'event_type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<EventLedger trace={str(self.trace_id)[:8]} type={self.event_type} seq={self.event_sequence}>'
    
    def to_dict(self):
        """Convert event to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'trace_id': str(self.trace_id),
            'event_type': self.event_type,
            'event_sequence': self.event_sequence,
            'session_id': self.session_id,
            'status': self.status,
            'event_payload': self.event_payload,
            'event_metadata': self.event_metadata,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'duration_ms': self.duration_ms
        }
    
    @staticmethod
    def generate_trace_id() -> uuid.UUID:
        """Generate a new UUIDv7 for event tracing (time-ordered)."""
        # Note: UUIDv7 isn't in standard library yet, using UUID4 for now
        # TODO: Upgrade to UUIDv7 when available for time-based ordering
        return uuid.uuid4()
