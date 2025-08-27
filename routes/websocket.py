import time
import json
import traceback
import uuid
from contextlib import contextmanager
from functools import wraps
from flask import request
from flask_socketio import emit, join_room, disconnect
from app import socketio, db, WS_DEBUG, STUB_TRANSCRIPTION
import logging
import os

# Import services
from services.audio_io import decode_audio_b64, AudioChunkTooLarge, AudioChunkDecodeError
# FIXED: Lazy import to prevent circular dependency
# from services.transcription_service import TranscriptionService
# from models.session import Session

logger = logging.getLogger(__name__)

# FIXED: Initialize transcription service lazily to prevent circular import
tsvc = None
tsvc_config = None

def get_transcription_service():
    """Lazy initialization of transcription service to prevent circular imports."""
    global tsvc, tsvc_config
    if tsvc is None:
        from services.transcription_service import TranscriptionService, TranscriptionServiceConfig
        tsvc_config = TranscriptionServiceConfig()
        tsvc = TranscriptionService(tsvc_config)
    return tsvc

# 🔥 PHASE 1: Session management and debugging counters
_CHUNK_COUNT = {}  # per session counters for debug tracking
_SESSION_STATES = {}  # track session join status

# Initialize performance monitoring for WebSocket routes
try:
    from services.performance_monitor import performance_monitor
    websocket_performance_monitor = performance_monitor
    logger.info("WebSocket performance monitoring initialized")
except ImportError:
    websocket_performance_monitor = None
    logger.warning("WebSocket performance monitoring not available")

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

# 🔥 ENHANCED: Robust error handling decorator
def handle_socket_errors(f):
    """Decorator for comprehensive WebSocket error handling."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"🚨 WebSocket error in {f.__name__}: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # 🔥 CRITICAL FIX: Specific error messages with recovery guidance
            try:
                error_type = 'system_error'
                error_message = 'An unexpected error occurred. Please refresh and try again.'
                recovery_action = 'refresh_page'
                
                # Provide specific error messages based on error type
                error_str = str(e).lower()
                if 'last_activity' in error_str:
                    error_type = 'session_cleanup_error'
                    error_message = 'Session cleanup failed. Your session may still be active.'
                    recovery_action = 'continue_session'
                elif 'session' in error_str and 'not found' in error_str:
                    error_type = 'session_not_found'
                    error_message = 'Session expired or not found. Starting a new session...'
                    recovery_action = 'create_new_session'
                elif 'audio' in error_str:
                    error_type = 'audio_processing_error'
                    error_message = 'Audio processing failed. Check your microphone and try again.'
                    recovery_action = 'restart_recording'
                elif 'transcription' in error_str:
                    error_type = 'transcription_service_error'
                    error_message = 'Transcription service temporarily unavailable. Retrying...'
                    recovery_action = 'retry_transcription'
                
                emit('error', {
                    'type': error_type,
                    'message': error_message,
                    'recovery_action': recovery_action,
                    'timestamp': time.time(),
                    'debug_info': str(e) if WS_DEBUG else None
                })
            except Exception as emit_error:
                logger.error(f"Failed to emit error to client: {emit_error}")
    return wrapper

# 🔥 PHASE 1: Session join protocol - explicit session management
@socketio.on('join_session')
@handle_socket_errors
def join_session(data):
    """🔥 CRITICAL: Explicit session joining before audio streaming."""
    try:
        payload = data or {}
        session_id = payload.get('session_id')
        
        if not session_id:
            emit('error', {
                'type': 'missing_session_id',
                'message': 'Missing session_id in join_session request',
                'timestamp': time.time()
            })
            return
        
        # Join the room for this session
        join_room(session_id)
        _SESSION_STATES[session_id] = {
            'joined_at': time.time(),
            'chunk_count': 0,
            'last_activity': time.time()
        }
        
        # 🔥 CRITICAL FIX: Create transcription service session when joining WebSocket session
        print(f"🔧 CREATING TRANSCRIPTION SESSION for: {session_id}")  # Force output
        logger.info(f"🔧 CREATING TRANSCRIPTION SESSION for: {session_id}")
        
        try:
            # Initialize session in the transcription service directly (synchronous approach)
            current_time = time.time()
            
            # Create session data structure
            session_data = {
                'created_at': current_time,
                'status': 'active',
                'stats': {
                    'total_segments': 0,
                    'average_confidence': 0.0,
                    'total_audio_duration': 0.0
                },
                'config': tsvc_config.__dict__,
                'streaming_state': {
                    'buffer_strategy': 'balanced',
                    'optimization_level': 'normal'
                }
            }
            
            # Add to transcription service
            service = get_transcription_service()
            service.active_sessions[session_id] = session_data
            service.session_callbacks[session_id] = []
            service.total_sessions += 1
            
            # 🔥 CRITICAL FIX: Register WebSocket emission callback for transcription results
            def emit_transcription_result(result):
                """Emit transcription result via WebSocket."""
                try:
                    text = result.text.strip()
                    if not text:
                        return
                        
                    event_name = 'final_transcript' if result.is_final else 'interim_transcript'
                    
                    emit_data = {
                        'session_id': session_id,
                        'text': text,
                        'confidence': result.confidence,
                        'is_final': result.is_final,
                        'timestamp': result.timestamp,
                        'language': result.language
                    }
                    
                    # Emit to specific client and room
                    emit(event_name, emit_data)
                    emit(event_name, emit_data, to=session_id)
                    
                    logger.info(f"✅ CALLBACK EMIT {event_name.upper()}: '{text[:50]}...' for session {session_id}")
                    
                except Exception as e:
                    logger.error(f"🚨 Error emitting transcription result: {e}")
            
            # Register the callback
            service.add_session_callback(session_id, emit_transcription_result)
            
            print(f"🔧 TRANSCRIPTION SESSION CREATED: {session_id}")  # Force output
            logger.info(f"🔧 TRANSCRIPTION SESSION CREATED: {session_id}")
            logger.info(f"🔧 Session data: {session_data}")
                    
        except Exception as e:
            logger.error(f"🚨 Failed to create transcription service session: {e}")
            logger.error(f"🚨 Full traceback: {traceback.format_exc()}")
            emit('error', {
                'type': 'transcription_session_error',
                'message': f'Failed to initialize transcription: {str(e)}',
                'timestamp': time.time()
            })
            return
        
        # 🔥 DEBUG: Always log session creation for debugging
        logger.info(f"📝 SESSION JOIN: Client joined session {session_id}")
        service = get_transcription_service()
        logger.info(f"🔧 Active transcription sessions: {list(service.active_sessions.keys())}")
        logger.info(f"🔧 Total sessions in service: {len(service.active_sessions)}")
        
        emit('joined_session', {
            'session_id': session_id,
            'timestamp': time.time(),
            'debug_mode': WS_DEBUG,
            'stub_mode': STUB_TRANSCRIPTION
        })
        
    except Exception as e:
        logger.error(f"🚨 SESSION JOIN ERROR: {e}")
        emit('error', {
            'type': 'session_join_error',
            'message': f'Failed to join session: {str(e)}',
            'timestamp': time.time()
        })

@socketio.on('connect')
@handle_socket_errors
def on_connect(auth):
    """🔥 ENHANCED: Handle client connection with comprehensive tracking and error recovery."""
    try:
        from flask import session as flask_session
        client_id = flask_session.get('client_id', str(uuid.uuid4()))
    except:
        client_id = str(uuid.uuid4())
    
    connection_time = time.time()
    
    # 🔥 ENHANCED: Structured logging for better monitoring
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
    # Get session ID from Flask-SocketIO context
    try:
        from flask import session as flask_session
        client_id = flask_session.get('client_id', str(uuid.uuid4()))
    except:
        client_id = str(uuid.uuid4())
    disconnect_time = time.time()
    
    logger.info({
        "event": "client_disconnected", 
        "client_id": client_id,
        "reason": disconnect_reason,
        "timestamp": disconnect_time
    })
    
    # Clean up any active sessions for this client
    try:
        service = get_transcription_service()
        service.cleanup_client_sessions(client_id)
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
        def get_session_model():
            from models.session import Session
            return Session
        
        session = get_session_model()(
            title=title,
            locale=language,
            external_id=str(uuid.uuid4())[:8]
        )
        db.session.add(session)
        db.session.commit()
        
        # Initialize transcription service session
        service = get_transcription_service()
        service.start_session_sync(session.external_id, {
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

# Duplicate join_session handler removed - keeping only the first one (lines 118-204)

# --- Audio Processing Events ---

# 🔥 PHASE 1: Enhanced audio_chunk handler with stub support and comprehensive validation
@socketio.on('audio_chunk')
@handle_socket_errors
def audio_chunk(data):
    """🔥 CRITICAL: Robust audio chunk handler with schema validation, acks, and stub mode."""
    started = time.time()
    
    try:
        # 🔥 PAYLOAD VALIDATION: Strict schema enforcement
        payload = data or {}
        session_id = payload.get('session_id')
        
        if not session_id:
            emit('error', {
                'type': 'missing_session_id',
                'message': 'Missing session_id in audio_chunk',
                'timestamp': time.time()
            })
            return
        
        # 🔥 SESSION STATE VALIDATION: Ensure session was properly joined
        if session_id not in _SESSION_STATES:
            emit('error', {
                'type': 'session_not_joined',
                'message': f'Session {session_id} not joined. Call join_session first.',
                'timestamp': time.time()
            })
            return
        
        # 🔥 EXTRACT & VALIDATE PAYLOAD SCHEMA
        audio_data_b64 = payload.get('audio_data_b64', '')
        is_final = bool(payload.get('is_final_chunk', False))
        mime_type = payload.get('mime_type', '')
        rms = float(payload.get('rms', 0.0))
        ts_client = payload.get('ts_client')
        
        # 🔥 RATE LIMITING & DEBUG COUNTERS
        if not _rate_ok(session_id, started):
            emit('error', {
                'type': 'rate_limit_exceeded',
                'message': 'Too many audio chunks per minute',
                'timestamp': time.time()
            })
            return
        
        # Update session state and chunk counter
        chunk_count = _CHUNK_COUNT.get(session_id, 0) + 1
        _CHUNK_COUNT[session_id] = chunk_count
        _SESSION_STATES[session_id]['chunk_count'] = chunk_count
        _SESSION_STATES[session_id]['last_activity'] = started
        
        if WS_DEBUG:
            logger.info(f"📊 CHUNK #{chunk_count}: Session {session_id}, {len(audio_data_b64)} b64 chars, final={is_final}")
        
        # 🔥 DECODE AUDIO DATA (if not final-only signal)
        raw_audio = b""
        if audio_data_b64:
            try:
                raw_audio = decode_audio_b64(audio_data_b64)
                if WS_DEBUG:
                    logger.info(f"🎵 AUDIO DECODED: {len(raw_audio)} bytes for session {session_id}")
            except (AudioChunkTooLarge, AudioChunkDecodeError) as e:
                emit('error', {
                    'type': 'audio_decode_error',
                    'message': f'Audio decode failed: {str(e)}',
                    'timestamp': time.time()
                })
                return
        
        # 🔥 ENHANCED: Always emit acknowledgment for received audio chunk
        emit('audio_acknowledged', {
            'session_id': session_id,
            'chunk_size': len(raw_audio) if raw_audio else 0,
            'timestamp': time.time(),
            'is_final': is_final,
            'received': True
        })
        
        # 🔥 STUB TRANSCRIPTION MODE: Test wiring without real API calls
        if STUB_TRANSCRIPTION:
            if is_final:
                emit('final_transcript', {
                    'session_id': session_id,
                    'text': f'Final stub transcript for session {session_id}.',
                    'confidence': 1.0,
                    'timestamp': time.time()
                }, to=session_id)
                
                if WS_DEBUG:
                    logger.info(f"🎭 STUB FINAL: Emitted for session {session_id}")
            else:
                # Throttle interim updates: emit every few chunks
                if chunk_count % 2 == 0:  # Every 2nd chunk
                    emit('interim_transcript', {
                        'session_id': session_id,
                        'text': f'Stub interim #{chunk_count} for session {session_id}',
                        'confidence': 0.8,
                        'timestamp': time.time()
                    }, to=session_id)
                    
                    if WS_DEBUG:
                        logger.info(f"🎭 STUB INTERIM: #{chunk_count} emitted for session {session_id}")
            
            # Always send acknowledgment in stub mode
            emit('ack', {
                'ok': True,
                'seq': chunk_count,
                'latency_ms': int((time.time() - started) * 1000),
                'mode': 'stub'
            })
            return
        
        # 🔥 REAL TRANSCRIPTION PATH
        if WS_DEBUG:
            logger.info(f"🎤 REAL PROCESSING: Session {session_id}, {len(raw_audio)} bytes, final={is_final}")
        
        service = get_transcription_service()
        result = service.process_audio_sync(
            session_id=session_id,
            audio_data=raw_audio,
            timestamp=ts_client / 1000 if ts_client else started,
            is_final_signal=is_final
        )
        
        # 🔥 HANDLE TRANSCRIPTION RESULTS
        if result:
            transcription = result.get('transcription', {})
            text = transcription.get('text', '')
            confidence = transcription.get('confidence', 0.0)
            is_final_result = transcription.get('is_final', False)
            
            if text:
                event_name = 'final_transcript' if is_final_result else 'interim_transcript'
                
                # Emit to the specific client (using request.sid)
                emit(event_name, {
                    'session_id': session_id,
                    'text': text,
                    'confidence': confidence,
                    'timestamp': time.time()
                })
                
                # Also emit to room if different from individual client
                emit(event_name, {
                    'session_id': session_id,
                    'text': text,
                    'confidence': confidence,
                    'timestamp': time.time()
                }, to=session_id)
                
                if WS_DEBUG:
                    logger.info(f"✅ {event_name.upper()}: '{text[:50]}...' emitted to client and room {session_id}")
        
        # 🔥 CRITICAL FIX: Broadcast real-time session metrics after processing
        try:
            # 🔥 CRITICAL FIX: Use correct SQLAlchemy 2.0 syntax
            from sqlalchemy import select
            stmt = select(Session).filter_by(external_id=session_id)
            session = db.session.execute(stmt).scalar_one_or_none()
            if session:
                # Calculate current session metrics
                segment_count = len(session.segments) if session.segments else 0
                avg_confidence = session.average_confidence or 0.0
                total_duration = session.total_duration or 0.0
                
                # Update session statistics with latest data
                if session.segments:
                    confidences = [seg.avg_confidence for seg in session.segments if seg.avg_confidence]
                    if confidences:
                        avg_confidence = sum(confidences) / len(confidences)
                        session.average_confidence = avg_confidence
                    
                    durations = [seg.duration_ms for seg in session.segments if seg.duration_ms]
                    if durations:
                        total_duration = sum(durations)
                        session.total_duration = total_duration
                
                # Commit database updates
                db.session.commit()
                
                # Broadcast metrics to client
                session_metrics = {
                    'session_id': session_id,
                    'segments_count': segment_count,
                    'avg_confidence': round(avg_confidence * 100, 1),  # Convert to percentage
                    'speaking_time': round(total_duration, 1),
                    'quality': 'Excellent' if avg_confidence > 0.8 else 'Good' if avg_confidence > 0.6 else 'Fair' if avg_confidence > 0.4 else 'Poor',
                    'last_update': time.time(),
                    'processing_status': 'active',
                    'chunk_count': chunk_count
                }
                
                emit('session_metrics_update', session_metrics, to=session_id)
                
                if WS_DEBUG:
                    logger.info(f"📊 Session metrics broadcast: segments={segment_count}, confidence={avg_confidence:.2f}, duration={total_duration:.1f}s")
        except Exception as metrics_error:
            logger.error(f"Failed to broadcast session metrics: {metrics_error}")

        # 🔥 ALWAYS SEND ACKNOWLEDGMENT
        emit('ack', {
            'ok': True,
            'seq': chunk_count,
            'latency_ms': int((time.time() - started) * 1000),
            'has_result': bool(result and result.get('transcription', {}).get('text')),
            'mode': 'real'
        })
        
    except (AudioChunkTooLarge, AudioChunkDecodeError) as e:
        emit('error', {
            'type': 'audio_processing_error',
            'message': f'Audio processing failed: {str(e)}',
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"🚨 AUDIO CHUNK EXCEPTION: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        emit('error', {
            'type': 'server_exception',
            'message': f'Server error: {type(e).__name__}',
            'timestamp': time.time()
        })
        raise  # Re-raise for debugging in development

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
            "client_id": "socket_client",
            "timestamp": time.time()
        })
        
        # End session and get final statistics
        service = get_transcription_service()
        final_stats = service.end_session(session_id)
        
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
def handle_ping(data=None):
    """Simple ping/pong for connection testing."""
    emit('pong', {'timestamp': time.time()})

# Function for app.py compatibility
def register_websocket_handlers(socketio_instance):
    """Register websocket handlers with socketio instance."""
    # All handlers are already registered via decorators above
    logger.info("WebSocket handlers registered successfully")
    return socketio_instance