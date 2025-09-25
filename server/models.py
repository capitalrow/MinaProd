from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utcnow():
    return datetime.utcnow()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=True)
    tz = db.Column(db.String(64), nullable=True, default="Europe/London")
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    title = db.Column(db.String(255), nullable=False, default="Untitled Conversation")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    duration_s = db.Column(db.Integer, default=0)
    word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(32), default="final")  # draft|live|final
    source = db.Column(db.String(32), default="realtime")
    tz = db.Column(db.String(64), default="Europe/London")
    device = db.Column(db.String(64), default="browser")

class Segment(db.Model):
    __tablename__ = "segments"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), index=True, nullable=False)
    idx = db.Column(db.Integer, nullable=False, index=True)
    start_ms = db.Column(db.Integer, default=0)
    end_ms = db.Column(db.Integer, default=0)
    text = db.Column(db.Text, default="")
    is_final = db.Column(db.Boolean, default=False)

class Highlight(db.Model):
    __tablename__ = "highlights"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), index=True, nullable=False)
    start_ms = db.Column(db.Integer, default=0)
    end_ms = db.Column(db.Integer, default=0)
    text = db.Column(db.Text, default="")
    label = db.Column(db.String(64), default="")

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), index=True, nullable=False)
    text = db.Column(db.Text, default="")
    assignee = db.Column(db.String(120), default="")
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(24), default="open")
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

class Share(db.Model):
    __tablename__ = "shares"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey("conversations.id"), nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, index=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    can_comment = db.Column(db.Boolean, default=False)