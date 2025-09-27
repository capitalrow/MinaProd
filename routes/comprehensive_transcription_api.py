# routes/comprehensive_transcription_api.py
"""
COMPREHENSIVE TRANSCRIPTION API
Unified integration of all enhanced transcription systems including:
- Advanced audio processing with noise reduction and quality enhancement
- Multi-speaker diarization with voice identification
- Real-time punctuation and capitalization
- Enhanced session management with persistence
- Advanced performance monitoring and analytics
"""

import logging
import json
import time
import asyncio
from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from typing import Dict, List, Any, Optional
import numpy as np

# Import all enhanced systems
from services.advanced_audio_processor import get_advanced_audio_processor
from services.multi_speaker_diarization import get_multi_speaker_diarization
from services.real_time_punctuation import get_punctuation_engine
from services.enhanced_session_manager import get_enhanced_session_manager
from services.session_buffer_manager import get_session_buffer_manager
from services.openai_client_manager import get_openai_client_manager

logger = logging.getLogger(__name__)

# Create blueprint
comprehensive_bp = Blueprint('comprehensive_transcription', __name__)

class ComprehensiveTranscriptionProcessor:
    """Unified processor integrating all enhanced transcription systems"""
    
    def __init__(self):
        # Initialize all enhanced systems
        self.audio_processor = get_advanced_audio_processor()
        self.diarization = get_multi_speaker_diarization()
        self.punctuation_engine = get_punctuation_engine()
        self.session_manager = get_enhanced_session_manager()
        self.buffer_manager = get_session_buffer_manager()
        self.openai_client = get_openai_client_manager()
        
        # Processing state
        self.active_sessions = {}
        
        # Performance metrics
        self.processing_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'average_latency': 0.0,
            'error_rate': 0.0
        }
        
        logger.info("🚀 Comprehensive Transcription Processor initialized")
    
    async def process_audio_comprehensive(
        self, 
        session_id: str,
        audio_data: bytes,
        client_id: str,
        is_final: bool = False
    ) -> Dict[str, Any]:
        """Process audio through complete enhanced pipeline"""
        
        start_time = time.time()
        self.processing_metrics['total_requests'] += 1
        
        try:
            # === STAGE 1: ADVANCED AUDIO PROCESSING ===
            
            # Convert audio to numpy array for processing
            audio_samples = self._bytes_to_numpy(audio_data)
            
            # Process through advanced audio processor
            audio_segment = self.audio_processor.process_audio_segment(
                audio_data=audio_data,
                sample_rate=16000,
                channels=1,
                enable_enhancement=True
            )
            
            # === STAGE 2: VOICE ACTIVITY DETECTION & QUALITY ASSESSMENT ===
            
            voice_active = audio_segment.is_speech
            quality_score = audio_segment.metrics.audio_quality_score
            
            # Skip processing if no speech detected and not final
            if not voice_active and not is_final:
                return {
                    'session_id': session_id,
                    'voice_activity': False,
                    'quality_score': quality_score,
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'stage': 'voice_activity_detection'
                }
            
            # === STAGE 3: BUFFER MANAGEMENT ===
            
            # Add to session buffer
            buffer_result = await self.buffer_manager.add_audio_chunk_async(
                session_id=session_id,
                audio_data=audio_segment.audio_data,
                timestamp=time.time(),
                metadata={
                    'quality_score': quality_score,
                    'voice_activity': voice_active,
                    'audio_metrics': audio_segment.metrics.__dict__
                }
            )
            
            # === STAGE 4: TRANSCRIPTION PROCESSING ===
            
            transcription_result = None
            if buffer_result['should_transcribe'] or is_final:
                # Get processed audio from buffer
                processed_audio = buffer_result.get('processed_audio', audio_segment.audio_data)
                
                # Transcribe with OpenAI
                transcription_result = await self._transcribe_audio(
                    audio_data=processed_audio,
                    session_id=session_id
                )
            
            # === STAGE 5: SPEAKER DIARIZATION ===
            
            speaker_segment = None
            if transcription_result and transcription_result.get('text'):
                speaker_segment = self.diarization.process_audio_segment(
                    audio_samples=audio_samples,
                    timestamp=time.time(),
                    segment_id=f"{session_id}_{int(time.time() * 1000)}",
                    existing_transcript=transcription_result['text']
                )
            
            # === STAGE 6: REAL-TIME PUNCTUATION ===
            
            enhanced_text = ""
            if transcription_result and transcription_result.get('text'):
                punctuation_segment = self.punctuation_engine.process_text_segment(
                    text=transcription_result['text'],
                    confidence=transcription_result.get('confidence', 0.0),
                    is_final=is_final,
                    context=self._get_recent_context(session_id)
                )
                enhanced_text = punctuation_segment.text
            
            # === STAGE 7: SESSION MANAGEMENT ===
            
            # Update session with comprehensive data
            session_update = {
                'transcription_segments': [{
                    'text': enhanced_text,
                    'original_text': transcription_result.get('text', '') if transcription_result else '',
                    'speaker_id': speaker_segment.speaker_id if speaker_segment else 'unknown',
                    'speaker_confidence': speaker_segment.speaker_confidence if speaker_segment else 0.0,
                    'audio_quality': quality_score,
                    'voice_activity': voice_active,
                    'timestamp': start_time,
                    'is_final': is_final,
                    'processing_stages': {
                        'audio_enhanced': True,
                        'speaker_identified': speaker_segment is not None,
                        'punctuation_applied': len(enhanced_text) > 0,
                        'buffer_processed': buffer_result['processed']
                    }
                }],
                'speaker_profiles': {
                    speaker_segment.speaker_id: {
                        'confidence': speaker_segment.speaker_confidence,
                        'voice_features': speaker_segment.voice_features.tolist() if speaker_segment and speaker_segment.voice_features is not None else [],
                        'last_seen': start_time
                    }
                } if speaker_segment else {},
                'audio_metrics_history': [{
                    'timestamp': start_time,
                    'quality_score': quality_score,
                    'voice_activity': voice_active,
                    'rms_energy': audio_segment.metrics.rms_energy,
                    'snr_db': audio_segment.metrics.snr_db,
                    'speech_probability': audio_segment.metrics.speech_probability
                }],
                'processing_events': [{
                    'event': 'comprehensive_processing',
                    'timestamp': start_time,
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'stages_completed': ['audio_processing', 'vad', 'buffering', 'transcription', 'diarization', 'punctuation']
                }]
            }
            
            # Update session
            self.session_manager.update_session(session_id, session_update)
            
            # === STAGE 8: RESPONSE PREPARATION ===
            
            processing_time = (time.time() - start_time) * 1000
            self.processing_metrics['successful_requests'] += 1
            self._update_average_latency(processing_time)
            
            comprehensive_result = {
                'session_id': session_id,
                'text': enhanced_text,
                'original_text': transcription_result.get('text', '') if transcription_result else '',
                'confidence': transcription_result.get('confidence', 0.0) if transcription_result else 0.0,
                'is_final': is_final,
                'voice_activity': voice_active,
                'quality_score': quality_score,
                'speaker_info': {
                    'speaker_id': speaker_segment.speaker_id if speaker_segment else 'unknown',
                    'speaker_confidence': speaker_segment.speaker_confidence if speaker_segment else 0.0,
                    'overlap_detected': speaker_segment.overlap_detected if speaker_segment else False,
                    'background_speakers': speaker_segment.background_speakers if speaker_segment else []
                },
                'audio_metrics': {
                    'rms_energy': audio_segment.metrics.rms_energy,
                    'peak_amplitude': audio_segment.metrics.peak_amplitude,
                    'snr_db': audio_segment.metrics.snr_db,
                    'speech_probability': audio_segment.metrics.speech_probability,
                    'noise_level': audio_segment.metrics.noise_level
                },
                'processing_info': {
                    'processing_time_ms': processing_time,
                    'buffer_status': buffer_result.get('status', 'unknown'),
                    'enhancement_applied': True,
                    'punctuation_applied': len(enhanced_text) > 0,
                    'speaker_identified': speaker_segment is not None
                },
                'system_metrics': self.get_system_metrics()
            }
            
            logger.debug(f"🎯 Comprehensive processing completed for session {session_id}: "
                        f"{processing_time:.1f}ms, quality={quality_score:.2f}")
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"❌ Comprehensive processing failed: {e}")
            self._update_error_rate()
            
            return {
                'session_id': session_id,
                'error': str(e),
                'processing_time_ms': (time.time() - start_time) * 1000,
                'system_metrics': self.get_system_metrics()
            }
    
    async def _transcribe_audio(self, audio_data: bytes, session_id: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio using OpenAI client"""
        try:
            # Use the enhanced OpenAI client manager
            result = await self.openai_client.transcribe_audio_async(
                audio_data=audio_data,
                session_id=session_id
            )
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return None
    
    def _bytes_to_numpy(self, audio_data: bytes) -> np.ndarray:
        """Convert audio bytes to numpy array"""
        try:
            # Try to detect format and convert appropriately
            if len(audio_data) < 44:
                return np.array([])
            
            # For simplicity, assume 16-bit PCM
            if len(audio_data) % 2 != 0:
                audio_data = audio_data[:-1]
            
            samples = np.frombuffer(audio_data, dtype=np.int16)
            return samples.astype(np.float32) / 32768.0
            
        except Exception as e:
            logger.warning(f"⚠️ Audio conversion failed: {e}")
            return np.array([])
    
    def _get_recent_context(self, session_id: str) -> str:
        """Get recent context for punctuation processing"""
        try:
            session_state = self.session_manager.get_session(session_id)
            if not session_state or not session_state.transcription_segments:
                return ""
            
            # Get last few segments for context
            recent_segments = session_state.transcription_segments[-3:]
            context_text = " ".join(segment.get('text', '') for segment in recent_segments)
            return context_text
            
        except Exception:
            return ""
    
    def _update_average_latency(self, processing_time_ms: float):
        """Update average latency metric"""
        try:
            current_avg = self.processing_metrics['average_latency']
            total_requests = self.processing_metrics['successful_requests']
            
            # Exponential moving average
            alpha = 0.1
            self.processing_metrics['average_latency'] = (
                alpha * processing_time_ms + (1 - alpha) * current_avg
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Latency update failed: {e}")
    
    def _update_error_rate(self):
        """Update error rate metric"""
        try:
            total = self.processing_metrics['total_requests']
            successful = self.processing_metrics['successful_requests']
            errors = total - successful
            
            self.processing_metrics['error_rate'] = errors / total if total > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"⚠️ Error rate update failed: {e}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        try:
            return {
                'processing_metrics': self.processing_metrics,
                'audio_processor_stats': self.audio_processor.get_processor_stats(),
                'diarization_summary': self.diarization.get_speaker_summary(),
                'punctuation_stats': self.punctuation_engine.get_processing_statistics(),
                'session_analytics': self.session_manager.get_global_analytics(),
                'buffer_status': self.buffer_manager.get_system_status()
            }
            
        except Exception as e:
            logger.error(f"❌ System metrics retrieval failed: {e}")
            return {}

# Global processor instance
_comprehensive_processor = None

def get_comprehensive_processor():
    """Get global comprehensive processor instance"""
    global _comprehensive_processor
    if _comprehensive_processor is None:
        _comprehensive_processor = ComprehensiveTranscriptionProcessor()
    return _comprehensive_processor

# REST API Routes
@comprehensive_bp.route('/api/transcription/comprehensive/session', methods=['POST'])
def create_comprehensive_session():
    """Create new comprehensive transcription session"""
    try:
        data = request.get_json() or {}
        
        session_manager = get_enhanced_session_manager()
        session_id = session_manager.create_session(
            user_id=data.get('user_id'),
            session_name=data.get('session_name', ''),
            language=data.get('language', 'en')
        )
        
        logger.info(f"🆕 Created comprehensive session: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Comprehensive transcription session created'
        })
        
    except Exception as e:
        logger.error(f"❌ Session creation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@comprehensive_bp.route('/api/transcription/comprehensive/session/<session_id>', methods=['GET'])
def get_comprehensive_session(session_id: str):
    """Get comprehensive session information"""
    try:
        session_manager = get_enhanced_session_manager()
        analytics = session_manager.get_session_analytics(session_id)
        
        if not analytics:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'session_analytics': analytics
        })
        
    except Exception as e:
        logger.error(f"❌ Session retrieval failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@comprehensive_bp.route('/api/transcription/comprehensive/session/<session_id>/export', methods=['POST'])
def export_comprehensive_session(session_id: str):
    """Export comprehensive session in various formats"""
    try:
        data = request.get_json() or {}
        export_format = data.get('format', 'json')
        
        session_manager = get_enhanced_session_manager()
        export_data = session_manager.export_session(session_id, export_format)
        
        if not export_data:
            return jsonify({
                'success': False,
                'error': 'Export failed or session not found'
            }), 404
        
        # Return appropriate content type
        content_types = {
            'json': 'application/json',
            'txt': 'text/plain',
            'srt': 'text/plain',
            'csv': 'text/csv'
        }
        
        from flask import Response
        return Response(
            export_data,
            mimetype=content_types.get(export_format, 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename=session_{session_id}.{export_format}'
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Session export failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@comprehensive_bp.route('/api/transcription/comprehensive/metrics', methods=['GET'])
def get_comprehensive_metrics():
    """Get comprehensive system metrics"""
    try:
        processor = get_comprehensive_processor()
        metrics = processor.get_system_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"❌ Metrics retrieval failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket Event Handlers (for Socket.IO integration)
def register_comprehensive_websocket_handlers(socketio):
    """Register comprehensive WebSocket handlers"""
    
    @socketio.on('join_comprehensive_session')
    def handle_join_comprehensive_session(data):
        """Join comprehensive transcription session"""
        try:
            session_id = data.get('session_id')
            if not session_id:
                emit('error', {'message': 'Session ID required'})
                return
            
            join_room(f"comprehensive_{session_id}")
            emit('joined_comprehensive_session', {
                'session_id': session_id,
                'status': 'connected'
            })
            
            logger.info(f"🔗 Client joined comprehensive session: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Join session failed: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('comprehensive_audio_data')
    def handle_comprehensive_audio_data(data):
        """Handle comprehensive audio processing"""
        try:
            session_id = data.get('session_id')
            audio_data = data.get('audio_data')
            client_id = data.get('client_id', 'unknown')
            is_final = data.get('is_final', False)
            
            if not session_id or not audio_data:
                emit('error', {'message': 'Session ID and audio data required'})
                return
            
            # Convert base64 audio to bytes
            import base64
            try:
                audio_bytes = base64.b64decode(audio_data)
            except Exception:
                emit('error', {'message': 'Invalid audio data format'})
                return
            
            # Process through comprehensive pipeline
            processor = get_comprehensive_processor()
            
            # Use asyncio to run the async function
            import asyncio
            try:
                result = asyncio.run(processor.process_audio_comprehensive(
                    session_id=session_id,
                    audio_data=audio_bytes,
                    client_id=client_id,
                    is_final=is_final
                ))
                
                # Emit result to all clients in the session
                socketio.emit('comprehensive_transcription_result', result, 
                            room=f"comprehensive_{session_id}")
                
            except Exception as e:
                logger.error(f"❌ Async processing failed: {e}")
                emit('error', {'message': f'Processing failed: {str(e)}'})
            
        except Exception as e:
            logger.error(f"❌ Audio data handling failed: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('leave_comprehensive_session')
    def handle_leave_comprehensive_session(data):
        """Leave comprehensive transcription session"""
        try:
            session_id = data.get('session_id')
            if session_id:
                leave_room(f"comprehensive_{session_id}")
                emit('left_comprehensive_session', {'session_id': session_id})
                logger.info(f"🔌 Client left comprehensive session: {session_id}")
            
        except Exception as e:
            logger.error(f"❌ Leave session failed: {e}")
            emit('error', {'message': str(e)})

logger.info("✅ Comprehensive Transcription API initialized")