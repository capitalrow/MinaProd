"""
Participant Model for Meeting Speaker Management
SQLAlchemy 2.0-safe model for meeting participants with speaker diarization and role management.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Float, ForeignKey, func, JSON, Boolean
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .meeting import Meeting
    from .user import User


class Participant(Base):
    """
    Meeting participant model with speaker diarization data and role management.
    Links users to meetings with detailed participation metrics.
    """
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Relationships
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    meeting: Mapped["Meeting"] = relationship(back_populates="participants")
    
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped[Optional["User"]] = relationship()
    
    # Participant information
    name: Mapped[str] = mapped_column(String(128), nullable=False)  # Display name
    email: Mapped[Optional[str]] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(32), default="participant")  # organizer, presenter, participant, observer
    
    # Speaker diarization data
    speaker_id: Mapped[Optional[str]] = mapped_column(String(64))  # AI-assigned speaker identifier
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # Speaker identification confidence
    
    # Participation metrics
    talk_time_seconds: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    interruption_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    question_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    
    # Engagement metrics
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # Average sentiment (-1 to 1)
    engagement_score: Mapped[Optional[float]] = mapped_column(Float)  # Calculated engagement (0 to 1)
    participation_percentage: Mapped[Optional[float]] = mapped_column(Float)  # % of meeting time speaking
    
    # Status and settings
    is_present: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Additional metadata
    device_info: Mapped[Optional[dict]] = mapped_column(JSON)
    audio_quality_score: Mapped[Optional[float]] = mapped_column(Float)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f'<Participant {self.name} in Meeting {self.meeting_id}>'

    @property
    def talk_time_minutes(self) -> float:
        """Get talk time in minutes."""
        return (self.talk_time_seconds or 0) / 60.0

    @property
    def talk_time_formatted(self) -> str:
        """Get formatted talk time as MM:SS."""
        if not self.talk_time_seconds:
            return "00:00"
        
        minutes = int(self.talk_time_seconds // 60)
        seconds = int(self.talk_time_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def is_organizer(self) -> bool:
        """Check if participant is the meeting organizer."""
        return self.role == "organizer"

    @property
    def is_presenter(self) -> bool:
        """Check if participant is a presenter."""
        return self.role in ["organizer", "presenter"]

    def calculate_participation_percentage(self, total_meeting_duration: float):
        """Calculate participation percentage based on talk time and meeting duration."""
        if not total_meeting_duration or not self.talk_time_seconds:
            self.participation_percentage = 0.0
            return
        
        self.participation_percentage = min(100.0, (self.talk_time_seconds / total_meeting_duration) * 100)

    def update_talk_metrics(self, additional_seconds: float, words: int = 0):
        """Update talk time and word count."""
        self.talk_time_seconds = (self.talk_time_seconds or 0) + additional_seconds
        self.word_count = (self.word_count or 0) + words

    def set_sentiment(self, sentiment: float):
        """Set sentiment score (between -1 and 1)."""
        self.sentiment_score = max(-1.0, min(1.0, sentiment))

    def join_meeting(self):
        """Record participant joining the meeting."""
        self.is_present = True
        self.joined_at = datetime.utcnow()

    def leave_meeting(self):
        """Record participant leaving the meeting."""
        self.is_present = False
        self.left_at = datetime.utcnow()

    def to_dict(self):
        """Convert participant to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'speaker_id': self.speaker_id,
            'confidence_score': self.confidence_score,
            'talk_time_seconds': self.talk_time_seconds,
            'talk_time_minutes': self.talk_time_minutes,
            'talk_time_formatted': self.talk_time_formatted,
            'word_count': self.word_count,
            'interruption_count': self.interruption_count,
            'question_count': self.question_count,
            'sentiment_score': self.sentiment_score,
            'engagement_score': self.engagement_score,
            'participation_percentage': self.participation_percentage,
            'is_present': self.is_present,
            'is_organizer': self.is_organizer,
            'is_presenter': self.is_presenter,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'left_at': self.left_at.isoformat() if self.left_at else None,
            'audio_quality_score': self.audio_quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }