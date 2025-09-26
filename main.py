"""
Mina — entrypoint (single Socket.IO runtime)
"""
from app import app  # Use the consolidated app.py

if __name__ == "__main__":
    # app.py handles the socketio.run internally
    pass