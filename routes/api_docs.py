"""
API documentation routes using Swagger UI.
"""
from flask import Blueprint, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
import os

SWAGGER_URL = '/api/docs'
API_URL = '/api/openapi.yaml'

swagger_bp = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Mina API Documentation",
        'docExpansion': 'list',
        'defaultModelsExpandDepth': 3,
        'displayOperationId': False,
        'displayRequestDuration': True
    }
)

# Blueprint to serve the OpenAPI spec file
spec_bp = Blueprint('api_spec', __name__)

@spec_bp.route('/api/openapi.yaml')
def serve_openapi_spec():
    """Serve the OpenAPI specification file."""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'api')
    return send_from_directory(docs_dir, 'openapi.yaml')
