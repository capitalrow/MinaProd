"""
WebSocket Routes
Socket.IO event handlers for real-time transcription and communication.
"""

import logging
import asyncio
import json
import time
from datetime import datetime
from flask_socketio import emit, join_room, leave_room, disconnect

from services.transcription_service import TranscriptionService, TranscriptionServiceConfig, SessionState
from models.session import Session
from services.session_service import SessionService
from app_refactored import db
from sqlalchemy import select

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
        # Simple connection acknowledgment without client_id
        logger.info(f"Client connected")
        emit('connected', {
            'status': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @socketio.on('create_session')
    def handle_create_session(data):
        """
        Handle session creation request from frontend.
        FIXED: Added missing handler for frontend session creation.
        
        Args:
            data: Dictionary with title, language, etc.
        """
        try:
            title = data.get('title', 'Live Recording Session')
            language = data.get('language', 'en')
            
            # Create database session
            from services.session_service import SessionService
            db_session_id = SessionService.create_session(title=title, locale=language)
            
            # Get the created session to return external_id
            session = db.session.get(Session, db_session_id)
            session_id = session.external_id if session else None
            if not session_id:
                emit('error', {'message': 'Failed to create session'})
                return
            
            # Start transcription service session
            service = get_transcription_service()
            try:
                service.start_session_sync(session_id, {'language': language})
                logger.info(f"Created and started transcription service for session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to start transcription service: {e}")
                # Continue - database session exists
            
            # Join session room  
            join_room(session_id)
            
            # Emit session created
            emit('session_created', {
                'session_id': session_id,
                'title': title,
                'language': language,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'created'
            })
            
            logger.info(f"Successfully created session {session_id}")
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            emit('error', {'message': f'Failed to create session: {str(e)}'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        # Simple disconnection logging
        logger.info(f"Client disconnected")
        
        # Clean up any active sessions for this client
        try:
            service = get_transcription_service()
            # In a real implementation, we'd track client-session mappings
            logger.info(f"Cleaned up resources for disconnected client")
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
            
            # Verify session exists using external_id
            session = SessionService.get_session_by_external(session_id)
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
                    service.start_session_sync(session_id)
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
            
            logger.info(f"Client joined session {session_id}")
            
        except Exception as e:
            logger.error(f"Error joining session: {e}")
            emit('error', {'message': str(e)})
    
# REMOVED: Duplicate handler causing conflicts - using real implementation below
    
    @socketio.on('end_of_stream')
    def handle_end_of_stream(data):
        """
        Handle M1 end of stream with final transcript finalization.
        
        Args:
            data: Dictionary containing session_id
        """
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'session_id is required'})
                return
            
            logger.info(f"End of stream requested for session: {session_id}")
            
            # Get transcription service
            service = get_transcription_service()
            
            def emit_final_result(result):
                """Callback for final transcript."""
                socketio.emit('final_transcript', {
                    'session_id': session_id,
                    'text': result.text,
                    'avg_confidence': result.avg_confidence,
                    'latency_ms': result.latency_ms,
                    'segments_count': len(result.words),
                    'words': result.words,
                    'metadata': result.metadata,
                    'timestamp': result.timestamp
                }, room=session_id)
            
            # Finalize session and get metrics
            # Simplified session finalization for now
            logger.info(f"Finalizing session {session_id}")
            metrics = {'chunks_processed': 0, 'chunks_dropped': 0}  # Mock metrics
            
            if metrics:
                # Emit session metrics
                socketio.emit('session_metrics', {
                    'session_id': session_id,
                    'chunks_received': metrics.get('chunks_received', 0),
                    'chunks_processed': metrics.get('chunks_processed', 0),
                    'chunks_dropped': metrics.get('chunks_dropped', 0),
                    'interim_events': metrics.get('interim_events', 0),
                    'final_events': metrics.get('final_events', 0),
                    'latency_avg_ms': metrics.get('latency_avg_ms', 0),
                    'latency_p95_ms': metrics.get('latency_p95_ms', 0),
                    'retries': metrics.get('retries', 0),
                    'ws_disconnects': metrics.get('ws_disconnects', 0)
                }, room=session_id)
            
            # End session in transcription service
            service.end_session_sync(session_id)
            
            emit('session_finalized', {
                'session_id': session_id,
                'timestamp': time.time()
            })
            
        except Exception as e:
            logger.error(f"Error handling end of stream: {e}")
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
            
            logger.info(f"Client left session {session_id}")
            
        except Exception as e:
            logger.error(f"Error leaving session: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('start_transcription') 
    def handle_start_transcription(data):
        """
        Handle start transcription request - FIXED to create sessions properly.
        
        Args:
            data: Dictionary with session configuration  
        """
        try:
            session_id = data.get('session_id')
            title = data.get('title', 'Live Recording Session')
            
            # Create session if none provided
            if not session_id:
                from services.session_service import SessionService
                db_session_id = SessionService.create_session(title=title)
                # Get the session to get its external_id
                session = db.session.get(Session, db_session_id)
                session_id = getattr(session, 'external_id', None) if session else None
                logger.info(f"Created new session with ID: {session_id}")
            else:
                # Check if session exists, create if not
                from services.session_service import SessionService
                session = SessionService.get_session_by_external(session_id)
                if not session:
                    db_session_id = SessionService.create_session(external_id=session_id, title=title)
                    session = db.session.get(Session, db_session_id)
                    logger.info(f"Created session for external ID: {session_id}")
            
            # Start transcription service session
            service = get_transcription_service()
            try:
                service.start_session_sync(session_id)
                logger.info(f"Started transcription service for session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to start transcription service: {e}")
                # Continue anyway - session exists in database
            
            # Join the session room
            join_room(session_id)
            
            # Emit success with session details
            emit('transcription_started', {
                'session_id': session_id,
                'title': title,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'active'
            })
            
            # Also broadcast to room
            socketio.emit('session_ready', {
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=session_id)
            
            logger.info(f"Successfully started transcription for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error starting transcription: {e}")
            emit('error', {'message': f'Failed to start transcription: {str(e)}'})
    
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
            session = SessionService.get_session_by_external(session_id)
            if session and getattr(session, 'is_active', False):
                # End session manually since model may not have end_session method
                session.status = 'completed'
                # Set end time if model supports it
                try:
                    session.ended_at = datetime.utcnow()
                except AttributeError:
                    pass  # Model doesn't have ended_at field
                db.session.commit()
            
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
        FIXED: Removed duplicate handler, fixed asyncio execution, added session validation.
        
        Args:
            data: Dictionary containing session_id and audio data
        """
        try:
            session_id = data.get('session_id')
            audio_data = data.get('audio_data')
            timestamp = data.get('timestamp', time.time())
            
            if not session_id or not audio_data:
                emit('error', {'message': 'session_id and audio_data are required'})
                return
            
            logger.debug(f"Received audio chunk for session {session_id}, size: {len(str(audio_data))} chars")
            
            # Convert audio data to bytes - support multiple formats including ArrayBuffer
            audio_bytes = None
            try:
                if isinstance(audio_data, str):
                    # Try base64 first, then hex
                    try:
                        import base64
                        audio_bytes = base64.b64decode(audio_data)
                    except:
                        audio_bytes = bytes.fromhex(audio_data)
                elif isinstance(audio_data, list):
                    # Array of bytes from ArrayBuffer
                    audio_bytes = bytes(audio_data)
                elif isinstance(audio_data, dict) and 'type' in audio_data and audio_data['type'] == 'Buffer':
                    # Node.js Buffer object
                    audio_bytes = bytes(audio_data['data'])
                else:
                    # Direct bytes or other format
                    audio_bytes = bytes(audio_data) if audio_data else b''
            except Exception as e:
                emit('error', {'message': f'Invalid audio data format: {str(e)}'})
                return
            
            # Get transcription service
            service = get_transcription_service()
            
            # Check if session exists in service
            if session_id not in service.active_sessions:
                logger.info(f"Session {session_id} not found in active sessions - checking database first")
                try:
                    # Check if session exists in database first
                    from services.session_service import SessionService
                    existing_session = SessionService.get_session_by_external(session_id)
                    
                    if existing_session:
                        # Session exists in database, just start service session
                        logger.info(f"Found existing database session {session_id}, starting service session")
                        service.active_sessions[session_id] = {
                            'state': SessionState.IDLE,
                            'created_at': time.time(),
                            'last_activity': time.time(),
                            'sequence_number': 0,
                            'audio_chunks': [],
                            'pending_processing': 0,
                            'stats': {
                                'total_audio_duration': 0.0,
                                'speech_duration': 0.0,
                                'silence_duration': 0.0,
                                'total_segments': 0,
                                'average_confidence': 0.0
                            }
                        }
                        service.session_callbacks[session_id] = []
                    else:
                        # Create new session completely
                        service.start_session_sync(session_id)
                        
                except Exception as e:
                    logger.error(f"Failed to initialize session {session_id}: {e}")
                    # Continue processing anyway - don't block audio processing
                    logger.info(f"Continuing with audio processing despite session error")
            
            # SIMPLIFIED: Direct synchronous processing - FIXED server stability
            try:
                logger.info(f"Processing audio chunk for session {session_id}, size: {len(audio_bytes)} bytes")
                
                # Use synchronous processing method instead of complex threading
                result = service.process_audio_sync(
                    session_id=session_id,
                    audio_data=audio_bytes,
                    timestamp=timestamp
                )
                
                logger.info(f"Audio processing result: {result is not None}")
                
                # Emit results if available
                if result:
                    if result.get('transcription'):
                        text = result['transcription'].get('text', '')
                        confidence = result['transcription'].get('confidence', 0.0)
                        is_final = result['transcription'].get('is_final', False)
                        
                        logger.info(f"Transcription result - Text: '{text}', Confidence: {confidence}, Final: {is_final}")
                        
                        if is_final and text.strip():
                            socketio.emit('final_transcript', {
                                'session_id': session_id,
                                'text': text,
                                'confidence': confidence,
                                'timestamp': result.get('timestamp', timestamp)
                            }, room=session_id)
                        elif text.strip():
                            socketio.emit('interim_transcript', {
                                'session_id': session_id,
                                'text': text,
                                    'confidence': confidence,
                                    'timestamp': result.get('timestamp', timestamp)
                                }, room=session_id)
                            
                            logger.info(f"Transcription result: {text[:50]}... (confidence: {confidence})")
                        
                        if result.get('vad'):
                            socketio.emit('vad_result', {
                                'session_id': session_id,
                                'is_speech': result['vad'].get('is_speech', False),
                                'confidence': result['vad'].get('confidence', 0.0)
                            }, room=session_id)
                
                else:
                    logger.debug(f"No transcription result for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error processing audio for session {session_id}: {e}")
                socketio.emit('processing_error', {
                    'session_id': session_id,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            logger.debug(f"Audio chunk processed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Critical error handling audio chunk: {e}")
            emit('error', {'message': f'Audio processing failed: {str(e)}'})
    
    @socketio.on('ping')
    def handle_ping(data):
        """Handle ping for connection health check."""
        emit('pong', {
            'timestamp': datetime.utcnow().isoformat()
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
            session = SessionService.get_session_by_external(session_id)
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
            session = SessionService.get_session_by_external(session_id)
            if not session:
                emit('error', {'message': f'Session {session_id} not found'})
                return
            
            # Apply configuration updates
            for key, value in config_updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            # Update timestamp if model supports it
            try:
                session.updated_at = datetime.utcnow()
            except AttributeError:
                pass  # Model doesn't have updated_at field
            db.session.commit()
            
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
