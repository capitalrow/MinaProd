"""
Session Security Middleware

Implements comprehensive session hardening following OWASP guidelines:
- Session timeout (idle and absolute)
- Session rotation after login
- Session fixation prevention
- Secure cookie configuration
- Session invalidation

Phase 0 - Task 0.21: Secure Session Management
"""

from flask import session, request, g
from datetime import datetime, timedelta
from functools import wraps
import secrets


# Session configuration constants
SESSION_IDLE_TIMEOUT = 30 * 60  # 30 minutes of inactivity
SESSION_ABSOLUTE_TIMEOUT = 8 * 60 * 60  # 8 hours maximum session lifetime
SESSION_REFRESH_THRESHOLD = 5 * 60  # Refresh if less than 5 minutes remain


def configure_session_security(app):
    """
    Configure Flask session security settings.
    
    This function should be called during app initialization to set
    secure session cookie parameters and enable session protection.
    """
    # Session cookie configuration
    app.config.update(
        # Cookie security
        SESSION_COOKIE_SECURE=app.config.get('ENV') == 'production',  # HTTPS only in production
        SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access
        SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection (Lax allows GET from external sites)
        
        # Session lifetime
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),  # 8 hour absolute timeout
        
        # Session protection
        SESSION_PROTECTION='strong',  # Flask-Login session protection mode
    )
    
    app.logger.info("✅ Session security configured: HTTPONLY, SAMESITE=Lax, 8h lifetime")


def session_security_middleware(app):
    """
    Apply session security middleware to Flask app.
    
    Implements:
    - Idle timeout tracking
    - Absolute timeout enforcement
    - Session rotation on privilege escalation
    - Activity timestamp updates
    """
    
    @app.before_request
    def check_session_timeout():
        """
        Check session timeout and enforce both idle and absolute timeouts.
        
        Two types of timeout:
        1. Idle Timeout: Session expires after X minutes of inactivity
        2. Absolute Timeout: Session expires after X hours regardless of activity
        """
        # Skip for non-authenticated sessions
        if not session.get('_user_id'):
            return None
        
        now = datetime.utcnow()
        
        # Check absolute timeout (session created time)
        session_start = session.get('_session_start')
        if session_start:
            session_start_dt = datetime.fromisoformat(session_start)
            session_age = (now - session_start_dt).total_seconds()
            
            if session_age > SESSION_ABSOLUTE_TIMEOUT:
                app.logger.warning(
                    f"Session expired (absolute timeout): "
                    f"user_id={session.get('_user_id')}, "
                    f"age={session_age}s"
                )
                session.clear()
                g.session_expired = True
                g.session_expire_reason = 'absolute_timeout'
                return None
        
        # Check idle timeout (last activity time)
        last_activity = session.get('_last_activity')
        if last_activity:
            last_activity_dt = datetime.fromisoformat(last_activity)
            idle_time = (now - last_activity_dt).total_seconds()
            
            if idle_time > SESSION_IDLE_TIMEOUT:
                app.logger.warning(
                    f"Session expired (idle timeout): "
                    f"user_id={session.get('_user_id')}, "
                    f"idle={idle_time}s"
                )
                session.clear()
                g.session_expired = True
                g.session_expire_reason = 'idle_timeout'
                return None
        
        # Update last activity timestamp
        session['_last_activity'] = now.isoformat()
        session.modified = True
    
    @app.before_request
    def track_session_metadata():
        """Track session creation time and client fingerprint for fixation prevention."""
        if session.get('_user_id') and not session.get('_session_start'):
            session['_session_start'] = datetime.utcnow().isoformat()
            session['_session_id'] = secrets.token_urlsafe(32)
            
            # Store client fingerprint for session fixation detection
            # (basic fingerprint, could be enhanced with User-Agent hash, etc.)
            session['_client_ip'] = request.remote_addr
    
    app.logger.info("✅ Session security middleware enabled: idle=30m, absolute=8h")


def rotate_session():
    """
    Rotate the session identifier.
    
    Call this after login or privilege escalation to prevent session fixation.
    Preserves session data while changing the session ID.
    
    Usage:
        from middleware.session_security import rotate_session
        
        @auth_bp.route('/login', methods=['POST'])
        def login():
            # ... authenticate user ...
            login_user(user)
            rotate_session()  # Prevent session fixation
            return redirect(url_for('dashboard.index'))
    """
    # Store current session data
    session_data = dict(session)
    
    # Clear the session (changes session ID)
    session.clear()
    
    # Restore session data
    for key, value in session_data.items():
        session[key] = value
    
    # Mark as new session
    session['_session_start'] = datetime.utcnow().isoformat()
    session['_session_id'] = secrets.token_urlsafe(32)
    session['_last_activity'] = datetime.utcnow().isoformat()
    session.modified = True


def session_required(f):
    """
    Decorator to ensure a valid session exists before accessing a route.
    
    Checks for session expiration and redirects to login if expired.
    
    Usage:
        @app.route('/dashboard')
        @login_required  # Flask-Login
        @session_required  # Session timeout check
        def dashboard():
            return render_template('dashboard.html')
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if session was expired by middleware
        if hasattr(g, 'session_expired') and g.session_expired:
            from flask import flash, redirect, url_for
            
            reason = getattr(g, 'session_expire_reason', 'timeout')
            if reason == 'idle_timeout':
                flash('Your session expired due to inactivity. Please log in again.', 'warning')
            elif reason == 'absolute_timeout':
                flash('Your session expired. Please log in again.', 'warning')
            else:
                flash('Your session is no longer valid. Please log in again.', 'warning')
            
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_session_info():
    """
    Get information about the current session for debugging/monitoring.
    
    Returns dict with session metadata (does not expose sensitive data).
    """
    if not session.get('_user_id'):
        return None
    
    now = datetime.utcnow()
    
    session_start = session.get('_session_start')
    last_activity = session.get('_last_activity')
    
    info = {
        'user_id': session.get('_user_id'),
        'session_id': session.get('_session_id', 'unknown')[:16] + '...',  # Truncated for security
        'authenticated': True,
    }
    
    if session_start:
        session_start_dt = datetime.fromisoformat(session_start)
        info['session_age_seconds'] = int((now - session_start_dt).total_seconds())
        info['session_age_hours'] = round(info['session_age_seconds'] / 3600, 2)
    
    if last_activity:
        last_activity_dt = datetime.fromisoformat(last_activity)
        info['idle_seconds'] = int((now - last_activity_dt).total_seconds())
        info['idle_minutes'] = round(info['idle_seconds'] / 60, 1)
    
    # Time remaining
    if session_start:
        absolute_remaining = SESSION_ABSOLUTE_TIMEOUT - info['session_age_seconds']
        info['absolute_timeout_remaining_seconds'] = max(0, absolute_remaining)
        info['absolute_timeout_remaining_minutes'] = round(absolute_remaining / 60, 1)
    
    if last_activity:
        idle_remaining = SESSION_IDLE_TIMEOUT - info['idle_seconds']
        info['idle_timeout_remaining_seconds'] = max(0, idle_remaining)
        info['idle_timeout_remaining_minutes'] = round(idle_remaining / 60, 1)
    
    return info


def invalidate_session():
    """
    Completely invalidate the current session.
    
    Use this for logout or when session should be terminated
    (e.g., password change, permission revocation).
    """
    user_id = session.get('_user_id')
    session.clear()
    
    if user_id:
        from flask import current_app
        current_app.logger.info(f"Session invalidated for user_id={user_id}")
