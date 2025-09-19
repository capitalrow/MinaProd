# models/task.py
from datetime import datetime
from app_refactored import db

class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(
        db.Integer,
        db.ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=True,
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    assignee = db.Column(db.String(120))
    due_at = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="open")  # open|in_progress|done|blocked

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # relationship set from Meeting.tasks
    meeting = db.relationship("Meeting", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"