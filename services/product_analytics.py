"""
Product analytics service for tracking user events and behavior.
Separate from meeting analytics (analytics_service.py).
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from models import db
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class AnalyticsEvent(db.Model):
    """Store product analytics events."""
    __tablename__ = 'analytics_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), index=True)
    properties = db.Column(db.JSON, default={})
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    session_id = db.Column(db.String(36))
    
    __table_args__ = (
        db.Index('ix_analytics_event_timestamp', 'event_name', 'timestamp'),
        db.Index('ix_analytics_user_timestamp', 'user_id', 'timestamp'),
    )


class ProductAnalytics:
    """Track and analyze product usage events."""
    
    def __init__(self):
        self.enabled = True
    
    def track(
        self,
        event_name: str,
        user_id: Optional[int] = None,
        workspace_id: Optional[int] = None,
        properties: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """
        Track a product analytics event.
        
        Args:
            event_name: Event identifier (e.g., 'meeting.created')
            user_id: User who triggered the event
            workspace_id: Workspace context
            properties: Additional event properties
            session_id: Session identifier
        """
        if not self.enabled:
            return
        
        try:
            event = AnalyticsEvent(
                event_name=event_name,
                user_id=user_id,
                workspace_id=workspace_id,
                properties=properties or {},
                session_id=session_id
            )
            
            db.session.add(event)
            db.session.commit()
            
            logger.debug(f"Tracked event: {event_name}", extra={
                'event_name': event_name,
                'user_id': user_id,
                'workspace_id': workspace_id
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to track event {event_name}: {e}")
    
    def track_user_signup(self, user_id: int, workspace_id: int, properties: Optional[Dict] = None):
        """Track user signup event."""
        self.track('user.signup', user_id=user_id, workspace_id=workspace_id, properties=properties)
    
    def track_user_login(self, user_id: int, properties: Optional[Dict] = None):
        """Track user login event."""
        self.track('user.login', user_id=user_id, properties=properties)
    
    def track_meeting_created(self, user_id: int, workspace_id: int, meeting_id: int, properties: Optional[Dict] = None):
        """Track meeting creation event."""
        props = properties or {}
        props['meeting_id'] = meeting_id
        self.track('meeting.created', user_id=user_id, workspace_id=workspace_id, properties=props)
    
    def track_session_started(self, user_id: int, session_id: str, properties: Optional[Dict] = None):
        """Track transcription session started."""
        self.track('session.started', user_id=user_id, session_id=session_id, properties=properties)
    
    def track_session_completed(self, user_id: int, session_id: str, properties: Optional[Dict] = None):
        """Track transcription session completed."""
        self.track('session.completed', user_id=user_id, session_id=session_id, properties=properties)
    
    def track_task_created(self, user_id: int, workspace_id: int, task_id: int, properties: Optional[Dict] = None):
        """Track task creation event."""
        props = properties or {}
        props['task_id'] = task_id
        self.track('task.created', user_id=user_id, workspace_id=workspace_id, properties=props)
    
    def track_task_completed(self, user_id: int, workspace_id: int, task_id: int, properties: Optional[Dict] = None):
        """Track task completion event."""
        props = properties or {}
        props['task_id'] = task_id
        self.track('task.completed', user_id=user_id, workspace_id=workspace_id, properties=props)
    
    def get_activation_rate(self, days: int = 7) -> float:
        """
        Calculate activation rate (users who started first session within N days of signup).
        
        Args:
            days: Days since signup to check for activation
            
        Returns:
            Activation rate (0-1)
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Users who signed up in period
            signups = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(
                AnalyticsEvent.event_name == 'user.signup',
                AnalyticsEvent.timestamp >= cutoff
            ).scalar() or 0
            
            # Users who started first session
            activated = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(
                AnalyticsEvent.event_name == 'session.started',
                AnalyticsEvent.user_id.in_(
                    db.session.query(AnalyticsEvent.user_id).filter(
                        AnalyticsEvent.event_name == 'user.signup',
                        AnalyticsEvent.timestamp >= cutoff
                    )
                )
            ).scalar() or 0
            
            return activated / signups if signups > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate activation rate: {e}")
            return 0.0
    
    def get_engagement_score(self, user_id: int, days: int = 30) -> float:
        """
        Calculate user engagement score (0-100).
        
        Components:
        - Meeting frequency: 30 points
        - Task creation: 25 points
        - Task completion: 25 points
        - Feature adoption: 20 points
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            # Meeting frequency (30 points)
            meetings = db.session.query(func.count(AnalyticsEvent.id)).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_name == 'meeting.created',
                AnalyticsEvent.timestamp >= cutoff
            ).scalar() or 0
            meeting_score = min(meetings / days * 100, 30)
            
            # Task creation (25 points)
            tasks_created = db.session.query(func.count(AnalyticsEvent.id)).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_name == 'task.created',
                AnalyticsEvent.timestamp >= cutoff
            ).scalar() or 0
            task_create_score = min(tasks_created / (days * 2) * 25, 25)
            
            # Task completion (25 points)
            tasks_completed = db.session.query(func.count(AnalyticsEvent.id)).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.event_name == 'task.completed',
                AnalyticsEvent.timestamp >= cutoff
            ).scalar() or 0
            task_complete_score = min(tasks_completed / (days * 2) * 25, 25)
            
            # Feature adoption (20 points) - unique event types used
            unique_events = db.session.query(func.count(func.distinct(AnalyticsEvent.event_name))).filter(
                AnalyticsEvent.user_id == user_id,
                AnalyticsEvent.timestamp >= cutoff
            ).scalar() or 0
            feature_score = min(unique_events / 10 * 20, 20)
            
            total_score = meeting_score + task_create_score + task_complete_score + feature_score
            return round(total_score, 1)
            
        except Exception as e:
            logger.error(f"Failed to calculate engagement score: {e}")
            return 0.0
    
    def get_retention_cohort(self, cohort_days: int = 7) -> Dict[str, Any]:
        """
        Calculate retention for cohort (users who signed up N days ago).
        
        Returns dict with signup count and retained count.
        """
        try:
            cohort_date = datetime.utcnow() - timedelta(days=cohort_days)
            cohort_start = cohort_date.replace(hour=0, minute=0, second=0)
            cohort_end = cohort_start + timedelta(days=1)
            
            # Users who signed up in cohort day
            cohort_users = db.session.query(AnalyticsEvent.user_id).filter(
                AnalyticsEvent.event_name == 'user.signup',
                AnalyticsEvent.timestamp >= cohort_start,
                AnalyticsEvent.timestamp < cohort_end
            ).distinct().all()
            
            cohort_user_ids = [u[0] for u in cohort_users]
            
            # Users from cohort who had activity in last 7 days
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            retained = db.session.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
                AnalyticsEvent.user_id.in_(cohort_user_ids),
                AnalyticsEvent.timestamp >= recent_cutoff
            ).scalar() or 0
            
            cohort_size = len(cohort_user_ids)
            retention_rate = (retained / cohort_size * 100) if cohort_size > 0 else 0
            
            return {
                'cohort_date': cohort_start.date().isoformat(),
                'cohort_size': cohort_size,
                'retained': retained,
                'retention_rate': round(retention_rate, 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate retention cohort: {e}")
            return {}
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """Get conversion funnel metrics."""
        try:
            # Total signups
            total_signups = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(AnalyticsEvent.event_name == 'user.signup').scalar() or 0
            
            # Users who created first meeting
            first_meeting = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(AnalyticsEvent.event_name == 'meeting.created').scalar() or 0
            
            # Users who started session
            first_session = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(AnalyticsEvent.event_name == 'session.started').scalar() or 0
            
            # Users who created tasks
            created_task = db.session.query(
                func.count(func.distinct(AnalyticsEvent.user_id))
            ).filter(AnalyticsEvent.event_name == 'task.created').scalar() or 0
            
            return {
                'signup': total_signups,
                'first_meeting': first_meeting,
                'first_session': first_session,
                'created_task': created_task,
                'signup_to_meeting_rate': (first_meeting / total_signups * 100) if total_signups > 0 else 0,
                'signup_to_session_rate': (first_session / total_signups * 100) if total_signups > 0 else 0,
                'signup_to_task_rate': (created_task / total_signups * 100) if total_signups > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get conversion funnel: {e}")
            return {}


product_analytics = ProductAnalytics()
