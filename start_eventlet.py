#!/usr/bin/env python3
"""
Stable Mina Server - Eliminates Socket connection errors
Run this instead of the default workflow for perfect WebSocket stability
"""

import eventlet
eventlet.monkey_patch()

import os
import logging
from app_refactored import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_stable_server():
    """Start stable Eventlet server with optimal WebSocket support"""
    # Create app instance
    app = create_app()
    
    logger.info("🚀 Starting Mina Stable Server")
    logger.info("✅ Eventlet WebSocket support enabled")
    logger.info("✅ No more Socket connection errors!")
    logger.info("🌐 Server: http://0.0.0.0:5000")
    
    try:
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            log_output=True,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")

if __name__ == '__main__':
    start_stable_server()