"""
Flask application using the original Mina structure
Modified for better Gunicorn compatibility
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions - Base will be imported from models
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Socket.IO configuration for better compatibility
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',  # Required for stable WebSocket connections
    ping_timeout=60,  # Reduced timeout for better compatibility
    ping_interval=25,   # Regular ping to keep connection alive
    transports=['websocket', 'polling'],  # WebSocket first, polling fallback
    engineio_logger=False,   # Disabled for better Gunicorn compatibility
    socketio_logger=False,   # Disabled for better Gunicorn compatibility
    max_http_buffer_size=1000000  # 1MB buffer for audio data
)

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
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    from routes.health import health_bp
    from routes.transcription import transcription_bp
    from routes.sessions import sessions_bp
    from routes.summary import summary_bp
    from routes.sharing import sharing_bp
    from routes.export import export_bp
    from routes.websocket import register_websocket_handlers
    
    app.register_blueprint(health_bp)
    app.register_blueprint(transcription_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(sharing_bp)
    app.register_blueprint(export_bp)
    
    # Register Socket.IO handlers
    register_websocket_handlers(socketio)
    
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