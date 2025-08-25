"""
Main entry point using Eventlet for production WebSocket support.
This replaces the standard Gunicorn approach with WebSocket-optimized server.
"""
from app_refactored import create_app
import os

# Create the application with SocketIO
app, socketio = create_app()

def run_with_eventlet():
    """Run the application with Eventlet support."""
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Mina with Eventlet WebSocket support...")
    print("✅ WebSocket compatibility: ENABLED")
    print("✅ Real-time transcription: READY")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        log_output=True
    )

if __name__ == '__main__':
    run_with_eventlet()

# For Gunicorn with eventlet worker
# Use: gunicorn --worker-class eventlet --bind 0.0.0.0:5000 main_eventlet:app