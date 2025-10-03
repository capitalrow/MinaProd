"""
Comment Model for Transcript Segments
SQLAlchemy 2.0-safe model for collaborative commenting on transcript segments.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, func, Index
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .user import User
    from .segment import Segment

class Comment(Base):
    """
    Comment model for adding notes and discussions to transcript segments.
    Enables team collaboration on meeting transcripts.
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Relationships
    segment_id: Mapped[int] = mapped_column(ForeignKey("segments.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Comment content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Threading support (for replies)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Metadata
    is_edited: Mapped[bool] = mapped_column(default=False)
    is_resolved: Mapped[bool] = mapped_column(default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    segment: Mapped["Segment"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship(back_populates="comments")
    
    # Self-referential relationship for threading
    parent: Mapped[Optional["Comment"]] = relationship("Comment", remote_side=[id], back_populates="replies")
    replies: Mapped[list["Comment"]] = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    
    # Database indexes for query optimization
    __table_args__ = (
        Index('ix_comments_segment_created', 'segment_id', 'created_at'),
        Index('ix_comments_user', 'user_id'),
        Index('ix_comments_parent', 'parent_id'),
    )
    
    def __repr__(self):
        return f'<Comment {self.id} by User {self.user_id}: "{self.text[:50]}...">'
    
    def to_dict(self, include_replies=False):
        """Convert comment to dictionary for JSON serialization."""
        result = {
            'id': self.id,
            'segment_id': self.segment_id,
            'user_id': self.user_id,
            'text': self.text,
            'author_name': self.user.username if self.user else 'Unknown',
            'author_avatar': self.user.avatar_url if self.user else None,
            'parent_id': self.parent_id,
            'is_edited': self.is_edited,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_replies and self.replies:
            result['replies'] = [reply.to_dict(include_replies=False) for reply in self.replies]
        
        return result
    
    def edit(self, new_text: str):
        """Edit comment text and mark as edited."""
        self.text = new_text
        self.is_edited = True
    
    def resolve(self):
        """Mark comment as resolved."""
        self.is_resolved = True
    
    def unresolve(self):
        """Mark comment as unresolved."""
        self.is_resolved = False
