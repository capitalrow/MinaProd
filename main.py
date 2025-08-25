"""
Mina - Meeting Insights & Action Platform
FIXED: Clean single-server architecture using only Socket.IO server.
Eliminates Gunicorn conflicts and provides stable WebSocket support.
"""

import os
import sys
import logging
from app_refactored import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_socketio_server():
    """
    Start Socket.IO server with WebSocket support.
    FIXED: Single server approach - no Gunicorn conflicts.
    """
    host = '0.0.0.0'
    port = 5000
    
    logger.info("🚀 Starting Mina Socket.IO Server")
    logger.info(f"🌐 Server: http://{host}:{port}")
    logger.info("🎯 Live transcription: /live")
    logger.info("✅ WebSocket and HTTP support enabled")
    
    # Create app instance
    app = create_app()
    
    try:
        # Start Socket.IO server with optimized settings
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Stable production-like mode
            use_reloader=False,  # Disable auto-reload for stability
            log_output=True,  # Enable request logging
            allow_unsafe_werkzeug=True  # Allow Socket.IO server mode
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error("❌ Port 5000 is already in use!")
            logger.error("💡 Please stop other servers or use a different port")
            sys.exit(1)
        else:
            raise
    except Exception as e:
        logger.error(f"❌ Server startup error: {e}")
        sys.exit(1)

# Create app for WSGI compatibility (though we use Socket.IO server directly)
app = create_app()

if __name__ == '__main__':
    start_socketio_server()

# Clean WSGI application (fallback - should not be used)
def application(environ, start_response):
    """WSGI fallback - Socket.IO server is preferred."""
    return app(environ, start_response)