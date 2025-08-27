"""
Library WebSocket Routes - Status endpoints for WebSocket library server
"""

import logging
from flask import Blueprint, jsonify
from services.websockets_library_server import get_library_server_status

logger = logging.getLogger(__name__)

library_ws_bp = Blueprint('library_websocket', __name__)

@library_ws_bp.route('/library-status')
def library_websocket_status():
    """Get WebSocket library server status."""
    try:
        status = get_library_server_status()
        logger.info(f"📊 WebSocket library server status: {status}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Error getting WebSocket library status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def register_library_websocket_routes(app):
    """Register WebSocket library routes with the Flask app."""
    app.register_blueprint(library_ws_bp)
    logger.info("✅ WebSocket library routes registered")