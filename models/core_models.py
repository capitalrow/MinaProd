from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlalchemy.dialects.postgresql import JSONB
from extensions import db

class SummaryDoc(db.Model):
    __tablename__ = "summary_docs"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, index=True, nullable=False, unique=True)
    summary = db.Column(db.Text)
    actions = db.Column(JSONB)          # list[str]
    decisions = db.Column(JSONB)        # list[str]
    risks = db.Column(JSONB)            # list[str]
    language = db.Column(db.String(8))
    model = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Team(db.Model):
    __tablename__ = "teams"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.String(64), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Membership(db.Model):
    __tablename__ = "memberships"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    role = db.Column(db.String(24), default="member")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SessionComment(db.Model):
    __tablename__ = "session_comments"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, index=True, nullable=False)
    user_id = db.Column(db.String(64), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def to_dict(self):
        return {"id": self.id, "session_id": self.session_id, "user_id": self.user_id, "text": self.text, "timestamp_ms": self.timestamp_ms, "created_at": self.created_at.isoformat()}

class FeatureFlag(db.Model):
    __tablename__ = "feature_flags"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    enabled = db.Column(db.Boolean, default=False, nullable=False)
    note = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self): return {"key": self.key, "enabled": self.enabled, "note": self.note, "updated_at": self.updated_at.isoformat()}

class IntegrationToken(db.Model):
    __tablename__ = "integration_tokens"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True, nullable=False)
    provider = db.Column(db.String(24), index=True, nullable=False)  # "slack" or "notion"
    access_token = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    __tablename__ = "customers"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    stripe_customer_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Subscription(db.Model):
    __tablename__ = "subscriptions"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    stripe_subscription_id = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(32), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)