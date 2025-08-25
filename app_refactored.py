"""
Flask application factory with Socket.IO support and layered architecture.
Consolidates configuration from multiple codebases into a production-ready setup.
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
# from whitenoise import WhiteNoise  # Disabled to avoid Socket.IO conflicts

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize extensions - Base will be imported from models
db = SQLAlchemy()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='eventlet',  # Use eventlet for production compatibility
    ping_timeout=60,
    ping_interval=25,
    transport=['websocket', 'polling']
)

def create_app(config_class=Config):
    """
    Application factory pattern for creating Flask app with all extensions.
    Integrates Socket.IO, ProxyFix, WhiteNoise, and layered architecture.
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
    
    # Serve static files via Flask for now to avoid Socket.IO conflicts
    # WhiteNoise can interfere with Socket.IO upgrades, so we'll use Flask's built-in static serving
    
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
        # Import M2 + M3 models with new SQLAlchemy 2.0 Base
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
