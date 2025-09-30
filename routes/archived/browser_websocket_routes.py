"""
Browser WebSocket Routes - Status endpoints for browser WebSocket server
"""

import logging
from flask import Blueprint, jsonify
from services.browser_websocket_server import get_browser_server_status

logger = logging.getLogger(__name__)

browser_ws_bp = Blueprint('browser_websocket', __name__)

@browser_ws_bp.route('/browser-status')
def browser_websocket_status():
    """Get browser WebSocket server status."""
    try:
        status = get_browser_server_status()
        logger.info(f"🌐 Browser WebSocket server status: {status}")
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Error getting browser WebSocket status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def register_browser_websocket_routes(app):
    """Register browser WebSocket routes with the Flask app."""
    app.register_blueprint(browser_ws_bp)
    logger.info("✅ Browser WebSocket routes registered")