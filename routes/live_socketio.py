"""
Socket.IO handlers for live transcription
"""
from flask import request
from flask_socketio import emit
from app import socketio
import logging
import time

logger = logging.getLogger(__name__)

@socketio.on('connect', namespace='/live-transcription')
def handle_connect():
    """Client connected to /live-transcription namespace"""
    logger.info("Client connected to live transcription")
    emit('connected', {'status': 'connected', 'message': 'Ready for live transcription'})

@socketio.on('disconnect', namespace='/live-transcription')
def handle_disconnect():
    """Client disconnected from /live-transcription namespace"""
    logger.info(f"Client disconnected from live transcription")

@socketio.on('start_session', namespace='/live-transcription')
def handle_start_session(data):
    """Start a new transcription session"""
    logger.info(f"Starting transcription session with data: {data}")
    emit('session_started', {
        'status': 'started',
        'session_id': f'session_{int(time.time())}',
        'message': 'Transcription session started'
    })

@socketio.on('audio_data', namespace='/live-transcription')
def handle_audio_data(data):
    """Receive audio data for transcription"""
    logger.debug(f"Received audio data: {len(data.get('data', [])) if isinstance(data, dict) else 0} bytes")
    # TODO: Process audio and emit transcription results
    # For now, just acknowledge receipt
    emit('audio_received', {'status': 'ok'})

@socketio.on('end_session', namespace='/live-transcription')
def handle_end_session():
    """End the transcription session"""
    logger.info(f"Ending transcription session")
    emit('session_ended', {
        'status': 'ended',
        'message': 'Transcription session ended'
    })

def register_live_socketio():
    """Register the live transcription Socket.IO handlers"""
    logger.info("✅ Live transcription Socket.IO handlers registered")
