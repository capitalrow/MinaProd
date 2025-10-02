"""
Session replay service for recording and playing back user sessions.
Uses rrweb (open source session recording library).
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from models import db

logger = logging.getLogger(__name__)


class SessionReplay(db.Model):
    """Store session replay recordings."""
    __tablename__ = 'session_replays'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), index=True)
    session_id = db.Column(db.String(36), nullable=False, unique=True)
    events = db.Column(db.JSON, default=[])
    duration_ms = db.Column(db.Integer)
    page_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_redacted = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.Index('ix_replay_user_created', 'user_id', 'created_at'),
    )


class SessionReplayService:
    """
    Manage session replay recordings.
    Privacy-first implementation with automatic redaction.
    """
    
    def __init__(self):
        self.enabled = True
        self.retention_days = 30
        
        # Sensitive selectors to redact
        self.redact_selectors = [
            'input[type="password"]',
            'input[name*="password"]',
            'input[name*="secret"]',
            'input[name*="token"]',
            'input[name*="api_key"]',
            '[data-private]',
            '[data-sensitive]'
        ]
    
    def save_recording(
        self,
        user_id: int,
        workspace_id: int,
        session_id: str,
        events: List[Dict[str, Any]]
    ) -> bool:
        """
        Save session replay recording.
        
        Args:
            user_id: User who created the session
            workspace_id: Workspace context
            session_id: Unique session identifier
            events: rrweb event array
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            # Redact sensitive data
            redacted_events = self._redact_events(events)
            
            # Calculate metrics
            duration_ms = self._calculate_duration(redacted_events)
            page_count = self._count_pages(redacted_events)
            
            replay = SessionReplay(
                user_id=user_id,
                workspace_id=workspace_id,
                session_id=session_id,
                events=redacted_events,
                duration_ms=duration_ms,
                page_count=page_count,
                is_redacted=True
            )
            
            db.session.add(replay)
            db.session.commit()
            
            logger.info(f"Saved session replay {session_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save session replay: {e}")
            return False
    
    def get_recording(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session replay recording.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Replay data or None
        """
        try:
            replay = db.session.query(SessionReplay).filter_by(
                session_id=session_id
            ).first()
            
            if not replay:
                return None
            
            return {
                'id': replay.id,
                'session_id': replay.session_id,
                'events': replay.events,
                'duration_ms': replay.duration_ms,
                'page_count': replay.page_count,
                'created_at': replay.created_at.isoformat(),
                'is_redacted': replay.is_redacted
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve session replay: {e}")
            return None
    
    def list_user_recordings(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        List session replays for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of recordings
            
        Returns:
            List of replay metadata
        """
        try:
            replays = db.session.query(SessionReplay).filter_by(
                user_id=user_id
            ).order_by(SessionReplay.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': r.id,
                    'session_id': r.session_id,
                    'duration_ms': r.duration_ms,
                    'page_count': r.page_count,
                    'created_at': r.created_at.isoformat()
                }
                for r in replays
            ]
            
        except Exception as e:
            logger.error(f"Failed to list user recordings: {e}")
            return []
    
    def delete_recording(self, session_id: str) -> bool:
        """
        Delete session replay (GDPR compliance).
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        try:
            replay = db.session.query(SessionReplay).filter_by(
                session_id=session_id
            ).first()
            
            if replay:
                db.session.delete(replay)
                db.session.commit()
                logger.info(f"Deleted session replay {session_id}")
                return True
            
            return False
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete session replay: {e}")
            return False
    
    def cleanup_old_recordings(self):
        """
        Delete recordings older than retention period.
        Runs as scheduled job.
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
            
            deleted = db.session.query(SessionReplay).filter(
                SessionReplay.created_at < cutoff
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleaned up {deleted} old session replays")
            return deleted
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old recordings: {e}")
            return 0
    
    def _redact_events(self, events: List[Dict]) -> List[Dict]:
        """
        Redact sensitive data from rrweb events.
        
        This is a simplified implementation. In production, use
        rrweb's built-in privacy options or more sophisticated redaction.
        """
        redacted = []
        
        for event in events:
            event_copy = event.copy()
            
            # Redact text input events
            if event.get('type') == 3 and event.get('data', {}).get('source') == 5:
                # Input event
                if any(selector in str(event.get('data', {})) for selector in self.redact_selectors):
                    event_copy['data']['text'] = '***REDACTED***'
            
            # Could add more sophisticated redaction here
            # - Remove specific DOM nodes
            # - Blur sensitive areas
            # - Hash values
            
            redacted.append(event_copy)
        
        return redacted
    
    def _calculate_duration(self, events: List[Dict]) -> int:
        """Calculate session duration from events."""
        if not events or len(events) < 2:
            return 0
        
        timestamps = [e.get('timestamp', 0) for e in events if 'timestamp' in e]
        if len(timestamps) < 2:
            return 0
        
        return max(timestamps) - min(timestamps)
    
    def _count_pages(self, events: List[Dict]) -> int:
        """Count page navigations in session."""
        page_count = 0
        
        for event in events:
            if event.get('type') == 4:  # Meta event
                if event.get('data', {}).get('href'):
                    page_count += 1
        
        return max(1, page_count)  # At least 1 page


session_replay_service = SessionReplayService()
