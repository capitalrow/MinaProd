"""
CORS Middleware Configuration
Cross-Origin Resource Sharing setup for development and production.
"""

import logging
import os
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
        # PRODUCTION: Replace with actual production domains
        allowed_origins = os.environ.get('ALLOWED_ORIGINS', '').split(',') if os.environ.get('ALLOWED_ORIGINS') else [
            'https://REPLACE_WITH_YOUR_DOMAIN.com',
            'https://app.REPLACE_WITH_YOUR_DOMAIN.com',
            'https://admin.REPLACE_WITH_YOUR_DOMAIN.com'
        ]
        # Remove empty strings from split
        allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
        
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
