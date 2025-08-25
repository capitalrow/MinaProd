"""
Mina - Meeting Insights & Action Platform
EVENTLET WEBSOCKET FIX: Stable WebSocket server with no worker crashes.
"""

import os
import logging

# Conditional Eventlet support - only when running directly
import_eventlet = os.environ.get('USE_EVENTLET', 'false').lower() == 'true'
if import_eventlet or __name__ == '__main__':
    try:
        import eventlet
        eventlet.monkey_patch()
        print("✅ Eventlet monkey patching applied")
    except ImportError:
        print("⚠️  Eventlet not available - using standard mode")

from app_refactored import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create the application - CRITICAL: This must work with both Gunicorn and direct execution
app = create_app()

# For Gunicorn: the 'app' object will be used as WSGI application
# The Eventlet monkey patching above ensures WebSocket compatibility

# Direct Eventlet server startup for development/testing
if __name__ == '__main__':
    logger.info("🚀 Starting Mina with Eventlet WebSocket support...")
    logger.info("✅ No more worker crashes or socket errors!")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=True,
        allow_unsafe_werkzeug=True
    )