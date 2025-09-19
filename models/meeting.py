# models/meeting.py  (only the relationship line is important here)
from app_refactored import db

class Meeting(db.Model):
    __tablename__ = "meetings"
    id = db.Column(db.Integer, primary_key=True)
    # ... your existing columns ...

    # add or ensure this exists:
    tasks = db.relationship(
        "Task",
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )