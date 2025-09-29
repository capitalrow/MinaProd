# routes/transcription_websocket.py
"""
WebSocket handlers specifically for the /transcription namespace
"""
import logging
import time
import uuid
import base64
import requests
import threading
from datetime import datetime

from flask import session
from flask_socketio import emit, disconnect, join_room, leave_room
from flask_login import current_user

# Import the socketio instance from the consolidated app
from app import socketio

# Import advanced buffer management
from services.session_buffer_manager import buffer_registry, BufferConfig

# Import database models for persistence
from models import db
from models.session import Session
from models.segment import Segment

# Import critical database session cleanup decorator
from utils.db_helpers import socketio_db_cleanup

logger = logging.getLogger(__name__)

# Session state storage with advanced buffering
active_sessions = {}
buffer_config = BufferConfig(
    max_buffer_ms=30000,
    min_flush_ms=2000,
    max_flush_ms=8000,
    enable_vad=True,
    enable_quality_gating=True
)

# Background processing worker
processing_workers = {}

def _background_processor(session_id: str, buffer_manager):
    """Simple background worker for processing buffered audio chunks"""
    logger.info(f"🔧 Started background processor for session {session_id}")
    
    try:
        while session_id in active_sessions:
            time.sleep(1)  # Simple polling interval
            # Basic background processing - can be enhanced later
            if session_id not in active_sessions:
                break
                
    except Exception as e:
        logger.error(f"Background processor error for session {session_id}: {e}")
    finally:
        logger.info(f"🔧 Background processor stopped for session {session_id}")

@socketio.on('connect', namespace='/transcription')
@socketio_db_cleanup
def on_connect(auth=None):
    """Handle client connection to transcription namespace with authentication"""
    # Check authentication - require valid user session
    if not current_user.is_authenticated:
        logger.warning(f"[transcription] Unauthenticated connection attempt")
        emit('error', {'message': 'Authentication required'})
        disconnect()
        return False
    
    logger.info(f"[transcription] Authenticated client connected (user: {current_user.id})")
    join_room(f"user_{current_user.id}")
    emit('status', {
        'status': 'connected', 
        'message': 'Connected to transcription service',
        'user_id': current_user.id
    })

@socketio.on('disconnect', namespace='/transcription')
@socketio_db_cleanup
def on_disconnect():
    """Handle client disconnection with comprehensive cleanup"""
    logger.info(f"[transcription] Client disconnected")
    # Clean up only sessions for this specific socket connection
    sessions_to_remove = []
    for session_id, session_info in active_sessions.items():
        if session_info.get('socket_id') == session.get('socket_id'):
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        # Comprehensive session cleanup
        session_info = active_sessions.get(session_id, {})
        
        # End buffer manager session
        if 'buffer_manager' in session_info:
            buffer_manager = session_info['buffer_manager']
            buffer_manager.end_session()
        
        # Release from buffer registry  
        buffer_registry.release(session_id)
        
        # Terminate processing thread if exists
        if session_id in processing_workers:
            worker = processing_workers[session_id]
            logger.info(f"[transcription] Terminating processing thread for session: {session_id}")
            # The thread will terminate when session is removed from active_sessions
            processing_workers.pop(session_id, None)
        
        # Complete session in database before cleanup
        if 'db_session_id' in session_info:
            try:
                db_session_record = db.session.get(Session, session_info['db_session_id'])
                if db_session_record:
                    db_session_record.complete()
                    db.session.commit()
                    logger.info(f"✅ [database] Completed session: {db_session_record.id}")
                    
                    # Broadcast session completion to user's dashboard room
                    socketio.emit('session_completed', {
                        'session_id': db_session_record.id,
                        'external_id': session_info.get('external_id'),
                        'user_id': session_info.get('user_id')
                    }, namespace='/dashboard', to=f'user_{session_info.get("user_id")}')
            except Exception as e:
                logger.error(f"Error completing session in database: {e}")
        
        # Remove from active sessions
        active_sessions.pop(session_id, None)
        logger.info(f"[transcription] Comprehensive cleanup completed for session: {session_id}")

@socketio.on('start_session', namespace='/transcription')
@socketio_db_cleanup
def on_start_session(data):
    """Start a new transcription session with database persistence"""
    try:
        # Generate session IDs
        session_id = str(uuid.uuid4())
        external_id = Session.generate_external_id()
        
        # Create database session record
        db_session = Session(
            external_id=external_id,
            title=data.get('title', 'Live Recording Session'),
            status='active',
            locale=data.get('language', 'en'),
            device_info=data.get('device_info', {}),
            meta={'created_via': 'websocket', 'user_id': current_user.id}
        )
        
        # Save to database
        db.session.add(db_session)
        db.session.commit()
        
        logger.info(f"✅ [database] Created session record: {db_session.id} (external: {external_id})")
        
        # Store session info with advanced buffer manager
        buffer_manager = buffer_registry.get_or_create_session(session_id)
        
        active_sessions[session_id] = {
            'user_id': current_user.id,
            'socket_id': f'user_{current_user.id}',  # Use user_id as socket identifier
            'db_session_id': db_session.id,
            'external_id': external_id,
            'started_at': datetime.utcnow(),
            'language': data.get('language', 'en'),
            'enhance_audio': data.get('enhance_audio', True),
            'buffer_manager': buffer_manager,
            'audio_buffer': bytearray(),
            'webm_header': None,
            'last_process_time': 0
        }
        
        # Start background processing worker for this session
        worker = threading.Thread(
            target=_background_processor,
            args=(session_id, buffer_manager),
            daemon=True
        )
        worker.start()
        processing_workers[session_id] = worker
        
        # Join the session room
        join_room(session_id)
        
        logger.info(f"[transcription] Started session: {session_id}")
        
        # Broadcast to user's dashboard room for real-time updates
        socketio.emit('session_created', {
            'session_id': db_session.id,
            'external_id': external_id,
            'title': db_session.title,
            'status': 'active',
            'user_id': current_user.id
        }, namespace='/dashboard', to=f'user_{current_user.id}')
        
        emit('session_started', {
            'session_id': session_id,
            'db_session_id': db_session.id,
            'external_id': external_id,
            'status': 'ready',
            'message': 'Transcription session started'
        })
        
    except Exception as e:
        logger.error(f"[transcription] Error starting session: {e}")
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('audio_data', namespace='/transcription')
@socketio_db_cleanup
def on_audio_data(data):
    """Handle incoming audio data"""
    try:
        # Enhanced audio data handling with robust format detection
        if isinstance(data, dict) and 'data' in data:
            # Structured format with metadata
            try:
                audio_bytes = base64.b64decode(data['data'])
                mime_type = data.get('mimeType', 'audio/webm')
                data_size = data.get('size', len(audio_bytes))
                
                logger.info(f"[transcription] Received {mime_type} audio: {len(audio_bytes)} bytes (reported: {data_size})")
                
                # Validate audio data integrity
                if len(audio_bytes) < 100:
                    logger.warning(f"[transcription] Audio chunk too small: {len(audio_bytes)} bytes")
                    return  # Skip small chunks silently
                    
                # Detect format discrepancies
                if abs(len(audio_bytes) - data_size) > 100:
                    logger.warning(f"[transcription] Size mismatch: actual={len(audio_bytes)}, reported={data_size}")
                    
            except Exception as e:
                logger.error(f"[transcription] Failed to decode structured audio: {e}")
                emit('error', {'message': 'Invalid audio data format'})
                return
                
        elif isinstance(data, str):
            # Legacy base64 string format
            try:
                audio_bytes = base64.b64decode(data)
                mime_type = 'audio/webm'
                logger.info(f"[transcription] Legacy format: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.error(f"[transcription] Invalid base64 audio data: {e}")
                emit('error', {'message': 'Invalid base64 audio data'})
                return
                
        elif isinstance(data, (bytes, bytearray)):
            # Raw bytes format
            audio_bytes = bytes(data)
            mime_type = 'audio/webm'
            logger.info(f"[transcription] Raw bytes: {len(audio_bytes)} bytes")
        else:
            logger.error(f"[transcription] Unsupported data type: {type(data)}")
            emit('error', {'message': 'Unsupported audio data format'})
            return
        
        # Find the current session for this user
        session_id = None
        for sid, session_info in active_sessions.items():
            if session_info.get('user_id') == current_user.id:
                session_id = sid
                break
        
        if not session_id:
            emit('error', {'message': 'No active session found'})
            return
        
        # 🔥 CRITICAL FIX: Buffer chunks and reconstruct proper WebM containers
        session_info = active_sessions[session_id]
        
        # Initialize WebM reconstruction data
        if 'webm_header' not in session_info:
            session_info['webm_header'] = None
            session_info['last_process_time'] = 0
            
        # Detect and store EBML header from first chunk
        if session_info['webm_header'] is None and len(audio_bytes) > 12:
            if audio_bytes[:4] == b'\x1a\x45\xdf\xa3':  # EBML signature
                session_info['webm_header'] = audio_bytes
                logger.info(f"🎯 [transcription] Captured WebM header chunk: {len(audio_bytes)} bytes")
            
        # Buffer the audio chunk
        session_info['audio_buffer'].extend(audio_bytes)
        buffer_size = len(session_info['audio_buffer'])
        
        # Process buffered audio more frequently for real-time transcription
        current_time = time.time()
        should_process = (
            buffer_size > 30000 or 
            (buffer_size > 5000 and current_time - session_info['last_process_time'] > 2)
        )
        
        if should_process:
            # Reconstruct proper WebM container
            if session_info['webm_header'] and len(session_info['audio_buffer']) > len(session_info['webm_header']):
                # Create proper WebM by ensuring EBML header is present
                if session_info['audio_buffer'][:4] != b'\x1a\x45\xdf\xa3':
                    reconstructed_audio = session_info['webm_header'] + bytes(session_info['audio_buffer'])
                    logger.info(f"🔧 [transcription] Reconstructed WebM with header: {len(reconstructed_audio)} bytes")
                else:
                    reconstructed_audio = bytes(session_info['audio_buffer'])
            else:
                reconstructed_audio = bytes(session_info['audio_buffer'])
        
            try:
                # Send reconstructed audio to transcription API
                file_extension = '.wav' if 'wav' in mime_type else '.webm'
                response = requests.post(
                    'http://localhost:5000/api/transcribe-audio',
                    files={'audio': (f'audio{file_extension}', reconstructed_audio, mime_type)},
                    data={
                        'session_id': session_id,
                        'is_interim': 'true',
                        'chunk_id': str(int(time.time() * 1000))
                    },
                    timeout=10
                )
            
                if response.status_code == 200:
                    result = response.json()
                    text = result.get('final_text', '') or result.get('text', '')
                    if text and text.strip():
                        # Save segment to database
                        db_session_id = session_info['db_session_id']
                        segment = Segment(
                            session_id=db_session_id,
                            kind='final' if result.get('is_final', True) else 'interim',
                            text=text,
                            avg_confidence=result.get('confidence', 0.9),
                            start_ms=result.get('start_ms'),
                            end_ms=result.get('end_ms')
                        )
                        
                        db.session.add(segment)
                        db.session.commit()
                        
                        logger.info(f"✅ [database] Saved segment: {segment.id}")
                        
                        # Emit properly formatted transcription result
                        transcription_data = {
                            'text': text,
                            'is_final': result.get('is_final', True),
                            'confidence': result.get('confidence', 0.9),
                            'timestamp': int(time.time() * 1000),
                            'speaker_id': result.get('speaker_id', 'Speaker 1'),
                            'processing_time_ms': result.get('processing_time_ms', 100),
                            'segment_id': segment.id,
                            'session_id': db_session_id
                        }
                        
                        emit('transcription_result', transcription_data)
                        
                        # Broadcast to user's dashboard room for real-time updates
                        socketio.emit('transcription_update', {
                            'session_id': db_session_id,
                            'segment_id': segment.id,
                            'text': text,
                            'is_final': segment.is_final,
                            'user_id': current_user.id
                        }, namespace='/dashboard', to=f'user_{current_user.id}')
                        
                        logger.info(f"✅ [transcription] Emitted result: '{text[:50]}...'")
                    else:
                        logger.debug(f"📝 [transcription] Empty result, skipping emission")
                        pass
                else:
                    logger.warning(f"[transcription] API error: {response.status_code}")
                    
            except requests.RequestException as e:
                logger.error(f"[transcription] API request failed: {e}")
                # Don't emit error for network issues, just log them
            
            # Reset buffer with some overlap for context continuity
            overlap_size = min(5000, len(session_info['audio_buffer']) // 3)
            session_info['audio_buffer'] = session_info['audio_buffer'][-overlap_size:]
            session_info['last_process_time'] = current_time
            logger.info(f"🔄 [transcription] Buffer reset, kept {overlap_size} bytes overlap")
        
    except Exception as e:
        logger.error(f"[transcription] Error processing audio: {e}")
        emit('error', {'message': f'Audio processing error: {str(e)}'})

@socketio.on('end_session', namespace='/transcription')
@socketio_db_cleanup
def on_end_session(data=None):
    """End the current transcription session"""
    try:
        # Find sessions for this client
        sessions_to_end = []
        for session_id, session_info in active_sessions.items():
            if session_info.get('user_id') == getattr(current_user, 'id', None):
                sessions_to_end.append(session_id)
        
        for session_id in sessions_to_end:
            # Leave the room
            leave_room(session_id)
            
            # Clean up session
            active_sessions.pop(session_id, None)
            
            logger.info(f"[transcription] Ended session: {session_id}")
            
            emit('session_ended', {
                'session_id': session_id,
                'status': 'completed',
                'message': 'Transcription session ended'
            })
        
    except Exception as e:
        logger.error(f"[transcription] Error ending session: {e}")
        emit('error', {'message': f'Failed to end session: {str(e)}'})

logger.info("✅ Transcription WebSocket namespace handlers registered")