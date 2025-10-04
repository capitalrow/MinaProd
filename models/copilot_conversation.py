"""
Copilot Conversation model for storing chat history and context.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db

if TYPE_CHECKING:
    from .user import User


class CopilotConversation(db.Model):
    """
    Model for storing Copilot conversation messages and context.
    Enables context-aware responses by maintaining chat history.
    """
    __tablename__ = 'copilot_conversations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # User relationship
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship(back_populates="copilot_conversations", foreign_keys=[user_id])
    
    # Message content
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Contextual metadata
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Group messages by conversation session
    context_filter: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # What context was active (all, recent, today, etc.)
    template_used: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # Template name if used
    
    # Token usage tracking
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert conversation to dictionary for API responses."""
        return {
            'id': self.id,
            'role': self.role,
            'message': self.message,
            'session_id': self.session_id,
            'context_filter': self.context_filter,
            'template_used': self.template_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<CopilotConversation(id={self.id}, user_id={self.user_id}, role='{self.role}', session='{self.session_id}')>"
