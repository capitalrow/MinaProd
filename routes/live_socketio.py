"""
Socket.IO handlers for live transcription (CROWN+ Event Architecture)
"""
from flask import request
from flask_socketio import emit, join_room
from app import socketio
from models import db
from services.session_service import SessionService
from services.session_event_coordinator import get_session_event_coordinator
from services.live_transcription_service import get_live_transcription_service
from datetime import datetime
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
    
    # Finalize session if it was active
    if sid in active_sessions:
        try:
            session_id = active_sessions[sid]
            session = SessionService.get_session_by_id(session_id)
            
            if session and session.status not in ['completed', 'finalized']:
                logger.warning(f"Client disconnected mid-recording, finalizing session {session.external_id}")
                # Finalize session to prevent orphaned records
                SessionService.finalize_session(
                    session_id=session_id,
                    room=session.external_id,
                    metadata={
                        'client_sid': sid,
                        'ended_by': 'disconnect',
                        'reason': 'Client disconnected'
                    }
                )
        except Exception as e:
            logger.error(f"Error finalizing session on disconnect: {e}", exc_info=True)
        finally:
            # Always clean up tracking
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
        
        # ALSO emit directly to caller for guaranteed delivery
        emit('record_start', {
            'external_id': session.external_id,
            'session_id': session.id,
            'status': 'recording',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ Session {session.external_id} started [trace={str(session.trace_id)[:8]}]")
        
    except Exception as e:
        logger.error(f"❌ Failed to start session: {e}", exc_info=True)
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('audio_data', namespace='/live-transcription')
def handle_audio_data(data):
    """Receive audio data and transcribe using OpenAI Whisper"""
    sid = request.sid
    
    if sid not in active_sessions:
        logger.warning(f"Received audio from unregistered session: {sid}")
        return
    
    try:
        session_id = active_sessions[sid]
        session = SessionService.get_session_by_id(session_id)
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        # Extract audio data
        audio_bytes = data.get('data')
        mime_type = data.get('mimeType', 'audio/webm')
        
        if not audio_bytes:
            logger.warning("No audio data in chunk")
            return
        
        # Convert to bytes if needed
        if isinstance(audio_bytes, (list, dict)):
            import base64
            if isinstance(audio_bytes, dict):
                audio_bytes = base64.b64decode(audio_bytes.get('data', ''))
            else:
                audio_bytes = bytes(audio_bytes)
        
        logger.info(f"📥 Processing {len(audio_bytes)} bytes of audio for session {session.external_id}")
        
        # Initialize chunk counter for this session
        if not hasattr(handle_audio_data, 'chunk_counters'):
            handle_audio_data.chunk_counters = {}
        if not hasattr(handle_audio_data, 'session_start_times'):
            handle_audio_data.session_start_times = {}
        
        counter_key = f"chunk_count_{session.id}"
        start_time_key = f"start_time_{session.id}"
        
        # Track session start time
        if start_time_key not in handle_audio_data.session_start_times:
            handle_audio_data.session_start_times[start_time_key] = time.time()
        
        chunk_count = handle_audio_data.chunk_counters.get(counter_key, 0) + 1
        handle_audio_data.chunk_counters[counter_key] = chunk_count
        
        # Calculate elapsed time for timestamps
        elapsed_ms = int((time.time() - handle_audio_data.session_start_times[start_time_key]) * 1000)
        
        # Get transcription service
        transcription_service = get_live_transcription_service()
        
        # Transcribe every chunk, but treat every 2nd chunk as final
        is_final = (chunk_count % 2 == 0)
        
        # Call OpenAI Whisper API
        result = transcription_service.transcribe_audio_chunk(
            audio_bytes=audio_bytes,
            mime_type=mime_type,
            is_interim=not is_final
        )
        
        if not result or not result.get('text'):
            logger.debug("Empty transcription result, skipping")
            return
        
        text = result['text']
        confidence = result.get('confidence', 0.85)
        
        # Emit appropriate event based on whether it's final or interim
        if is_final:
            # Emit final segment
            emit('transcript_segment', {
                'text': text,
                'speaker': 'Speaker 1',  # TODO: Add speaker diarization
                'speaker_id': 1,
                'timestamp': datetime.now().isoformat(),
                'is_final': True,
                'confidence': confidence
            }, room=session.external_id)
            
            # Store final segment in database
            try:
                from models import Segment
                segment = Segment(
                    session_id=session.id,
                    kind='final',  # Use correct schema field
                    text=text,
                    avg_confidence=confidence,
                    start_ms=elapsed_ms - 2000,  # Approximate 2 second chunk
                    end_ms=elapsed_ms,
                    created_at=datetime.utcnow()
                )
                db.session.add(segment)
                db.session.commit()
                logger.info(f"✅ Stored final segment: '{text[:50]}...'")
            except Exception as e:
                logger.error(f"❌ Failed to store segment: {e}", exc_info=True)
                db.session.rollback()
        else:
            # Emit interim (partial) result
            emit('transcript_partial', {
                'text': text,
                'speaker': 'Speaker 1',
                'speaker_id': 1,
                'timestamp': datetime.now().isoformat(),
                'is_final': False,
                'confidence': confidence
            }, room=session.external_id)
            
            # Optionally store interim segments for better context
            try:
                from models import Segment
                segment = Segment(
                    session_id=session.id,
                    kind='interim',  # Use correct schema field
                    text=text,
                    avg_confidence=confidence,
                    start_ms=elapsed_ms - 1000,
                    end_ms=elapsed_ms,
                    created_at=datetime.utcnow()
                )
                db.session.add(segment)
                db.session.commit()
                logger.debug(f"📝 Stored interim segment: '{text[:50]}...'")
            except Exception as e:
                logger.error(f"⚠️ Failed to store interim segment: {e}")
                db.session.rollback()
        
    except Exception as e:
        logger.error(f"❌ Error processing audio data: {e}", exc_info=True)
        # Emit error to client
        emit('error', {'message': f'Transcription error: {str(e)}'})

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
