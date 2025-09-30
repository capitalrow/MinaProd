"""
Native WebSocket Routes - Flask integration for native WebSocket testing
"""

from flask import Blueprint, render_template, current_app
import logging

logger = logging.getLogger(__name__)

# Create blueprint for native WebSocket routes
native_ws_bp = Blueprint('native_websocket', __name__)

@native_ws_bp.route('/native-test')
def native_websocket_test():
    """Serve the native WebSocket test page."""
    logger.info("📱 Serving native WebSocket test page")
    return render_template('native_websocket_client.html')

@native_ws_bp.route('/native-status')
def native_websocket_status():
    """Get the status of the native WebSocket server."""
    try:
        # Check if native WebSocket server is running
        from services.native_websocket_server import get_native_websocket_server
        server = get_native_websocket_server()
        
        status = {
            'status': 'running',
            'host': server.host,
            'port': server.port,
            'active_clients': len(server.clients),
            'active_sessions': len(server.active_sessions),
            'websocket_url': f'ws://{server.host}:{server.port}'
        }
        
        logger.info(f"📊 Native WebSocket server status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"❌ Error getting native WebSocket status: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }, 500

def register_native_websocket_routes(app):
    """Register native WebSocket routes with the Flask app."""
    app.register_blueprint(native_ws_bp)
    logger.info("✅ Native WebSocket routes registered")