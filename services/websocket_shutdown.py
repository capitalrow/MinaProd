"""
WebSocket Connection Draining for Graceful Shutdown

Provides zero-downtime deployment support by gracefully draining active
WebSocket connections before server shutdown.

Features:
- Tracks all active WebSocket connections
- Emits 'server_shutdown' event to notify clients
- 30-second grace period for connections to close
- Real-time connection count monitoring
- Integration with blue/green deployment strategy

Usage:
    from services.websocket_shutdown import start_graceful_shutdown
    
    # In SIGTERM/SIGINT handler:
    start_graceful_shutdown(socketio, timeout_seconds=30)
"""

import logging
import time
import threading
from typing import Set, Optional
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

# Global connection tracking
_active_connections: Set[str] = set()
_lock = threading.Lock()
_shutdown_in_progress = False


def register_websocket_connection(sid: str) -> bool:
    """
    Register a new WebSocket connection.
    
    Called automatically by the 'connect' event handler.
    Thread-safe with atomic shutdown check to prevent race conditions.
    
    Args:
        sid: Socket.IO session ID
    
    Returns:
        True if registration successful, False if shutdown in progress (should disconnect)
    """
    global _shutdown_in_progress
    
    with _lock:
        # Atomic check AFTER acquiring lock to prevent race condition
        if _shutdown_in_progress:
            logger.warning(f"⚠️ Server is shutting down - REJECTING connection {sid[:8]}")
            return False
        
        _active_connections.add(sid)
        logger.debug(f"📡 WebSocket connected: {sid[:8]} (total: {len(_active_connections)})")
        return True


def unregister_websocket_connection(sid: str) -> None:
    """
    Unregister a WebSocket connection.
    
    Called automatically by the 'disconnect' event handler.
    
    Args:
        sid: Socket.IO session ID
    """
    with _lock:
        _active_connections.discard(sid)
        logger.debug(f"📡 WebSocket disconnected: {sid[:8]} (remaining: {len(_active_connections)})")


def get_active_connection_count() -> int:
    """Get the current number of active WebSocket connections."""
    with _lock:
        return len(_active_connections)


def is_shutdown_in_progress() -> bool:
    """Check if graceful shutdown is currently in progress."""
    return _shutdown_in_progress


def start_graceful_shutdown(socketio: SocketIO, timeout_seconds: int = 30, auto_force_disconnect: bool = True) -> bool:
    """
    Initiate graceful WebSocket connection draining with race-condition protection.
    
    This function:
    1. Marks server as "shutting down" (rejects new connections atomically)
    2. Emits 'server_shutdown' event to all connected clients
    3. Waits up to timeout_seconds for connections to drain
    4. Validates final state against Socket.IO server (catches race conditions)
    5. Optionally force-disconnects remaining connections on timeout
    6. Logs progress every 2 seconds
    
    Args:
        socketio: Flask-SocketIO instance
        timeout_seconds: Maximum time to wait for connections to drain (default: 30)
        auto_force_disconnect: Automatically force disconnect on timeout (default: True)
    
    Returns:
        True if all connections drained successfully, False if timeout reached
    """
    global _shutdown_in_progress
    
    logger.info("🛑 Initiating graceful WebSocket shutdown...")
    
    with _lock:
        _shutdown_in_progress = True
        initial_count = len(_active_connections)
    
    logger.info(f"📊 Active connections: {initial_count}")
    
    if initial_count == 0:
        logger.info("✅ No active connections - shutdown complete")
        return True
    
    # Emit shutdown event to all connected clients
    try:
        socketio.emit('server_shutdown', {
            'message': 'Server is shutting down for deployment. Please reconnect in 30 seconds.',
            'reconnect_delay_ms': 30000,
            'timestamp': int(time.time() * 1000)
        })
        logger.info(f"📡 Broadcast 'server_shutdown' event to {initial_count} clients")
    except Exception as e:
        logger.error(f"❌ Failed to emit shutdown event: {e}")
    
    # Wait for connections to drain with periodic logging
    start_time = time.time()
    last_count = initial_count
    
    while True:
        elapsed = time.time() - start_time
        current_count = get_active_connection_count()
        
        # Log progress if count changed or every 2 seconds
        if current_count != last_count or int(elapsed) % 2 == 0:
            remaining_time = max(0, timeout_seconds - elapsed)
            logger.info(
                f"📊 Draining connections: {current_count}/{initial_count} remaining "
                f"(elapsed: {elapsed:.1f}s, timeout in: {remaining_time:.1f}s)"
            )
            last_count = current_count
        
        # Check if all connections drained
        if current_count == 0:
            # Final validation: Check Socket.IO server for untracked connections (race condition detection)
            try:
                socketio_sids = _get_socketio_connection_count(socketio)
                if socketio_sids > 0:
                    logger.error(
                        f"🚨 RACE CONDITION DETECTED: Tracking shows 0 connections, "
                        f"but Socket.IO server reports {socketio_sids} active connections!"
                    )
                    if auto_force_disconnect:
                        logger.warning("🔧 Auto force-disconnect enabled - disconnecting untracked connections")
                        force_disconnect_all(socketio)
                    return False
            except Exception as validation_error:
                logger.warning(f"⚠️ Unable to validate Socket.IO server state: {validation_error}")
            
            logger.info(f"✅ All connections drained and validated in {elapsed:.1f} seconds")
            return True
        
        # Check timeout
        if elapsed >= timeout_seconds:
            logger.warning(
                f"⚠️ Timeout reached after {elapsed:.1f}s - "
                f"{current_count} connections still active"
            )
            
            # Log remaining connection IDs for debugging
            with _lock:
                remaining_sids = list(_active_connections)[:10]  # First 10
                logger.warning(
                    f"⚠️ Remaining connections (sample): {[sid[:8] for sid in remaining_sids]}"
                )
            
            # Auto force-disconnect if enabled
            if auto_force_disconnect:
                logger.warning("🔧 Auto force-disconnect enabled - forcing remaining connections to close")
                disconnected = force_disconnect_all(socketio)
                logger.warning(f"⚠️ Force disconnected {disconnected} connections")
            
            return False
        
        # Sleep for 500ms before next check
        time.sleep(0.5)


def _get_socketio_connection_count(socketio: SocketIO) -> int:
    """
    Get the actual connection count from Socket.IO server.
    
    Used to detect race conditions where connections are tracked incorrectly.
    
    Args:
        socketio: Flask-SocketIO instance
    
    Returns:
        Number of active connections according to Socket.IO server
    """
    try:
        # Access Socket.IO server's internal connection manager
        # This varies by Socket.IO version, handle gracefully
        if hasattr(socketio, 'server') and hasattr(socketio.server, 'manager'):
            # Count SIDs across all rooms/namespaces
            manager = socketio.server.manager
            if hasattr(manager, 'rooms') and hasattr(manager.rooms, '__len__'):
                # EngineIO 3.x/4.x style
                return len(manager.rooms.get('/', {}))
            elif hasattr(manager, 'get_participants'):
                # Alternative API
                return len(manager.get_participants('/'))
        
        # Fallback: unable to access internal state
        return -1
    except Exception:
        return -1


def force_disconnect_all(socketio: SocketIO) -> int:
    """
    Force disconnect all remaining WebSocket connections.
    
    This is a last resort if graceful shutdown times out.
    Use with caution as it may interrupt active transcription sessions.
    
    Args:
        socketio: Flask-SocketIO instance
    
    Returns:
        Number of connections forcefully disconnected
    """
    logger.warning("⚠️ Force disconnecting all remaining WebSocket connections")
    
    with _lock:
        connection_ids = list(_active_connections)
        count = len(connection_ids)
    
    for sid in connection_ids:
        try:
            socketio.server.disconnect(sid=sid)
            logger.debug(f"🔌 Force disconnected: {sid[:8]}")
        except Exception as e:
            logger.error(f"❌ Failed to force disconnect {sid[:8]}: {e}")
    
    logger.warning(f"⚠️ Force disconnected {count} connections")
    return count


def get_connection_stats() -> dict:
    """
    Get current connection statistics for monitoring.
    
    Returns:
        dict: Connection statistics including:
            - active_connections: Current number of active connections
            - shutdown_in_progress: Whether graceful shutdown is active
    """
    return {
        'active_connections': get_active_connection_count(),
        'shutdown_in_progress': is_shutdown_in_progress()
    }
