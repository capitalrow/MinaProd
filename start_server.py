#!/usr/bin/env python3
"""
Startup script for Mina with proper Socket.IO support
"""

import os
import sys
from app_refactored import create_app, socketio

def main():
    """Start the Mina application with Socket.IO support."""
    print("🚀 Starting Mina - Meeting Insights & Action Platform")
    print("📡 Socket.IO WebSocket support enabled")
    
    # Create Flask app with Socket.IO
    app = create_app()
    
    # Configuration
    host = '0.0.0.0'
    port = 5000
    debug = True
    
    print(f"🌐 Server starting on http://{host}:{port}")
    print("🎯 Live transcription available at /live")
    
    try:
        # Use Socket.IO's built-in server with async support
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Disable debug for stability
            allow_unsafe_werkzeug=True,
            use_reloader=False,  # Disable reloader for background running
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server shutdown requested")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()