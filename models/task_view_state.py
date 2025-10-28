"""
TaskViewState Model for CROWN⁴.5 Compliance
Stores user-specific view state for Tasks page (filter, sort, query, selections, toast)
Enables deterministic UI restoration and cache-first architecture.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, JSON, Text, Index, Boolean
from .base import Base

if TYPE_CHECKING:
    from .user import User


class TaskViewState(Base):
    """
    User-specific view state for Tasks page.
    Supports cache-first bootstrap and deterministic UI restoration.
    """
    __tablename__ = "task_view_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User association (one view state per user)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship(back_populates="task_view_state")
    
    # Filter state
    active_filter: Mapped[str] = mapped_column(String(64), default="all")  # all, assigned_to_me, created_by_me, pending, completed, snoozed
    status_filter: Mapped[Optional[list]] = mapped_column(JSON)  # ['todo', 'in_progress', 'completed']
    priority_filter: Mapped[Optional[list]] = mapped_column(JSON)  # ['high', 'urgent']
    label_filter: Mapped[Optional[list]] = mapped_column(JSON)  # Selected label IDs
    date_range: Mapped[Optional[dict]] = mapped_column(JSON)  # {start_date: str, end_date: str}
    
    # Sort state
    sort_field: Mapped[str] = mapped_column(String(32), default="due_date")  # due_date, priority, created_at, status
    sort_direction: Mapped[str] = mapped_column(String(4), default="asc")  # asc, desc
    
    # Search query
    search_query: Mapped[Optional[str]] = mapped_column(Text)  # Current search query
    
    # Multi-select state
    selected_task_ids: Mapped[Optional[list]] = mapped_column(JSON)  # Currently selected task IDs
    
    # Toast/notification state
    toast_state: Mapped[Optional[dict]] = mapped_column(JSON)  # {message: str, type: success|error|info, timestamp: int}
    
    # CROWN⁴.5: Event sequencing for deterministic restore
    last_event_id: Mapped[Optional[int]] = mapped_column(Integer)  # Last processed event ID for delta sync
    
    # CROWN⁴.5: Scroll position for seamless restore
    scroll_position: Mapped[int] = mapped_column(Integer, default=0)  # Scroll position in pixels
    
    # CROWN⁴.5: View mode preferences
    view_mode: Mapped[str] = mapped_column(String(16), default="list")  # list, kanban, timeline
    density: Mapped[str] = mapped_column(String(16), default="comfortable")  # compact, comfortable, spacious
    
    # CROWN⁴.5: Animation preferences
    animations_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Database indexes for query optimization
    __table_args__ = (
        Index('ix_task_view_states_user', 'user_id'),
        Index('ix_task_view_states_last_event', 'last_event_id'),
    )

    def __repr__(self):
        return f'<TaskViewState user_id={self.user_id} filter={self.active_filter}>'

    def to_dict(self) -> dict:
        """Convert view state to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'active_filter': self.active_filter,
            'status_filter': self.status_filter,
            'priority_filter': self.priority_filter,
            'label_filter': self.label_filter,
            'date_range': self.date_range,
            'sort_field': self.sort_field,
            'sort_direction': self.sort_direction,
            'search_query': self.search_query,
            'selected_task_ids': self.selected_task_ids,
            'toast_state': self.toast_state,
            'last_event_id': self.last_event_id,
            'scroll_position': self.scroll_position,
            'view_mode': self.view_mode,
            'density': self.density,
            'animations_enabled': self.animations_enabled,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def update_from_dict(self, data: dict):
        """Update view state from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'user_id', 'created_at', 'updated_at']:
                setattr(self, key, value)
