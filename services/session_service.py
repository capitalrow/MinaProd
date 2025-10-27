"""
Session Service (M2)
Service layer for managing session CRUD operations and persistence.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from models import db
from models.session import Session
from models.segment import Segment

logger = logging.getLogger(__name__)


class SessionService:
    """Service class for session management and persistence."""
    
    @staticmethod
    def create_session(title: Optional[str] = None, external_id: Optional[str] = None, 
                      locale: Optional[str] = None, device_info: Optional[dict] = None,
                      user_id: Optional[int] = None, workspace_id: Optional[int] = None,
                      meeting_id: Optional[int] = None) -> int:
        """
        Create a new session.
        
        Args:
            title: Session title, defaults to 'Untitled Meeting'
            external_id: External session identifier (for WS), auto-generated if None
            locale: Language/locale code
            device_info: Device information dictionary
            user_id: User who owns this session (nullable for anonymous)
            workspace_id: Workspace this session belongs to (nullable for anonymous)
            meeting_id: Meeting this session is linked to (nullable)
            
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
            meta={},
            user_id=user_id,
            workspace_id=workspace_id,
            meeting_id=meeting_id
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
        stmt = select(Session).where(Session.external_id == external_id)
        return db.session.scalars(stmt).first()
    
    @staticmethod
    def get_session_by_id(session_id: int) -> Optional[Session]:
        """
        Get session by database ID.
        
        Args:
            session_id: Database session ID
            
        Returns:
            Session instance or None
        """
        stmt = select(Session).where(Session.id == session_id)
        return db.session.scalars(stmt).first()
    
    @staticmethod
    def complete_session(session_id: int, create_meeting: bool = True) -> bool:
        """
        Mark session as completed and optionally create meeting.
        
        Args:
            session_id: Database session ID
            create_meeting: Whether to create meeting from session (default True)
            
        Returns:
            True if session was updated, False if not found
        """
        session = SessionService.get_session_by_id(session_id)
        if session:
            session.complete()
            db.session.commit()
            
            # Create meeting from session if requested
            if create_meeting:
                try:
                    from services.meeting_lifecycle_service import MeetingLifecycleService
                    result = MeetingLifecycleService.finalize_session_with_meeting(session_id)
                    logger.info(f"Meeting creation result: {result}")
                except Exception as e:
                    logger.error(f"Failed to create meeting from session: {e}")
            
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
        stmt = select(Session)
        
        # Apply search filter
        if q:
            stmt = stmt.where(Session.title.ilike(f'%{q}%'))
        
        # Apply status filter
        if status:
            stmt = stmt.where(Session.status == status)
        
        # Apply ordering and pagination
        stmt = stmt.order_by(Session.started_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        return list(db.session.scalars(stmt).all())
    
    @staticmethod
    def get_session_detail(session_id: int, kind: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information including segments.
        
        Args:
            session_id: Database session ID
            kind: Optional filter for segment kind ('final', 'interim', or None for all)
            
        Returns:
            Dictionary with session and segments data, or None
        """
        session = SessionService.get_session_by_id(session_id)
        if not session:
            return None
        
        # Get session segments using SQLAlchemy 2.0
        segments_stmt = select(Segment).where(Segment.session_id == session_id)
        
        # Filter by kind if specified
        if kind:
            segments_stmt = segments_stmt.where(Segment.kind == kind)
        
        segments_stmt = segments_stmt.order_by(Segment.start_ms, Segment.created_at)
        segments = db.session.scalars(segments_stmt).all()
        
        return {
            'session': session.to_dict(),
            'segments': [segment.to_dict() for segment in segments],
            'total_segments': len(segments)
        }
    
    @staticmethod
    def get_session_detail_by_external(external_id: str, kind: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed session information including segments by external ID.
        
        Args:
            external_id: External session identifier
            kind: Optional filter for segment kind ('final', 'interim', or None for all)
            
        Returns:
            Dictionary with session and segments data, or None
        """
        session = SessionService.get_session_by_external(external_id)
        if not session:
            return None
        
        # Get session segments using SQLAlchemy 2.0
        segments_stmt = select(Segment).where(Segment.session_id == session.id)
        
        # Filter by kind if specified
        if kind:
            segments_stmt = segments_stmt.where(Segment.kind == kind)
        
        segments_stmt = segments_stmt.order_by(Segment.start_ms, Segment.created_at)
        segments = db.session.scalars(segments_stmt).all()
        
        return {
            'session': session.to_dict(),
            'segments': [segment.to_dict() for segment in segments],
            'total_segments': len(segments)
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
            # Count sessions by status using SQLAlchemy 2.0
            active_count = db.session.scalars(select(func.count()).select_from(Session).where(Session.status == 'active')).one()
            completed_count = db.session.scalars(select(func.count()).select_from(Session).where(Session.status == 'completed')).one()
            error_count = db.session.scalars(select(func.count()).select_from(Session).where(Session.status == 'error')).one()
            total_count = db.session.scalars(select(func.count()).select_from(Session)).one()
            
            # Count total segments
            segments_count = db.session.scalars(select(func.count()).select_from(Segment)).one()
            
            return {
                'active_sessions': active_count,
                'completed_sessions': completed_count,
                'error_sessions': error_count,
                'total_sessions': total_count,
                'total_segments': segments_count
            }
        except Exception:
            # 🔥 CRITICAL FIX: Actually query database for real session counts  
            active_count = db.session.scalars(
                select(func.count()).select_from(Session).where(Session.status == 'active')
            ).one()
            
            completed_count = db.session.scalars(
                select(func.count()).select_from(Session).where(Session.status == 'completed')
            ).one()
            
            error_count = db.session.scalars(
                select(func.count()).select_from(Session).where(Session.status == 'error')
            ).one()
            
            total_sessions = db.session.scalars(
                select(func.count()).select_from(Session)
            ).one()
            
            total_segments = db.session.scalars(
                select(func.count()).select_from(Segment)
            ).one()
            
            return {
                'active_sessions': int(active_count),
                'completed_sessions': int(completed_count),
                'error_sessions': int(error_count),
                'total_sessions': int(total_sessions),
                'total_segments': int(total_segments)
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
        from sqlalchemy import select
        stmt = select(Segment).filter(
            Segment.session_id == session_id,
            Segment.kind == 'interim'
        )
        interim_segments = db.session.execute(stmt).scalars().all()
        
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

    @staticmethod
    def finalize_session(session_id: int, final_text: Optional[str] = None, trigger_summary: Optional[bool] = None) -> Dict[str, Any]:
        """
        Complete a session by finalizing segments and updating status.
        
        M3: Includes auto-summary generation if enabled.
        
        Args:
            session_id: Database session ID
            final_text: Optional final transcript text
            trigger_summary: Override auto-summary setting (for testing)
            
        Returns:
            Session finalization result
        """
        session = db.session.get(Session, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Finalize segments
        finalized_count = SessionService.finalize_session_segments(session_id, final_text)
        
        # Update session status
        session.status = 'completed'
        session.completed_at = datetime.utcnow()
        db.session.commit()
        
        # M3: Trigger auto-summary if enabled
        from flask import current_app
        should_trigger = trigger_summary if trigger_summary is not None else current_app.config.get('AUTO_SUMMARY_ON_FINALIZE', False)
        
        if should_trigger:
            try:
                from app import socketio
                from routes.summary import trigger_auto_summary
                
                # Start background task for summary generation
                socketio.start_background_task(trigger_auto_summary, session_id)
                logger.info(f"Auto-summary triggered for session {session_id}")
                
            except Exception as e:
                logger.warning(f"Failed to trigger auto-summary for session {session_id}: {e}")
        
        logger.info(f"Session {session_id} finalized with {finalized_count} segments")
        return {
            'status': 'completed',
            'finalized_segments': finalized_count,
            'message': f'Session {session_id} completed',
            'auto_summary_triggered': should_trigger
        }