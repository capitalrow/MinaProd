"""
WebSocket event handlers for real-time transcription
"""
from extensions import socketio
from flask_socketio import emit

@socketio.on('connect')
def handle_connect():
    print('[websocket] Client connected')
    emit('server_hello', {'message': 'Connected to Mina transcription service'})

@socketio.on('disconnect')
def handle_disconnect():
    print('[websocket] Client disconnected')

@socketio.on('transcription:start')
def handle_transcription_start(data):
    """Handle start of transcription session"""
    print('[websocket] Transcription session started:', data)
    emit('transcription:started', {'status': 'started'})

@socketio.on('transcription:stop')
def handle_transcription_stop(data):
    """Handle end of transcription session"""
    print('[websocket] Transcription session stopped:', data)
    emit('transcription:stopped', {'status': 'stopped'})

# Example handlers for the events used in mina.socket.js
@socketio.on('audio_data')
def handle_audio_data(data):
    """Handle incoming audio data for transcription"""
    # In a real implementation, this would process audio and return transcription
    # For now, just acknowledge receipt
    emit('transcription:interim', {
        'text': '[Mock interim transcription...]',
        'start_ms': 0,
        'end_ms': 1000
    })
