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
from .metrics import ChunkMetric, SessionMetric

# Import Summary last to avoid circular imports
try:
    from .summary import Summary
except ImportError:
    # Handle circular import gracefully
    Summary = None

__all__ = ['db', 'Base', 'Session', 'Segment', 'Summary', 'SharedLink', 'ChunkMetric', 'SessionMetric']
