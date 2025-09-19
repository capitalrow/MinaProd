"""
Shared Link Model for M4 Sharing functionality.
Enables view-only session sharing with expirable tokens.
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.base import Base
from extensions import db

class SharedLink(Base):
    """Model for session sharing links with expiration support."""
    
    __tablename__ = "shared_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    session: Mapped["Session"] = relationship(back_populates="shared_links")

    def __repr__(self):
        return f"<SharedLink(id={self.id}, token={self.token[:8]}..., session_id={self.session_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the shared link has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if the shared link is active and not expired."""
        return self.is_active and not self.is_expired