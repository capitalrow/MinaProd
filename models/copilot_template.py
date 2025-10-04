"""
Copilot Template model for storing user-defined and system prompt templates.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db

if TYPE_CHECKING:
    from .user import User


class CopilotTemplate(db.Model):
    """
    Model for storing Copilot prompt templates.
    Supports both system templates and user-defined templates.
    """
    __tablename__ = 'copilot_templates'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Template identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Template metadata
    category: Mapped[str] = mapped_column(String(50), nullable=False, default='general')  # general, meetings, tasks, analysis, email
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Icon name for UI
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # System vs user-defined
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # User relationship
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # NULL for system templates
    user: Mapped[Optional["User"]] = relationship(back_populates="copilot_templates", foreign_keys=[user_id])
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert template to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'prompt': self.prompt,
            'category': self.category,
            'icon': self.icon,
            'is_system': self.is_system,
            'is_favorite': self.is_favorite,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def increment_usage(self):
        """Increment usage counter and update last used timestamp."""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        return f"<CopilotTemplate(id={self.id}, name='{self.name}', category='{self.category}', is_system={self.is_system})>"
