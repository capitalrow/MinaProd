"""
Segment Model (M2)
SQLAlchemy 2.0-safe model for transcription segments with durable storage.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, DateTime, Text, ForeignKey, Float, Boolean, func, Index
from .base import Base

# Forward reference for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .session import Session
    from .comment import Comment

class Segment(Base):
    """
    Transcription segment model for M2 persistent storage.
    Represents individual transcribed text segments within a session.
    """
    __tablename__ = "segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(16))  # interim|final
    text: Mapped[str] = mapped_column(Text)
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float)
    start_ms: Mapped[Optional[int]] = mapped_column(BigInteger().with_variant(BigInteger(), 'postgresql'))  # Support JS timestamps
    end_ms: Mapped[Optional[int]] = mapped_column(BigInteger().with_variant(BigInteger(), 'postgresql'))    # Support JS timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 🔹 NEW: Interactive transcript attributes
    is_highlighted: Mapped[bool] = mapped_column(Boolean, default=False)
    highlight_color: Mapped[Optional[str]] = mapped_column(String(24), default="yellow")
    
    # CROWN+ Specification: Version control for concurrent edit conflict resolution
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    edited_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id'), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="segments")
    comments: Mapped[list["Comment"]] = relationship(back_populates="segment", cascade="all, delete-orphan")
    
    # Database indexes for query optimization
    __table_args__ = (
        # Index for filtering final segments
        Index('ix_segments_kind', 'kind'),
    )
    
    def __repr__(self):
        return f'<Segment {self.id}: "{self.text[:50]}...">' 
    
    @property
    def is_final(self):
        """Check if segment is final."""
        return self.kind == 'final'
    
    @property
    def duration_ms(self):
        """Get segment duration in milliseconds."""
        if self.start_ms is not None and self.end_ms is not None:
            return self.end_ms - self.start_ms
        return None
    
    @property
    def start_time_formatted(self):
        """Get formatted start time (MM:SS)."""
        if self.start_ms is None:
            return "00:00"
        total_seconds = self.start_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def is_high_confidence(self):
        """Check if segment has high confidence."""
        return (self.avg_confidence or 0.0) >= 0.8
    
    def to_dict(self):
        """Convert segment to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'kind': self.kind,
            'text': self.text,
            'avg_confidence': self.avg_confidence,
            'start_ms': self.start_ms,
            'end_ms': self.end_ms,
            'duration_ms': self.duration_ms,
            'start_time_formatted': self.start_time_formatted,
            'is_final': self.is_final,
            'is_high_confidence': self.is_high_confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def finalize(self):
        """Mark segment as final."""
        self.kind = 'final'