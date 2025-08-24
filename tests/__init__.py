"""
Mina Test Package
Test suite for the Meeting Insights & Action platform.
"""

import os
import sys
import pytest
import logging
from pathlib import Path

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests.log', mode='w')
    ]
)

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'WTF_CSRF_ENABLED': False,
    'SECRET_KEY': 'test-secret-key',
    'ENABLE_REALTIME': True,
    'VAD_SENSITIVITY': 0.5,
    'MIN_CONFIDENCE': 0.7,
}

# Mock data helpers
class MockAudioData:
    """Helper class for generating mock audio data for tests."""
    
    @staticmethod
    def generate_silent_audio(duration_ms=1000, sample_rate=16000):
        """Generate silent audio data."""
        import numpy as np
        samples = int(duration_ms * sample_rate / 1000)
        return np.zeros(samples, dtype=np.float32).tobytes()
    
    @staticmethod
    def generate_noise_audio(duration_ms=1000, sample_rate=16000, amplitude=0.1):
        """Generate random noise audio data."""
        import numpy as np
        samples = int(duration_ms * sample_rate / 1000)
        noise = np.random.normal(0, amplitude, samples).astype(np.float32)
        return noise.tobytes()
    
    @staticmethod
    def generate_sine_wave(frequency=440, duration_ms=1000, sample_rate=16000, amplitude=0.5):
        """Generate sine wave audio data."""
        import numpy as np
        samples = int(duration_ms * sample_rate / 1000)
        t = np.linspace(0, duration_ms / 1000, samples, False)
        wave = amplitude * np.sin(2 * np.pi * frequency * t).astype(np.float32)
        return wave.tobytes()

class TestFixtures:
    """Common test fixtures and utilities."""
    
    @staticmethod
    def create_test_app():
        """Create a test Flask application instance."""
        from app_refactored import create_app
        from config import TestingConfig
        
        app = create_app(TestingConfig)
        return app
    
    @staticmethod
    def create_test_session_data():
        """Create test session data."""
        return {
            'title': 'Test Meeting Session',
            'description': 'A test meeting for unit testing',
            'language': 'en',
            'enable_speaker_detection': True,
            'enable_sentiment_analysis': False,
            'enable_realtime': True
        }
    
    @staticmethod
    def create_test_segment_data():
        """Create test transcription segment data."""
        return {
            'text': 'This is a test transcription segment for unit testing purposes.',
            'confidence': 0.85,
            'start_time': 0.0,
            'end_time': 3.5,
            'speaker_id': 'speaker_1',
            'speaker_name': 'Test Speaker',
            'language': 'en',
            'is_final': True
        }

# Pytest fixtures
@pytest.fixture
def app():
    """Create application for testing."""
    app = TestFixtures.create_test_app()
    
    with app.app_context():
        from app_refactored import db
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()

@pytest.fixture
def database(app):
    """Create test database."""
    from app_refactored import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def mock_audio_data():
    """Provide mock audio data for tests."""
    return MockAudioData()

@pytest.fixture
def test_session_data():
    """Provide test session data."""
    return TestFixtures.create_test_session_data()

@pytest.fixture
def test_segment_data():
    """Provide test segment data."""
    return TestFixtures.create_test_segment_data()

# Test utilities
def assert_valid_session(session_dict):
    """Assert that a session dictionary contains required fields."""
    required_fields = ['session_id', 'title', 'status', 'created_at']
    for field in required_fields:
        assert field in session_dict, f"Session missing required field: {field}"
    
    assert isinstance(session_dict['session_id'], str)
    assert len(session_dict['session_id']) > 0
    assert session_dict['status'] in ['created', 'active', 'paused', 'completed', 'error']

def assert_valid_segment(segment_dict):
    """Assert that a segment dictionary contains required fields."""
    required_fields = ['segment_id', 'text', 'confidence', 'start_time', 'end_time']
    for field in required_fields:
        assert field in segment_dict, f"Segment missing required field: {field}"
    
    assert isinstance(segment_dict['text'], str)
    assert len(segment_dict['text']) > 0
    assert 0 <= segment_dict['confidence'] <= 1
    assert segment_dict['start_time'] >= 0
    assert segment_dict['end_time'] > segment_dict['start_time']

def assert_valid_api_response(response_dict):
    """Assert that an API response has valid structure."""
    assert isinstance(response_dict, dict)
    if 'success' in response_dict:
        assert isinstance(response_dict['success'], bool)
    if 'error' in response_dict:
        assert isinstance(response_dict['error'], str)

# Test constants
TEST_AUDIO_FORMATS = ['webm', 'wav', 'mp3', 'ogg']
TEST_LANGUAGES = ['en', 'es', 'fr', 'de', 'zh']
TEST_SAMPLE_RATES = [8000, 16000, 22050, 44100]
TEST_CONFIDENCE_LEVELS = [0.5, 0.7, 0.8, 0.9, 0.95]

# Export commonly used items
__all__ = [
    'TEST_CONFIG',
    'MockAudioData',
    'TestFixtures',
    'assert_valid_session',
    'assert_valid_segment',
    'assert_valid_api_response',
    'TEST_AUDIO_FORMATS',
    'TEST_LANGUAGES',
    'TEST_SAMPLE_RATES',
    'TEST_CONFIDENCE_LEVELS'
]
