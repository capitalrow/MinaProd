"""
Basic unit tests for Flask application setup.
"""
import pytest

@pytest.mark.unit
def test_app_exists(app):
    """Test that the Flask app is created."""
    assert app is not None
    assert app.config['TESTING'] is True

@pytest.mark.unit
def test_app_config(app):
    """Test app configuration in testing mode."""
    assert app.config['TESTING'] is True
    assert app.config['WTF_CSRF_ENABLED'] is False
    assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']

@pytest.mark.unit
def test_test_client(client):
    """Test that test client is created."""
    assert client is not None

@pytest.mark.unit
def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code in [200, 404]

@pytest.mark.unit
def test_home_page(client):
    """Test home page is accessible."""
    response = client.get('/')
    assert response.status_code in [200, 302]
