"""
Health Check Tests
Test suite for health check endpoints and system monitoring.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

def test_basic_health_check(client):
    """Test basic health check endpoint."""
    response = client.get('/health')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'version' in data
    assert 'timestamp' in data
    assert 'environment' in data
    
    # Verify timestamp format
    timestamp = datetime.fromisoformat(data['timestamp'])
    assert isinstance(timestamp, datetime)

def test_health_check_with_database_success(client, database):
    """Test health check when database is accessible."""
    response = client.get('/health')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['database'] == 'connected'

@patch('app_refactored.db')
def test_health_check_with_database_error(mock_db, client):
    """Test health check when database connection fails."""
    # Mock database connection failure
    mock_db.session.execute.side_effect = Exception('Database connection failed')
    
    response = client.get('/health')
    
    # Should still return 200 in development, but show database error
    data = json.loads(response.data)
    assert 'database_error' in data
    assert data['database'] == 'error'

def test_detailed_health_check(client, database):
    """Test detailed health check endpoint."""
    response = client.get('/health/detailed')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'system' in data
    assert 'database' in data
    assert 'services' in data
    
    # Check system information structure
    system = data['system']
    assert 'python_version' in system
    assert 'platform' in system
    assert 'memory' in system
    assert 'disk' in system
    
    # Check database statistics
    db_stats = data['database']
    if 'error' not in db_stats:
        assert 'sessions_count' in db_stats
        assert 'segments_count' in db_stats

def test_readiness_check_success(client, database):
    """Test readiness probe when system is ready."""
    response = client.get('/health/ready')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'ready'
    assert 'timestamp' in data

@patch('app_refactored.db')
def test_readiness_check_failure(mock_db, client):
    """Test readiness probe when system is not ready."""
    # Mock database connection failure
    mock_db.session.execute.side_effect = Exception('Database not ready')
    
    response = client.get('/health/ready')
    
    assert response.status_code == 503
    
    data = json.loads(response.data)
    assert data['status'] == 'not_ready'
    assert 'error' in data

def test_liveness_check(client):
    """Test liveness probe."""
    response = client.get('/health/live')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['status'] == 'alive'
    assert 'timestamp' in data

def test_health_check_environment_variables(client, monkeypatch):
    """Test health check with different environment variables."""
    # Set test environment variables
    monkeypatch.setenv('APP_VERSION', '1.2.3')
    monkeypatch.setenv('GIT_SHA', 'abc123def456')
    monkeypatch.setenv('FLASK_ENV', 'production')
    
    response = client.get('/health')
    
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['version'] == '1.2.3'
    assert data['git_sha'] == 'abc123def456'
    assert data['environment'] == 'production'

def test_health_check_content_type(client):
    """Test health check response content type."""
    response = client.get('/health')
    
    assert response.content_type == 'application/json'

def test_health_check_caching_headers(client):
    """Test that health check responses are not cached."""
    response = client.get('/health')
    
    # Should not have caching headers that would cache the response
    assert 'Cache-Control' not in response.headers or 'no-cache' in response.headers.get('Cache-Control', '')

@patch('routes.health.logger')
def test_health_check_logging(mock_logger, client):
    """Test that health check failures are properly logged."""
    with patch('app_refactored.db') as mock_db:
        mock_db.session.execute.side_effect = Exception('Test database error')
        
        client.get('/health')
        
        mock_logger.error.assert_called()

def test_health_check_multiple_requests(client):
    """Test multiple concurrent health check requests."""
    responses = []
    
    # Make multiple requests
    for _ in range(5):
        response = client.get('/health')
        responses.append(response)
    
    # All should succeed
    for response in responses:
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

def test_health_check_performance(client):
    """Test health check response time."""
    import time
    
    start_time = time.time()
    response = client.get('/health')
    end_time = time.time()
    
    response_time = end_time - start_time
    
    # Health check should respond quickly (less than 1 second)
    assert response_time < 1.0
    assert response.status_code == 200

@pytest.mark.parametrize('endpoint', [
    '/health',
    '/health/detailed',
    '/health/ready',
    '/health/live'
])
def test_health_endpoints_methods(client, endpoint):
    """Test that health endpoints only accept GET requests."""
    # GET should work
    response = client.get(endpoint)
    assert response.status_code in [200, 503]  # 503 is acceptable for readiness checks
    
    # Other methods should not be allowed
    response = client.post(endpoint)
    assert response.status_code == 405
    
    response = client.put(endpoint)
    assert response.status_code == 405
    
    response = client.delete(endpoint)
    assert response.status_code == 405

def test_health_check_with_services(client):
    """Test health check including transcription services."""
    response = client.get('/health')
    
    data = json.loads(response.data)
    
    # Should include transcription service status
    assert 'transcription_service' in data

@patch('services.transcription_service.TranscriptionService')
def test_health_check_service_error(mock_service, client):
    """Test health check when transcription service has issues."""
    # Mock service initialization failure
    mock_service.side_effect = Exception('Service unavailable')
    
    response = client.get('/health')
    
    data = json.loads(response.data)
    assert data['transcription_service'] == 'error'

def test_detailed_health_check_statistics(client, database):
    """Test detailed health check includes proper statistics."""
    # Create some test data
    from models.session import Session
    from models.segment import Segment
    from app_refactored import db
    
    # Create test session
    session = Session(
        session_id='test-session-1',
        title='Test Session',
        status='completed'
    )
    db.session.add(session)
    db.session.commit()
    
    # Create test segment
    segment = Segment(
        session_id='test-session-1',
        segment_id='test-segment-1',
        sequence_number=1,
        start_time=0.0,
        end_time=5.0,
        text='Test transcription',
        confidence=0.9,
        is_final=True
    )
    db.session.add(segment)
    db.session.commit()
    
    response = client.get('/health/detailed')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Should include database counts
    if 'error' not in data['database']:
        assert data['database']['sessions_count'] >= 1
        assert data['database']['segments_count'] >= 1

def test_health_check_error_handling(client):
    """Test health check handles unexpected errors gracefully."""
    with patch('routes.health.datetime') as mock_datetime:
        # Mock an unexpected error
        mock_datetime.utcnow.side_effect = Exception('Unexpected error')
        
        response = client.get('/health')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'error' in data

def test_health_check_json_serialization(client):
    """Test health check response is properly JSON serialized."""
    response = client.get('/health')
    
    # Should be valid JSON
    try:
        data = json.loads(response.data)
        assert isinstance(data, dict)
    except json.JSONDecodeError:
        pytest.fail("Health check response is not valid JSON")

@patch('psutil.virtual_memory')
@patch('psutil.disk_usage')
@patch('psutil.cpu_count')
def test_detailed_health_system_info(mock_cpu, mock_disk, mock_memory, client):
    """Test detailed health check system information."""
    # Mock system information
    mock_memory.return_value = MagicMock(
        total=8589934592,  # 8GB
        available=4294967296,  # 4GB
        percent=50.0
    )
    mock_disk.return_value = MagicMock(
        total=1000000000000,  # 1TB
        free=500000000000,   # 500GB
        percent=50.0
    )
    mock_cpu.return_value = 8
    
    response = client.get('/health/detailed')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    system = data['system']
    assert system['cpu_count'] == 8
    assert system['memory']['total'] == 8589934592
    assert system['memory']['percent'] == 50.0
    assert system['disk']['percent'] == 50.0
