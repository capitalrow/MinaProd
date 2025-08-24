"""
CORS Middleware Configuration
Cross-Origin Resource Sharing setup for development and production.
"""

import logging
from flask import request
from flask_cors import CORS

logger = logging.getLogger(__name__)

def configure_cors(app):
    """
    Configure CORS for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    if app.config.get('DEVELOPMENT'):
        # Development CORS - more permissive
        CORS(app, 
             origins=['http://localhost:*', 'http://127.0.0.1:*'],
             allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
             supports_credentials=True)
        
        logger.info("CORS configured for development environment")
    
    else:
        # Production CORS - more restrictive
        allowed_origins = [
            'https://yourdomain.com',
            'https://app.yourdomain.com',
            # Add your production domains here
        ]
        
        CORS(app,
             origins=allowed_origins,
             allow_headers=['Content-Type', 'Authorization'],
             methods=['GET', 'POST', 'PUT', 'DELETE'],
             supports_credentials=True)
        
        logger.info("CORS configured for production environment")
    
    @app.after_request
    def after_request(response):
        """Add additional CORS headers if needed."""
        
        # Add Socket.IO specific headers for development
        if app.config.get('DEVELOPMENT'):
            origin = request.headers.get('Origin')
            if origin and ('localhost' in origin or '127.0.0.1' in origin):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
