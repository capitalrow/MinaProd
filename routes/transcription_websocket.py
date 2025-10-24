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
from flask import session, request
from flask_socketio import emit, disconnect, join_room, leave_room
from flask_login import current_user

# Import the socketio instance from the consolidated app
from app import socketio

# Import database models
from models import db
from models.session import Session
from models.segment import Segment

# Import advanced buffer management
from services.session_buffer_manager import buffer_registry, BufferConfig
# After existing imports
import asyncio
from jobs.analysis_dispatcher import AnalysisDispatcher


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

# 🔥 PRODUCTION FIX: Segment buffer for batch commits
segment_buffers = {}  # session_id -> list of pending segments
BATCH_COMMIT_SIZE = 5  # Commit every 5 segments to reduce DB load
BATCH_COMMIT_INTERVAL = 10  # Or commit every 10 seconds

def _safe_commit_segments(session_id: str, force=False):
    """
    Thread-safe batch commit of buffered segments.
    Only commits when batch size reached or force=True.
    Uses Flask app context for safety.
    """
    if session_id not in segment_buffers:
        return
    
    pending = segment_buffers[session_id]
    
    # Only commit if we have enough segments or forced
    if not force and len(pending) < BATCH_COMMIT_SIZE:
        return
    
    if not pending:
        return
    
    try:
        # Use Flask app context for thread safety
        from flask import current_app
        with current_app.app_context():
            # Add all pending segments
            for segment_data in pending:
                segment = Segment(**segment_data)
                db.session.add(segment)
            
            db.session.commit()
            logger.info(f"💾 [batch-commit] Saved {len(pending)} segments for session {session_id}")
            
            # Clear buffer after successful commit
            segment_buffers[session_id] = []
            
    except Exception as e:
        logger.error(f"❌ [batch-commit] Failed to commit segments: {e}")
        db.session.rollback()
        # Keep segments in buffer for retry
        
def _background_processor(session_id: str, buffer_manager):
    """Background worker for processing buffered audio chunks and periodic batch commits"""
    logger.info(f"🔧 Started background processor for session {session_id}")
    
    last_commit_time = time.time()
    
    try:
        while session_id in active_sessions:
            time.sleep(1)  # Poll every second
            
            # Check if it's time for a periodic batch commit
            current_time = time.time()
            if current_time - last_commit_time >= BATCH_COMMIT_INTERVAL:
                _safe_commit_segments(session_id, force=False)  # Commit if threshold met
                last_commit_time = current_time
            
            if session_id not in active_sessions:
                break
                
    except Exception as e:
        logger.error(f"Background processor error for session {session_id}: {e}")
    finally:
        # Final commit of any remaining segments
        _safe_commit_segments(session_id, force=True)
        logger.info(f"🔧 Background processor stopped for session {session_id}")

@socketio.on('connect', namespace='/transcription')
def on_connect(auth=None):
    """Handle client connection to transcription namespace with authentication"""
    # Check authentication - require valid user session
    if not current_user.is_authenticated:
        logger.warning(f"[transcription] Unauthenticated connection attempt from {request.sid}")
        emit('error', {'message': 'Authentication required'})
        disconnect()
        return False
    
    logger.info(f"[transcription] Authenticated client connected: {request.sid} (user: {current_user.id})")
    join_room(f"user_{current_user.id}")
    emit('status', {
        'status': 'connected', 
        'message': 'Connected to transcription service',
        'user_id': current_user.id
    })

@socketio.on('disconnect', namespace='/transcription')
def on_disconnect():
    """Handle client disconnection with comprehensive cleanup"""
    logger.info(f"[transcription] Client disconnected: {request.sid}")
    # Clean up any active sessions for this client
    sessions_to_remove = []
    for session_id, session_info in active_sessions.items():
        if session_info.get('client_sid') == request.sid:
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
        
        # Remove from active sessions
        active_sessions.pop(session_id, None)
        logger.info(f"[transcription] Comprehensive cleanup completed for session: {session_id}")

@socketio.on('start_session', namespace='/transcription')
def on_start_session(data):
    """Start a new transcription session"""
    try:
        session_id = str(uuid.uuid4())
        
        # 🔥 CREATE DATABASE SESSION RECORD
        db_session = Session(
            external_id=session_id,
            title=data.get('title', f"Live Recording - {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            status="active",
            locale=data.get('language', 'en'),
            started_at=datetime.utcnow(),
            user_id=current_user.id if current_user.is_authenticated else None,
            workspace_id=current_user.default_workspace_id if (current_user.is_authenticated and hasattr(current_user, 'default_workspace_id')) else None,
            meta={
                'client_sid': request.sid,
                'enhance_audio': data.get('enhance_audio', True)
            }
        )
        db.session.add(db_session)
        db.session.commit()
        logger.info(f"✅ [transcription] Created database Session record: {session_id} (DB ID: {db_session.id})")
        
        # Store session info with advanced buffer manager
        buffer_manager = buffer_registry.get_or_create_session(session_id)
        
        active_sessions[session_id] = {
            'client_sid': request.sid,
            'db_session_id': db_session.id,  # Store DB ID for later use
            'started_at': datetime.utcnow(),
            'language': data.get('language', 'en'),
            'enhance_audio': data.get('enhance_audio', True),
            'buffer_manager': buffer_manager,
            'audio_buffer': bytearray(),
            'webm_header': None,
            'last_process_time': 0,
            'segment_counter': 0,  # Track segments for this session
            'session_start_ms': int(time.time() * 1000)  # Track absolute start time
        }
        
        # 🔥 Initialize segment buffer for batch commits
        segment_buffers[session_id] = []
        
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
        
        emit('session_started', {
            'session_id': session_id,
            'status': 'ready',
            'message': 'Transcription session started'
        })
        
    except Exception as e:
        logger.error(f"[transcription] Error starting session: {e}")
        db.session.rollback()  # Rollback on error
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('audio_data', namespace='/transcription')
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
        
        # Find the current session for this client
        session_id = None
        for sid, session_info in active_sessions.items():
            if session_info.get('client_sid') == request.sid:
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
                        # 🔥 PRODUCTION FIX: Buffer segments for batch commit
                        try:
                            is_final = result.get('is_final', True)
                            db_session_id = session_info.get('db_session_id')
                            
                            if db_session_id:
                                # Calculate relative timing from session start
                                session_start_ms = session_info.get('session_start_ms', 0)
                                current_ms = int(time.time() * 1000)
                                relative_start_ms = current_ms - session_start_ms
                                
                                # Use processing_time from response if available, otherwise estimate
                                processing_time = result.get('processing_time', result.get('processing_time_ms', 0))
                                
                                # Create segment data dict (don't create object yet for thread safety)
                                segment_data = {
                                    'session_id': db_session_id,
                                    'kind': "final" if is_final else "interim",
                                    'text': text,
                                    'avg_confidence': result.get('confidence', 0.9),
                                    'start_ms': relative_start_ms,
                                    'end_ms': relative_start_ms + processing_time if processing_time else None,
                                    'created_at': datetime.utcnow()
                                }
                                
                                # Add to buffer instead of immediate commit
                                if session_id not in segment_buffers:
                                    segment_buffers[session_id] = []
                                segment_buffers[session_id].append(segment_data)
                                
                                # Update segment counter
                                session_info['segment_counter'] = session_info.get('segment_counter', 0) + 1
                                
                                logger.info(f"📝 [transcription] Buffered segment #{session_info['segment_counter']} (kind: {segment_data['kind']}, buffer size: {len(segment_buffers[session_id])})")
                                
                                # Trigger batch commit if threshold reached
                                if len(segment_buffers[session_id]) >= BATCH_COMMIT_SIZE:
                                    _safe_commit_segments(session_id, force=True)
                            else:
                                logger.warning(f"⚠️ [transcription] No db_session_id found, cannot save segment")
                        except Exception as buffer_error:
                            logger.error(f"❌ [transcription] Failed to buffer segment: {buffer_error}")
                        
                        # Emit properly formatted transcription result
                        emit('transcription_result', {
                            'text': text,
                            'is_final': result.get('is_final', True),
                            'confidence': result.get('confidence', 0.9),
                            'timestamp': int(time.time() * 1000),
                            'speaker_id': result.get('speaker_id', 'Speaker 1'),
                            'processing_time_ms': result.get('processing_time_ms', 100)
                        })
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
def on_end_session(data=None):
    """End the current transcription session and trigger post-meeting analysis"""
    try:
        sessions_to_end = []
        for session_id, session_info in active_sessions.items():
            if session_info.get('client_sid') == request.sid:
                sessions_to_end.append(session_id)

        for session_id in sessions_to_end:
            # 🧹 Clean up WebSocket rooms and local buffers
            leave_room(session_id)
            session_info = active_sessions.pop(session_id, None)
            logger.info(f"[transcription] Ended session: {session_id}")

            # 🔥 PRODUCTION FIX: Commit any remaining buffered segments first
            logger.info(f"[transcription] Finalizing session {session_id}, committing remaining segments...")
            _safe_commit_segments(session_id, force=True)
            
            # Clean up segment buffer
            if session_id in segment_buffers:
                del segment_buffers[session_id]
            
            # 🔥 MARK SESSION AS COMPLETED IN DATABASE
            try:
                db_session_id = session_info.get('db_session_id') if session_info else None
                if db_session_id:
                    # Use Flask app context for thread safety
                    from flask import current_app
                    with current_app.app_context():
                        db_session_obj = db.session.query(Session).filter_by(id=db_session_id).first()
                        if db_session_obj:
                            db_session_obj.status = "completed"
                            db_session_obj.completed_at = datetime.utcnow()
                            
                            # Update session statistics from ALL segments (final only)
                            final_segments = db.session.query(Segment).filter_by(
                                session_id=db_session_id, 
                                kind="final"
                            ).all()
                            
                            db_session_obj.total_segments = len(final_segments)
                            
                            if final_segments:
                                # Calculate average confidence from final segments
                                total_confidence = sum(s.avg_confidence or 0.0 for s in final_segments)
                                db_session_obj.average_confidence = total_confidence / len(final_segments)
                                
                                # Calculate total duration from segment timings
                                if final_segments[-1].end_ms and final_segments[0].start_ms:
                                    db_session_obj.total_duration = (final_segments[-1].end_ms - final_segments[0].start_ms) / 1000.0  # Convert to seconds
                            
                            db.session.commit()
                            logger.info(f"💾 [transcription] Session completed in DB (ID: {db_session_id}, final_segments: {db_session_obj.total_segments}, avg_conf: {db_session_obj.average_confidence:.2f if db_session_obj.average_confidence else 0})")
                        else:
                            logger.warning(f"⚠️ [transcription] Session not found in database: {db_session_id}")
                else:
                    logger.warning(f"⚠️ [transcription] No db_session_id found for session: {session_id}")
            except Exception as db_error:
                logger.error(f"❌ [transcription] Failed to update session in database: {db_error}")
                db.session.rollback()

            # 🗂️ Optional: persist final transcript before triggering analysis
            try:
                buffer_manager = session_info.get("buffer_manager") if session_info else None
                if buffer_manager:
                    final_transcript = buffer_manager.flush_and_finalize(session_id=session_id)
                    logger.info(f"[transcription] Final transcript stored for session {session_id} ({len(final_transcript)} chars)")
                else:
                    logger.warning(f"[transcription] No buffer manager found for session {session_id}")
            except Exception as e:
                logger.error(f"[transcription] Error finalizing transcript: {e}")

            # 🚀 Kick off downstream analytics + summary generation asynchronously
            try:
                asyncio.create_task(
                    AnalysisDispatcher.run_full_analysis(
                        session_id=session_id,
                        meeting_id=session_info.get("meeting_id", str(uuid.uuid4())) if session_info else str(uuid.uuid4())  # fallback if not tracked
                    )
                )
                logger.info(f"[analysis] Dispatched background analytics job for session {session_id}")
            except Exception as e:
                logger.error(f"[analysis] Failed to dispatch analytics job: {e}")

            # ✅ Notify the client that the session is done
            emit('session_ended', {
                'session_id': session_id,
                'status': 'completed',
                'message': 'Transcription session ended. Analysis started in background.'
            })

    except Exception as e:
        logger.error(f"[transcription] Error ending session: {e}")
        emit('error', {'message': f'Failed to end session: {str(e)}'})

logger.info("✅ Transcription WebSocket namespace handlers registered")