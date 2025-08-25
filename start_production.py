#!/usr/bin/env python3
"""
Alternative production server start script using Gunicorn with Eventlet workers.
This provides the most robust solution for WebSocket + HTTP handling.
"""

import subprocess
import sys
import os

def start_with_eventlet():
    """Start server using Gunicorn with Eventlet workers."""
    
    cmd = [
        'gunicorn',
        '--worker-class', 'eventlet',
        '--workers', '1',  # Single worker for WebSocket state consistency
        '--bind', '0.0.0.0:5000',
        '--timeout', '120',
        '--keepalive', '5',
        '--max-requests', '1000',
        '--log-level', 'info',
        'main:app'
    ]
    
    print("🚀 Starting Mina with Eventlet workers...")
    print("✅ WebSocket compatibility: ENABLED")
    print("✅ Real-time transcription: READY")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_with_eventlet()