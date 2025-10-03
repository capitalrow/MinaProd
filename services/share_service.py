"""
Share Service for M4 Sharing functionality.
Handles creation and validation of session sharing links.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import select

from models import db, Session, SharedLink


class ShareService:
    """Service for managing session sharing links."""
    
    def __init__(self, db_session: Optional[DBSession] = None):
        """Initialize share service with database session."""
        self.db_session = db_session or db.session
    
    def create_share_link(self, session_id: int, days: int = 7) -> str:
        """
        Create a new share link for a session.
        
        Args:
            session_id: ID of the session to share
            days: Number of days until link expires (default: 7)
            
        Returns:
            Generated token for the share link
            
        Raises:
            ValueError: If session doesn't exist
        """
        # Verify session exists
        session = self.db_session.get(Session, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Generate secure random token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiration date
        expires_at = datetime.utcnow() + timedelta(days=days)
        
        # Create shared link record
        shared_link = SharedLink(
            session_id=session_id,
            token=token,
            expires_at=expires_at,
            is_active=True
        )
        
        self.db_session.add(shared_link)
        self.db_session.commit()
        
        return token
    
    def validate_share_token(self, token: str) -> Optional[Session]:
        """
        Validate a share token and return associated session.
        
        Args:
            token: Share token to validate
            
        Returns:
            Session object if token is valid, None otherwise
        """
        # Find shared link by token
        stmt = select(SharedLink).where(SharedLink.token == token)
        shared_link = self.db_session.scalars(stmt).first()
        
        if not shared_link:
            return None
        
        # Check if link is still valid
        if not shared_link.is_valid:
            return None
        
        # Return associated session
        return shared_link.session
    
    def deactivate_share_link(self, session_id: int, token: str) -> bool:
        """
        Deactivate a specific share link.
        
        Args:
            session_id: ID of the session
            token: Token to deactivate
            
        Returns:
            True if link was deactivated, False if not found
        """
        stmt = select(SharedLink).where(
            SharedLink.session_id == session_id,
            SharedLink.token == token
        )
        shared_link = self.db_session.scalars(stmt).first()
        
        if not shared_link:
            return False
        
        shared_link.is_active = False
        self.db_session.commit()
        return True
    
    def get_active_share_links(self, session_id: int) -> list[SharedLink]:
        """
        Get all active share links for a session.
        
        Args:
            session_id: ID of the session
            
        Returns:
            List of active SharedLink objects
        """
        stmt = select(SharedLink).where(
            SharedLink.session_id == session_id,
            SharedLink.is_active == True
        ).order_by(SharedLink.created_at.desc())
        
        return list(self.db_session.scalars(stmt))
    
    def cleanup_expired_links(self) -> int:
        """
        Clean up expired share links by marking them inactive.
        
        Returns:
            Number of links cleaned up
        """
        now = datetime.utcnow()
        stmt = select(SharedLink).where(
            SharedLink.expires_at < now,
            SharedLink.is_active == True
        )
        
        expired_links = list(self.db_session.scalars(stmt))
        
        for link in expired_links:
            link.is_active = False
        
        if expired_links:
            self.db_session.commit()
        
        return len(expired_links)