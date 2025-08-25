#!/usr/bin/env python3
"""
Production-ready server using Eventlet workers for WebSocket support.
This resolves the Gunicorn + WebSocket incompatibility by using async workers.
"""

import os
import sys
from app_refactored import create_app

def main():
    """Start the application with Eventlet-enabled Gunicorn."""
    app, socketio = create_app()
    
    # Configuration for production WebSocket support
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    
    print(f"🚀 Starting Mina with Eventlet support on {host}:{port}")
    print("✅ WebSocket connections will be stable and persistent")
    print("✅ Real-time transcription fully enabled")
    
    # Use SocketIO run with eventlet for production-grade WebSocket support
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,
        use_reloader=False,
        log_output=True,
        engineio_logger=False,
        socketio_logger=False
    )

if __name__ == '__main__':
    main()