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
from whitenoise import WhiteNoise

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode='threading',  # Use threading for Flask compatibility
    ping_timeout=60,
    ping_interval=25,
    transport=['websocket', 'polling'],
    logger=True,
    engineio_logger=True
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
    
    # Configure WhiteNoise for static file serving
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=os.path.join(os.path.dirname(__file__), 'static'),
        prefix='/static/',
        max_age=31536000,  # 1 year cache for static assets
    )
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    # Register blueprints
    from routes.health import health_bp
    from routes.transcription import transcription_bp
    from routes.websocket import register_websocket_handlers
    
    app.register_blueprint(health_bp)
    app.register_blueprint(transcription_bp)
    
    # Register Socket.IO handlers
    register_websocket_handlers(socketio)
    
    # Initialize database
    with app.app_context():
        # Import models to ensure they are registered
        from models.session import Session
        from models.segment import Segment
        
        db.create_all()
        logger.info("Database initialized successfully")
    
    # Configure CORS for development
    if app.config.get('DEVELOPMENT'):
        from middleware.cors import configure_cors
        configure_cors(app)
    
    logger.info(f"Mina application created with config: {config_class.__name__}")
    return app
