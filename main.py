"""
Mina — entrypoint (single Socket.IO runtime)
"""
from app import app, socketio  # Import both app and socketio

# For Gunicorn with eventlet worker, just expose the Flask app
# Flask-SocketIO automatically integrates when eventlet worker is used
application = app

if __name__ == "__main__":
    # For development with eventlet
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)