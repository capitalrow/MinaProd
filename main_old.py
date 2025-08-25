"""
Mina - Meeting Insights & Action Platform
Entry point for the Flask application with Socket.IO support.

CRITICAL: This app requires WebSocket support. Gunicorn sync worker will NOT work.
We force Socket.IO's built-in server regardless of how this is started.
"""

import os
import sys
import logging
import threading
import time
from app_refactored import create_app, socketio

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def force_socketio_server():
    """Force start Socket.IO server with WebSocket support."""
    print("🚀 FORCE-STARTING Socket.IO Server (WebSocket Compatible)")
    print("⚠️  Bypassing Gunicorn - Socket.IO needs WebSocket support!")
    
    host = '0.0.0.0'
    port = 5000
    
    print(f"🌐 Server: http://{host}:{port}")
    print("🎯 Live transcription: /live")
    print("✅ WebSocket connections enabled")
    
    # Create fresh app instance
    app = create_app()
    
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Disable for stability
            use_reloader=False,
            log_output=True,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"❌ Socket.IO server error: {e}")
        sys.exit(1)

# Detect if being called by Gunicorn and override
if 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '') or 'gunicorn' in str(sys.argv):
    print("🔄 DETECTED: Gunicorn attempting to start with incompatible sync worker")
    print("🛑 BLOCKING: Gunicorn sync worker (breaks WebSocket)")
    
    # Start Socket.IO server in a separate thread to bypass Gunicorn
    socketio_thread = threading.Thread(target=force_socketio_server, daemon=True)
    socketio_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("👋 Shutdown requested")
        sys.exit(0)

# Create the Flask app with Socket.IO
app = create_app()

if __name__ == '__main__':
    # Direct execution - use Socket.IO server
    force_socketio_server()

# For compatibility when imported as WSGI app (though we override above)
def application(environ, start_response):
    """WSGI application - should not be used due to WebSocket requirements."""
    print("⚠️  WARNING: WSGI mode detected - WebSocket may not work!")
    return app(environ, start_response)
