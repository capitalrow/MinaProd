"""
Mina — entrypoint (single Socket.IO runtime)
"""
import os
import eventlet
eventlet.monkey_patch()

from app_refactored import create_app, socketio
# main.py – gunicorn entrypoint
from app import app  # exposes "app" so gunicorn can load main:app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    socketio.run(app, host="0.0.0.0", port=port)