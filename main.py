"""
Mina - Meeting Insights & Action Platform
Entry point for the Flask application with Socket.IO support.
"""

import os
import logging
from app_refactored import create_app, socketio

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_ENV') == 'development' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create the Flask app with Socket.IO
app = create_app()

if __name__ == '__main__':
    # Use Socket.IO's run method for development
    # In production, use a proper WSGI server like gunicorn with eventlet
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting Mina with Socket.IO WebSocket support")
    print(f"🌐 Server: http://{host}:{port}")
    print("🎯 Live transcription: /live")
    
    socketio.run(
        app,
        host=host,
        port=port,
        debug=False,  # Disable for stability
        use_reloader=False,
        log_output=True,
        allow_unsafe_werkzeug=True
    )
