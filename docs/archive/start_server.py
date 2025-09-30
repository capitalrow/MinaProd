#!/usr/bin/env python3
"""
Startup script for Mina with proper Socket.IO support
"""

import os
import sys
import signal
import time
from app_refactored import create_app, socketio

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n👋 Server shutdown requested (signal {signum})")
    sys.exit(0)

def main():
    """Start the Mina application with Socket.IO support."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Mina - Meeting Insights & Action Platform")
    print("📡 Socket.IO WebSocket support enabled")
    print("⚠️  Using Socket.IO built-in server (NOT Gunicorn)")
    
    # Create Flask app with Socket.IO
    try:
        app = create_app()
        print("✅ Flask app created successfully")
    except Exception as e:
        print(f"❌ Failed to create Flask app: {e}")
        sys.exit(1)
    
    # Configuration
    host = '0.0.0.0'
    port = 5000
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print("🎯 Live transcription available at /live")
    print("🔗 WebSocket connections will be handled properly")
    
    try:
        # Use Socket.IO's built-in server with async support
        print("🚀 Starting Socket.IO server...")
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Disable debug for stability
            allow_unsafe_werkzeug=True,
            use_reloader=False,  # Disable reloader for background running
            log_output=False  # Reduce log noise
        )
    except KeyboardInterrupt:
        print("\n👋 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()