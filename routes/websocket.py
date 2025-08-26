import time
import json
import traceback
import uuid
from contextlib import contextmanager
from flask import request
from flask_socketio import emit, join_room, disconnect
from app import socketio, db
import logging

# Import services
from services.audio_io import decode_audio_b64, AudioChunkTooLarge, AudioChunkDecodeError
from services.transcription_service import TranscriptionService
from models.session import Session

logger = logging.getLogger(__name__)

# Initialize transcription service
tsvc = TranscriptionService()

# 🔥 INT-LIVE-I2: Simple in-memory rate limiting (swap to Redis if you want x-proc)
_PER_SESSION_RATE = {}  # {session_id: [timestamps...]}

def _rate_ok(session_id: str, now: float, per_minute: int = 600) -> bool:
    """Check if session is within rate limits."""
    win = _PER_SESSION_RATE.setdefault(session_id, [])
    # keep only last 60s
    cutoff = now - 60.0
    while win and win[0] < cutoff:
        win.pop(0)
    if len(win) >= per_minute:
        return False
    win.append(now)
    return True

# --- Session Management Events ---

@contextmanager
def timeout_context(seconds):
    """Context manager for operation timeout protection."""
    import signal
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

@socketio.on('connect')
def on_connect():
    """Handle client connection with enhanced tracking."""
    # Use Flask-SocketIO's built-in session management
    client_id = request.sid if hasattr(request, 'sid') else str(uuid.uuid4())
    connection_time = time.time()
    
    logger.info({
        "event": "client_connected",
        "client_id": client_id,
        "timestamp": connection_time,
        "user_agent": request.headers.get('User-Agent', 'Unknown'),
        "remote_addr": getattr(request, 'remote_addr', 'unknown')
    })
    
    emit('connected', {
        'status': 'Connected to Mina transcription service',
        'client_id': client_id,
        'server_time': connection_time
    })

@socketio.on('disconnect')
def on_disconnect(disconnect_reason=None):
    """Handle client disconnection with cleanup."""
    # Use Flask-SocketIO's built-in session management
    client_id = request.sid if hasattr(request, 'sid') else str(uuid.uuid4())
    disconnect_time = time.time()
    
    logger.info({
        "event": "client_disconnected", 
        "client_id": client_id,
        "reason": disconnect_reason,
        "timestamp": disconnect_time
    })
    
    # Clean up any active sessions for this client
    try:
        tsvc.cleanup_client_sessions(client_id)
    except Exception as e:
        logger.error({
            "event": "cleanup_error",
            "client_id": client_id,
            "error": str(e)
        })

@socketio.on('create_session')
def create_session(data):
    """Create a new transcription session."""
    try:
        payload = data or {}
        title = payload.get('title', 'Untitled Session')
        language = payload.get('language', 'en')
        
        # Create database session
        import uuid
        session = Session(
            title=title,
            locale=language,
            external_id=str(uuid.uuid4())[:8]
        )
        db.session.add(session)
        db.session.commit()
        
        # Initialize transcription service session
        tsvc.start_session_sync(session.external_id, {
            'language': language,
            'title': title
        })
        
        logger.info(f"Created session: {session.external_id}")
        emit('session_created', {
            'session_id': session.external_id,
            'title': title,
            'language': language
        })
        
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        emit('error', {'message': f'Failed to create session: {str(e)}'})

@socketio.on('join_session')
def join_session(data):
    """Join a session room for real-time updates."""
    try:
        session_id = (data or {}).get('session_id')
        if not session_id:
            emit('error', {'message': 'Missing session_id in join_session'})
            return
        
        join_room(session_id)
        logger.info(f"Client {request.sid} joined session room: {session_id}")
        emit('joined_session', {'session_id': session_id})
        
    except Exception as e:
        logger.error(f"Error joining session: {e}")
        emit('error', {'message': 'Failed to join session'})

# --- Audio Processing Events ---

@socketio.on('audio_chunk')
def audio_chunk(data):
    """
    Enhanced audio chunk handler with comprehensive error tracking and timeout protection.
    
    Expected payload:
    {
        "session_id": "abc123",
        "is_final_chunk": false,
        "audio_data_b64": "...",
        "mime_type": "audio/webm", 
        "rms": 0.03,
        "ts_client": 1712345678901,
        "chunk_id": "optional_unique_id"
    }
    """
    start_time = time.time()
    # Use Flask-SocketIO's built-in session management
    client_id = request.sid if hasattr(request, 'sid') else str(uuid.uuid4())
    payload = data or {}
    
    # Extract and validate payload
    session_id = payload.get('session_id')
    chunk_id = payload.get('chunk_id', f"{session_id}_{int(start_time * 1000)}_{uuid.uuid4().hex[:8]}")
    is_final_chunk = bool(payload.get('is_final_chunk', False))
    rms = float(payload.get('rms', 0.0))
    mime_type = payload.get('mime_type') or ""
    client_ts = payload.get('ts_client')

    if not session_id:
        emit('error', {'code': 'MISSING_SESSION_ID', 'message': 'Missing session_id'})
        return
    
    # Validate session is active
    if not tsvc.is_session_active(session_id):
        emit('error', {'code': 'INVALID_SESSION', 'message': 'Session not found or inactive'})
        return
    
    # Rate limiting with enhanced logging
    if not _rate_ok(session_id, start_time):
        logger.warning({
            "event": "rate_limit_exceeded",
            "session_id": session_id,
            "client_id": client_id,
            "timestamp": start_time
        })
        emit('error', {'code': 'RATE_LIMITED', 'message': 'Rate limit exceeded'})
        return
    
    # Decode audio data safely
    raw_bytes = b""
    if payload.get('audio_data_b64'):
        try:
            raw_bytes = decode_audio_b64(payload['audio_data_b64'])
        except AudioChunkTooLarge:
            logger.error({
                "event": "chunk_too_large",
                "session_id": session_id,
                "chunk_id": chunk_id,
                "max_size": "10MB"
            })
            emit('error', {'code': 'CHUNK_TOO_LARGE', 'message': 'Audio chunk too large'})
            return
        except AudioChunkDecodeError as e:
            logger.error({
                "event": "decode_error", 
                "session_id": session_id,
                "chunk_id": chunk_id,
                "error": str(e)
            })
            emit('error', {'code': 'INVALID_AUDIO_DATA', 'message': 'Invalid audio data encoding'})
            return
    
    # Process audio with timeout protection
    try:
        # Log audio chunk processing attempt
        logger.info({
            "event": "audio_chunk_processing_start",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "chunk_size": len(raw_bytes),
            "mime_type": mime_type,
            "rms": rms,
            "is_final": is_final_chunk
        })
        
        with timeout_context(30):  # 30 second max processing time
            result = tsvc.process_audio_sync(
                session_id=session_id,
                audio_data=raw_bytes,
                timestamp=client_ts,
                mime_type=mime_type,
                client_rms=rms,
                is_final_signal=is_final_chunk
            )
            
        logger.info({
            "event": "audio_chunk_processing_success",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "result_keys": list(result.keys()) if result else []
        })
            
        # Send acknowledgment to client
        emit('audio_received', {
            'chunk_id': chunk_id,
            'processing_time_ms': (time.time() - start_time) * 1000,
            'status': 'processed'
        })
            
    except TimeoutError:
        processing_time = (time.time() - start_time) * 1000
        logger.error({
            "event": "processing_timeout",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "processing_time_ms": processing_time,
            "chunk_size": len(raw_bytes)
        })
        emit('error', {'code': 'PROCESSING_TIMEOUT', 'message': 'Audio processing timed out'})
        return
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error({
            "event": "audio_processing_error",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "processing_time_ms": processing_time,
            "chunk_size": len(raw_bytes),
            "mime_type": mime_type,
            "is_final": is_final_chunk
        })
        emit('error', {'code': 'PROCESSING_ERROR', 'message': 'Audio processing failed'})
        return
    
    # Handle transcription results
    if not result or 'transcription' not in result:
        # No transcription result - normal for many chunks
        logger.debug({
            "event": "no_transcription_result",
            "session_id": session_id,
            "chunk_id": chunk_id,
            "chunk_size": len(raw_bytes)
        })
        return
    
    tr = result['transcription']
    txt = (tr.get('text') or '').strip()
    conf = float(tr.get('confidence') or 0.0)
    is_final = bool(tr.get('is_final'))
    processing_time = (time.time() - start_time) * 1000
    
    # Log transcription emission
    logger.info({
        "event": "transcription_result",
        "session_id": session_id,
        "chunk_id": chunk_id,
        "text_length": len(txt),
        "confidence": conf,
        "is_final": is_final,
        "processing_time_ms": processing_time,
        "rms": rms,
        "mime_type": mime_type
    })
    
    if not txt:
        return
    
    # Emit transcription results to session room
    transcript_payload = {
        "session_id": session_id,
        "text": txt,
        "avg_confidence": conf,
        "timestamp": start_time,
        "chunk_id": chunk_id,
        "processing_time_ms": processing_time
    }
    
    if is_final:
        socketio.emit('final_transcript', transcript_payload, room=session_id)
    else:
        socketio.emit('interim_transcript', transcript_payload, room=session_id)

@socketio.on('end_of_stream')
def end_of_stream(data):
    """Handle end of stream signal."""
    try:
        session_id = (data or {}).get('session_id')
        if not session_id:
            emit('error', {'message': 'Missing session_id'})
            return
        
        logger.info({
            "event": "end_of_stream",
            "session_id": session_id,
            "client_id": request.sid,
            "timestamp": time.time()
        })
        
        # End session and get final statistics
        final_stats = tsvc.end_session(session_id)
        
        emit('stream_ended', {
            'session_id': session_id,
            'final_stats': final_stats,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Error ending stream: {e}")
        emit('error', {'message': 'Failed to end stream'})

# --- Error Handling ---

@socketio.on_error_default
def default_error_handler(e):
    """Handle any socketio errors."""
    logger.error(f"SocketIO error: {e}")
    emit('error', {'message': 'An unexpected error occurred'})

# --- Test Events ---

@socketio.on('ping')
def handle_ping():
    """Simple ping/pong for connection testing."""
    emit('pong', {'timestamp': time.time()})

# Function for app.py compatibility
def register_websocket_handlers(socketio_instance):
    """Register websocket handlers with socketio instance."""
    # All handlers are already registered via decorators above
    logger.info("WebSocket handlers registered successfully")
    return socketio_instance