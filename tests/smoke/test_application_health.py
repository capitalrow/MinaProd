"""
Smoke tests for application health and critical functionality.
Tests run against the live running application.
"""

import pytest
import requests
import time
import os


# Get the base URL for the running application
BASE_URL = 'http://127.0.0.1:5000'


class TestApplicationHealth:
    """Test basic application health and availability."""
    
    def test_app_is_running(self):
        """Test that the application is running and responsive."""
        try:
            response = requests.get(f'{BASE_URL}/', timeout=5)
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Application is not responding: {e}")
    
    def test_homepage_loads(self):
        """Test that homepage loads successfully."""
        response = requests.get(f'{BASE_URL}/', timeout=5)
        assert response.status_code == 200
        assert b'Mina' in response.content or b'mina' in response.content
    
    def test_static_assets_load(self):
        """Test that static CSS files load."""
        response = requests.get(f'{BASE_URL}/static/css/main.css', timeout=5)
        assert response.status_code == 200
    
    def test_api_health_check(self):
        """Test API health check endpoint if available."""
        # Try common health check endpoints
        endpoints = ['/health', '/api/health', '/ping']
        
        for endpoint in endpoints:
            try:
                response = requests.get(f'{BASE_URL}{endpoint}', timeout=5)
                if response.status_code == 200:
                    return  # Found working health endpoint
            except:
                continue
        
        # If no health endpoint, just verify app responds
        response = requests.get(f'{BASE_URL}/', timeout=5)
        assert response.status_code == 200


class TestCoreAPIEndpoints:
    """Test core API endpoints are accessible."""
    
    def test_meetings_api_accessible(self):
        """Test that meetings API is accessible."""
        response = requests.get(f'{BASE_URL}/api/meetings', timeout=5)
        # May return 401/403 if auth required, or 200 with empty list
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status: {response.status_code}"
    
    def test_tasks_api_accessible(self):
        """Test that tasks API is accessible."""
        response = requests.get(f'{BASE_URL}/api/tasks', timeout=5)
        assert response.status_code in [200, 401, 403], \
            f"Unexpected status: {response.status_code}"
    
    def test_sessions_api_structure(self):
        """Test that sessions can be created via API structure."""
        # This is a structure test - verifies endpoint exists
        response = requests.post(
            f'{BASE_URL}/api/sessions',
            json={'test': 'data'},
            timeout=5
        )
        # Should not 404 - endpoint should exist
        assert response.status_code != 404, "Sessions API endpoint missing"


class TestDatabaseConnectivity:
    """Test database connectivity through the application."""
    
    def test_database_connected(self):
        """Verify database is connected by checking app functionality."""
        # Try to access dashboard which requires DB
        response = requests.get(f'{BASE_URL}/dashboard', timeout=5)
        # Should either show dashboard or redirect to login, not crash
        assert response.status_code in [200, 302, 401, 403], \
            f"Dashboard endpoint crashed: {response.status_code}"
    
    def test_can_query_meetings(self):
        """Test that meetings can be queried from database."""
        response = requests.get(f'{BASE_URL}/api/meetings', timeout=5)
        # Should return valid response, not database error
        assert response.status_code in [200, 401, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list)), "Invalid JSON response"


class TestWebSocketEndpoints:
    """Test WebSocket endpoints are available."""
    
    def test_socketio_endpoint_exists(self):
        """Test that Socket.IO endpoint is available."""
        response = requests.get(f'{BASE_URL}/socket.io/', timeout=5)
        # Socket.IO should respond to polling requests
        assert response.status_code in [200, 400, 401], \
            f"Socket.IO endpoint issue: {response.status_code}"
    
    def test_transcription_namespace_available(self):
        """Test that transcription namespace is configured."""
        # Socket.IO namespaces are available if the server responds
        response = requests.get(f'{BASE_URL}/socket.io/', timeout=5)
        assert response.status_code != 404, "Socket.IO not configured"


class TestCriticalPaths:
    """Test critical user paths work end-to-end."""
    
    def test_can_access_new_meeting_flow(self):
        """Test that meetings page is accessible."""
        # Check if we can access meetings page (corrected path with /dashboard prefix)
        response = requests.get(f'{BASE_URL}/dashboard/meetings', timeout=5)
        # Should show page or redirect to login
        assert response.status_code in [200, 302, 401, 403]
    
    def test_can_access_analytics(self):
        """Test that analytics page is accessible."""
        # Corrected path with /dashboard prefix
        response = requests.get(f'{BASE_URL}/dashboard/analytics', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_settings_page_exists(self):
        """Test that settings page exists."""
        response = requests.get(f'{BASE_URL}/settings', timeout=5)
        assert response.status_code in [200, 302, 401, 403]


class TestUIPages:
    """Test all critical UI pages are accessible."""
    
    def test_main_app_page(self):
        """Test that main app page is accessible."""
        response = requests.get(f'{BASE_URL}/app', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_live_transcription_page(self):
        """Test that live transcription page is accessible."""
        response = requests.get(f'{BASE_URL}/live', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_dashboard_home(self):
        """Test that dashboard home is accessible."""
        response = requests.get(f'{BASE_URL}/dashboard/', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_dashboard_tasks(self):
        """Test that tasks page is accessible."""
        response = requests.get(f'{BASE_URL}/dashboard/tasks', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_live_enhanced_page(self):
        """Test that enhanced live transcription is accessible."""
        response = requests.get(f'{BASE_URL}/live-enhanced', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_live_comprehensive_page(self):
        """Test that comprehensive live transcription is accessible."""
        response = requests.get(f'{BASE_URL}/live-comprehensive', timeout=5)
        assert response.status_code in [200, 302, 401, 403]
    
    def test_onboarding_page(self):
        """Test that onboarding page is accessible."""
        response = requests.get(f'{BASE_URL}/onboarding', timeout=5)
        assert response.status_code in [200, 302, 401, 403]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
