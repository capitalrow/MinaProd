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

from app import app, socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# For Gunicorn compatibility - the 'app' and 'socketio' objects will be used directly
# Direct server startup for development/testing
if __name__ == '__main__':
    logger.info("🚀 Starting Mina with direct Socket.IO server...")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=True,
        allow_unsafe_werkzeug=True
    )