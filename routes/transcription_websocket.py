# routes/transcription_websocket.py
"""
WebSocket handlers specifically for the /transcription namespace
"""
import logging
import time
import uuid
import base64
import requests
from datetime import datetime

from flask import request
from flask_socketio import emit, disconnect, join_room, leave_room

# Import the socketio instance from the consolidated app
from app import socketio

logger = logging.getLogger(__name__)

# Session state storage
active_sessions = {}

@socketio.on('connect', namespace='/transcription')
def on_connect():
    """Handle client connection to transcription namespace"""
    logger.info(f"[transcription] Client connected: {request.sid}")
    emit('status', {'status': 'connected', 'message': 'Connected to transcription service'})

@socketio.on('disconnect', namespace='/transcription')
def on_disconnect():
    """Handle client disconnection"""
    logger.info(f"[transcription] Client disconnected: {request.sid}")
    # Clean up any active sessions for this client
    sessions_to_remove = []
    for session_id, session_info in active_sessions.items():
        if session_info.get('client_sid') == request.sid:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        active_sessions.pop(session_id, None)
        logger.info(f"[transcription] Cleaned up session: {session_id}")

@socketio.on('start_session', namespace='/transcription')
def on_start_session(data):
    """Start a new transcription session"""
    try:
        session_id = str(uuid.uuid4())
        
        # Store session info
        active_sessions[session_id] = {
            'client_sid': request.sid,
            'started_at': datetime.utcnow(),
            'language': data.get('language', 'en'),
            'enhance_audio': data.get('enhance_audio', True),
            'audio_buffer': bytearray()
        }
        
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
        emit('error', {'message': f'Failed to start session: {str(e)}'})

@socketio.on('audio_data', namespace='/transcription')
def on_audio_data(data):
    """Handle incoming audio data"""
    try:
        # Handle structured audio data from frontend
        if isinstance(data, dict) and 'data' in data:
            # New structured format
            try:
                audio_bytes = base64.b64decode(data['data'])
                mime_type = data.get('mimeType', 'audio/wav')
                logger.info(f"[transcription] Received {mime_type} audio: {len(audio_bytes)} bytes")
            except Exception as e:
                logger.error(f"[transcription] Failed to decode structured audio: {e}")
                emit('error', {'message': 'Invalid audio data format'})
                return
        elif isinstance(data, str):
            # Legacy base64 string format
            try:
                audio_bytes = base64.b64decode(data)
                mime_type = 'audio/webm'
            except Exception as e:
                logger.error(f"[transcription] Invalid base64 audio data: {e}")
                emit('error', {'message': 'Invalid base64 audio data'})
                return
        elif isinstance(data, (bytes, bytearray)):
            # Raw bytes format
            audio_bytes = bytes(data)
            mime_type = 'audio/webm'
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
        
        # Process audio via unified transcription API
        try:
            # Send audio with proper format info
            file_extension = '.wav' if 'wav' in mime_type else '.webm'
            response = requests.post(
                'http://localhost:5000/api/transcribe-audio',
                files={'audio': (f'audio{file_extension}', audio_bytes, mime_type)},
                data={
                    'session_id': session_id,
                    'is_interim': 'true',
                    'chunk_id': str(int(time.time() * 1000))
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('text'):
                    emit('transcription_result', {
                        'transcript': result['text'],
                        'is_final': result.get('is_final', False),
                        'confidence': result.get('confidence', 0.9),
                        'segment_id': result.get('chunk_id', str(uuid.uuid4())),
                        'latency_ms': result.get('processing_time', 100)
                    })
                else:
                    # Silent handling for empty results
                    pass
            else:
                logger.warning(f"[transcription] API error: {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"[transcription] API request failed: {e}")
            # Don't emit error for network issues, just log them
        
    except Exception as e:
        logger.error(f"[transcription] Error processing audio: {e}")
        emit('error', {'message': f'Audio processing error: {str(e)}'})

@socketio.on('end_session', namespace='/transcription')
def on_end_session(data=None):
    """End the current transcription session"""
    try:
        # Find sessions for this client
        sessions_to_end = []
        for session_id, session_info in active_sessions.items():
            if session_info.get('client_sid') == request.sid:
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