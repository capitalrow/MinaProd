"""
Mina Models Package (M2 + M3)
SQLAlchemy 2.0 models for meeting sessions, transcription segments, and AI summaries.
"""

from flask_sqlalchemy import SQLAlchemy
from .base import Base

# Create db instance with the existing Base
db = SQLAlchemy(model_class=Base)

from .session import Session
from .segment import Segment
from .shared_link import SharedLink
from .team_share import TeamShare
from .share_analytics import ShareAnalytic
from .metrics import ChunkMetric, SessionMetric

# Import new comprehensive models for Mina productivity platform
from .user import User
from .workspace import Workspace
from .meeting import Meeting
from .participant import Participant
from .task import Task
from .calendar_event import CalendarEvent
from .analytics import Analytics
from .marker import Marker
from .comment import Comment
from .copilot_template import CopilotTemplate
from .copilot_conversation import CopilotConversation
from .event_ledger import EventLedger, EventType, EventStatus

# Import Summary last to avoid circular imports
try:
    from .summary import Summary
except ImportError:
    # Handle circular import gracefully
    Summary = None

__all__ = [
    'db', 'Base', 'Session', 'Segment', 'Summary', 'SharedLink', 'TeamShare', 'ShareAnalytic',
    'ChunkMetric', 'SessionMetric', 'User', 'Workspace', 'Meeting', 
    'Participant', 'Task', 'CalendarEvent', 'Analytics', 'Marker', 'Comment', 'CopilotTemplate',
    'CopilotConversation', 'EventLedger', 'EventType', 'EventStatus'
]
