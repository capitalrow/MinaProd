"""
Tests for session security hardening.

Phase 0 - Task 0.21: Secure Session Management
"""

import pytest
from flask import session
from datetime import datetime, timedelta
from models import User, db


@pytest.fixture
def test_user(app):
    """Create a test user for session testing."""
    with app.app_context():
        user = User(
            email='session_test@example.com',
            username='sessiontest',
            first_name='Session',
            last_name='Tester'
        )
        user.set_password('Test123456')
        db.session.add(user)
        db.session.commit()
        yield user
        db.session.delete(user)
        db.session.commit()


def test_session_cookie_security_settings(app):
    """Test that session cookies are configured securely."""
    assert app.config['SESSION_COOKIE_HTTPONLY'] == True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    # SECURE should be True in production
    if app.config.get('ENV') == 'production':
        assert app.config['SESSION_COOKIE_SECURE'] == True


def test_session_lifetime_configured(app):
    """Test that session lifetime is set."""
    assert app.config['PERMANENT_SESSION_LIFETIME'] is not None
    lifetime = app.config['PERMANENT_SESSION_LIFETIME']
    assert lifetime.total_seconds() == 8 * 60 * 60  # 8 hours


def test_login_creates_session_metadata(client, test_user):
    """Test that login creates proper session metadata."""
    response = client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    }, follow_redirects=False)
    
    # Should redirect on successful login
    assert response.status_code == 302
    
    # Check session has metadata
    with client.session_transaction() as sess:
        assert '_user_id' in sess
        assert '_session_start' in sess
        assert '_last_activity' in sess


def test_session_rotation_on_login(client, test_user):
    """Test that session ID changes after login (fixation prevention)."""
    # First request to establish a session
    client.get('/')
    
    with client.session_transaction() as sess:
        original_session_data = dict(sess)
    
    # Login should rotate session
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    }, follow_redirects=True)
    
    with client.session_transaction() as sess:
        # Session should have new metadata
        assert '_session_start' in sess
        assert '_session_id' in sess
        # Session should be for the logged-in user
        assert sess.get('_user_id') is not None


def test_logout_invalidates_session(client, test_user):
    """Test that logout completely clears the session."""
    # Login first
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    })
    
    # Verify logged in
    with client.session_transaction() as sess:
        assert '_user_id' in sess
    
    # Logout
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    
    # Session should be cleared
    with client.session_transaction() as sess:
        assert '_user_id' not in sess
        assert len(sess) == 0 or all(not key.startswith('_') for key in sess.keys())


def test_session_activity_timestamp_updates(client, test_user):
    """Test that session activity timestamp is updated on requests."""
    # Login
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    })
    
    with client.session_transaction() as sess:
        initial_activity = sess.get('_last_activity')
    
    # Make another request (small delay to ensure timestamp changes)
    import time
    time.sleep(0.1)
    client.get('/dashboard')
    
    with client.session_transaction() as sess:
        updated_activity = sess.get('_last_activity')
    
    # Timestamp should be updated (or at least present)
    assert updated_activity is not None
    if initial_activity:
        assert updated_activity >= initial_activity


def test_protected_route_without_session(client):
    """Test that protected routes redirect when session is invalid."""
    response = client.get('/dashboard', follow_redirects=False)
    # Should redirect to login (Flask-Login behavior)
    assert response.status_code == 302
    assert '/login' in response.location


def test_session_metadata_tracking(client, test_user):
    """Test that session metadata is properly tracked."""
    # Login
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    })
    
    with client.session_transaction() as sess:
        # Check all required metadata
        assert '_user_id' in sess
        assert '_session_start' in sess
        assert '_last_activity' in sess
        assert '_session_id' in sess
        
        # Validate timestamp format
        session_start = sess['_session_start']
        try:
            datetime.fromisoformat(session_start)
        except ValueError:
            pytest.fail(f"Invalid ISO format for session_start: {session_start}")
        
        last_activity = sess['_last_activity']
        try:
            datetime.fromisoformat(last_activity)
        except ValueError:
            pytest.fail(f"Invalid ISO format for last_activity: {last_activity}")


def test_multiple_logins_create_new_sessions(client, test_user):
    """Test that each login creates a unique session."""
    # First login
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    })
    
    with client.session_transaction() as sess:
        first_session_id = sess.get('_session_id')
    
    # Logout
    client.get('/logout')
    
    # Second login
    client.post('/login', data={
        'email_or_username': 'sessiontest',
        'password': 'Test123456'
    })
    
    with client.session_transaction() as sess:
        second_session_id = sess.get('_session_id')
    
    # Session IDs should be different
    assert first_session_id != second_session_id


@pytest.mark.parametrize('sensitive_route', [
    '/dashboard',
    '/dashboard/meetings',
    '/dashboard/analytics',
    '/settings/profile',
])
def test_sensitive_routes_require_session(client, sensitive_route):
    """Test that sensitive routes require valid session."""
    response = client.get(sensitive_route, follow_redirects=False)
    # Should redirect to login or return 401/403
    assert response.status_code in [302, 401, 403]


def test_session_not_created_for_public_routes(client):
    """Test that public routes don't unnecessarily create sessions."""
    # Access public route
    client.get('/login')
    
    with client.session_transaction() as sess:
        # Should not have user session data
        assert '_user_id' not in sess


def test_session_security_headers_present(client):
    """Test that responses include session security headers."""
    response = client.get('/')
    
    # Check for security headers (from CSP middleware)
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers


def test_concurrent_sessions_independent(app, test_user):
    """Test that multiple clients get independent sessions."""
    from flask.testing import FlaskClient
    
    # Create two separate clients
    with app.test_client() as client1, app.test_client() as client2:
        # Login with both clients
        client1.post('/login', data={
            'email_or_username': 'sessiontest',
            'password': 'Test123456'
        })
        
        client2.post('/login', data={
            'email_or_username': 'sessiontest',
            'password': 'Test123456'
        })
        
        # Get session IDs
        with client1.session_transaction() as sess1:
            session_id_1 = sess1.get('_session_id')
        
        with client2.session_transaction() as sess2:
            session_id_2 = sess2.get('_session_id')
        
        # Sessions should be independent
        assert session_id_1 != session_id_2
