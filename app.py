"""
Flask application using the original Mina structure
Modified for better Gunicorn compatibility
"""

import os
import logging
from flask import Flask
# Keep SocketIO disabled due to dependency conflicts, use HTTP endpoints instead
# from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

# 🔥 PHASE 1: Environment configuration for debugging and testing
WS_DEBUG = os.getenv("WS_DEBUG", "false").lower() == "true"
STUB_TRANSCRIPTION = os.getenv("STUB_TRANSCRIPTION", "false").lower() == "true"

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions - Base will be imported from models
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# WebSocket Server Integration
from services.native_websocket_server import start_native_websocket_server_thread
from routes.native_websocket_routes import register_native_websocket_routes
from routes.sync_websocket_routes import register_sync_websocket_routes
from routes.library_websocket_routes import register_library_websocket_routes
from routes.browser_websocket_routes import register_browser_websocket_routes

# Start Browser WebSocket Server for guaranteed browser compatibility
try:
    from services.browser_websocket_server import start_browser_websocket_server
    start_browser_websocket_server()
    logger.info("✅ Browser WebSocket Server started successfully")
except Exception as e:
    logger.error(f"❌ Failed to start Browser WebSocket Server: {e}")

# Use HTTP endpoints for audio processing instead
socketio = None

def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app with all extensions.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Set secret key from environment
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-change-in-production")
    
    # Configure ProxyFix for proper URL generation behind reverse proxies
    app.wsgi_app = ProxyFix(
        app.wsgi_app, 
        x_proto=1, 
        x_host=1, 
        x_for=1,
        x_port=1
    )
    
    # Configure CORS middleware  
    from middleware.cors import configure_cors
    configure_cors(app)
    
    # SECURITY: Add production security headers
    @app.after_request
    def add_security_headers(response):
        """Add comprehensive security headers for production deployment."""
        from flask import request
        
        # Content Security Policy - Allow same origin and specific trusted sources
        if not app.config.get('DEVELOPMENT'):
            # Production CSP - restrictive but functional for WebSocket/audio apps
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Required for Socket.IO and audio processing
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "  # Bootstrap and inline styles
                "connect-src 'self' wss: ws: https://api.openai.com; "  # WebSocket and OpenAI API
                "media-src 'self' blob:; "  # Audio blob URLs
                "worker-src 'self' blob:; "  # Web workers for audio
                "frame-ancestors 'none'; "  # Prevent embedding
                "object-src 'none'; "
                "base-uri 'self'"
            )
        else:
            # Development CSP - more permissive for localhost
            csp_policy = (
                "default-src 'self' localhost:* 127.0.0.1:* *.replit.dev *.replit.app; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' localhost:* 127.0.0.1:* *.replit.dev *.replit.app; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net localhost:* 127.0.0.1:* *.replit.dev *.replit.app; "
                "connect-src 'self' wss: ws: https://api.openai.com localhost:* 127.0.0.1:* *.replit.dev *.replit.app; "
                "media-src 'self' blob: localhost:* 127.0.0.1:* *.replit.dev *.replit.app; "
                "worker-src 'self' blob:; "
                "frame-ancestors 'self' localhost:* 127.0.0.1:* *.replit.dev *.replit.app"
            )
        
        response.headers['Content-Security-Policy'] = csp_policy
        
        # HTTP Strict Transport Security (HSTS) - only for HTTPS
        if request.is_secure or app.config.get('FORCE_HTTPS'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # Allow same-origin framing for Replit
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection (legacy but still useful)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy - protect user privacy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy - restrict dangerous features
        response.headers['Permissions-Policy'] = (
            'microphone=(self), '  # Required for transcription
            'camera=(), '  # Not needed
            'geolocation=(), '
            'payment=(), '
            'usb=()'
        )
        
        return response
    
    # Initialize extensions
    db.init_app(app)
    
    # MANUAL MONITORING RECOMMENDATION #1: Enhanced WebSocket already initialized
    logger.info("✅ Using enhanced WebSocket infrastructure for real-time transcription")
    
    # Register blueprints
    from routes.health import health_bp
    from routes.transcription import transcription_bp
    from routes.sessions import sessions_bp
    from routes.summary import summary_bp
    from routes.sharing import sharing_bp
    from routes.export import export_bp
    from routes.api_performance import api_performance
    
    app.register_blueprint(health_bp)
    app.register_blueprint(transcription_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(api_performance)
    
    # Register API endpoints for advanced features
    try:
        from routes.api import api_bp
        app.register_blueprint(api_bp)
        logger.info("✅ API endpoints registered successfully")
    except Exception as e:
        logger.warning(f"⚠️ API endpoints not available: {e}")
    
    # Register WebSocket routes
    try:
        from routes.native_websocket_routes import register_native_websocket_routes
        register_native_websocket_routes(app)
        register_sync_websocket_routes(app)
        register_library_websocket_routes(app)
        register_browser_websocket_routes(app)
        logger.info("✅ WebSocket routes registered")
    except Exception as e:
        logger.error(f"❌ Failed to register WebSocket routes: {e}")
    
    # Register HTTP audio endpoints for direct processing
    try:
        from routes.audio_http import audio_http_bp
        app.register_blueprint(audio_http_bp)
        logger.info("✅ HTTP audio endpoints registered")
    except Exception as e:
        logger.error(f"❌ Failed to register HTTP audio endpoints: {e}")
    
    # MANUAL MONITORING RECOMMENDATION #1: Enhanced WebSocket routes already registered
    logger.info("✅ Enhanced WebSocket event handlers active")
    
    # 🔧 ACTIVATE EXISTING MONITORING SYSTEMS
    try:
        from activate_monitoring import setup_monitoring_endpoints, start_continuous_monitoring
        setup_monitoring_endpoints()
        start_continuous_monitoring()
        logger.info("✅ Enhanced monitoring systems activated")
    except Exception as e:
        logger.warning(f"⚠️ Enhanced monitoring not available: {e}")
    
    # Initialize database
    with app.app_context():
        # Import models with new SQLAlchemy 2.0 Base
        from models.base import Base
        from models import Session, Segment, Summary, SharedLink  # noqa: F401
        
        # Create tables if they don't exist (for development)
        if app.config.get('DEVELOPMENT', True):
            Base.metadata.create_all(bind=db.engine)
        
        logger.info("Database initialized successfully")
    
    # Configure CORS for development
    if app.config.get('DEVELOPMENT'):
        from middleware.cors import configure_cors
        configure_cors(app)
    
    logger.info(f"Mina application created with config: {config_class.__name__}")
    return app

# Create the app for Gunicorn
app = create_app()