"""
Configuration settings for Mina application.
Consolidates environment-based configuration with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class with common settings."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-change-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    DEVELOPMENT = DEBUG
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///mina.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Real-time transcription settings
    ENABLE_REALTIME = os.environ.get('ENABLE_REALTIME', 'true').lower() == 'true'
    MAX_CHUNK_MS = int(os.environ.get('MAX_CHUNK_MS', '640'))
    MIN_CHUNK_MS = int(os.environ.get('MIN_CHUNK_MS', '100'))
    LANGUAGE_HINT = os.environ.get('LANGUAGE_HINT', 'en')
    MIN_CONFIDENCE = float(os.environ.get('MIN_CONFIDENCE', '0.6'))
    
    # M1 Quality Settings
    MAX_QUEUE_LEN = int(os.environ.get('MAX_QUEUE_LEN', '8'))
    VOICE_TAIL_MS = int(os.environ.get('VOICE_TAIL_MS', '300'))
    METRICS_SAMPLE_RATE = float(os.environ.get('METRICS_SAMPLE_RATE', '1.0'))
    DEDUP_OVERLAP_THRESHOLD = float(os.environ.get('DEDUP_OVERLAP_THRESHOLD', '0.9'))
    TRANSCRIPTION_ENGINE = os.environ.get('TRANSCRIPTION_ENGINE', 'mock')
    
    # VAD (Voice Activity Detection) settings
    VAD_SENSITIVITY = float(os.environ.get('VAD_SENSITIVITY', '0.5'))
    VAD_MIN_SPEECH_DURATION = int(os.environ.get('VAD_MIN_SPEECH_DURATION', '300'))  # ms
    VAD_MIN_SILENCE_DURATION = int(os.environ.get('VAD_MIN_SILENCE_DURATION', '500'))  # ms
    
    # Audio processing settings
    SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', '16000'))
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '1024'))
    AUDIO_FORMAT = os.environ.get('AUDIO_FORMAT', 'webm')
    
    # Whisper API settings (if using OpenAI Whisper)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'whisper-1')
    
    # Socket.IO settings
    SOCKETIO_PING_TIMEOUT = int(os.environ.get('SOCKETIO_PING_TIMEOUT', '60'))
    SOCKETIO_PING_INTERVAL = int(os.environ.get('SOCKETIO_PING_INTERVAL', '25'))
    
    # M3: Analysis and Summary settings
    ANALYSIS_ENGINE = os.environ.get('ANALYSIS_ENGINE', 'mock')
    AUTO_SUMMARY_ON_FINALIZE = os.environ.get('AUTO_SUMMARY_ON_FINALIZE', 'false').lower() == 'true'
    SUMMARY_CONTEXT_CHARS = int(os.environ.get('SUMMARY_CONTEXT_CHARS', '12000'))
    
    # Debug Configuration
    SHOW_DEBUG_PANEL = os.environ.get('SHOW_DEBUG_PANEL', 'false').lower() == 'true'
    
    # Application metadata
    APP_VERSION = os.environ.get('APP_VERSION', '0.1.0')
    GIT_SHA = os.environ.get('GIT_SHA', 'dev')

class ProductionConfig(Config):
    """Production configuration with security hardening."""
    DEBUG = False
    DEVELOPMENT = False
    
    # Require HTTPS in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
