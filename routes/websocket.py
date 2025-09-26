"""
Real-time WebSocket handlers for live transcription with actual OpenAI Whisper integration
"""
import logging
import io
import time
from extensions import socketio
from flask_socketio import emit
from flask import current_app
from services.openai_whisper_client import transcribe_bytes
from server.models import db, Conversation, Segment

logger = logging.getLogger(__name__)

# Active session tracking
active_sessions = {}

@socketio.on('connect')
def handle_connect():
    logger.info('[websocket] Client connected')
    emit('server_hello', {'message': 'Connected to Mina transcription service'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('[websocket] Client disconnected')

@socketio.on('join_session')
def handle_join_session(data):
    """Handle session initialization - create conversation record"""
    session_id = data.get('session_id')
    if not session_id:
        logger.error('[websocket] No session_id provided')
        emit('session_error', {'error': 'No session ID provided'})
        return
    
    logger.info(f'[websocket] Joining session: {session_id}')
    
    # Create conversation record with Flask app context
    try:
        with current_app.app_context():
            conversation = Conversation()
            conversation.title = f"Live Session {session_id}"
            conversation.status = "live"
            conversation.source = "realtime"
            
            db.session.add(conversation)
            db.session.commit()
            
            logger.info(f'[websocket] Created conversation {conversation.id} for session {session_id}')
        
        # Track active session
        active_sessions[session_id] = {
            'conversation_id': conversation.id,
            'start_time': time.time(),
            'segment_count': 0,
            'audio_buffer': b'',
            'last_chunk_time': time.time()
        }
        
        logger.info(f'[websocket] Session {session_id} initialized with conversation {conversation.id}')
        emit('session_joined', {'status': 'joined', 'conversation_id': conversation.id})
        
    except Exception as e:
        logger.error(f'[websocket] Failed to create conversation for session {session_id}: {e}')
        emit('session_error', {'error': 'Failed to initialize session'})

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """Handle incoming audio data and process with real Whisper transcription"""
    session_id = None
    audio_data = None
    
    # Handle different data formats
    if isinstance(data, dict):
        session_id = data.get('session_id')
        audio_data = data.get('audio_data_b64') or data.get('audio_data')
        if isinstance(audio_data, str):
            import base64
            try:
                audio_data = base64.b64decode(audio_data)
            except Exception as e:
                logger.error(f'[websocket] Failed to decode base64 audio: {e}')
                return
    elif hasattr(data, 'read'):  # File-like object from MediaRecorder
        try:
            audio_data = data.read() if hasattr(data, 'read') else bytes(data)
            # Extract session from active sessions (use most recent if no session_id)
            if active_sessions:
                session_id = list(active_sessions.keys())[-1]
        except Exception as e:
            logger.error(f'[websocket] Failed to read audio data: {e}')
            return
    else:
        # Raw bytes from MediaRecorder
        try:
            audio_data = bytes(data) if data else b''
            if active_sessions:
                session_id = list(active_sessions.keys())[-1]
        except Exception as e:
            logger.error(f'[websocket] Failed to process raw audio data: {e}')
            return
    
    if not session_id or session_id not in active_sessions:
        logger.warning(f'[websocket] No active session found for audio chunk')
        return
    
    if not audio_data or len(audio_data) == 0:
        logger.warning(f'[websocket] Empty audio data received for session {session_id}')
        return
    
    session_info = active_sessions[session_id]
    logger.info(f'[websocket] Processing audio chunk for session {session_id}: {len(audio_data)} bytes')
    
    try:
        # Accumulate audio data for better transcription quality
        session_info['audio_buffer'] += audio_data
        session_info['last_chunk_time'] = time.time()
        
        # Process chunks when buffer reaches reasonable size (1-2 seconds of audio)
        # WebM opus at 16kHz mono is roughly 2KB per second
        min_buffer_size = 4096  # ~2 seconds
        max_buffer_age = 2.0    # Process every 2 seconds regardless
        
        current_time = time.time()
        buffer_age = current_time - session_info.get('last_process_time', session_info['start_time'])
        
        should_process = (
            len(session_info['audio_buffer']) >= min_buffer_size or 
            buffer_age >= max_buffer_age
        )
        
        if should_process and session_info['audio_buffer']:
            logger.info(f'[websocket] Transcribing {len(session_info["audio_buffer"])} bytes for session {session_id}')
            
            # Real OpenAI Whisper transcription
            try:
                transcript_text = transcribe_bytes(
                    session_info['audio_buffer'],
                    mime_hint='audio/webm',
                    language='en'
                )
                
                session_info['last_process_time'] = current_time
                session_info['audio_buffer'] = b''  # Clear buffer after processing
                
                if transcript_text and transcript_text.strip():
                    logger.info(f'[websocket] Transcription result: "{transcript_text[:50]}..."')
                    
                    # Store segment in database
                    conversation_id = session_info['conversation_id']
                    segment_idx = session_info['segment_count']
                    session_info['segment_count'] += 1
                    
                    # Store segment with Flask app context
                    with current_app.app_context():
                        segment = Segment()
                        segment.conversation_id = conversation_id
                        segment.idx = segment_idx
                        segment.start_ms = int((current_time - session_info['start_time']) * 1000) - 2000
                        segment.end_ms = int((current_time - session_info['start_time']) * 1000)
                        segment.text = transcript_text
                        segment.is_final = True
                        
                        db.session.add(segment)
                        db.session.commit()
                        
                        logger.info(f'[websocket] Stored segment {segment.id} for conversation {conversation_id}')
                    
                    # Send real interim transcript (for live feedback)
                    emit('interim_transcript', {
                        'text': transcript_text,
                        'start_ms': segment.start_ms,
                        'end_ms': segment.end_ms,
                        'confidence': 0.9
                    })
                    
                    # Also send as final transcript
                    emit('final_transcript', {
                        'text': transcript_text,
                        'start_ms': segment.start_ms,
                        'end_ms': segment.end_ms,
                        'confidence': 0.9,
                        'segment_id': segment.id
                    })
                else:
                    logger.info(f'[websocket] No transcription result for session {session_id}')
                    
            except Exception as e:
                logger.error(f'[websocket] Transcription failed for session {session_id}: {e}')
                # Send error to client
                emit('transcription_error', {'error': 'Transcription service unavailable'})
    
    except Exception as e:
        logger.error(f'[websocket] Error processing audio chunk for session {session_id}: {e}')
        emit('transcription_error', {'error': 'Audio processing failed'})

@socketio.on('finalize_session')
def handle_finalize_session(data):
    """Handle session finalization"""
    session_id = data.get('session_id') if data else None
    
    if not session_id and active_sessions:
        # Use the most recent session
        session_id = list(active_sessions.keys())[-1]
    
    if session_id and session_id in active_sessions:
        logger.info(f'[websocket] Finalizing session: {session_id}')
        
        session_info = active_sessions[session_id]
        
        try:
            # Process any remaining audio buffer
            if session_info.get('audio_buffer'):
                transcript_text = transcribe_bytes(
                    session_info['audio_buffer'],
                    mime_hint='audio/webm',
                    language='en'
                )
                
                if transcript_text and transcript_text.strip():
                    # Store final segment
                    conversation_id = session_info['conversation_id']
                    segment_idx = session_info['segment_count']
                    
                    # Store final segment with Flask app context
                    with current_app.app_context():
                        segment = Segment()
                        segment.conversation_id = conversation_id
                        segment.idx = segment_idx
                        segment.start_ms = int((time.time() - session_info['start_time']) * 1000) - 2000
                        segment.end_ms = int((time.time() - session_info['start_time']) * 1000)
                        segment.text = transcript_text
                        segment.is_final = True
                        
                        db.session.add(segment)
                        db.session.commit()
                        
                        logger.info(f'[websocket] Stored final segment {segment.id} for conversation {conversation_id}')
                    
                    emit('final_transcript', {
                        'text': transcript_text,
                        'start_ms': segment.start_ms,
                        'end_ms': segment.end_ms,
                        'confidence': 0.9,
                        'segment_id': segment.id
                    })
            
            # Update conversation status with Flask app context
            with current_app.app_context():
                conversation = Conversation.query.get(session_info['conversation_id'])
                if conversation:
                    conversation.status = 'final'
                    conversation.duration_s = int(time.time() - session_info['start_time'])
                    
                    # Calculate word count from all segments
                    segments = Segment.query.filter_by(conversation_id=conversation.id).all()
                    total_words = sum(len(seg.text.split()) for seg in segments)
                    conversation.word_count = total_words
                    
                    db.session.commit()
                    
                    logger.info(f'[websocket] Finalized conversation {conversation.id} with {total_words} words')
            
            # Clean up session
            del active_sessions[session_id]
            
            emit('session_finalized', {
                'session_id': session_id,
                'total_segments': session_info['segment_count'],
                'duration_s': int(time.time() - session_info['start_time'])
            })
            
        except Exception as e:
            logger.error(f'[websocket] Error finalizing session {session_id}: {e}')
            emit('session_error', {'error': 'Failed to finalize session'})
    else:
        logger.warning(f'[websocket] No active session to finalize: {session_id}')

# Legacy event handlers for compatibility
@socketio.on('transcription:start')
def handle_transcription_start(data):
    """Handle start of transcription session (legacy)"""
    logger.info('[websocket] Legacy transcription:start event')
    emit('transcription:started', {'status': 'started'})

@socketio.on('transcription:stop')
def handle_transcription_stop(data):
    """Handle end of transcription session (legacy)"""
    logger.info('[websocket] Legacy transcription:stop event')
    emit('transcription:stopped', {'status': 'stopped'})

@socketio.on('audio_data')
def handle_audio_data(data):
    """Legacy audio_data handler - redirect to audio_chunk"""
    logger.info('[websocket] Legacy audio_data event, redirecting to audio_chunk')
    handle_audio_chunk(data)