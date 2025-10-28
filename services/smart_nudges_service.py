"""
Smart Nudges and Follow-up Suggestions Service for Mina.

This module provides intelligent nudging and follow-up suggestions based on
meeting content, task patterns, and user behavior to enhance productivity.
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class NudgeType(Enum):
    """Types of smart nudges."""
    OVERDUE_TASK = "overdue_task"
    UPCOMING_DEADLINE = "upcoming_deadline" 
    MISSING_FOLLOW_UP = "missing_follow_up"
    INACTIVE_PROJECT = "inactive_project"
    MEETING_PREPARATION = "meeting_preparation"
    ACTION_REVIEW = "action_review"
    DECISION_CONFIRMATION = "decision_confirmation"
    COLLABORATION_REMINDER = "collaboration_reminder"
    INSIGHT_REMINDER = "insight_reminder"  # AI-generated predictive reminder


class Priority(Enum):
    """Priority levels for nudges."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NudgeChannel(Enum):
    """Channels for delivering nudges."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SLACK = "slack"


@dataclass
class SmartNudge:
    """A smart nudge with context-aware suggestions."""
    id: str
    type: NudgeType
    priority: Priority
    title: str
    message: str
    action_text: str
    action_url: str
    context: Dict[str, Any]
    related_entities: List[str]  # task IDs, meeting IDs, etc.
    suggested_channels: List[NudgeChannel]
    created_at: datetime
    expires_at: Optional[datetime] = None
    dismissed: bool = False
    acted_upon: bool = False
    
    def __post_init__(self):
        if self.expires_at is None:
            # Default expiry based on priority
            if self.priority == Priority.URGENT:
                self.expires_at = self.created_at + timedelta(hours=2)
            elif self.priority == Priority.HIGH:
                self.expires_at = self.created_at + timedelta(hours=12)
            elif self.priority == Priority.MEDIUM:
                self.expires_at = self.created_at + timedelta(days=1)
            else:
                self.expires_at = self.created_at + timedelta(days=3)


@dataclass
class FollowUpSuggestion:
    """A follow-up suggestion based on meeting content."""
    id: str
    title: str
    description: str
    suggested_action: str
    context: Dict[str, Any]
    confidence: float
    related_meeting_id: int
    related_entities: List[str]
    suggested_due_date: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    category: str = "general"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class UserBehaviorPattern:
    """User behavior pattern for personalized nudging."""
    user_id: int
    preferred_nudge_times: List[int]  # Hours of day (0-23)
    preferred_channels: List[NudgeChannel]
    response_rate_by_type: Dict[str, float]
    avg_response_time_hours: float
    activity_patterns: Dict[str, Any]
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class SmartNudgesService:
    """Service for generating smart nudges and follow-up suggestions."""
    
    def __init__(self):
        self.nudges_cache: Dict[int, List[SmartNudge]] = defaultdict(list)
        self.user_patterns: Dict[int, UserBehaviorPattern] = {}
        self.follow_up_suggestions: Dict[int, List[FollowUpSuggestion]] = defaultdict(list)
        # 24-hour throttling: track last reminder time per user
        self.last_insight_reminder: Dict[int, datetime] = {}
    
    def generate_nudges(self, user_id: int) -> List[SmartNudge]:
        """
        Generate smart nudges for a user based on their tasks, meetings, and patterns.
        
        Args:
            user_id: User ID to generate nudges for
            
        Returns:
            List of smart nudges
        """
        try:
            nudges = []
            
            # Get user data
            user_data = self._get_user_data(user_id)
            if not user_data:
                return []
            
            # Generate different types of nudges
            nudges.extend(self._generate_task_nudges(user_id, user_data))
            nudges.extend(self._generate_meeting_nudges(user_id, user_data))
            nudges.extend(self._generate_follow_up_nudges(user_id, user_data))
            nudges.extend(self._generate_collaboration_nudges(user_id, user_data))
            nudges.extend(self._generate_review_nudges(user_id, user_data))
            
            # Personalize nudges based on user patterns
            nudges = self._personalize_nudges(user_id, nudges)
            
            # Sort by priority and relevance
            nudges.sort(key=lambda n: (n.priority.value, n.created_at), reverse=True)
            
            # Cache the nudges
            self.nudges_cache[user_id] = nudges
            
            return nudges
            
        except Exception as e:
            logger.error(f"Error generating nudges for user {user_id}: {e}")
            return []
    
    def generate_follow_up_suggestions(self, meeting_id: int) -> List[FollowUpSuggestion]:
        """
        Generate follow-up suggestions based on a specific meeting.
        
        Args:
            meeting_id: Meeting/session ID to analyze
            
        Returns:
            List of follow-up suggestions
        """
        try:
            # Get meeting data
            meeting_data = self._get_meeting_data(meeting_id)
            if not meeting_data:
                return []
            
            suggestions = []
            
            # Analyze meeting content for suggestions
            suggestions.extend(self._suggest_from_action_items(meeting_data))
            suggestions.extend(self._suggest_from_decisions(meeting_data))
            suggestions.extend(self._suggest_from_topics(meeting_data))
            suggestions.extend(self._suggest_from_participants(meeting_data))
            suggestions.extend(self._suggest_from_timeline(meeting_data))
            
            # Score and rank suggestions
            suggestions = self._score_suggestions(suggestions)
            
            # Cache suggestions
            if meeting_data.get('user_id'):
                self.follow_up_suggestions[meeting_data['user_id']].extend(suggestions)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating follow-up suggestions for meeting {meeting_id}: {e}")
            return []
    
    def get_active_nudges(self, user_id: int, channel: Optional[NudgeChannel] = None) -> List[SmartNudge]:
        """Get active nudges for a user, optionally filtered by channel."""
        try:
            all_nudges = self.nudges_cache.get(user_id, [])
            
            # Filter active nudges
            active_nudges = [
                nudge for nudge in all_nudges
                if not nudge.dismissed 
                and not nudge.acted_upon
                and (nudge.expires_at is None or nudge.expires_at > datetime.now())
            ]
            
            # Filter by channel if specified
            if channel:
                active_nudges = [
                    nudge for nudge in active_nudges
                    if channel in nudge.suggested_channels
                ]
            
            return active_nudges
            
        except Exception as e:
            logger.error(f"Error getting active nudges for user {user_id}: {e}")
            return []
    
    def dismiss_nudge(self, user_id: int, nudge_id: str) -> bool:
        """Mark a nudge as dismissed."""
        try:
            nudges = self.nudges_cache.get(user_id, [])
            for nudge in nudges:
                if nudge.id == nudge_id:
                    nudge.dismissed = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Error dismissing nudge {nudge_id}: {e}")
            return False
    
    def mark_nudge_acted(self, user_id: int, nudge_id: str) -> bool:
        """Mark a nudge as acted upon."""
        try:
            nudges = self.nudges_cache.get(user_id, [])
            for nudge in nudges:
                if nudge.id == nudge_id:
                    nudge.acted_upon = True
                    return True
            return False
        except Exception as e:
            logger.error(f"Error marking nudge {nudge_id} as acted upon: {e}")
            return False
    
    def update_user_patterns(self, user_id: int, action: str, timestamp: datetime = None):
        """Update user behavior patterns based on actions."""
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = UserBehaviorPattern(
                    user_id=user_id,
                    preferred_nudge_times=[9, 14, 17],  # Default times
                    preferred_channels=[NudgeChannel.IN_APP],
                    response_rate_by_type={},
                    avg_response_time_hours=2.0,
                    activity_patterns={}
                )
            
            pattern = self.user_patterns[user_id]
            
            # Update activity patterns
            hour = timestamp.hour
            if 'active_hours' not in pattern.activity_patterns:
                pattern.activity_patterns['active_hours'] = defaultdict(int)
            pattern.activity_patterns['active_hours'][hour] += 1
            
            # Update preferred nudge times based on activity
            active_hours = pattern.activity_patterns['active_hours']
            top_hours = sorted(active_hours.items(), key=lambda x: x[1], reverse=True)[:3]
            pattern.preferred_nudge_times = [hour for hour, _ in top_hours]
            
            pattern.last_updated = timestamp
            
        except Exception as e:
            logger.error(f"Error updating user patterns for {user_id}: {e}")
    
    def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user data for nudge generation."""
        try:
            from models.session import Session
            from models.task import Task
            from models.summary import Summary
            from app import db
            
            # Get recent sessions
            sessions = db.session.query(Session).filter_by(user_id=user_id).order_by(
                Session.created_at.desc()
            ).limit(50).all()
            
            # Get tasks
            tasks = db.session.query(Task).filter_by(user_id=user_id).all()
            
            # Get summaries
            session_ids = [s.id for s in sessions]
            summaries = db.session.query(Summary).filter(
                Summary.session_id.in_(session_ids)
            ).all() if session_ids else []
            
            return {
                'user_id': user_id,
                'sessions': sessions,
                'tasks': tasks,
                'summaries': summaries
            }
            
        except Exception as e:
            logger.error(f"Error getting user data for {user_id}: {e}")
            return {}
    
    def _get_meeting_data(self, meeting_id: int) -> Dict[str, Any]:
        """Get meeting data for follow-up suggestions."""
        try:
            from models.session import Session
            from models.segment import Segment
            from models.summary import Summary
            from models.task import Task
            from app import db
            
            # Get session
            session = db.session.query(Session).filter_by(id=meeting_id).first()
            if not session:
                return {}
            
            # Get segments
            segments = db.session.query(Segment).filter_by(session_id=meeting_id).all()
            
            # Get summary
            summary = db.session.query(Summary).filter_by(session_id=meeting_id).first()
            
            # Get tasks
            tasks = db.session.query(Task).filter_by(session_id=meeting_id).all()
            
            return {
                'session': session,
                'segments': segments,
                'summary': summary,
                'tasks': tasks,
                'user_id': session.user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting meeting data for {meeting_id}: {e}")
            return {}
    
    def _generate_task_nudges(self, user_id: int, user_data: Dict[str, Any]) -> List[SmartNudge]:
        """Generate task-related nudges."""
        nudges = []
        tasks = user_data.get('tasks', [])
        
        now = datetime.now()
        
        for task in tasks:
            # Overdue tasks
            if task.due_date and task.due_date < now and task.status != 'completed':
                days_overdue = (now - task.due_date).days
                priority = Priority.URGENT if days_overdue > 3 else Priority.HIGH
                
                nudge = SmartNudge(
                    id=f"overdue_task_{task.id}",
                    type=NudgeType.OVERDUE_TASK,
                    priority=priority,
                    title=f"Overdue Task: {task.text[:50]}...",
                    message=f"This task is {days_overdue} days overdue. Consider updating or completing it.",
                    action_text="View Task",
                    action_url=f"/tasks/{task.id}",
                    context={'task_id': task.id, 'days_overdue': days_overdue},
                    related_entities=[str(task.id)],
                    suggested_channels=[NudgeChannel.IN_APP, NudgeChannel.PUSH],
                    created_at=now
                )
                nudges.append(nudge)
            
            # Upcoming deadlines
            elif task.due_date and task.status != 'completed':
                days_until = (task.due_date - now).days
                if 0 <= days_until <= 2:
                    priority = Priority.HIGH if days_until == 0 else Priority.MEDIUM
                    
                    nudge = SmartNudge(
                        id=f"upcoming_deadline_{task.id}",
                        type=NudgeType.UPCOMING_DEADLINE,
                        priority=priority,
                        title=f"Deadline Approaching: {task.text[:50]}...",
                        message=f"This task is due in {days_until} days.",
                        action_text="Work on Task",
                        action_url=f"/tasks/{task.id}",
                        context={'task_id': task.id, 'days_until': days_until},
                        related_entities=[str(task.id)],
                        suggested_channels=[NudgeChannel.IN_APP],
                        created_at=now
                    )
                    nudges.append(nudge)
        
        return nudges
    
    def _generate_meeting_nudges(self, user_id: int, user_data: Dict[str, Any]) -> List[SmartNudge]:
        """Generate meeting-related nudges."""
        nudges = []
        sessions = user_data.get('sessions', [])
        
        now = datetime.now()
        
        # Check for sessions without follow-up action
        for session in sessions[:5]:  # Recent 5 sessions
            if session.created_at < (now - timedelta(days=2)):  # Older than 2 days
                # Check if there are tasks created from this session
                session_tasks = [t for t in user_data.get('tasks', []) if t.session_id == session.id]
                
                if not session_tasks:
                    nudge = SmartNudge(
                        id=f"missing_follow_up_{session.id}",
                        type=NudgeType.MISSING_FOLLOW_UP,
                        priority=Priority.MEDIUM,
                        title=f"No Follow-up: {session.title[:50]}...",
                        message="This meeting has no follow-up tasks. Consider reviewing for action items.",
                        action_text="Review Meeting",
                        action_url=f"/sessions/{session.id}",
                        context={'session_id': session.id},
                        related_entities=[str(session.id)],
                        suggested_channels=[NudgeChannel.IN_APP],
                        created_at=now
                    )
                    nudges.append(nudge)
        
        return nudges
    
    def _generate_follow_up_nudges(self, user_id: int, user_data: Dict[str, Any]) -> List[SmartNudge]:
        """Generate follow-up related nudges."""
        nudges = []
        
        # Check for patterns in completed tasks
        completed_tasks = [t for t in user_data.get('tasks', []) if t.status == 'completed']
        if completed_tasks:
            # Suggest reviewing completed work
            recent_completions = [
                t for t in completed_tasks 
                if t.updated_at and t.updated_at > (datetime.now() - timedelta(days=7))
            ]
            
            if len(recent_completions) >= 3:
                nudge = SmartNudge(
                    id=f"action_review_{user_id}",
                    type=NudgeType.ACTION_REVIEW,
                    priority=Priority.LOW,
                    title="Great Progress!",
                    message=f"You've completed {len(recent_completions)} tasks this week. Consider sharing your progress.",
                    action_text="View Achievements",
                    action_url="/dashboard",
                    context={'completed_count': len(recent_completions)},
                    related_entities=[],
                    suggested_channels=[NudgeChannel.IN_APP],
                    created_at=datetime.now()
                )
                nudges.append(nudge)
        
        return nudges
    
    def _generate_collaboration_nudges(self, user_id: int, user_data: Dict[str, Any]) -> List[SmartNudge]:
        """Generate collaboration-related nudges."""
        nudges = []
        sessions = user_data.get('sessions', [])
        
        # Look for mentioned people in recent sessions
        mentioned_people = set()
        for session in sessions[:10]:  # Recent 10 sessions
            # Simple pattern to find @mentions or "with John" patterns
            title_words = session.title.lower().split()
            for word in title_words:
                if word.startswith('@') or word in ['with', 'and']:
                    # Could be a person mention
                    pass
        
        # This could be enhanced with more sophisticated NLP
        return nudges
    
    def _generate_review_nudges(self, user_id: int, user_data: Dict[str, Any]) -> List[SmartNudge]:
        """Generate review-related nudges."""
        nudges = []
        
        # Suggest periodic reviews
        now = datetime.now()
        if now.weekday() == 4:  # Friday - weekly review
            nudge = SmartNudge(
                id=f"weekly_review_{user_id}",
                type=NudgeType.ACTION_REVIEW,
                priority=Priority.LOW,
                title="Weekly Review Time",
                message="It's Friday! Consider reviewing your week's meetings and tasks.",
                action_text="Start Review",
                action_url="/insights",
                context={'review_type': 'weekly'},
                related_entities=[],
                suggested_channels=[NudgeChannel.IN_APP],
                created_at=now
            )
            nudges.append(nudge)
        
        return nudges
    
    def generate_insight_reminder(self, user_id: int, workspace_id: int) -> Optional[SmartNudge]:
        """
        Generate AI-powered insight reminder with 24-hour throttling.
        Uses predictive AI to identify the most valuable reminder based on user patterns.
        
        Args:
            user_id: User ID
            workspace_id: Workspace ID
            
        Returns:
            SmartNudge with insight reminder or None if throttled/no insight
        """
        try:
            # Check 24-hour throttling
            now = datetime.now()
            last_reminder = self.last_insight_reminder.get(user_id)
            
            if last_reminder and (now - last_reminder) < timedelta(hours=24):
                hours_remaining = 24 - (now - last_reminder).total_seconds() / 3600
                logger.info(f"Insight reminder throttled for user {user_id} ({hours_remaining:.1f}h remaining)")
                return None
            
            # Get user data for analysis
            user_data = self._get_user_data(user_id)
            if not user_data:
                return None
            
            # Use AI to analyze patterns and generate insight
            insight = self._generate_ai_insight(user_data)
            if not insight:
                # Fallback to rule-based insights when AI fails
                logger.info(f"AI insight failed for user {user_id}, using rule-based fallback")
                insight = self._generate_fallback_insight(user_data)
                if not insight:
                    return None
            
            # Create insight reminder nudge
            nudge = SmartNudge(
                id=f"insight_reminder_{user_id}_{int(now.timestamp())}",
                type=NudgeType.INSIGHT_REMINDER,
                priority=Priority.MEDIUM,
                title=insight.get('title', 'Meeting Insight'),
                message=insight.get('message', 'Check your recent meetings for important updates'),
                action_text=insight.get('action_text', 'View Details'),
                action_url=insight.get('action_url', '/dashboard'),
                context={
                    'insight_type': insight.get('type', 'general'),
                    'confidence': insight.get('confidence', 0.7),
                    'workspace_id': workspace_id
                },
                related_entities=insight.get('related_entities', []),
                suggested_channels=[NudgeChannel.IN_APP, NudgeChannel.PUSH],
                created_at=now
            )
            
            # Update throttle timestamp
            self.last_insight_reminder[user_id] = now
            
            logger.info(f"Generated insight reminder for user {user_id}: {nudge.title}")
            return nudge
            
        except Exception as e:
            logger.error(f"Error generating insight reminder for user {user_id}: {e}")
            return None
    
    def _generate_ai_insight(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use AI to generate intelligent insights from user's recent activities.
        
        Args:
            user_data: Comprehensive user data (sessions, tasks, summaries)
            
        Returns:
            Dictionary with insight data or None
        """
        try:
            from services.ai_insights_service import AIInsightsService
            
            ai_service = AIInsightsService()
            if not ai_service.is_available():
                return self._generate_fallback_insight(user_data)
            
            # Analyze recent meetings and tasks
            sessions = user_data.get('sessions', [])[:5]  # Last 5 meetings
            tasks = user_data.get('tasks', [])
            
            # Build context for AI
            incomplete_tasks = [t for t in tasks if t.status != 'completed']
            overdue_tasks = [
                t for t in incomplete_tasks 
                if t.due_date and t.due_date < datetime.now()
            ]
            
            recent_meetings_summary = []
            for session in sessions:
                recent_meetings_summary.append(f"- {session.title} ({session.created_at.strftime('%Y-%m-%d')})")
            
            # Construct AI prompt
            prompt = f"""Analyze these meeting patterns and tasks to generate ONE actionable insight reminder:

RECENT MEETINGS ({len(sessions)}):
{chr(10).join(recent_meetings_summary[:5])}

TASKS STATUS:
- Total tasks: {len(tasks)}
- Incomplete: {len(incomplete_tasks)}
- Overdue: {len(overdue_tasks)}

Generate a single, specific, actionable insight in JSON format:
{{
    "title": "Brief, attention-grabbing title (max 50 chars)",
    "message": "Specific, actionable message (max 150 chars)",
    "action_text": "Clear action button text",
    "action_url": "/dashboard or /tasks or /sessions/{{id}}",
    "type": "pattern|overdue|follow_up|decision",
    "confidence": 0.0-1.0,
    "related_entities": ["task_id" or "session_id"]
}}

Focus on: overdue tasks, missing follow-ups, recurring patterns, or important decisions needing attention."""

            # Call AI service
            response = ai_service.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are a productivity assistant. Generate concise, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            insight = json.loads(response.choices[0].message.content)
            return insight
            
        except Exception as e:
            logger.error(f"Error generating AI insight: {e}")
            return self._generate_fallback_insight(user_data)
    
    def _generate_fallback_insight(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate rule-based insight when AI is unavailable."""
        tasks = user_data.get('tasks', [])
        sessions = user_data.get('sessions', [])
        
        # Find most urgent item
        incomplete_tasks = [t for t in tasks if t.status != 'completed']
        overdue_tasks = [
            t for t in incomplete_tasks 
            if t.due_date and t.due_date < datetime.now()
        ]
        
        if overdue_tasks:
            task = overdue_tasks[0]
            days_overdue = (datetime.now() - task.due_date).days
            return {
                'title': f"Overdue: {task.text[:40]}...",
                'message': f"{days_overdue} days overdue. Time to take action!",
                'action_text': "View Task",
                'action_url': f"/tasks",
                'type': "overdue",
                'confidence': 0.9,
                'related_entities': [str(task.id)]
            }
        
        elif sessions and not any(t.session_id == sessions[0].id for t in tasks):
            # Recent meeting with no follow-up tasks
            session = sessions[0]
            return {
                'title': f"Missing Follow-up: {session.title[:40]}...",
                'message': "No tasks created from this meeting. Review for action items?",
                'action_text': "Review Meeting",
                'action_url': f"/sessions/{session.id}",
                'type': "follow_up",
                'confidence': 0.7,
                'related_entities': [str(session.id)]
            }
        
        return None
    
    def _personalize_nudges(self, user_id: int, nudges: List[SmartNudge]) -> List[SmartNudge]:
        """Personalize nudges based on user patterns."""
        if user_id not in self.user_patterns:
            return nudges
        
        pattern = self.user_patterns[user_id]
        
        for nudge in nudges:
            # Adjust channels based on user preferences
            if pattern.preferred_channels:
                nudge.suggested_channels = [
                    ch for ch in nudge.suggested_channels 
                    if ch in pattern.preferred_channels
                ]
                if not nudge.suggested_channels:
                    nudge.suggested_channels = pattern.preferred_channels[:1]
        
        return nudges
    
    def _suggest_from_action_items(self, meeting_data: Dict[str, Any]) -> List[FollowUpSuggestion]:
        """Generate suggestions based on action items."""
        suggestions = []
        summary = meeting_data.get('summary')
        
        if summary and summary.action_items:
            try:
                action_items = json.loads(summary.action_items) if isinstance(summary.action_items, str) else summary.action_items
                
                for i, action in enumerate(action_items):
                    suggestion = FollowUpSuggestion(
                        id=f"action_follow_{meeting_data['session'].id}_{i}",
                        title=f"Follow up: {action[:50]}...",
                        description=f"Create a task to track this action item: {action}",
                        suggested_action="Create Task",
                        context={'action_item': action, 'source': 'meeting_summary'},
                        confidence=0.9,
                        related_meeting_id=meeting_data['session'].id,
                        related_entities=[],
                        suggested_due_date=datetime.now() + timedelta(days=7),
                        priority=Priority.HIGH,
                        category="action_item"
                    )
                    suggestions.append(suggestion)
            except json.JSONDecodeError:
                pass
        
        return suggestions
    
    def _suggest_from_decisions(self, meeting_data: Dict[str, Any]) -> List[FollowUpSuggestion]:
        """Generate suggestions based on decisions made."""
        suggestions = []
        summary = meeting_data.get('summary')
        
        if summary and summary.decisions:
            try:
                decisions = json.loads(summary.decisions) if isinstance(summary.decisions, str) else summary.decisions
                
                for i, decision in enumerate(decisions):
                    suggestion = FollowUpSuggestion(
                        id=f"decision_follow_{meeting_data['session'].id}_{i}",
                        title=f"Document decision: {decision[:40]}...",
                        description=f"Consider documenting this decision and communicating it to stakeholders: {decision}",
                        suggested_action="Document Decision",
                        context={'decision': decision, 'source': 'meeting_summary'},
                        confidence=0.8,
                        related_meeting_id=meeting_data['session'].id,
                        related_entities=[],
                        suggested_due_date=datetime.now() + timedelta(days=3),
                        priority=Priority.MEDIUM,
                        category="decision"
                    )
                    suggestions.append(suggestion)
            except json.JSONDecodeError:
                pass
        
        return suggestions
    
    def _suggest_from_topics(self, meeting_data: Dict[str, Any]) -> List[FollowUpSuggestion]:
        """Generate suggestions based on topics discussed."""
        suggestions = []
        segments = meeting_data.get('segments', [])
        
        # Look for question patterns in the transcript
        question_patterns = [
            r'\b(?:what|how|when|where|why|who)\b.*\?',
            r'\b(?:should we|can we|will we|do we)\b.*\?',
            r'\b(?:next steps?|follow up|action)\b'
        ]
        
        questions_found = []
        for segment in segments:
            if segment.text:
                for pattern in question_patterns:
                    matches = re.findall(pattern, segment.text, re.IGNORECASE)
                    questions_found.extend(matches)
        
        if questions_found:
            suggestion = FollowUpSuggestion(
                id=f"questions_follow_{meeting_data['session'].id}",
                title="Unanswered Questions",
                description=f"Found {len(questions_found)} questions that might need follow-up.",
                suggested_action="Review Questions",
                context={'questions': questions_found[:5], 'source': 'transcript_analysis'},
                confidence=0.6,
                related_meeting_id=meeting_data['session'].id,
                related_entities=[],
                suggested_due_date=datetime.now() + timedelta(days=5),
                priority=Priority.LOW,
                category="questions"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_from_participants(self, meeting_data: Dict[str, Any]) -> List[FollowUpSuggestion]:
        """Generate suggestions based on participants."""
        suggestions = []
        segments = meeting_data.get('segments', [])
        
        # Find unique speakers
        speakers = set()
        for segment in segments:
            if segment.speaker_label:
                speakers.add(segment.speaker_label)
        
        if len(speakers) > 2:
            suggestion = FollowUpSuggestion(
                id=f"participants_follow_{meeting_data['session'].id}",
                title="Share Meeting Summary",
                description=f"Meeting had {len(speakers)} participants. Consider sharing a summary.",
                suggested_action="Share Summary",
                context={'participant_count': len(speakers), 'source': 'participant_analysis'},
                confidence=0.7,
                related_meeting_id=meeting_data['session'].id,
                related_entities=list(speakers),
                suggested_due_date=datetime.now() + timedelta(days=1),
                priority=Priority.MEDIUM,
                category="communication"
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _suggest_from_timeline(self, meeting_data: Dict[str, Any]) -> List[FollowUpSuggestion]:
        """Generate suggestions based on meeting timeline."""
        suggestions = []
        session = meeting_data.get('session')
        
        if session and session.duration_seconds:
            duration_minutes = session.duration_seconds / 60
            
            # Long meetings might need follow-up
            if duration_minutes > 60:
                suggestion = FollowUpSuggestion(
                    id=f"long_meeting_follow_{session.id}",
                    title="Long Meeting Follow-up",
                    description=f"This {duration_minutes:.0f}-minute meeting might benefit from a summary email.",
                    suggested_action="Send Summary",
                    context={'duration_minutes': duration_minutes, 'source': 'timeline_analysis'},
                    confidence=0.6,
                    related_meeting_id=session.id,
                    related_entities=[],
                    suggested_due_date=datetime.now() + timedelta(hours=4),
                    priority=Priority.LOW,
                    category="communication"
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def _score_suggestions(self, suggestions: List[FollowUpSuggestion]) -> List[FollowUpSuggestion]:
        """Score and rank suggestions by relevance."""
        # Sort by confidence and priority
        suggestions.sort(key=lambda s: (s.confidence, s.priority.value), reverse=True)
        return suggestions[:10]  # Return top 10 suggestions


# Global service instance
smart_nudges_service = SmartNudgesService()