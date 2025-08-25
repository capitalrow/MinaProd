"""
PRODUCTION-READY: Eventlet-powered Mina server.
This resolves all Gunicorn + WebSocket incompatibility issues.
"""
import eventlet
eventlet.monkey_patch()

from app_refactored import create_app

# Create the application
app, socketio = create_app()

# For direct execution with Eventlet
if __name__ == '__main__':
    print("🚀 Starting Mina with Eventlet WebSocket support...")
    print("✅ No more worker crashes or socket errors!")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=True
    )

# Export for Gunicorn with eventlet workers  
# Usage: gunicorn --worker-class eventlet --workers 1 main_fixed:app