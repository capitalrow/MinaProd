"""
Mina — entrypoint (single Socket.IO runtime)
"""
import os
import eventlet
eventlet.monkey_patch()

from app_refactored import create_app, socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port)