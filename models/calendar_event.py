"""
Calendar Event Model for Meeting Scheduling Integration
SQLAlchemy 2.0-safe model for calendar integration with external providers.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, Boolean, ForeignKey, func, JSON
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .meeting import Meeting


class CalendarEvent(Base):
    """
    Calendar event model for integration with external calendar providers.
    Links meetings to calendar events across different platforms.
    """
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Meeting relationship
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    meeting: Mapped["Meeting"] = relationship(back_populates="calendar_events")
    
    # Calendar provider information
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # google, outlook, apple, other
    external_event_id: Mapped[str] = mapped_column(String(256), nullable=False)  # Provider's event ID
    calendar_id: Mapped[Optional[str]] = mapped_column(String(256))  # Provider's calendar ID
    
    # Event details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(256))
    
    # Scheduling
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(Text)  # RRULE string
    
    # Event metadata
    attendees: Mapped[Optional[list]] = mapped_column(JSON)  # List of attendee email addresses
    organizer_email: Mapped[Optional[str]] = mapped_column(String(120))
    
    # Integration status
    sync_status: Mapped[str] = mapped_column(String(32), default="synced")  # synced, pending, failed
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sync_error: Mapped[Optional[str]] = mapped_column(Text)
    
    # Meeting integration settings
    auto_create_meeting: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_start_recording: Mapped[bool] = mapped_column(Boolean, default=False)
    send_meeting_link: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f'<CalendarEvent {self.provider}:{self.external_event_id}>'

    @property
    def duration_minutes(self) -> int:
        """Calculate event duration in minutes."""
        duration = self.end_time - self.start_time
        return int(duration.total_seconds() / 60)

    @property
    def is_past(self) -> bool:
        """Check if event is in the past."""
        return self.end_time < datetime.utcnow()

    @property
    def is_upcoming(self) -> bool:
        """Check if event is upcoming (within next 24 hours)."""
        now = datetime.utcnow()
        return self.start_time > now and (self.start_time - now).total_seconds() < 86400

    @property
    def is_happening_now(self) -> bool:
        """Check if event is currently happening."""
        now = datetime.utcnow()
        return self.start_time <= now <= self.end_time

    def mark_sync_success(self):
        """Mark calendar event as successfully synced."""
        self.sync_status = "synced"
        self.last_synced = datetime.utcnow()
        self.sync_error = None

    def mark_sync_failed(self, error: str):
        """Mark calendar event sync as failed."""
        self.sync_status = "failed"
        self.sync_error = error

    def to_dict(self):
        """Convert calendar event to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'meeting_id': self.meeting_id,
            'provider': self.provider,
            'external_event_id': self.external_event_id,
            'calendar_id': self.calendar_id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'timezone': self.timezone,
            'is_all_day': self.is_all_day,
            'is_recurring': self.is_recurring,
            'recurrence_rule': self.recurrence_rule,
            'attendees': self.attendees,
            'organizer_email': self.organizer_email,
            'sync_status': self.sync_status,
            'last_synced': self.last_synced.isoformat() if self.last_synced else None,
            'sync_error': self.sync_error,
            'auto_create_meeting': self.auto_create_meeting,
            'auto_start_recording': self.auto_start_recording,
            'send_meeting_link': self.send_meeting_link,
            'duration_minutes': self.duration_minutes,
            'is_past': self.is_past,
            'is_upcoming': self.is_upcoming,
            'is_happening_now': self.is_happening_now,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }