"""
Workspace Model for Multi-Tenant Team Management
SQLAlchemy 2.0-safe model for team workspaces and collaboration.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, Text, JSON, func, ForeignKey
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .user import User
    from .meeting import Meeting
    from .session import Session


class Workspace(Base):
    """
    Workspace model for team collaboration and multi-tenant support.
    Each workspace can have multiple users and meetings.
    """
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Owner relationship
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship(foreign_keys=[owner_id], post_update=True)
    
    # Workspace settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    plan: Mapped[str] = mapped_column(String(32), default="free")  # free, pro, enterprise
    max_users: Mapped[int] = mapped_column(Integer, default=5)
    
    # Branding and customization
    logo_url: Mapped[Optional[str]] = mapped_column(String(256))
    theme_settings: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Integration settings
    integrations: Mapped[Optional[dict]] = mapped_column(JSON)  # Calendar, Slack, etc.
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    members: Mapped[list["User"]] = relationship(back_populates="workspace", foreign_keys="User.workspace_id")
    sessions: Mapped[list["Session"]] = relationship(back_populates="workspace", foreign_keys="Session.workspace_id")
    meetings: Mapped[list["Meeting"]] = relationship(back_populates="workspace")

    def __repr__(self):
        return f'<Workspace {self.slug}: {self.name}>'

    @property
    def member_count(self) -> int:
        """Get number of members in workspace."""
        return len(self.members) if self.members else 0

    @property
    def is_over_limit(self) -> bool:
        """Check if workspace is over user limit."""
        return self.member_count > self.max_users

    def can_add_user(self) -> bool:
        """Check if workspace can add more users."""
        return self.member_count < self.max_users

    def to_dict(self, include_members=False):
        """Convert workspace to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'owner_id': self.owner_id,
            'is_active': self.is_active,
            'plan': self.plan,
            'max_users': self.max_users,
            'member_count': self.member_count,
            'logo_url': self.logo_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_members and self.members:
            data['members'] = [member.to_dict() for member in self.members]
            
        return data

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-safe slug from workspace name."""
        import re
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug)
        return slug[:64]  # Limit to 64 characters