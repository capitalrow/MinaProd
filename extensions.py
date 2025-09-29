"""
🔧 Flask Extensions & Dependency Injection
Centralizes all Flask extensions to eliminate circular imports and provide clean dependency injection.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    """SQLAlchemy declarative base"""
    pass

# Global extension instances (no app binding at import time)
db = SQLAlchemy(model_class=Base)

# Use eventlet for production stability (from original working config)
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="eventlet",  # More stable for production
    ping_timeout=60,
    ping_interval=25,
    logger=False,
    engineio_logger=False
)

login_manager = LoginManager()
compress = Compress()
csrf = CSRFProtect()

class ServiceContainer:
    """Lightweight dependency injection container for services"""
    
    def __init__(self):
        self._services = {}
        self._initialized = False
        
    def register_service(self, name: str, service_factory):
        """Register a service factory"""
        self._services[name] = service_factory
        
    def get_service(self, name: str):
        """Get a service instance"""
        if name not in self._services:
            raise ValueError(f"Service '{name}' not registered")
            
        service_factory = self._services[name]
        
        # Call factory if it's a callable, otherwise return directly
        if callable(service_factory):
            return service_factory()
        return service_factory
    
    def initialize_services(self, app):
        """Initialize all services with app context"""
        if self._initialized:
            return
            
        try:
            from services.transcription_service import TranscriptionService
            from services.openai_client_manager import OpenAIClientManager
            from services.export_service import ExportService
            from services.health_monitor import HealthMonitor
            from services.alerting_system import get_alerting_system
            from services.websocket_monitor import get_websocket_monitor
            from services.business_metrics import get_business_metrics
            from services.dependency_monitor import get_dependency_monitor
            
            # Register core services
            self.register_service('transcription', lambda: TranscriptionService())
            self.register_service('openai_client', lambda: OpenAIClientManager())
            self.register_service('export', lambda: ExportService())
            self.register_service('health_monitor', lambda: HealthMonitor())
            self.register_service('alerting', lambda: get_alerting_system())
            self.register_service('websocket_monitor', lambda: get_websocket_monitor())
            self.register_service('business_metrics', lambda: get_business_metrics())
            self.register_service('dependency_monitor', lambda: get_dependency_monitor())
            
            # Store app reference for services that need it
            self._app = app
            self._initialized = True
            
            logger.info("🔧 Service container initialized with all core services")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")

# Global service container
container = ServiceContainer()

def init_extensions(app):
    """Initialize all extensions with the Flask app"""
    
    # Configure SQLAlchemy - ensure database URL is set
    import os
    database_url = (
        app.config.get("DATABASE_URL") or 
        os.environ.get("DATABASE_URL") or
        "sqlite:///mina.db"  # Fallback for development
    )
    
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    
    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app)
    
    # Configure LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Initialize other extensions
    compress.init_app(app)
    csrf.init_app(app)
    
    # Attach container to app
    app.container = container
    
    # Initialize services
    container.initialize_services(app)
    
    # Create database tables in app context
    with app.app_context():
        # Import models to ensure they're registered
        try:
            import models.session  # noqa: F401
            import models.segment  # noqa: F401
            import models.user  # noqa: F401
        except ImportError:
            logger.warning("Some model imports failed - tables may not be created")
        
        db.create_all()
    
    logger.info("🔧 All extensions initialized successfully")

def get_service(name: str):
    """Get a service from the container (for use in routes)"""
    from flask import current_app
    return current_app.container.get_service(name)

# Convenience functions for common services
def get_db():
    """Get database instance"""
    return db

def get_socketio():
    """Get SocketIO instance"""
    return socketio

def get_login_manager():
    """Get LoginManager instance"""
    return login_manager