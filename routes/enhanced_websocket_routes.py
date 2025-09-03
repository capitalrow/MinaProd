"""
Enhanced WebSocket Routes - Google Recorder Level Integration
Flask routes that expose the enhanced WebSocket handler for production use.
"""

import asyncio
import logging
from flask import Blueprint, jsonify
import websockets
import threading
import socket

logger = logging.getLogger(__name__)

try:
    from .enhanced_websocket_handler import enhanced_websocket_handler
    handler = enhanced_websocket_handler
    logger.info("✅ Using full enhanced WebSocket handler")
except Exception as e:
    logger.warning(f"⚠️ Full enhanced handler failed: {e}, using simple version")
    from .enhanced_websocket_simple import simple_enhanced_websocket_handler
    handler = simple_enhanced_websocket_handler

enhanced_ws_bp = Blueprint('enhanced_websocket', __name__)

# WebSocket server configuration
ENHANCED_WS_HOST = '0.0.0.0'
ENHANCED_WS_PORT = 8765
enhanced_ws_server = None
enhanced_ws_thread = None

def find_available_port(start_port=8765, max_attempts=10):
    """Find an available port starting from start_port."""
    for i in range(max_attempts):
        port = start_port + i
        try:
            # Test if port is available
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result != 0:  # Port is available
                return port
        except Exception:
            continue
    
    return start_port  # Fallback to original port

async def start_enhanced_websocket_server():
    """Start the enhanced WebSocket server."""
    global enhanced_ws_server
    
    try:
        port = find_available_port(ENHANCED_WS_PORT)
        logger.info(f"🚀 Starting Enhanced WebSocket Server on {ENHANCED_WS_HOST}:{port}")
        
        enhanced_ws_server = await websockets.serve(
            handler.handle_connection,
            ENHANCED_WS_HOST,
            port,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=10,
            max_size=1024*1024,  # 1MB max message size
            compression=None  # Disable compression for lower latency
        )
        
        logger.info(f"✅ Enhanced WebSocket Server started successfully on port {port}")
        
        # Keep server running
        await enhanced_ws_server.wait_closed()
        
    except Exception as e:
        logger.error(f"❌ Enhanced WebSocket Server failed to start: {e}")
        raise

def run_enhanced_websocket_server():
    """Run the enhanced WebSocket server in a thread."""
    try:
        asyncio.run(start_enhanced_websocket_server())
    except Exception as e:
        logger.error(f"❌ Enhanced WebSocket Server thread failed: {e}")

def start_enhanced_websocket_server_thread():
    """Start the enhanced WebSocket server in a background thread."""
    global enhanced_ws_thread
    
    if enhanced_ws_thread and enhanced_ws_thread.is_alive():
        logger.warning("⚠️ Enhanced WebSocket Server thread already running")
        return
    
    try:
        enhanced_ws_thread = threading.Thread(
            target=run_enhanced_websocket_server,
            daemon=True,
            name="EnhancedWebSocketServer"
        )
        enhanced_ws_thread.start()
        
        logger.info("🚀 Enhanced WebSocket Server thread started")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Enhanced WebSocket Server thread: {e}")

# HTTP endpoints for WebSocket information

@enhanced_ws_bp.route('/enhanced-ws/info')
def websocket_info():
    """Get enhanced WebSocket server information."""
    try:
        port = find_available_port(ENHANCED_WS_PORT)
        
        return jsonify({
            'enhanced_websocket': {
                'host': ENHANCED_WS_HOST,
                'port': port,
                'url': f'ws://{ENHANCED_WS_HOST}:{port}',
                'status': 'running' if enhanced_ws_thread and enhanced_ws_thread.is_alive() else 'stopped',
                'features': {
                    'google_recorder_level': True,
                    'latency_optimization': True,
                    'context_correlation': True,
                    'progressive_interim': True,
                    'hallucination_prevention': True,
                    'adaptive_quality': True
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket info error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_ws_bp.route('/enhanced-ws/metrics')
def websocket_metrics():
    """Get enhanced WebSocket server metrics."""
    try:
        metrics = handler.get_global_metrics()
        
        return jsonify({
            'metrics': metrics,
            'server_status': {
                'thread_alive': enhanced_ws_thread and enhanced_ws_thread.is_alive(),
                'server_running': enhanced_ws_server is not None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_ws_bp.route('/enhanced-ws/start', methods=['POST'])
def start_websocket_server():
    """Manually start the enhanced WebSocket server."""
    try:
        start_enhanced_websocket_server_thread()
        
        return jsonify({
            'message': 'Enhanced WebSocket Server start initiated',
            'status': 'starting'
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket start error: {e}")
        return jsonify({'error': str(e)}), 500

@enhanced_ws_bp.route('/enhanced-ws/health')
def websocket_health():
    """Health check for enhanced WebSocket server."""
    try:
        is_healthy = (
            enhanced_ws_thread and 
            enhanced_ws_thread.is_alive() and
            enhanced_ws_server is not None
        )
        
        metrics = handler.get_global_metrics()
        
        return jsonify({
            'healthy': is_healthy,
            'status': 'healthy' if is_healthy else 'unhealthy',
            'checks': {
                'thread_running': enhanced_ws_thread and enhanced_ws_thread.is_alive(),
                'server_exists': enhanced_ws_server is not None,
                'low_error_rate': metrics['performance']['error_rate'] < 0.1
            },
            'metrics_summary': {
                'active_connections': metrics['connections']['active'],
                'active_sessions': metrics['connections']['active_sessions'],
                'avg_latency_ms': metrics['performance']['avg_latency_ms'],
                'error_rate': metrics['performance']['error_rate']
            }
        })
        
    except Exception as e:
        logger.error(f"❌ WebSocket health check error: {e}")
        return jsonify({
            'healthy': False,
            'status': 'error',
            'error': str(e)
        }), 500

# Auto-start the enhanced WebSocket server when the blueprint is registered
try:
    start_enhanced_websocket_server_thread()
except Exception as e:
    logger.error(f"❌ Auto-start Enhanced WebSocket Server failed: {e}")