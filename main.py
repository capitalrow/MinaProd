"""
Mina - Meeting Insights & Action Platform
Entry point compatible with both Gunicorn and direct execution.
"""

import os
import logging

# Only monkey patch when running directly (not with Gunicorn)
if __name__ == '__main__' and 'gunicorn' not in os.environ.get('SERVER_SOFTWARE', ''):
    import eventlet
    eventlet.monkey_patch()

from app import app
# socketio temporarily disabled for native WebSocket testing
socketio = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# For Gunicorn compatibility - the 'app' object will be used directly
# Direct server startup for development/testing
if __name__ == '__main__':
    logger.info("🚀 Starting Mina with Flask server (native WebSocket on port 8765)...")
    
    # Use standard Flask server since Socket.IO is disabled
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )