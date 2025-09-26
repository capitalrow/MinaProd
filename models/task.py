"""
Task Model for AI-Extracted Action Items and Task Management
SQLAlchemy 2.0-safe model for action items extracted from meetings with full task management capabilities.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Date, Text, Boolean, ForeignKey, func, JSON, Float
from .base import Base

# Forward reference for type checking
if TYPE_CHECKING:
    from .meeting import Meeting
    from .user import User


class Task(Base):
    """
    Task model for action items extracted from meetings with comprehensive task management.
    Supports AI extraction, assignment, status tracking, and collaboration.
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Task content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Task classification
    task_type: Mapped[str] = mapped_column(String(32), default="action_item")  # action_item, follow_up, decision, research
    priority: Mapped[str] = mapped_column(String(16), default="medium")  # low, medium, high, urgent
    category: Mapped[Optional[str]] = mapped_column(String(64))  # Custom categorization
    
    # Task status and lifecycle
    status: Mapped[str] = mapped_column(String(32), default="todo")  # todo, in_progress, blocked, completed, cancelled
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    
    # Scheduling and deadlines
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    reminder_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    meeting: Mapped["Meeting"] = relationship(back_populates="tasks")
    
    assigned_to_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_to: Mapped[Optional["User"]] = relationship(back_populates="assigned_tasks")
    
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    
    # AI extraction metadata
    extracted_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # AI confidence (0-1)
    extraction_context: Mapped[Optional[dict]] = mapped_column(JSON)  # Context from transcript
    
    # Task details
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float)
    tags: Mapped[Optional[list]] = mapped_column(JSON)  # Task tags
    
    # Dependencies and relationships
    depends_on_task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    depends_on_task: Mapped[Optional["Task"]] = relationship(remote_side="Task.id")
    
    # Collaboration and comments
    is_collaborative: Mapped[bool] = mapped_column(Boolean, default=False)
    watchers: Mapped[Optional[list]] = mapped_column(JSON)  # User IDs watching this task
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due_date or self.status == "completed":
            return False
        return date.today() > self.due_date

    @property
    def is_due_soon(self, days: int = 3) -> bool:
        """Check if task is due within specified days."""
        if not self.due_date or self.status == "completed":
            return False
        days_until_due = (self.due_date - date.today()).days
        return 0 <= days_until_due <= days

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"

    @property
    def is_in_progress(self) -> bool:
        """Check if task is in progress."""
        return self.status == "in_progress"

    @property
    def days_until_due(self) -> Optional[int]:
        """Get number of days until due date."""
        if not self.due_date:
            return None
        return (self.due_date - date.today()).days

    def complete_task(self):
        """Mark task as completed."""
        self.status = "completed"
        self.completion_percentage = 100
        self.completed_at = datetime.utcnow()

    def start_task(self):
        """Mark task as in progress."""
        if self.status == "todo":
            self.status = "in_progress"

    def block_task(self, reason: Optional[str] = None):
        """Mark task as blocked."""
        self.status = "blocked"
        if reason and self.extraction_context:
            self.extraction_context["blocked_reason"] = reason

    def update_progress(self, percentage: int):
        """Update task completion percentage."""
        self.completion_percentage = max(0, min(100, percentage))
        if percentage == 100:
            self.complete_task()
        elif percentage > 0 and self.status == "todo":
            self.start_task()

    def assign_to_user(self, user_id: int):
        """Assign task to a user."""
        self.assigned_to_id = user_id

    def add_watcher(self, user_id: int):
        """Add a user to watch this task."""
        if not self.watchers:
            self.watchers = []
        if user_id not in self.watchers:
            self.watchers.append(user_id)

    def remove_watcher(self, user_id: int):
        """Remove a user from watching this task."""
        if self.watchers and user_id in self.watchers:
            self.watchers.remove(user_id)

    def to_dict(self, include_relationships=False):
        """Convert task to dictionary for JSON serialization."""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'priority': self.priority,
            'category': self.category,
            'status': self.status,
            'completion_percentage': self.completion_percentage,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'reminder_date': self.reminder_date.isoformat() if self.reminder_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'meeting_id': self.meeting_id,
            'assigned_to_id': self.assigned_to_id,
            'created_by_id': self.created_by_id,
            'extracted_by_ai': self.extracted_by_ai,
            'confidence_score': self.confidence_score,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'tags': self.tags,
            'depends_on_task_id': self.depends_on_task_id,
            'is_collaborative': self.is_collaborative,
            'watchers': self.watchers,
            'is_overdue': self.is_overdue,
            'is_due_soon': self.is_due_soon,
            'is_completed': self.is_completed,
            'is_in_progress': self.is_in_progress,
            'days_until_due': self.days_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relationships:
            if self.assigned_to:
                data['assigned_to'] = self.assigned_to.to_dict()
            if self.created_by:
                data['created_by'] = self.created_by.to_dict()
            if self.meeting:
                data['meeting'] = {
                    'id': self.meeting.id,
                    'title': self.meeting.title,
                    'scheduled_start': self.meeting.scheduled_start.isoformat() if self.meeting.scheduled_start else None
                }
                
        return data

    @staticmethod
    def create_from_ai_extraction(meeting_id: int, title: str, description: Optional[str] = None, 
                                 confidence: Optional[float] = None, context: Optional[dict] = None) -> "Task":
        """Create a task from AI extraction with metadata."""
        task = Task(
            meeting_id=meeting_id,
            title=title,
            description=description,
            extracted_by_ai=True,
            confidence_score=confidence,
            extraction_context=context
        )
        return task