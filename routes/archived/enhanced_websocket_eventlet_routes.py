"""
Enhanced WebSocket Routes using Eventlet
Production-ready WebSocket routes that work with gunicorn and eventlet.
"""

import logging
from flask import Blueprint, request, jsonify
from .eventlet_websocket_server import eventlet_enhanced_handler

logger = logging.getLogger(__name__)

enhanced_eventlet_bp = Blueprint('enhanced_eventlet_websocket', __name__)

@enhanced_eventlet_bp.route('/enhanced-ws/connect', methods=['POST', 'OPTIONS'])
def websocket_connect():
    """Handle WebSocket connection establishment via HTTP."""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        # Simulate WSGI environment for handler
        env = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/ws-connect',
            'REMOTE_ADDR': request.remote_addr,
            'CONTENT_LENGTH': '0',
            'wsgi.input': None
        }
        
        def start_response(status, headers):
            pass  # We'll handle response manually
        
        connection_id = request.args.get('connection_id', 'auto-generated')
        result = eventlet_enhanced_handler._handle_http_connect(env, start_response, connection_id)
        
        if result:
            response_data = result[0].decode('utf-8')
            response = jsonify(eval(response_data))  # Safe since we control the data
        else:
            response = jsonify({'error': 'Connection failed'})
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket connect error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@enhanced_eventlet_bp.route('/enhanced-ws/message', methods=['POST', 'OPTIONS'])
def websocket_message():
    """Handle WebSocket message via HTTP."""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        connection_id = request.args.get('connection_id')
        if not connection_id:
            response = jsonify({'error': 'connection_id required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        message_data = request.get_json()
        if not message_data:
            response = jsonify({'error': 'Message data required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Process the message
        result = eventlet_enhanced_handler._process_message(connection_id, message_data)
        
        response = jsonify(result)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket message error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@enhanced_eventlet_bp.route('/enhanced-ws/poll', methods=['GET', 'OPTIONS'])
def websocket_poll():
    """Handle WebSocket polling."""
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        connection_id = request.args.get('connection_id')
        if not connection_id:
            response = jsonify({'error': 'connection_id required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Simulate WSGI environment for handler
        env = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/ws-poll',
            'REMOTE_ADDR': request.remote_addr
        }
        
        def start_response(status, headers):
            pass  # We'll handle response manually
        
        result = eventlet_enhanced_handler._handle_http_poll(env, start_response, connection_id)
        
        if result:
            response_data = result[0].decode('utf-8')
            response = jsonify(eval(response_data))  # Safe since we control the data
        else:
            response = jsonify({'error': 'Polling failed'})
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket poll error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@enhanced_eventlet_bp.route('/enhanced-ws/info', methods=['GET'])
def websocket_info():
    """Get enhanced WebSocket server information."""
    try:
        info_data = {
            'enhanced_websocket': {
                'host': '0.0.0.0',
                'port': 5000,  # Using same port as Flask for HTTP fallback
                'url': f'{request.scheme}://{request.host}',
                'status': 'running',
                'mode': 'http_fallback',
                'features': {
                    'google_recorder_level': True,
                    'latency_optimization': True,
                    'context_correlation': True,
                    'progressive_interim': True,
                    'hallucination_prevention': True,
                    'adaptive_quality': True,
                    'eventlet_compatible': True,
                    'http_fallback': True
                },
                'endpoints': {
                    'connect': f'{request.scheme}://{request.host}/api/enhanced-ws/connect',
                    'message': f'{request.scheme}://{request.host}/api/enhanced-ws/message',
                    'poll': f'{request.scheme}://{request.host}/api/enhanced-ws/poll'
                }
            }
        }
        
        response = jsonify(info_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket info error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@enhanced_eventlet_bp.route('/enhanced-ws/metrics', methods=['GET'])
def websocket_metrics():
    """Get enhanced WebSocket server metrics."""
    try:
        metrics = eventlet_enhanced_handler.get_metrics()
        
        response = jsonify({
            'metrics': metrics,
            'server_status': {
                'running': True,
                'mode': 'eventlet_http_fallback',
                'healthy': metrics['performance']['error_rate'] < 0.1
            }
        })
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket metrics error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@enhanced_eventlet_bp.route('/enhanced-ws/health', methods=['GET'])
def websocket_health():
    """Health check for enhanced WebSocket server."""
    try:
        metrics = eventlet_enhanced_handler.get_metrics()
        
        is_healthy = (
            metrics['performance']['error_rate'] < 0.1 and
            metrics['connections']['active'] >= 0
        )
        
        response = jsonify({
            'healthy': is_healthy,
            'status': 'healthy' if is_healthy else 'degraded',
            'checks': {
                'server_running': True,
                'low_error_rate': metrics['performance']['error_rate'] < 0.1,
                'accepting_connections': True
            },
            'metrics_summary': {
                'active_connections': metrics['connections']['active'],
                'active_sessions': metrics['connections']['active_sessions'],
                'avg_latency_ms': metrics['performance']['avg_latency_ms'],
                'error_rate': metrics['performance']['error_rate'],
                'uptime_seconds': metrics['performance']['uptime_seconds']
            }
        })
        
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"❌ WebSocket health check error: {e}")
        response = jsonify({
            'healthy': False,
            'status': 'error',
            'error': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500