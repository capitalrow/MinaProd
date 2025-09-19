"""
Summary model for storing AI-generated meeting insights.

This module contains the Summary model for persisting Actions, Decisions, and Risks
extracted from meeting sessions using AI analysis.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app_refactored import db
from extensions import db

class Summary(db.Model):
    """
    Summary model for storing AI-generated insights from meeting sessions.
    
    Stores the AI-generated summary in markdown format along with structured
    Actions, Decisions, and Risks extracted from the session transcript.
    """
    __tablename__ = 'summaries'
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Foreign key to session (removed FK constraint to avoid circular import issues)
    session_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # AI-generated content
    summary_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    decisions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    risks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    
    # Analysis metadata
    engine: Mapped[str] = mapped_column(String(50), nullable=False, default='mock')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Note: Relationship removed to avoid circular import issues
    # Access session via: db.session.get(Session, summary.session_id)
    
    def to_dict(self) -> dict:
        """Convert summary to dictionary for API responses."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'summary_md': self.summary_md,
            'actions': self.actions or [],
            'decisions': self.decisions or [],
            'risks': self.risks or [],
            'engine': self.engine,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, session_id={self.session_id}, engine='{self.engine}')>"