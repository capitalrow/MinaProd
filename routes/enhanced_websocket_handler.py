"""
Enhanced WebSocket Handler - Google Recorder Level Integration
Integrates the enhanced transcription service with WebSocket infrastructure for real-time transcription.
Addresses Phase 0 hotfixes for production-ready performance.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional
import traceback
from dataclasses import asdict

# Import enhanced services
from services.enhanced_transcription_service import EnhancedTranscriptionService, GoogleRecorderConfig
from services.hallucination_prevention_system import ValidationContext
from services.hallucination_prevention_system import HallucinationPreventionSystem

# Import existing models and services
from models import Session, Segment
from app_refactored import db
from services.session_service import SessionService

logger = logging.getLogger(__name__)

class EnhancedWebSocketHandler:
    """
    🎯 Google Recorder-level WebSocket handler.
    
    Integrates enhanced transcription service with WebSocket infrastructure
    for production-ready real-time transcription with <400ms latency.
    """
    
    def __init__(self):
        # Initialize enhanced transcription service
        self.enhanced_service = EnhancedTranscriptionService(GoogleRecorderConfig())
        
        # Initialize hallucination prevention
        self.hallucination_prevention = HallucinationPreventionSystem(strictness_level=0.8)
        
        # Session management
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.session_to_connection: Dict[str, str] = {}
        
        # Performance tracking
        self.metrics = {
            'total_connections': 0,
            'active_sessions': 0,
            'total_chunks_processed': 0,
            'avg_latency_ms': 0.0,
            'error_count': 0
        }
        
        logger.info("🎯 Enhanced WebSocket Handler initialized")
    
    async def handle_connection(self, websocket, path):
        """🔗 Handle new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        client_ip = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        
        try:
            self.active_connections[connection_id] = {
                'websocket': websocket,
                'connected_at': time.time(),
                'client_ip': client_ip,
                'session_id': None,
                'last_activity': time.time()
            }
            
            self.metrics['total_connections'] += 1
            
            logger.info(f"🔗 New connection: {connection_id} from {client_ip}")
            
            # Send initial connection acknowledgment
            await self._send_message(websocket, {
                'type': 'connection_ack',
                'connection_id': connection_id,
                'enhanced_features': {
                    'google_recorder_level': True,
                    'latency_optimization': True,
                    'context_correlation': True,
                    'hallucination_prevention': True,
                    'adaptive_quality': True
                },
                'timestamp': time.time()
            })
            
            # Handle messages
            async for message in websocket:
                await self._handle_message(connection_id, message)
                
        except Exception as e:
            logger.error(f"❌ Connection error for {connection_id}: {e}")
            await self._cleanup_connection(connection_id)
        finally:
            await self._cleanup_connection(connection_id)
    
    async def _handle_message(self, connection_id: str, message: str):
        """📨 Handle incoming WebSocket message."""
        try:
            if connection_id not in self.active_connections:
                logger.warning(f"⚠️ Message from unknown connection: {connection_id}")
                return
            
            connection = self.active_connections[connection_id]
            connection['last_activity'] = time.time()
            
            # Parse message
            try:
                data = json.loads(message)
            except json.JSONDecodeError as e:
                await self._send_error(connection['websocket'], 'invalid_json', f"Invalid JSON: {e}")
                return
            
            message_type = data.get('type')
            
            # Route message to appropriate handler
            if message_type == 'start_session':
                await self._handle_start_session(connection_id, data)
            elif message_type == 'audio_chunk':
                await self._handle_audio_chunk(connection_id, data)
            elif message_type == 'end_session':
                await self._handle_end_session(connection_id, data)
            elif message_type == 'ping':
                await self._handle_ping(connection_id, data)
            else:
                await self._send_error(connection['websocket'], 'unknown_message_type', 
                                     f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"❌ Message handling error for {connection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if connection_id in self.active_connections:
                await self._send_error(self.active_connections[connection_id]['websocket'], 
                                     'message_processing_error', str(e))
    
    async def _handle_start_session(self, connection_id: str, data: Dict[str, Any]):
        """🚀 Handle session start request."""
        try:
            connection = self.active_connections[connection_id]
            
            # Generate session ID
            session_id = data.get('session_id') or str(uuid.uuid4())
            
            # Start enhanced transcription session
            result = await self.enhanced_service.start_session(
                session_id=session_id,
                language=data.get('language', 'en'),
                quality_mode=data.get('quality_mode', 'adaptive')
            )
            
            if result['success']:
                # Update connection tracking
                connection['session_id'] = session_id
                self.session_to_connection[session_id] = connection_id
                self.metrics['active_sessions'] += 1
                
                # Create database session record
                try:
                    db_session = Session(
                        external_id=session_id,
                        status='active',
                        locale=data.get('language', 'en'),
                        started_at=time.time(),
                        client_info=json.dumps({
                            'ip': connection['client_ip'],
                            'user_agent': data.get('user_agent', ''),
                            'enhanced_features': True
                        })
                    )
                    db.session.add(db_session)
                    db.session.commit()
                    
                    logger.info(f"🚀 Enhanced session started: {session_id}")
                    
                except Exception as db_error:
                    logger.error(f"❌ Database session creation failed: {db_error}")
                    # Continue without database - don't fail the session
                
                # Send success response
                await self._send_message(connection['websocket'], {
                    'type': 'session_started',
                    'session_id': session_id,
                    'enhanced_features': result.get('enhanced_features', {}),
                    'timestamp': time.time()
                })
                
            else:
                await self._send_error(connection['websocket'], 'session_start_failed', 
                                     result.get('error', 'Unknown error'))
                
        except Exception as e:
            logger.error(f"❌ Session start failed for {connection_id}: {e}")
            await self._send_error(self.active_connections[connection_id]['websocket'], 
                                 'session_start_error', str(e))
    
    async def _handle_audio_chunk(self, connection_id: str, data: Dict[str, Any]):
        """🎵 Handle audio chunk with enhanced processing."""
        start_time = time.time()
        
        try:
            connection = self.active_connections[connection_id]
            session_id = connection.get('session_id')
            
            if not session_id:
                await self._send_error(connection['websocket'], 'no_active_session', 
                                     'No active session. Start a session first.')
                return
            
            # Extract audio data
            audio_data = data.get('audio_data')
            if not audio_data:
                await self._send_error(connection['websocket'], 'missing_audio_data', 
                                     'Audio data is required')
                return
            
            # Decode base64 audio data
            import base64
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception as e:
                await self._send_error(connection['websocket'], 'invalid_audio_data', 
                                     f'Failed to decode audio data: {e}')
                return
            
            # Process with enhanced transcription service
            result = await self.enhanced_service.process_audio_chunk(
                session_id=session_id,
                audio_data=audio_bytes,
                is_final=data.get('is_final', False),
                timestamp=data.get('timestamp')
            )
            
            if result['success']:
                # Validate with hallucination prevention
                if result.get('transcript', '').strip():
                    validation_context = ValidationContext(
                        original_text=result['transcript'],
                        audio_duration=data.get('duration', 1.0),
                        audio_quality_score=result.get('quality_score', 0.8),
                        confidence_score=result.get('confidence', 0.8),
                        previous_segments=[],  # TODO: implement segment history
                        environmental_noise_level=0.1,  # TODO: get from audio analysis
                        speaker_detection_confidence=0.8,
                        language_detection_confidence=0.9
                    )
                    
                    hallucination_check = self.hallucination_prevention.validate_transcription(
                        result['transcript'], validation_context, session_id
                    )
                    
                    # Apply hallucination prevention
                    if hallucination_check.is_hallucination and hallucination_check.prevention_action == 'block':
                        logger.warning(f"🛡️ Blocked hallucination: {hallucination_check.evidence}")
                        # Don't send blocked content
                        return
                    elif hallucination_check.corrected_text:
                        result['transcript'] = hallucination_check.corrected_text
                
                # Update metrics
                self.metrics['total_chunks_processed'] += 1
                processing_latency = (time.time() - start_time) * 1000
                
                # Update average latency
                total_chunks = self.metrics['total_chunks_processed']
                current_avg = self.metrics['avg_latency_ms']
                self.metrics['avg_latency_ms'] = ((current_avg * (total_chunks - 1)) + processing_latency) / total_chunks
                
                # Send transcription result
                response = {
                    'type': 'transcription_result',
                    'session_id': session_id,
                    'transcript': result.get('transcript', ''),
                    'confidence': result.get('confidence', 0.0),
                    'is_final': result.get('is_final', False),
                    'latency_ms': result.get('latency_ms', processing_latency),
                    'meets_target': result.get('meets_target', False),
                    'quality_score': result.get('quality_score', 0.0),
                    'chunk_id': result.get('chunk_id', 0),
                    'timestamp': time.time()
                }
                
                # Add enhanced features if available
                if 'context_correlation' in result:
                    response['context_correlation'] = result['context_correlation']
                
                if 'interim_update' in result:
                    response['interim_update'] = result['interim_update']
                
                await self._send_message(connection['websocket'], response)
                
                # Save to database if final
                if result.get('is_final', False) and result.get('transcript', '').strip():
                    await self._save_segment_to_db(session_id, result)
                
            else:
                self.metrics['error_count'] += 1
                await self._send_error(connection['websocket'], 'transcription_failed', 
                                     result.get('error', 'Transcription processing failed'))
                
        except Exception as e:
            logger.error(f"❌ Audio chunk processing failed for {connection_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            self.metrics['error_count'] += 1
            if connection_id in self.active_connections:
                await self._send_error(self.active_connections[connection_id]['websocket'], 
                                     'audio_processing_error', str(e))
    
    async def _handle_end_session(self, connection_id: str, data: Dict[str, Any]):
        """⏹️ Handle session end request."""
        try:
            connection = self.active_connections[connection_id]
            session_id = connection.get('session_id')
            
            if session_id:
                # Stop enhanced transcription session
                result = await self.enhanced_service.stop_session(session_id)
                
                # Update database session
                try:
                    from sqlalchemy import select
                    stmt = select(Session).where(Session.external_id == session_id)
                    db_session = db.session.scalars(stmt).first()
                    
                    if db_session:
                        db_session.status = 'completed'
                        # Note: ended_at and statistics fields may need to be added to Session model
                        # db_session.ended_at = time.time()
                        
                        # Add session statistics if fields exist
                        if result.get('success', False):
                            final_stats = result.get('final_stats', {})
                            # db_session.total_segments = final_stats.get('chunk_count', 0)
                            # db_session.statistics = json.dumps({
                            #     'enhanced_features_used': True,
                            #     'avg_latency_ms': final_stats.get('avg_latency_ms', 0),
                            #     'avg_confidence': final_stats.get('avg_confidence', 0),
                            #     'total_duration': final_stats.get('session_duration', 0)
                            # })
                        
                        db.session.commit()
                        
                except Exception as db_error:
                    logger.error(f"❌ Database session update failed: {db_error}")
                
                # Clean up session tracking
                connection['session_id'] = None
                if session_id in self.session_to_connection:
                    del self.session_to_connection[session_id]
                
                self.metrics['active_sessions'] = max(0, self.metrics['active_sessions'] - 1)
                
                # Send response
                await self._send_message(connection['websocket'], {
                    'type': 'session_ended',
                    'session_id': session_id,
                    'final_stats': result.get('final_stats', {}),
                    'timestamp': time.time()
                })
                
                logger.info(f"⏹️ Enhanced session ended: {session_id}")
                
            else:
                await self._send_error(connection['websocket'], 'no_active_session', 
                                     'No active session to end')
                
        except Exception as e:
            logger.error(f"❌ Session end failed for {connection_id}: {e}")
            if connection_id in self.active_connections:
                await self._send_error(self.active_connections[connection_id]['websocket'], 
                                     'session_end_error', str(e))
    
    async def _handle_ping(self, connection_id: str, data: Dict[str, Any]):
        """🏓 Handle ping request."""
        try:
            connection = self.active_connections[connection_id]
            
            await self._send_message(connection['websocket'], {
                'type': 'pong',
                'timestamp': time.time(),
                'metrics': self._get_connection_metrics(connection_id)
            })
            
        except Exception as e:
            logger.error(f"❌ Ping handling failed for {connection_id}: {e}")
    
    async def _save_segment_to_db(self, session_id: str, result: Dict[str, Any]):
        """💾 Save transcription segment to database."""
        try:
            # Get database session
            from sqlalchemy import select
            stmt = select(Session).where(Session.external_id == session_id)
            db_session = db.session.scalars(stmt).first()
            
            if db_session:
                segment = Segment(
                    session_id=db_session.id,
                    text=result['transcript'],
                    confidence=result.get('confidence', 0.0),
                    start_time=result.get('start_time', 0.0),
                    end_time=result.get('end_time', 0.0),
                    speaker_id=result.get('speaker_id', 'default'),
                    metadata=json.dumps({
                        'enhanced_processing': True,
                        'latency_ms': result.get('latency_ms', 0),
                        'quality_score': result.get('quality_score', 0),
                        'chunk_id': result.get('chunk_id', 0)
                    })
                )
                
                db.session.add(segment)
                db.session.commit()
                
        except Exception as e:
            logger.error(f"❌ Database segment save failed: {e}")
    
    async def _send_message(self, websocket, message: Dict[str, Any]):
        """📤 Send message to WebSocket client."""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
    
    async def _send_error(self, websocket, error_type: str, message: str):
        """❌ Send error message to client."""
        try:
            error_response = {
                'type': 'error',
                'error_type': error_type,
                'message': message,
                'timestamp': time.time()
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"❌ Failed to send error message: {e}")
    
    async def _cleanup_connection(self, connection_id: str):
        """🧹 Clean up connection and associated resources."""
        try:
            if connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                session_id = connection.get('session_id')
                
                # Clean up session if active
                if session_id:
                    try:
                        await self.enhanced_service.stop_session(session_id)
                        if session_id in self.session_to_connection:
                            del self.session_to_connection[session_id]
                        self.metrics['active_sessions'] = max(0, self.metrics['active_sessions'] - 1)
                    except Exception as e:
                        logger.error(f"❌ Session cleanup failed: {e}")
                
                # Remove connection
                del self.active_connections[connection_id]
                
                logger.info(f"🧹 Connection cleaned up: {connection_id}")
                
        except Exception as e:
            logger.error(f"❌ Connection cleanup failed for {connection_id}: {e}")
    
    def _get_connection_metrics(self, connection_id: str) -> Dict[str, Any]:
        """📊 Get metrics for specific connection."""
        if connection_id not in self.active_connections:
            return {}
        
        connection = self.active_connections[connection_id]
        
        return {
            'connected_duration': time.time() - connection['connected_at'],
            'session_active': connection['session_id'] is not None,
            'session_id': connection['session_id']
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """📊 Get global handler metrics."""
        return {
            'connections': {
                'total': self.metrics['total_connections'],
                'active': len(self.active_connections),
                'active_sessions': self.metrics['active_sessions']
            },
            'performance': {
                'total_chunks_processed': self.metrics['total_chunks_processed'],
                'avg_latency_ms': self.metrics['avg_latency_ms'],
                'error_count': self.metrics['error_count'],
                'error_rate': self.metrics['error_count'] / max(1, self.metrics['total_chunks_processed'])
            },
            'enhanced_features': {
                'google_recorder_level': True,
                'latency_optimization': True,
                'context_correlation': True,
                'hallucination_prevention': True
            }
        }

# Global instance
enhanced_websocket_handler = EnhancedWebSocketHandler()