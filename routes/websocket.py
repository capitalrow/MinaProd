import time
import json
from flask import request
from flask_socketio import Namespace, emit, join_room, disconnect
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

@socketio.on('connect')
def on_connect():
    """Handle client connection."""
    client_id = request.sid
    logger.info(f"Client connected: {client_id}")
    emit('connected', {'status': 'Connected to Mina transcription service'})

@socketio.on('disconnect')
def on_disconnect(disconnect_reason=None):
    """Handle client disconnection."""
    client_id = request.sid
    logger.info(f"Client disconnected: {client_id} (reason: {disconnect_reason})")

@socketio.on('create_session')
def create_session(data):
    """Create a new transcription session."""
    try:
        payload = data or {}
        title = payload.get('title', 'Untitled Session')
        language = payload.get('language', 'en')
        
        # Create database session
        session = Session(
            title=title,
            language=language,
            external_id=Session.generate_external_id()
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
        logger.error(f"Error creating session: {e}")
        emit('error', {'message': 'Failed to create session'})

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
    🔥 INT-LIVE-I2: Complete audio chunk handler with safe base64 decode and rate limiting.
    
    Expected payload:
    {
        "session_id": "abc123",
        "is_final_chunk": false,  # 🔥 Fixed: defaults to False
        "audio_data_b64": "...",  # may be null/empty when signaling final only
        "mime_type": "audio/webm",
        "rms": 0.03,              # 🔥 Client-side RMS from WebAudio
        "ts_client": 1712345678901
    }
    """
    now = time.time()
    payload = data or {}
    session_id = payload.get('session_id')
    is_final_chunk = bool(payload.get('is_final_chunk', False))  # 🔥 Fixed default
    rms = float(payload.get('rms', 0.0))
    mime_type = payload.get('mime_type') or ""
    client_ts = payload.get('ts_client')

    if not session_id:
        emit('error', {'message': 'Missing session_id'})
        return
    
    # 🔥 INT-LIVE-I2: Basic rate limiting per session (very lightweight)
    if not _rate_ok(session_id, now):
        emit('error', {'message': 'Rate limit exceeded'})
        # 🔥 Track rate limit hits in metrics
        logger.warning(f"Rate limit exceeded for session {session_id}")
        return
    
    # 🔥 INT-LIVE-I2: Safe base64 decode with size limits
    raw_bytes = b""
    if payload.get('audio_data_b64'):
        try:
            raw_bytes = decode_audio_b64(payload['audio_data_b64'])
        except AudioChunkTooLarge:
            emit('error', {'message': 'Chunk too large'})
            return
        except AudioChunkDecodeError:
            emit('error', {'message': 'Invalid audio data'})
            return
    
    # === Process Audio ===
    # This returns None, or a dict like:
    # {'transcription': {'text': '...', 'confidence': 0.78, 'is_final': False}}
    try:
        result = tsvc.process_audio_sync(
            session_id=session_id,
            audio_data=raw_bytes,
            timestamp=client_ts,
            mime_type=mime_type,
            client_rms=rms,
            is_final_signal=is_final_chunk
        )
    except Exception as e:
        # 🔥 INT-LIVE-I2: Structured log for observability
        logger.error({
            "ev": "audio_chunk_error",
            "session_id": session_id,
            "err": str(e),
            "mime_type": mime_type,
            "chunk_size": len(raw_bytes),
            "is_final": is_final_chunk
        })
        emit('error', {'message': 'Processing error'})
        return
    
    if not result or 'transcription' not in result:
        # No interim to emit this time - normal for many chunks
        return
    
    tr = result['transcription']
    txt = (tr.get('text') or '').strip()
    conf = float(tr.get('confidence') or 0.0)
    is_final = bool(tr.get('is_final'))
    
    # 🔥 INT-LIVE-I2: Structured logging (tailor to your JSON logger)
    logger.info({
        "ev": "transcription_emit",
        "session_id": session_id,
        "len": len(txt),
        "conf": conf,
        "is_final": is_final,
        "rms": rms,
        "mime": mime_type,
    })
    
    if not txt:
        return
    
    if is_final:
        # Emit to all clients in the session room
        socketio.emit('final_transcript', {
            "session_id": session_id,
            "text": txt,
            "avg_confidence": conf,
            "timestamp": now
        }, room=session_id)
    else:
        # Interim transcript
        socketio.emit('interim_transcript', {
            "session_id": session_id,
            "text": txt,
            "avg_confidence": conf,
            "timestamp": now
        }, room=session_id)

@socketio.on('end_of_stream')
def end_of_stream(data):
    """Handle end of stream signal."""
    try:
        session_id = (data or {}).get('session_id')
        if not session_id:
            emit('error', {'message': 'Missing session_id'})
            return
        
        logger.info(f"End of stream for session: {session_id}")
        tsvc.end_session(session_id)
        emit('stream_ended', {'session_id': session_id})
        
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