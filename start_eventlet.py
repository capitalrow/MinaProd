#!/usr/bin/env python3
"""
Eventlet-powered startup script for Mina.
Use this to bypass Gunicorn sync worker issues.
"""

import eventlet
eventlet.monkey_patch()

from main import app, socketio

if __name__ == '__main__':
    print("🚀 Starting Mina with Eventlet (Direct SocketIO Server)")
    print("✅ Stable WebSocket connections - No worker crashes!")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        log_output=True,
        allow_unsafe_werkzeug=True
    )