"""
TaskCounters Model for CROWN⁴.5 Compliance
Stores cached task counts per user for instant UI updates and dashboard integration.
Enables <200ms bootstrap and real-time counter pulse animations.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, ForeignKey, func, Index, Boolean, String
from .base import Base

if TYPE_CHECKING:
    from .user import User


class TaskCounters(Base):
    """
    Cached task counts per user for instant UI updates.
    Updated via WebSocket events for real-time synchronization.
    """
    __tablename__ = "task_counters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # User association (one counter set per user)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    user: Mapped["User"] = relationship(back_populates="task_counters")
    
    # Core counters
    total_count: Mapped[int] = mapped_column(Integer, default=0)  # All tasks
    pending_count: Mapped[int] = mapped_column(Integer, default=0)  # todo + in_progress
    completed_count: Mapped[int] = mapped_column(Integer, default=0)  # completed
    
    # Extended counters
    overdue_count: Mapped[int] = mapped_column(Integer, default=0)  # Overdue tasks
    due_today_count: Mapped[int] = mapped_column(Integer, default=0)  # Due today
    due_this_week_count: Mapped[int] = mapped_column(Integer, default=0)  # Due within 7 days
    snoozed_count: Mapped[int] = mapped_column(Integer, default=0)  # Snoozed tasks
    
    # Priority-based counters
    urgent_count: Mapped[int] = mapped_column(Integer, default=0)  # Priority = urgent
    high_priority_count: Mapped[int] = mapped_column(Integer, default=0)  # Priority = high
    
    # AI-related counters
    ai_proposed_count: Mapped[int] = mapped_column(Integer, default=0)  # Pending AI suggestions
    ai_accepted_count: Mapped[int] = mapped_column(Integer, default=0)  # Accepted AI suggestions
    
    # Assignment counters
    assigned_to_me_count: Mapped[int] = mapped_column(Integer, default=0)  # Tasks assigned to user
    created_by_me_count: Mapped[int] = mapped_column(Integer, default=0)  # Tasks created by user
    
    # CROWN⁴.5: Reconciliation counters
    pending_sync_count: Mapped[int] = mapped_column(Integer, default=0)  # Tasks awaiting sync
    conflict_count: Mapped[int] = mapped_column(Integer, default=0)  # Tasks with conflicts
    
    # CROWN⁴.5: Checksum for cache validation
    checksum: Mapped[Optional[str]] = mapped_column(String(64))  # SHA-256 hash of all counters
    
    # Timestamps
    last_computed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Database indexes for query optimization
    __table_args__ = (
        Index('ix_task_counters_user', 'user_id'),
    )

    def __repr__(self):
        return f'<TaskCounters user_id={self.user_id} total={self.total_count} pending={self.pending_count}>'

    def to_dict(self) -> dict:
        """Convert counters to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_count': self.total_count,
            'pending_count': self.pending_count,
            'completed_count': self.completed_count,
            'overdue_count': self.overdue_count,
            'due_today_count': self.due_today_count,
            'due_this_week_count': self.due_this_week_count,
            'snoozed_count': self.snoozed_count,
            'urgent_count': self.urgent_count,
            'high_priority_count': self.high_priority_count,
            'ai_proposed_count': self.ai_proposed_count,
            'ai_accepted_count': self.ai_accepted_count,
            'assigned_to_me_count': self.assigned_to_me_count,
            'created_by_me_count': self.created_by_me_count,
            'pending_sync_count': self.pending_sync_count,
            'conflict_count': self.conflict_count,
            'checksum': self.checksum,
            'last_computed_at': self.last_computed_at.isoformat() if self.last_computed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def compute_checksum(self) -> str:
        """Compute SHA-256 checksum of all counter values for cache validation."""
        import hashlib
        counter_values = f"{self.total_count}{self.pending_count}{self.completed_count}{self.overdue_count}{self.due_today_count}{self.due_this_week_count}{self.snoozed_count}{self.urgent_count}{self.high_priority_count}{self.ai_proposed_count}{self.ai_accepted_count}{self.assigned_to_me_count}{self.created_by_me_count}{self.pending_sync_count}{self.conflict_count}"
        return hashlib.sha256(counter_values.encode()).hexdigest()

    def refresh_checksum(self):
        """Recompute and update checksum."""
        self.checksum = self.compute_checksum()
