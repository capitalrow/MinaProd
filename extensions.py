# extensions.py
from flask_socketio import SocketIO

# Threading works on Replit + polling
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)