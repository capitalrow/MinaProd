"""
WebSocket Routes
Socket.IO event handlers for real-time transcription and communication.
"""

import logging
import asyncio
import json
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room, disconnect

from services.transcription_service import TranscriptionService, TranscriptionServiceConfig
from models.session import Session

logger = logging.getLogger(__name__)

# Global transcription service instance
_transcription_service = None

def get_transcription_service():
    """Get or create the global transcription service instance."""
    global _transcription_service
    if _transcription_service is None:
        config = TranscriptionServiceConfig()
        _transcription_service = TranscriptionService(config)
    return _transcription_service

def register_websocket_handlers(socketio):
    """
    Register all Socket.IO event handlers.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {
            'status': 'connected',
            'client_id': request.sid,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info(f"Client disconnected: {request.sid}")
        
        # Clean up any active sessions for this client
        try:
            service = get_transcription_service()
            # In a real implementation, we'd track client-session mappings
            logger.info(f"Cleaned up resources for client: {request.sid}")
        except Exception as e:
            logger.error(f"Error during disconnect cleanup: {e}")
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """
        Handle client joining a transcription session.
        
        Args:
            data: Dictionary containing session_id and optional configuration
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # Verify session exists
            session = Session.query.filter_by(session_id=session_id).first()
            if not session:
                emit('error', {'message': f'Session {session_id} not found'})
                return
            
            # Join Socket.IO room
            join_room(session_id)
            
            # Get or create transcription service session
            service = get_transcription_service()
            
            # If session is not active in service, start it
            if session_id not in service.active_sessions:
                try:
                    asyncio.create_task(service.start_session(session_id))
                except Exception as e:
                    logger.error(f"Error starting service session: {e}")
            
            # Add callback for this session
            def session_callback(transcription_result):
                """Callback to emit transcription results to room."""
                try:
                    socketio.emit('transcription_result', {
                        'session_id': session_id,
                        'text': transcription_result.text,
                        'confidence': transcription_result.confidence,
                        'is_final': transcription_result.is_final,
                        'timestamp': transcription_result.timestamp,
                        'language': transcription_result.language,
                        'words': transcription_result.words,
                        'metadata': transcription_result.metadata
                    }, room=session_id)
                except Exception as e:
                    logger.error(f"Error emitting transcription result: {e}")
            
            service.add_session_callback(session_id, session_callback)
            
            emit('session_joined', {
                'session_id': session_id,
                'session': session.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Client {request.sid} joined session {session_id}")
            
        except Exception as e:
            logger.error(f"Error joining session: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """
        Handle client leaving a transcription session.
        
        Args:
            data: Dictionary containing session_id
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # Leave Socket.IO room
            leave_room(session_id)
            
            emit('session_left', {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Client {request.sid} left session {session_id}")
            
        except Exception as e:
            logger.error(f"Error leaving session: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('start_transcription')
    def handle_start_transcription(data):
        """
        Handle start transcription request.
        
        Args:
            data: Dictionary with session configuration
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # Update session status
            session = Session.query.filter_by(session_id=session_id).first()
            if session:
                session.start_session()
            
            # Notify room
            socketio.emit('transcription_started', {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
            
            logger.info(f"Started transcription for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error starting transcription: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('stop_transcription')
    def handle_stop_transcription(data):
        """
        Handle stop transcription request.
        
        Args:
            data: Dictionary containing session_id
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # End service session
            service = get_transcription_service()
            if session_id in service.active_sessions:
                final_stats = asyncio.create_task(service.end_session(session_id))
            
            # Update database session
            session = Session.query.filter_by(session_id=session_id).first()
            if session and session.is_active:
                session.end_session()
            
            # Notify room
            socketio.emit('transcription_stopped', {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
            
            logger.info(f"Stopped transcription for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error stopping transcription: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        """
        Handle incoming audio chunk for real-time transcription.
        
        Args:
            data: Dictionary containing session_id and audio data
        """
        try:
            session_id = data.get('session_id')
            audio_data = data.get('audio_data')
            timestamp = data.get('timestamp')
            
            if not session_id or not audio_data:
                emit('error', {'message': 'session_id and audio_data are required'})
                return
            
            # Convert base64 audio data to bytes if needed
            if isinstance(audio_data, str):
                import base64
                try:
                    audio_bytes = base64.b64decode(audio_data)
                except Exception as e:
                    emit('error', {'message': f'Invalid audio data format: {str(e)}'})
                    return
            else:
                audio_bytes = audio_data
            
            # Process audio through transcription service
            service = get_transcription_service()
            
            # Use asyncio to handle the async service call
            async def process_audio():
                try:
                    result = await service.process_audio(
                        session_id=session_id,
                        audio_data=audio_bytes,
                        timestamp=timestamp
                    )
                    
                    if result and result.get('transcription'):
                        # Emit interim result immediately
                        socketio.emit('interim_result', {
                            'session_id': session_id,
                            'vad': result.get('vad', {}),
                            'transcription': result['transcription'],
                            'timestamp': result['timestamp']
                        }, room=session_id)
                
                except Exception as e:
                    logger.error(f"Error processing audio for session {session_id}: {e}")
                    socketio.emit('processing_error', {
                        'session_id': session_id,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=session_id)
            
            # Schedule the coroutine
            asyncio.create_task(process_audio())
            
        except Exception as e:
            logger.error(f"Error handling audio chunk: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping for connection health check."""
        emit('pong', {
            'timestamp': datetime.utcnow().isoformat(),
            'client_id': request.sid
        })
    
    @socketio.on('get_session_status')
    def handle_get_session_status(data):
        """
        Get current session status and statistics.
        
        Args:
            data: Dictionary containing session_id
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # Get database session
            session = Session.query.filter_by(session_id=session_id).first()
            if not session:
                emit('error', {'message': f'Session {session_id} not found'})
                return
            
            # Get service status
            service = get_transcription_service()
            service_status = None
            
            try:
                if session_id in service.active_sessions:
                    service_status = service.get_session_status(session_id)
            except Exception as e:
                logger.warning(f"Could not get service status: {e}")
            
            # Combine database and service information
            status_data = session.to_dict()
            if service_status:
                status_data['service_status'] = service_status
            
            emit('session_status', status_data)
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('update_session_config')
    def handle_update_session_config(data):
        """
        Update session configuration in real-time.
        
        Args:
            data: Dictionary containing session_id and config updates
        """
        try:
            session_id = data.get('session_id')
            config_updates = data.get('config', {})
            
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            # Update database session
            session = Session.query.filter_by(session_id=session_id).first()
            if not session:
                emit('error', {'message': f'Session {session_id} not found'})
                return
            
            # Apply configuration updates
            for key, value in config_updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            session.updated_at = datetime.utcnow()
            session.save()
            
            # Update service configuration if session is active
            service = get_transcription_service()
            if session_id in service.active_sessions:
                # Update VAD and transcription service configs
                vad_config = {k: v for k, v in config_updates.items() 
                             if k.startswith('vad_') or k in ['sample_rate']}
                if vad_config:
                    service.vad_service.update_config(**vad_config)
                
                transcription_config = {k: v for k, v in config_updates.items() 
                                      if k in ['language', 'min_confidence']}
                if transcription_config:
                    service.whisper_service.update_config(**transcription_config)
            
            # Notify room of configuration update
            socketio.emit('config_updated', {
                'session_id': session_id,
                'config': config_updates,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
            
            emit('config_update_success', {
                'session_id': session_id,
                'applied_config': config_updates
            })
            
            logger.info(f"Updated config for session {session_id}: {config_updates}")
            
        except Exception as e:
            logger.error(f"Error updating session config: {e}")
            emit('error', {'message': str(e)})
    
    # Global error handler for Socket.IO
    @socketio.on_error_default
    def default_error_handler(e):
        """Handle Socket.IO errors."""
        logger.error(f"Socket.IO error: {e}")
        emit('error', {
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    return socketio
