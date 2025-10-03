"""
Share Analytics Model for Mina - Phase 2 Group 4 (T2.25)
Track views, visitors, and engagement on shared sessions.
"""

from datetime import datetime
from models import db


class ShareAnalytic(db.Model):
    """Analytics tracking for shared sessions."""
    
    __tablename__ = 'share_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    shared_link_id = db.Column(db.Integer, db.ForeignKey('shared_links.id'), nullable=False)
    visitor_ip = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    visitor_user_agent = db.Column(db.String(500), nullable=True)
    visitor_country = db.Column(db.String(100), nullable=True)
    referrer = db.Column(db.String(500), nullable=True)
    viewed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_spent_seconds = db.Column(db.Integer, nullable=True)  # How long they stayed
    
    # Relationships
    shared_link = db.relationship('SharedLink', backref='analytics')
    
    def __repr__(self):
        return f'<ShareAnalytic link={self.shared_link_id} viewed={self.viewed_at}>'
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'shared_link_id': self.shared_link_id,
            'visitor_ip': self.visitor_ip,
            'visitor_country': self.visitor_country,
            'referrer': self.referrer,
            'viewed_at': self.viewed_at.isoformat(),
            'time_spent_seconds': self.time_spent_seconds
        }
