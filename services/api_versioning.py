"""
API Versioning Service for Zero-Downtime Deployments

Provides backward compatibility during blue/green deployments by supporting
multiple API versions simultaneously. Ensures old clients continue working
while new features are rolled out gradually.

Key Features:
- Dual event emission (emit both old and new event names)
- Version negotiation via headers
- Automatic request/response transformation
- Gradual migration path (v1 → v2 → v3)

Usage:
    from services.api_versioning import emit_versioned, get_client_version
    
    # Emit to all versions
    emit_versioned('transcript_segment', data, versions=['v1', 'v2'])
    
    # Check client version
    version = get_client_version(request)
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from flask import request, jsonify, g
from flask_socketio import emit

logger = logging.getLogger(__name__)

# Current API version (latest)
CURRENT_VERSION = "v2"
SUPPORTED_VERSIONS = ["v1", "v2"]
DEFAULT_VERSION = "v1"  # For clients that don't specify

# Event name mapping for backward compatibility
# v1 event name → v2 event name  
EVENT_NAME_MAPPING = {
    "v1": {
        # Interim/partial transcriptions
        "transcription_result": "transcript_partial",  # v1 name → v2 name (interim events)
        "transcription_interim": "transcript_partial",
        # Final transcription
        "transcription_final": "transcript_complete",
        # Other events
        "audio_chunk_received": "audio_processed",
        "session_created": "recording_started",
        "session_finalized": "recording_completed",
    },
    "v2": {
        # v2 uses canonical names (no mapping needed)
    }
}

# Field name mapping for data transformation
# v1 field → v2 field
FIELD_NAME_MAPPING = {
    "v1": {
        "text": "content",  # Renamed for clarity
        "is_final": "is_complete",
        "session_id": "recording_id",
    },
    "v2": {
        # v2 uses canonical field names
    }
}


def get_client_version(req: Optional[Any] = None) -> str:
    """
    Determine client API version from request headers.
    
    Checks (in order):
    1. X-API-Version header
    2. Accept-Version header
    3. Query parameter ?api_version=v2
    4. Default to v1 for backward compatibility
    
    Args:
        req: Flask request object (defaults to current request)
    
    Returns:
        API version string (e.g., "v1", "v2")
    """
    if req is None:
        req = request
    
    # Try X-API-Version header (preferred)
    version = req.headers.get('X-API-Version')
    if version and version in SUPPORTED_VERSIONS:
        return version
    
    # Try Accept-Version header
    version = req.headers.get('Accept-Version')
    if version and version in SUPPORTED_VERSIONS:
        return version
    
    # Try query parameter
    version = req.args.get('api_version')
    if version and version in SUPPORTED_VERSIONS:
        return version
    
    # Default to v1 for backward compatibility
    return DEFAULT_VERSION


def set_response_version(version: str) -> None:
    """
    Set the API version for the response.
    
    Stores version in Flask's g object for use by response middleware.
    
    Args:
        version: API version string
    """
    g.api_version = version


def get_response_version() -> str:
    """
    Get the API version for the current response.
    
    Returns:
        API version string from g.api_version or default
    """
    return getattr(g, 'api_version', DEFAULT_VERSION)


def transform_event_name(event_name: str, from_version: str, to_version: str) -> str:
    """
    Transform event name from one API version to another.
    
    Args:
        event_name: Original event name
        from_version: Source API version
        to_version: Target API version
    
    Returns:
        Transformed event name
    """
    if from_version == to_version:
        return event_name
    
    # v1 → v2 transformation
    if from_version == "v1" and to_version == "v2":
        return EVENT_NAME_MAPPING["v1"].get(event_name, event_name)
    
    # v2 → v1 transformation (reverse mapping)
    if from_version == "v2" and to_version == "v1":
        reverse_map = {v: k for k, v in EVENT_NAME_MAPPING["v1"].items()}
        return reverse_map.get(event_name, event_name)
    
    return event_name


def transform_data(data: Dict[str, Any], from_version: str, to_version: str) -> Dict[str, Any]:
    """
    Transform data payload from one API version to another.
    
    Args:
        data: Original data dictionary
        from_version: Source API version
        to_version: Target API version
    
    Returns:
        Transformed data dictionary
    """
    if from_version == to_version:
        return data
    
    transformed = data.copy()
    
    # v1 → v2 transformation
    if from_version == "v1" and to_version == "v2":
        for old_field, new_field in FIELD_NAME_MAPPING["v1"].items():
            if old_field in transformed:
                transformed[new_field] = transformed.pop(old_field)
    
    # v2 → v1 transformation (reverse mapping)
    if from_version == "v2" and to_version == "v1":
        reverse_map = {v: k for k, v in FIELD_NAME_MAPPING["v1"].items()}
        for new_field, old_field in reverse_map.items():
            if new_field in transformed:
                transformed[old_field] = transformed.pop(new_field)
    
    return transformed


def emit_versioned(
    event_name: str,
    data: Dict[str, Any],
    versions: Optional[List[str]] = None,
    room: Optional[str] = None,
    source_version: str = CURRENT_VERSION
) -> None:
    """
    Emit WebSocket event to multiple API versions simultaneously.
    
    This enables zero-downtime deployments by supporting both old and new clients.
    
    Args:
        event_name: Canonical event name (v2 format)
        data: Event data payload
        versions: List of versions to emit to (defaults to all supported)
        room: Socket.IO room to emit to (optional)
        source_version: Version of the source data (defaults to current)
    
    Example:
        emit_versioned('transcript_segment', {
            'content': 'Hello world',
            'is_complete': True,
            'recording_id': '12345'
        }, versions=['v1', 'v2'])
        
        # Emits:
        # v1: 'transcription_result' with {text, is_final, session_id}
        # v2: 'transcript_segment' with {content, is_complete, recording_id}
    """
    if versions is None:
        versions = SUPPORTED_VERSIONS
    
    for target_version in versions:
        # Transform event name
        versioned_event_name = transform_event_name(event_name, source_version, target_version)
        
        # Transform data
        versioned_data = transform_data(data, source_version, target_version)
        
        # Add version metadata
        versioned_data['_api_version'] = target_version
        
        # Emit to room or broadcast
        if room:
            emit(versioned_event_name, versioned_data, room=room)
        else:
            emit(versioned_event_name, versioned_data)
        
        logger.debug(
            f"📡 Emitted {versioned_event_name} (API {target_version}) "
            f"to room={room or 'broadcast'}"
        )


def api_version_negotiation(f: Callable) -> Callable:
    """
    Decorator to add API version negotiation to REST endpoints.
    
    Automatically:
    - Detects client version from headers/query params
    - Stores version in g.api_version
    - Adds X-API-Version header to response
    
    Handles all Flask return types:
    - Response objects
    - (response, status) tuples
    - (response, status, headers) tuples
    - Plain strings/dicts (auto-converted to Response)
    
    Usage:
        @app.route('/api/sessions')
        @api_version_negotiation
        def get_sessions():
            version = get_response_version()
            # ... handle request based on version
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        from flask import make_response
        
        # Detect and store client version
        client_version = get_client_version()
        set_response_version(client_version)
        
        logger.debug(f"📡 API request with version: {client_version}")
        
        # Call the endpoint
        result = f(*args, **kwargs)
        
        # Normalize result to Response object (handles tuples, strings, dicts, etc.)
        response = make_response(result)
        
        # Add version header to response
        response.headers['X-API-Version'] = client_version
        
        return response
    
    return wrapper


def transform_response_data(
    data: Dict[str, Any],
    target_version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transform response data to match client's API version.
    
    Args:
        data: Response data dictionary
        target_version: Target API version (defaults to current response version)
    
    Returns:
        Transformed data dictionary
    """
    if target_version is None:
        target_version = get_response_version()
    
    return transform_data(data, CURRENT_VERSION, target_version)


def emit_dual_events(
    v1_event: str,
    v2_event: str,
    data: Dict[str, Any],
    room: Optional[str] = None
) -> None:
    """
    Emit both v1 and v2 events for maximum backward compatibility.
    
    This is a convenience wrapper for the most common use case.
    
    Args:
        v1_event: v1 event name
        v2_event: v2 event name (canonical)
        data: Event data (in v2 format)
        room: Socket.IO room (optional)
    
    Example:
        emit_dual_events(
            v1_event='transcription_result',
            v2_event='transcript_segment',
            data={'content': 'Hello', 'is_complete': True, 'recording_id': '123'}
        )
    """
    # Emit v2 (canonical)
    emit(v2_event, {**data, '_api_version': 'v2'}, room=room)
    
    # Transform and emit v1
    v1_data = transform_data(data, 'v2', 'v1')
    emit(v1_event, {**v1_data, '_api_version': 'v1'}, room=room)
    
    logger.debug(f"📡 Dual emit: {v1_event} (v1) + {v2_event} (v2)")


def create_version_middleware(app: Any) -> None:
    """
    Create middleware to automatically add X-API-Version header to all API responses.
    
    This applies version negotiation to ALL /api/* routes automatically,
    eliminating the need to decorate each endpoint individually.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def add_version_header(response):
        """Add X-API-Version header to all /api/* responses."""
        from flask import request
        
        # Only apply to API routes
        if request.path.startswith('/api/'):
            # Detect client version
            client_version = get_client_version(request)
            
            # Add version header if not already present
            if 'X-API-Version' not in response.headers:
                response.headers['X-API-Version'] = client_version
                logger.debug(f"📡 Added X-API-Version: {client_version} to {request.path}")
        
        return response
    
    logger.info("✅ API versioning middleware enabled for all /api/* routes")


def get_version_info() -> Dict[str, Any]:
    """
    Get API version information for the /api/version endpoint.
    
    Returns:
        Dictionary with version metadata
    """
    return {
        'current_version': CURRENT_VERSION,
        'supported_versions': SUPPORTED_VERSIONS,
        'default_version': DEFAULT_VERSION,
        'deprecation_schedule': {
            'v1': {
                'status': 'supported',
                'deprecated_date': None,
                'sunset_date': None,  # Will be set when v3 releases
                'migration_guide': '/docs/migration/v1-to-v2'
            },
            'v2': {
                'status': 'current',
                'deprecated_date': None,
                'sunset_date': None
            }
        }
    }
