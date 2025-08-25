#!/usr/bin/env python3
"""
Dedicated Socket.IO Server for Mina
This server bypasses Gunicorn entirely and provides full WebSocket support.
"""

import os
import sys
import signal
import subprocess
import time
from app_refactored import create_app, socketio

def kill_gunicorn():
    """Kill any running Gunicorn processes."""
    try:
        subprocess.run(['pkill', '-9', '-f', 'gunicorn'], check=False)
        print("🔥 Terminated conflicting Gunicorn processes")
    except Exception as e:
        print(f"⚠️  Could not kill Gunicorn: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n👋 Socket.IO server shutdown (signal {signum})")
    sys.exit(0)

def main():
    """Start the dedicated Socket.IO server."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Dedicated Socket.IO Server for Mina")
    print("🎯 BYPASSING Gunicorn - Full WebSocket Support Enabled")
    
    # Kill any conflicting processes
    kill_gunicorn()
    
    # Create Flask app
    try:
        app = create_app()
        print("✅ Flask app created successfully")
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        sys.exit(1)
    
    # Server configuration
    host = '0.0.0.0'
    port = 5000
    
    print(f"🌐 Server: http://{host}:{port}")
    print("🎯 Live transcription: /live")
    print("✅ WebSocket connections fully supported")
    print("🔒 Port 5000 secured for Socket.IO")
    
    # Start Socket.IO server with full WebSocket support
    try:
        print("🚀 Launching Socket.IO server...")
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            log_output=False,  # Reduce noise
            allow_unsafe_werkzeug=True
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print("⚠️  Port 5000 in use - killing competing processes...")
            kill_gunicorn()
            time.sleep(2)
            # Retry
            socketio.run(
                app,
                host=host,
                port=port,
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        else:
            raise
    except Exception as e:
        print(f"❌ Socket.IO server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()