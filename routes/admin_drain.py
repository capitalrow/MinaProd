"""
Admin Endpoints for WebSocket Connection Draining

Provides endpoints for manual connection draining during blue/green deployments.
These endpoints are authenticated and require admin privileges.
"""

import logging
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from services.websocket_shutdown import (
    get_connection_stats,
    start_graceful_shutdown,
    force_disconnect_all,
    get_active_connection_count
)
from app import socketio

logger = logging.getLogger(__name__)

admin_drain_bp = Blueprint('admin_drain', __name__)


def require_admin():
    """Decorator to require admin privileges."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    if not current_user.is_admin:
        return jsonify({'error': 'Admin privileges required'}), 403
    
    return None  # Auth passed


@admin_drain_bp.route('/admin/drain', methods=['POST'])
@login_required
def trigger_drain():
    """
    Manually trigger graceful WebSocket connection draining.
    
    This endpoint is used during blue/green deployments to drain connections
    before switching traffic to the new environment.
    
    Requires admin authentication (no header-based bypass).
    
    Returns:
        JSON response with drain status and connection count
    """
    # Check admin privileges
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    logger.info(f"🔧 Admin drain triggered by user {current_user.username}")
    
    # Get initial connection count
    initial_count = get_active_connection_count()
    
    if initial_count == 0:
        return jsonify({
            'status': 'no_connections',
            'message': 'No active connections to drain',
            'initial_connections': 0,
            'final_connections': 0,
            'drained': 0
        }), 200
    
    # Start graceful shutdown with 30-second timeout
    success = start_graceful_shutdown(socketio, timeout_seconds=30)
    
    final_count = get_active_connection_count()
    drained_count = initial_count - final_count
    
    if success:
        logger.info(f"✅ Admin drain successful: {drained_count} connections drained")
        return jsonify({
            'status': 'success',
            'message': f'Successfully drained {drained_count} connections',
            'initial_connections': initial_count,
            'final_connections': 0,
            'drained': drained_count,
            'timeout_reached': False
        }), 200
    else:
        logger.warning(f"⚠️ Admin drain timeout: {drained_count}/{initial_count} drained, {final_count} remaining")
        return jsonify({
            'status': 'timeout',
            'message': f'Timeout reached after 30 seconds - {final_count} connections still active',
            'initial_connections': initial_count,
            'final_connections': final_count,
            'drained': drained_count,
            'timeout_reached': True
        }), 200  # Still 200 since drain was initiated successfully


@admin_drain_bp.route('/admin/drain/force', methods=['POST'])
@login_required
def trigger_force_disconnect():
    """
    Force disconnect all WebSocket connections immediately.
    
    This is a last resort if graceful draining times out.
    Use with caution as it will interrupt active transcription sessions.
    
    Requires admin authentication.
    
    Returns:
        JSON response with number of connections forcefully disconnected
    """
    # Check admin privileges
    auth_error = require_admin()
    if auth_error:
        return auth_error
    
    logger.warning(f"🔧 Force disconnect triggered by user {current_user.username}")
    
    # Get initial count
    initial_count = get_active_connection_count()
    
    if initial_count == 0:
        return jsonify({
            'status': 'no_connections',
            'message': 'No active connections to disconnect',
            'disconnected': 0
        }), 200
    
    # Force disconnect all
    disconnected_count = force_disconnect_all(socketio)
    
    logger.warning(f"⚠️ Force disconnected {disconnected_count} connections")
    
    return jsonify({
        'status': 'success',
        'message': f'Force disconnected {disconnected_count} connections',
        'disconnected': disconnected_count
    }), 200


@admin_drain_bp.route('/api/metrics/connections', methods=['GET'])
def get_connection_metrics():
    """
    Get current WebSocket connection metrics.
    
    Public endpoint for monitoring connection count during deployments.
    
    Returns:
        JSON response with active connection count and shutdown status
    """
    stats = get_connection_stats()
    
    return jsonify({
        'active_connections': stats['active_connections'],
        'shutdown_in_progress': stats['shutdown_in_progress'],
        'timestamp': int(time.time() * 1000)
    }), 200


# Import time for timestamp
import time
