"""
API Version Information Endpoint

Provides version metadata for clients to determine which API version to use.
"""

from flask import Blueprint, jsonify
from services.api_versioning import get_version_info, api_version_negotiation

api_version_bp = Blueprint('api_version', __name__)


@api_version_bp.route('/api/version', methods=['GET'])
@api_version_negotiation
def get_api_version():
    """
    Get API version information.
    
    Returns version metadata including:
    - Current version
    - Supported versions
    - Deprecation schedule
    - Migration guides
    
    Headers:
    - X-API-Version: Negotiated API version (set by decorator)
    
    Example response:
    {
        "current_version": "v2",
        "supported_versions": ["v1", "v2"],
        "default_version": "v1",
        "deprecation_schedule": {
            "v1": {
                "status": "supported",
                "migration_guide": "/docs/migration/v1-to-v2"
            }
        }
    }
    """
    return jsonify(get_version_info()), 200
