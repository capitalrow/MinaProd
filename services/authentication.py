#!/usr/bin/env python3
# 🔐 Production Feature: Authentication and Authorization Framework
"""
Implements comprehensive authentication and authorization system
for enterprise-grade security and user management.

Addresses: "Authentication & Authorization" gap from production assessment.

Key Features:
- Secure user registration and login
- JWT token-based authentication
- Role-based access control (RBAC)
- Session management with security
- Password hashing with bcrypt
- OAuth 2.0 integration preparation
"""

import logging
import time
import secrets
import bcrypt
import jwt
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from flask import Flask, request, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import redis

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"

class Permission(Enum):
    """System permissions."""
    # Session management
    CREATE_SESSION = "create_session"
    JOIN_SESSION = "join_session"
    MANAGE_SESSION = "manage_session"
    DELETE_SESSION = "delete_session"
    
    # Transcription
    START_TRANSCRIPTION = "start_transcription"
    VIEW_TRANSCRIPTS = "view_transcripts"
    EXPORT_TRANSCRIPTS = "export_transcripts"
    DELETE_TRANSCRIPTS = "delete_transcripts"
    
    # Administration
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    SYSTEM_CONFIG = "system_config"
    
    # Data management
    DATA_EXPORT = "data_export"
    DATA_DELETE = "data_delete"

@dataclass
class UserProfile:
    """User profile information."""
    user_id: str
    email: str
    name: str
    role: UserRole
    permissions: List[Permission] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has specific role."""
        return self.role == role

@dataclass
class AuthConfig:
    """Authentication configuration."""
    # JWT settings
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expires_hours: int = 24
    refresh_token_expires_days: int = 30
    
    # Password requirements
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = False
    
    # Session security
    session_timeout_hours: int = 12
    max_concurrent_sessions: int = 3
    
    # Rate limiting
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    
    def __post_init__(self):
        if not self.jwt_secret_key:
            self.jwt_secret_key = secrets.token_urlsafe(32)

class User(UserMixin):
    """Flask-Login User class."""
    
    def __init__(self, user_profile: UserProfile):
        self.profile = user_profile
        self.id = user_profile.user_id
        self.email = user_profile.email
        self.name = user_profile.name
        self.role = user_profile.role
        self.is_active = user_profile.is_active
    
    def get_id(self):
        return self.profile.user_id
    
    def has_permission(self, permission: Permission) -> bool:
        return self.profile.has_permission(permission)
    
    def has_role(self, role: UserRole) -> bool:
        return self.profile.has_role(role)

class AuthenticationManager:
    """
    🔐 Production-grade authentication and authorization manager.
    
    Handles user registration, login, JWT tokens, RBAC, and session security
    with enterprise-grade security features.
    """
    
    def __init__(self, app: Flask, redis_client: redis.Redis, config: Optional[AuthConfig] = None):
        self.app = app
        self.redis_client = redis_client
        self.config = config or AuthConfig()
        
        # Flask-Login setup
        self.login_manager = LoginManager()
        self.login_manager.init_app(app)
        self.login_manager.user_loader(self._load_user)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = 'Please log in to access this page.'
        
        # Role-based permissions mapping
        self.role_permissions = self._initialize_role_permissions()
        
        # User storage (in production, use proper database)
        self.users: Dict[str, UserProfile] = {}
        
        # Security tracking
        self.login_attempts: Dict[str, List[float]] = {}
        self.active_sessions: Dict[str, List[str]] = {}  # {user_id: [session_ids]}
        
        # Metrics
        self.total_registrations = 0
        self.total_logins = 0
        self.failed_logins = 0
        self.locked_accounts = 0
        
        logger.info("🔐 Authentication manager initialized with RBAC and JWT")
    
    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize role-based permissions mapping."""
        return {
            UserRole.ADMIN: list(Permission),  # Admin has all permissions
            UserRole.MODERATOR: [
                Permission.CREATE_SESSION,
                Permission.JOIN_SESSION,
                Permission.MANAGE_SESSION,
                Permission.START_TRANSCRIPTION,
                Permission.VIEW_TRANSCRIPTS,
                Permission.EXPORT_TRANSCRIPTS,
                Permission.VIEW_ANALYTICS
            ],
            UserRole.USER: [
                Permission.CREATE_SESSION,
                Permission.JOIN_SESSION,
                Permission.START_TRANSCRIPTION,
                Permission.VIEW_TRANSCRIPTS,
                Permission.EXPORT_TRANSCRIPTS
            ],
            UserRole.GUEST: [
                Permission.JOIN_SESSION,
                Permission.VIEW_TRANSCRIPTS
            ]
        }
    
    def _load_user(self, user_id: str) -> Optional[User]:
        """Flask-Login user loader."""
        try:
            # Try to load from Redis cache first
            user_key = f"user:{user_id}"
            user_data = self.redis_client.get(user_key)
            
            if user_data:
                import json
                profile_data = json.loads(user_data)
                profile = UserProfile(
                    user_id=profile_data['user_id'],
                    email=profile_data['email'],
                    name=profile_data['name'],
                    role=UserRole(profile_data['role']),
                    permissions=[Permission(p) for p in profile_data['permissions']],
                    created_at=profile_data['created_at'],
                    last_login=profile_data.get('last_login'),
                    is_active=profile_data['is_active'],
                    metadata=profile_data.get('metadata', {})
                )
                return User(profile)
            
            # Fall back to in-memory storage
            if user_id in self.users:
                return User(self.users[user_id])
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading user {user_id}: {e}")
            return None
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength against requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if len(password) < self.config.min_password_length:
            issues.append(f"Password must be at least {self.config.min_password_length} characters")
        
        if self.config.require_uppercase and not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if self.config.require_lowercase and not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if self.config.require_numbers and not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if self.config.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        return len(issues) == 0, issues
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def register_user(self, email: str, password: str, name: str, 
                     role: UserRole = UserRole.USER) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: User password
            name: User display name
            role: User role (default: USER)
            
        Returns:
            Registration result
        """
        try:
            # Validate input
            if not email or not password or not name:
                return {
                    'success': False,
                    'error': 'missing_required_fields',
                    'message': 'Email, password, and name are required'
                }
            
            # Check if user already exists
            existing_user = self._find_user_by_email(email)
            if existing_user:
                return {
                    'success': False,
                    'error': 'user_exists',
                    'message': 'User with this email already exists'
                }
            
            # Validate password strength
            password_valid, password_issues = self.validate_password_strength(password)
            if not password_valid:
                return {
                    'success': False,
                    'error': 'weak_password',
                    'message': 'Password does not meet requirements',
                    'issues': password_issues
                }
            
            # Create user profile
            user_id = f"user_{int(time.time() * 1000)}_{secrets.token_hex(4)}"
            password_hash = self.hash_password(password)
            
            # Get role permissions
            permissions = self.role_permissions.get(role, [])
            
            profile = UserProfile(
                user_id=user_id,
                email=email.lower(),
                name=name,
                role=role,
                permissions=permissions,
                metadata={'password_hash': password_hash}
            )
            
            # Store user
            self.users[user_id] = profile
            self._cache_user(profile)
            
            self.total_registrations += 1
            
            logger.info(f"User registered: {email} ({role.value})")
            
            return {
                'success': True,
                'user_id': user_id,
                'email': email,
                'name': name,
                'role': role.value,
                'message': 'User registered successfully'
            }
            
        except Exception as e:
            logger.error(f"User registration failed: {e}")
            return {
                'success': False,
                'error': 'registration_failed',
                'message': str(e)
            }
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Authentication result with tokens if successful
        """
        try:
            # Check rate limiting
            if self._is_rate_limited(email):
                return {
                    'success': False,
                    'error': 'rate_limited',
                    'message': f'Too many failed attempts. Try again in {self.config.lockout_duration_minutes} minutes.'
                }
            
            # Find user
            user = self._find_user_by_email(email)
            if not user:
                self._record_failed_login(email)
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid email or password'
                }
            
            # Check if account is active
            if not user.is_active:
                return {
                    'success': False,
                    'error': 'account_disabled',
                    'message': 'Account is disabled'
                }
            
            # Verify password
            password_hash = user.metadata.get('password_hash', '')
            if not self.verify_password(password, password_hash):
                self._record_failed_login(email)
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid email or password'
                }
            
            # Generate tokens
            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)
            
            # Update user login info
            user.last_login = time.time()
            self._cache_user(user)
            
            # Manage session
            session_id = self._create_session(user.user_id)
            
            # Clear failed login attempts
            self.login_attempts.pop(email, None)
            
            self.total_logins += 1
            
            logger.info(f"User authenticated: {email}")
            
            return {
                'success': True,
                'user_id': user.user_id,
                'email': user.email,
                'name': user.name,
                'role': user.role.value,
                'permissions': [p.value for p in user.permissions],
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id,
                'expires_at': time.time() + (self.config.access_token_expires_hours * 3600)
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return {
                'success': False,
                'error': 'authentication_failed',
                'message': str(e)
            }
    
    def _find_user_by_email(self, email: str) -> Optional[UserProfile]:
        """Find user by email address."""
        email_lower = email.lower()
        for user in self.users.values():
            if user.email == email_lower:
                return user
        return None
    
    def _is_rate_limited(self, email: str) -> bool:
        """Check if email is rate limited due to failed login attempts."""
        current_time = time.time()
        cutoff_time = current_time - (self.config.lockout_duration_minutes * 60)
        
        if email in self.login_attempts:
            # Remove old attempts
            self.login_attempts[email] = [
                attempt for attempt in self.login_attempts[email]
                if attempt > cutoff_time
            ]
            
            # Check if over limit
            return len(self.login_attempts[email]) >= self.config.max_login_attempts
        
        return False
    
    def _record_failed_login(self, email: str):
        """Record a failed login attempt."""
        current_time = time.time()
        
        if email not in self.login_attempts:
            self.login_attempts[email] = []
        
        self.login_attempts[email].append(current_time)
        self.failed_logins += 1
        
        # Check if account should be locked
        cutoff_time = current_time - (self.config.lockout_duration_minutes * 60)
        recent_attempts = [
            attempt for attempt in self.login_attempts[email]
            if attempt > cutoff_time
        ]
        
        if len(recent_attempts) >= self.config.max_login_attempts:
            self.locked_accounts += 1
            logger.warning(f"Account locked due to failed attempts: {email}")
    
    def _generate_access_token(self, user: UserProfile) -> str:
        """Generate JWT access token."""
        payload = {
            'user_id': user.user_id,
            'email': user.email,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'exp': datetime.utcnow() + timedelta(hours=self.config.access_token_expires_hours),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def _generate_refresh_token(self, user: UserProfile) -> str:
        """Generate JWT refresh token."""
        payload = {
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(days=self.config.refresh_token_expires_days),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token, 
                self.config.jwt_secret_key, 
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Invalid token")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token or error
        """
        try:
            payload = self.verify_token(refresh_token)
            if not payload or payload.get('type') != 'refresh':
                return {
                    'success': False,
                    'error': 'invalid_refresh_token',
                    'message': 'Invalid refresh token'
                }
            
            user_id = payload.get('user_id')
            user = self.users.get(user_id)
            
            if not user or not user.is_active:
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': 'User not found or inactive'
                }
            
            # Generate new access token
            new_access_token = self._generate_access_token(user)
            
            return {
                'success': True,
                'access_token': new_access_token,
                'expires_at': time.time() + (self.config.access_token_expires_hours * 3600)
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return {
                'success': False,
                'error': 'refresh_failed',
                'message': str(e)
            }
    
    def _create_session(self, user_id: str) -> str:
        """Create new user session."""
        session_id = f"sess_{int(time.time() * 1000)}_{secrets.token_hex(8)}"
        
        # Track active sessions
        if user_id not in self.active_sessions:
            self.active_sessions[user_id] = []
        
        self.active_sessions[user_id].append(session_id)
        
        # Enforce concurrent session limit
        if len(self.active_sessions[user_id]) > self.config.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = self.active_sessions[user_id].pop(0)
            logger.info(f"Removed oldest session {oldest_session} for user {user_id}")
        
        # Store session in Redis
        session_key = f"auth_session:{session_id}"
        session_data = {
            'user_id': user_id,
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        self.redis_client.setex(
            session_key,
            self.config.session_timeout_hours * 3600,
            json.dumps(session_data)
        )
        
        return session_id
    
    def _cache_user(self, user: UserProfile):
        """Cache user in Redis."""
        import json
        user_key = f"user:{user.user_id}"
        user_data = {
            'user_id': user.user_id,
            'email': user.email,
            'name': user.name,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'created_at': user.created_at,
            'last_login': user.last_login,
            'is_active': user.is_active,
            'metadata': user.metadata
        }
        
        self.redis_client.setex(user_key, 3600, json.dumps(user_data))  # 1 hour cache
    
    def require_permission(self, permission: Permission):
        """Decorator to require specific permission."""
        def decorator(f):
            def wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return {'error': 'authentication_required'}, 401
                
                if not current_user.has_permission(permission):
                    return {'error': 'permission_denied', 'required_permission': permission.value}, 403
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, role: UserRole):
        """Decorator to require specific role."""
        def decorator(f):
            def wrapper(*args, **kwargs):
                if not current_user.is_authenticated:
                    return {'error': 'authentication_required'}, 401
                
                if not current_user.has_role(role):
                    return {'error': 'role_required', 'required_role': role.value}, 403
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        return {
            'total_users': len(self.users),
            'active_users': sum(1 for user in self.users.values() if user.is_active),
            'total_registrations': self.total_registrations,
            'total_logins': self.total_logins,
            'failed_logins': self.failed_logins,
            'locked_accounts': self.locked_accounts,
            'active_sessions': sum(len(sessions) for sessions in self.active_sessions.values()),
            'users_by_role': {
                role.value: sum(1 for user in self.users.values() if user.role == role)
                for role in UserRole
            }
        }

# Global authentication manager
_auth_manager: Optional[AuthenticationManager] = None

def get_auth_manager() -> Optional[AuthenticationManager]:
    """Get the global authentication manager."""
    return _auth_manager

def initialize_auth_manager(app: Flask, redis_client: redis.Redis, 
                           config: Optional[AuthConfig] = None) -> AuthenticationManager:
    """Initialize the global authentication manager."""
    global _auth_manager
    _auth_manager = AuthenticationManager(app, redis_client, config)
    return _auth_manager