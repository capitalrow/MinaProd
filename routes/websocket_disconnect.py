"""
WebSocket Disconnect Handler for CROWN+ Event Chain Enforcement

Ensures that record_stop → transcript_final → session_finalized events are logged
even if the client disconnects before calling finalize_session.

This is critical for the zero-tolerance event chain requirement.
"""

import logging
from datetime import datetime
from flask_socketio import disconnect
from app import socketio
from models import db
from models.session import Session
from services.event_tracking import get_event_tracker

logger = logging.getLogger(__name__)

# Get global event tracker
_event_tracker = get_event_tracker()

# Track active connections per session
_ACTIVE_CONNECTIONS = {}


def register_connection(session_id: str, sid: str):
    """Register a new WebSocket connection for a session."""
    if session_id not in _ACTIVE_CONNECTIONS:
        _ACTIVE_CONNECTIONS[session_id] = set()
    _ACTIVE_CONNECTIONS[session_id].add(sid)
    logger.info(f"📡 Registered connection {sid[:8]} for session {session_id}")


def unregister_connection(session_id: str, sid: str):
    """Unregister a WebSocket connection."""
    if session_id in _ACTIVE_CONNECTIONS:
        _ACTIVE_CONNECTIONS[session_id].discard(sid)
        if not _ACTIVE_CONNECTIONS[session_id]:
            # Last connection for this session closed
            del _ACTIVE_CONNECTIONS[session_id]
            return True  # Was last connection
    return False


@socketio.on('disconnect')
def on_disconnect():
    """
    Handle client disconnect - enforce CROWN+ event chain closure.
    
    If the session was never finalized, this handler will:
    1. Log record_stop event
    2. Log transcript_final event  
    3. Log session_finalized event
    4. Mark session as completed in database
    
    This ensures zero-tolerance event chain integrity.
    """
    from flask import request
    from services.websocket_shutdown import unregister_websocket_connection
    
    sid = request.sid
    
    # Unregister from graceful shutdown tracking
    unregister_websocket_connection(sid)
    
    logger.info(f"📡 Client disconnected: {sid[:8]}")
    
    # Find which session this connection belongs to
    disconnected_session_id = None
    for session_id, connections in list(_ACTIVE_CONNECTIONS.items()):
        if sid in connections:
            disconnected_session_id = session_id
            was_last = unregister_connection(session_id, sid)
            
            if was_last:
                logger.warning(f"⚠️ Last connection for session {session_id} disconnected - enforcing event chain closure")
                
                try:
                    session = db.session.query(Session).filter_by(external_id=session_id).first()
                    
                    if not session:
                        logger.debug(f"📡 No session found for {session_id} on disconnect")
                        return
                    
                    # CROWN+ Zero-Tolerance: Only log closure events if session has trace_id (record_start was called)
                    if not hasattr(session, 'trace_id') or not session.trace_id:
                        logger.warning(f"⚠️ Session {session_id} disconnected without trace_id - no record_start event, skipping closure events")
                        return
                    
                    # Only enforce closure if session is still active (not already finalized)
                    if session.status != 'active':
                        logger.debug(f"📡 Session {session_id} already {session.status}, skipping closure events")
                        return
                    
                    # Session was never finalized - enforce event chain closure
                    logger.error(f"🚨 CROWN+ ENFORCEMENT: Session {session_id} (trace={session.trace_id}) disconnected before finalize - closing event chain")
                    
                    try:
                        # CROWN+ Zero-Tolerance: EventTracker failures are FATAL
                        # Log record_stop
                        _event_tracker.record_stop(
                            session=session,
                            final_duration_ms=0  # Unknown duration
                        )
                        
                        # Log transcript_final
                        _event_tracker.transcript_final(
                            session=session,
                            total_segments=session.total_segments or 0,
                            total_words=0,
                            avg_confidence=0.0
                        )
                        
                        # Log session_finalized
                        _event_tracker.session_finalized(session=session)
                        
                        # Mark session as completed
                        session.status = 'completed'
                        session.completed_at = datetime.utcnow()
                        db.session.commit()
                        
                        logger.info(f"✅ CROWN+ event chain enforced on disconnect for session {session_id}")
                        
                    except Exception as tracker_error:
                        # EventTracker failure is FATAL - rollback and raise
                        db.session.rollback()
                        logger.error(f"❌ FATAL: EventTracker failed on disconnect for session {session_id}: {tracker_error}")
                        raise RuntimeError(f"CROWN+ VIOLATION: Event chain closure failed on disconnect: {tracker_error}") from tracker_error
                        
                except Exception as e:
                    logger.error(f"❌ Failed to enforce event chain on disconnect: {e}")
                    db.session.rollback()
                    # Re-raise to ensure visibility of critical failures
                    raise
            
            break
    
    if not disconnected_session_id:
        logger.debug(f"📡 Disconnect from untracked connection: {sid[:8]}")
