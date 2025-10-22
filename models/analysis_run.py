"""
models/analysis_run.py
Keeps a history of post-meeting analysis and summary jobs.
"""

from datetime import datetime
from app import db  # uses the same SQLAlchemy instance as the rest of Mina

class AnalysisRun(db.Model):
    __tablename__ = "analysis_runs"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, nullable=False)
    session_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="running")  # running / completed / failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    def mark_completed(self):
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, message: str):
        self.status = "failed"
        self.error_message = message
        self.completed_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "session_id": self.session_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }
