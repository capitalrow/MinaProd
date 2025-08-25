#!/usr/bin/env python3
"""
Direct Socket.IO Server - Stable WebSocket Architecture
Eliminates Gunicorn completely for robust real-time transcription.
"""

import os
import sys
import logging
from app_refactored import create_app, socketio

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the stable Socket.IO server."""
    host = '0.0.0.0'
    port = 5000
    
    logger.info("🚀 Starting Mina Direct Socket.IO Server")
    logger.info("🎯 WebSocket and HTTP support enabled")
    logger.info(f"🌐 Server: http://{host}:{port}")
    logger.info("📡 Live transcription: /live")
    
    # Create Flask app
    app = create_app()
    
    try:
        # Start Socket.IO server (handles both HTTP and WebSocket)
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Production stability
            use_reloader=False,  # No auto-reload for stability
            log_output=True,  # Request logging
            allow_unsafe_werkzeug=True  # Allow Socket.IO mode
        )
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"❌ Port {port} is already in use!")
            logger.error("💡 Stopping conflicting processes...")
            
            # Try to kill competing processes
            import subprocess
            try:
                subprocess.run(['pkill', '-f', 'gunicorn'], check=False)
                subprocess.run(['pkill', '-f', 'python.*main'], check=False)
                logger.info("🧹 Killed competing processes, retrying...")
                
                # Retry server start
                socketio.run(
                    app,
                    host=host,
                    port=port,
                    debug=False,
                    use_reloader=False,
                    log_output=True,
                    allow_unsafe_werkzeug=True
                )
            except Exception as retry_e:
                logger.error(f"❌ Retry failed: {retry_e}")
                sys.exit(1)
        else:
            logger.error(f"❌ Server error: {e}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()