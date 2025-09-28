"""
Summary model for storing AI-generated meeting insights.

This module contains the Summary model for persisting Actions, Decisions, and Risks
extracted from meeting sessions using AI analysis.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app import db


class SummaryLevel(enum.Enum):
    """Summary detail levels."""
    BRIEF = "brief"           # Executive summary - 2-3 sentences
    STANDARD = "standard"     # Standard summary - 1-2 paragraphs  
    DETAILED = "detailed"     # Comprehensive summary - multiple sections
    

class SummaryStyle(enum.Enum):
    """Summary style types."""
    EXECUTIVE = "executive"   # C-level focused, strategic decisions
    ACTION = "action"         # Task and action-item focused
    TECHNICAL = "technical"   # Technical details and decisions
    NARRATIVE = "narrative"   # Story-like, chronological flow
    BULLET = "bullet"         # Bullet points and lists


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
    
    # Summary configuration
    level: Mapped[SummaryLevel] = mapped_column(Enum(SummaryLevel), nullable=False, default=SummaryLevel.STANDARD)
    style: Mapped[SummaryStyle] = mapped_column(Enum(SummaryStyle), nullable=False, default=SummaryStyle.EXECUTIVE)
    
    # AI-generated content
    summary_md: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    decisions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    risks: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    
    # Multi-level content
    brief_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # 2-3 sentences
    detailed_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # Comprehensive analysis
    
    # Style-specific content
    executive_insights: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    technical_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    action_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)
    
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
            'level': self.level.value if self.level else None,
            'style': self.style.value if self.style else None,
            'summary_md': self.summary_md,
            'brief_summary': self.brief_summary,
            'detailed_summary': self.detailed_summary,
            'actions': self.actions or [],
            'decisions': self.decisions or [],
            'risks': self.risks or [],
            'executive_insights': self.executive_insights or [],
            'technical_details': self.technical_details or [],
            'action_plan': self.action_plan or [],
            'engine': self.engine,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, session_id={self.session_id}, level='{self.level.value}', style='{self.style.value}', engine='{self.engine}')>"