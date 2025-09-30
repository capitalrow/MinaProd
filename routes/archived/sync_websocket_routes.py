"""
Sync WebSocket Routes - Status endpoints for synchronous WebSocket server
"""

import logging
from flask import Blueprint, jsonify
from services.sync_websocket_server import get_sync_server_status

logger = logging.getLogger(__name__)

sync_ws_bp = Blueprint('sync_websocket', __name__)

@sync_ws_bp.route('/sync-status')
def sync_websocket_status():
    """Get sync WebSocket server status."""
    try:
        status = get_sync_server_status()
        logger.info(f"📊 Sync WebSocket server status: {status}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Error getting sync WebSocket status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def register_sync_websocket_routes(app):
    """Register sync WebSocket routes with the Flask app."""
    app.register_blueprint(sync_ws_bp)
    logger.info("✅ Sync WebSocket routes registered")