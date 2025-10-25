"""
Socket.IO handlers for live transcription (CROWN+ Event Architecture)
"""
from flask import request
from flask_socketio import emit, join_room
from app import socketio
from models import db
from services.session_service import SessionService
from services.session_event_coordinator import get_session_event_coordinator
import logging
import time

logger = logging.getLogger(__name__)

# Session state tracking
active_sessions = {}  # sid -> session_id mapping

@socketio.on('connect', namespace='/live-transcription')
def handle_connect():
    """Client connected to /live-transcription namespace"""
    logger.info(f"Client connected to live transcription: {request.sid}")
    emit('connected', {'status': 'connected', 'message': 'Ready for live transcription'})

@socketio.on('disconnect', namespace='/live-transcription')
def handle_disconnect():
    """Client disconnected from /live-transcription namespace"""
    sid = request.sid
    logger.info(f"Client disconnected from live transcription: {sid}")
    
    # Clean up session tracking
    if sid in active_sessions:
        del active_sessions[sid]

@socketio.on('start_session', namespace='/live-transcription')
def handle_start_session(data):
    """
    Start a new transcription session (CROWN+ record_start event).
    Creates session in database and emits standardized events.
    """
    sid = request.sid
    title = data.get('title', 'Untitled Meeting')
    
    logger.info(f"Starting transcription session: {title}")
    
    try:
        # Create session in database (generates trace_id automatically)
        session_id = SessionService.create_session(
            title=title,
            locale=data.get('locale', 'en'),
            device_info=data.get('device_info')
        )
        
        # Get session object with trace_id
        session = SessionService.get_session_by_id(session_id)
        if not session:
            emit('error', {'message': 'Failed to create session'})
            return
        
        # Track active session
        active_sessions[sid] = session.id
        
        # Join Socket.IO room for this session
        join_room(session.external_id)
        
        # Emit record_start event via coordinator (dual emission for backward compatibility)
        coordinator = get_session_event_coordinator()
        coordinator.emit_record_start(
            session=session,
            room=session.external_id,
            metadata={
                'client_sid': sid,
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
        )
        
        logger.info(f"✅ Session {session.external_id} started [trace={str(session.trace_id)[:8]}]")
        
    except Exception as e:
        logger.error(f"❌ Failed to start session: {e}", exc_info=True)
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('audio_data', namespace='/live-transcription')
def handle_audio_data(data):
    """Receive audio data for transcription"""
    logger.debug(f"Received audio data: {len(data.get('data', [])) if isinstance(data, dict) else 0} bytes")
    # TODO: Process audio and emit transcript_partial results
    # For now, just acknowledge receipt
    emit('audio_received', {'status': 'ok'})

@socketio.on('end_session', namespace='/live-transcription')
def handle_end_session(data=None):
    """
    End the transcription session (CROWN+ session_finalized event).
    Finalizes session and triggers post-transcription orchestration.
    """
    sid = request.sid
    logger.info(f"Ending transcription session for client {sid}")
    
    if sid not in active_sessions:
        logger.warning(f"No active session for client {sid}")
        emit('error', {'message': 'No active session to end'})
        return
    
    try:
        session_id = active_sessions[sid]
        session = SessionService.get_session_by_id(session_id)
        
        if not session:
            emit('error', {'message': 'Session not found'})
            return
        
        # Finalize session - this triggers:
        # 1. session_finalized event
        # 2. PostTranscriptionOrchestrator (async)
        success = SessionService.finalize_session(
            session_id=session_id,
            room=session.external_id,
            metadata={
                'client_sid': sid,
                'ended_by': 'user'
            }
        )
        
        if success:
            logger.info(f"✅ Session {session.external_id} finalized [trace={str(session.trace_id)[:8]}]")
            # Clean up tracking
            del active_sessions[sid]
        else:
            emit('error', {'message': 'Failed to finalize session'})
            
    except Exception as e:
        logger.error(f"❌ Failed to end session: {e}", exc_info=True)
        emit('error', {'message': f'Failed to end session: {str(e)}'})

def register_live_socketio():
    """Register the live transcription Socket.IO handlers"""
    logger.info("✅ Live transcription Socket.IO handlers registered (CROWN+ events)")
