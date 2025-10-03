"""
Team Share Model for Mina - Phase 2 Group 4 (T2.24)
Role-based permissions for sharing sessions with team members.
"""

from datetime import datetime
from models import db


class TeamShare(db.Model):
    """Team sharing with role-based permissions."""
    
    __tablename__ = 'team_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    shared_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')  # viewer, editor, admin
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = db.relationship('Session', backref='team_shares', foreign_keys=[session_id])
    user = db.relationship('User', backref='received_shares', foreign_keys=[user_id])
    shared_by = db.relationship('User', backref='given_shares', foreign_keys=[shared_by_id])
    
    # Role permissions
    ROLES = {
        'viewer': {'can_view': True, 'can_edit': False, 'can_share': False, 'can_delete': False},
        'editor': {'can_view': True, 'can_edit': True, 'can_share': False, 'can_delete': False},
        'admin': {'can_view': True, 'can_edit': True, 'can_share': True, 'can_delete': True}
    }
    
    def __repr__(self):
        return f'<TeamShare session={self.session_id} user={self.user_id} role={self.role}>'
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission."""
        role_perms = self.ROLES.get(self.role, {})
        return role_perms.get(permission, False)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else None,
            'user_name': self.user.username if self.user else None,
            'shared_by_id': self.shared_by_id,
            'shared_by_name': self.shared_by.username if self.shared_by else None,
            'role': self.role,
            'permissions': self.ROLES.get(self.role, {}),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
