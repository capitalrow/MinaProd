"""
Session Model (M2)
SQLAlchemy 2.0-safe model for meeting sessions with durable storage.
"""

import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, JSON, Boolean, Float, func
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .segment import Segment
    from .shared_link import SharedLink  
    from .metrics import ChunkMetric, SessionMetric

class Session(Base):
    """
    Meeting session model for M2 persistent storage.
    Represents a single transcription session with metadata.
    """
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # WS/session key
    title: Mapped[str] = mapped_column(String(255), default="Untitled Meeting")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active|completed|error
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    locale: Mapped[Optional[str]] = mapped_column(String(10))
    device_info: Mapped[Optional[dict]] = mapped_column(JSON)
    meta: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Statistics fields required by TranscriptionService
    total_segments: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    average_confidence: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    total_duration: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    
    segments: Mapped[list["Segment"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", lazy="noload"
    )
    
    # M3: Summary relationship - accessed via backref from Summary model
    # Note: Relationship defined in Summary model to avoid circular imports
    
    # M4: Shared links relationship  
    shared_links: Mapped[list["SharedLink"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    
    # 🎯 OBSERVER: Metrics relationships for comprehensive observability
    # TODO: OBSERVER-DASHBOARD-PIN - Once Mina app is stable, expose session_scores,
    # latency metrics, and text quality metrics in Founder Dashboard for visibility.
    chunk_metrics: Mapped[list["ChunkMetric"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    session_metrics: Mapped[Optional["SessionMetric"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", uselist=False
    )
    
    def __repr__(self):
        return f'<Session {self.external_id}: {self.title}>'
    
    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.status == 'active'
    
    @property
    def segments_count(self):
        """Get count of segments in session using denormalized count."""
        # Use denormalized total_segments field to avoid loading entire segments collection
        if self.total_segments is not None:
            return self.total_segments
        # Fallback to database count query if denormalized field is not available
        from . import db
        from .segment import Segment
        return db.session.scalar(func.count(Segment.id).where(Segment.session_id == self.id)) or 0
    
    def to_dict(self):
        """Convert session to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'title': self.title,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'locale': self.locale,
            'device_info': self.device_info,
            'meta': self.meta,
            'segments_count': self.segments_count
        }
    
    def complete(self):
        """Mark session as completed."""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
    
    def mark_error(self):
        """Mark session as error state."""
        self.status = 'error'
    
    @staticmethod
    def generate_external_id():
        """Generate a unique external ID for session identification."""
        return str(uuid.uuid4())
