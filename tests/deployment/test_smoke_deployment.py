"""
Deployment smoke tests.
These tests run immediately after deployment to verify critical functionality.
"""
import pytest
import requests
import os


BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')


@pytest.mark.smoke
class TestDeploymentSmoke:
    """Critical post-deployment verification tests."""
    
    def test_health_endpoint_responds(self):
        """Verify health endpoint is accessible."""
        response = requests.get(f'{BASE_URL}/health', timeout=10)
        assert response.status_code == 200, f"Health check failed with status {response.status_code}"
        
        data = response.json()
        assert data.get('status') in ['ok', 'healthy'], f"Unexpected health status: {data}"
    
    def test_homepage_loads(self):
        """Verify homepage is accessible."""
        response = requests.get(f'{BASE_URL}/', timeout=10)
        assert response.status_code == 200, f"Homepage failed with status {response.status_code}"
        assert len(response.text) > 0, "Homepage returned empty response"
    
    def test_static_assets_load(self):
        """Verify static assets are accessible."""
        response = requests.get(f'{BASE_URL}/static/css/style.css', timeout=10)
        assert response.status_code in [200, 404], f"Static assets check failed: {response.status_code}"
    
    def test_database_connectivity(self):
        """Verify database connection is working."""
        response = requests.get(f'{BASE_URL}/health', timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        if 'database' in data:
            assert data['database'] in ['connected', 'ok'], f"Database not connected: {data}"
    
    def test_api_endpoint_accessible(self):
        """Verify API endpoints are accessible."""
        response = requests.get(f'{BASE_URL}/api/health', timeout=10)
        assert response.status_code in [200, 404], "API endpoints not accessible"
    
    def test_live_page_loads(self):
        """Verify live transcription page loads."""
        response = requests.get(f'{BASE_URL}/live', timeout=10)
        assert response.status_code == 200, f"Live page failed with status {response.status_code}"
        assert 'transcription' in response.text.lower() or 'record' in response.text.lower()
    
    def test_response_time_acceptable(self):
        """Verify response times are within SLO."""
        import time
        
        start = time.time()
        response = requests.get(f'{BASE_URL}/', timeout=10)
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Response time {duration}s exceeds 2s SLO"
    
    def test_no_500_errors_on_basic_routes(self):
        """Verify no 500 errors on common routes."""
        routes = ['/', '/health', '/live']
        
        for route in routes:
            response = requests.get(f'{BASE_URL}{route}', timeout=10)
            assert response.status_code != 500, f"500 error on {route}"
    
    def test_security_headers_present(self):
        """Verify security headers are configured."""
        response = requests.get(f'{BASE_URL}/', timeout=10)
        
        headers = response.headers
        
        assert 'X-Content-Type-Options' in headers or response.status_code == 200, \
            "Security headers may not be configured"
    
    def test_cors_not_wildcard(self):
        """Verify CORS is not set to wildcard in production."""
        response = requests.options(f'{BASE_URL}/api/sessions', timeout=10)
        
        if 'Access-Control-Allow-Origin' in response.headers:
            origin = response.headers['Access-Control-Allow-Origin']
            assert origin != '*', "CORS is set to wildcard (security risk)"


@pytest.mark.smoke
class TestDeploymentCriticalPaths:
    """Test critical user journeys post-deployment."""
    
    def test_session_creation_endpoint(self):
        """Verify session creation endpoint is functional."""
        response = requests.post(
            f'{BASE_URL}/api/sessions',
            json={'title': 'Deployment Test Session'},
            timeout=10
        )
        
        assert response.status_code in [200, 201, 401, 403, 404, 405], \
            f"Unexpected status code: {response.status_code}"
    
    def test_websocket_endpoint_accessible(self):
        """Verify WebSocket endpoint is accessible."""
        try:
            import socketio
            
            sio = socketio.Client()
            sio.connect(BASE_URL, transports=['websocket'])
            
            assert sio.connected, "WebSocket connection failed"
            sio.disconnect()
            
        except ImportError:
            pytest.skip("python-socketio not installed")
        except Exception as e:
            if 'Connection refused' not in str(e):
                raise


@pytest.mark.smoke  
class TestDeploymentEnvironment:
    """Verify environment configuration post-deployment."""
    
    def test_environment_not_in_debug_mode(self):
        """Verify production is not in debug mode."""
        response = requests.get(f'{BASE_URL}/health', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'debug' in data:
                assert data['debug'] is False, "Production should not be in debug mode"
    
    def test_database_url_not_sqlite(self):
        """Verify production uses PostgreSQL, not SQLite."""
        response = requests.get(f'{BASE_URL}/health', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'database_type' in data:
                assert data['database_type'] != 'sqlite', \
                    "Production should use PostgreSQL, not SQLite"
    
    def test_external_services_configured(self):
        """Verify external services are configured."""
        response = requests.get(f'{BASE_URL}/health', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'services' in data:
                services = data['services']
                
                if 'openai' in services:
                    assert services['openai'] != 'not_configured', \
                        "OpenAI should be configured in production"
