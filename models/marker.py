"""
Marker Model
Represents meeting markers (/decision, /todo, /risk) captured during live transcription.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

if TYPE_CHECKING:
    from .user import User


class Marker(Base):
    """Model for meeting markers captured during transcription."""
    
    __tablename__ = 'markers'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False)  # 'decision', 'todo', 'risk'
    content = Column(Text, nullable=False)
    speaker = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign key to User
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relationship to User
    user = relationship("User", back_populates="markers")
    
    def __repr__(self):
        return f'<Marker {self.type}: {self.content[:50]}...>'
    
    def to_dict(self):
        """Convert marker to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'speaker': self.speaker,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp is not None else None,
            'created_at': self.created_at.isoformat() if self.created_at is not None else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at is not None else None,
            'user_id': self.user_id
        }