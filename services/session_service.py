"""
Session Service (M2)
Service layer for managing session CRUD operations and persistence.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app_refactored import db
from models.session import Session
from models.segment import Segment


class SessionService:
    """Service class for session management and persistence."""
    
    @staticmethod
    def create_session(title: Optional[str] = None, external_id: Optional[str] = None, 
                      locale: Optional[str] = None, device_info: Optional[dict] = None) -> int:
        """
        Create a new session.
        
        Args:
            title: Session title, defaults to 'Untitled Meeting'
            external_id: External session identifier (for WS), auto-generated if None
            locale: Language/locale code
            device_info: Device information dictionary
            
        Returns:
            Session database ID
        """
        if external_id is None:
            external_id = str(uuid.uuid4())
        
        if title is None:
            title = "Untitled Meeting"
        
        session = Session(
            external_id=external_id,
            title=title,
            status="active",
            started_at=datetime.utcnow(),
            locale=locale,
            device_info=device_info,
            meta={}
        )
        
        db.session.add(session)
        db.session.commit()
        return session.id
    
    @staticmethod
    def get_session_by_external(external_id: str) -> Optional[Session]:
        """
        Get session by external ID.
        
        Args:
            external_id: External session identifier
            
        Returns:
            Session instance or None
        """
        return db.session.query(Session).filter(Session.external_id == external_id).first()
    
    @staticmethod
    def get_session_by_id(session_id: int) -> Optional[Session]:
        """
        Get session by database ID.
        
        Args:
            session_id: Database session ID
            
        Returns:
            Session instance or None
        """
        return db.session.query(Session).filter(Session.id == session_id).first()
    
    @staticmethod
    def complete_session(session_id: int) -> bool:
        """
        Mark session as completed.
        
        Args:
            session_id: Database session ID
            
        Returns:
            True if session was updated, False if not found
        """
        session = SessionService.get_session_by_id(session_id)
        if session:
            session.complete()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def list_sessions(q: Optional[str] = None, status: Optional[str] = None, 
                     limit: int = 50, offset: int = 0) -> List[Session]:
        """
        List sessions with optional filtering.
        
        Args:
            q: Search query for title
            status: Status filter (active, completed, error)
            limit: Maximum number of results
            offset: Results offset for pagination
            
        Returns:
            List of Session instances
        """
        query = db.session.query(Session)
        
        # Apply search filter
        if q:
            query = query.filter(Session.title.ilike(f'%{q}%'))
        
        # Apply status filter
        if status:
            query = query.filter(Session.status == status)
        
        # Apply ordering and pagination
        query = query.order_by(Session.started_at.desc())
        query = query.offset(offset).limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_session_detail(session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information including segments.
        
        Args:
            session_id: Database session ID
            
        Returns:
            Dictionary with session and segments data, or None
        """
        session = db.session.query(Session).options(
            selectinload(Session.segments)
        ).filter(Session.id == session_id).first()
        
        if not session:
            return None
        
        # Get segments ordered by creation time
        segments = db.session.query(Segment).filter(
            Segment.session_id == session_id
        ).order_by(Segment.created_at).all()
        
        return {
            'session': session.to_dict(),
            'segments': [segment.to_dict() for segment in segments]
        }
    
    @staticmethod
    def create_segment(session_id: int, kind: str, text: str, 
                      avg_confidence: Optional[float] = None,
                      start_ms: Optional[int] = None, 
                      end_ms: Optional[int] = None) -> int:
        """
        Create a new segment for a session.
        
        Args:
            session_id: Database session ID
            kind: Segment kind ('interim' or 'final')
            text: Transcribed text
            avg_confidence: Average confidence score
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
            
        Returns:
            Segment database ID
        """
        segment = Segment(
            session_id=session_id,
            kind=kind,
            text=text,
            avg_confidence=avg_confidence,
            start_ms=start_ms,
            end_ms=end_ms
        )
        
        db.session.add(segment)
        db.session.commit()
        return segment.id
    
    @staticmethod
    def get_session_stats() -> Dict[str, int]:
        """
        Get overall session statistics.
        
        Returns:
            Dictionary with session counts by status
        """
        try:
            # Count sessions by status
            active_count = db.session.query(Session).filter(Session.status == 'active').count()
            completed_count = db.session.query(Session).filter(Session.status == 'completed').count()
            error_count = db.session.query(Session).filter(Session.status == 'error').count()
            total_count = db.session.query(Session).count()
            
            # Count total segments
            segments_count = db.session.query(Segment).count()
            
            return {
                'active_sessions': active_count,
                'completed_sessions': completed_count,
                'error_sessions': error_count,
                'total_sessions': total_count,
                'total_segments': segments_count
            }
        except Exception:
            return {
                'active_sessions': 0,
                'completed_sessions': 0,
                'error_sessions': 0,
                'total_sessions': 0,
                'total_segments': 0
            }
    
    @staticmethod
    def finalize_session_segments(session_id: int, final_text: Optional[str] = None) -> int:
        """
        Finalize all interim segments for a session and optionally add final segment.
        
        Args:
            session_id: Database session ID
            final_text: Optional final transcript text to add
            
        Returns:
            Number of segments finalized
        """
        # Mark all interim segments as final
        interim_segments = db.session.query(Segment).filter(
            Segment.session_id == session_id,
            Segment.kind == 'interim'
        ).all()
        
        for segment in interim_segments:
            segment.finalize()
        
        finalized_count = len(interim_segments)
        
        # Add final summary segment if provided
        if final_text:
            SessionService.create_segment(
                session_id=session_id,
                kind='final',
                text=final_text,
                avg_confidence=1.0
            )
            finalized_count += 1
        
        db.session.commit()
        return finalized_count