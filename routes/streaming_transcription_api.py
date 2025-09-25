"""
🚀 STREAMING TRANSCRIPTION API
Production-ready streaming transcription with background processing,
VAD filtering, and session persistence
"""

import logging
import time
from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from models.streaming_models import TranscriptionSession, TranscriptionChunk
from services.streaming_audio_processor import get_streaming_processor, ProcessingResult
from services.real_time_qa_bridge import get_qa_bridge

logger = logging.getLogger(__name__)

# Create streaming transcription blueprint
streaming_bp = Blueprint('streaming_transcription', __name__)


@streaming_bp.route('/api/streaming/start-session', methods=['POST'])
def start_streaming_session():
    """Start a new streaming transcription session"""
    try:
        data = request.get_json() or {}
        
        # Generate session ID
        session_id = f"stream_{int(time.time())}_{data.get('client_id', 'unknown')[:8]}"
        
        # Create database record
        session = TranscriptionSession(
            session_id=session_id,
            started_at=datetime.utcnow(),
            status='active',
            audio_format=data.get('audio_format', 'webm'),
            sample_rate=data.get('sample_rate', 16000),
            client_info=data.get('client_info', {})
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Start streaming processor session
        processor = get_streaming_processor()
        qa_bridge = get_qa_bridge()
        
        # Start performance monitoring (lazy import to avoid circular dependencies)
        try:
            from services.performance_monitor import get_performance_monitor
            performance_monitor = get_performance_monitor()
            performance_monitor.record_session_start(session_id)
        except Exception as e:
            logger.warning(f"Performance monitoring unavailable: {e}")
        
        # Start QA monitoring
        qa_bridge.start_qa_session(session_id)
        
        def result_callback(result: ProcessingResult):
            """Handle processing results"""
            handle_transcription_result(session_id, result)
        
        processor.start_session(session_id, result_callback)
        
        logger.info(f"📢 Started streaming session: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Streaming session started',
            'config': {
                'chunk_duration_ms': 300,
                'overlap_ms': 50,
                'vad_enabled': True,
                'sample_rate': 16000
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to start streaming session: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to start session: {str(e)}'
        }), 500


@streaming_bp.route('/api/streaming/process-chunk', methods=['POST'])
def process_audio_chunk():
    """Process streaming audio chunk"""
    try:
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400
        
        # Get audio data
        audio_data = None
        if 'audio_data' in request.form:
            # Base64 encoded
            import base64
            try:
                audio_data = base64.b64decode(request.form['audio_data'])
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid base64 audio data: {str(e)}'
                }), 400
        elif 'audio' in request.files:
            # File upload
            audio_file = request.files['audio']
            audio_data = audio_file.read()
        
        if not audio_data:
            return jsonify({
                'success': False,
                'error': 'No audio data provided'
            }), 400
        
        # Validate session exists
        session = TranscriptionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        if session.status != 'active':
            return jsonify({
                'success': False,
                'error': f'Session is {session.status}, not active'
            }), 400
        
        # Process with streaming processor
        processor = get_streaming_processor()
        processor.process_audio_chunk(audio_data, session_id)
        
        # Update session statistics
        session.total_chunks += 1
        db.session.commit()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Chunk queued for processing',
            'queue_length': processor.get_metrics()['queue_length']
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to process audio chunk: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500


@streaming_bp.route('/api/streaming/get-results', methods=['GET'])
def get_streaming_results():
    """Get latest transcription results for a session"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id parameter is required'
            }), 400
        
        # Get recent chunks
        since_timestamp = request.args.get('since', '0')
        try:
            since_time = datetime.fromtimestamp(float(since_timestamp))
        except:
            since_time = datetime.fromtimestamp(0)
        
        chunks = TranscriptionChunk.query.filter(
            TranscriptionChunk.session_id == session_id,
            TranscriptionChunk.created_at > since_time
        ).order_by(TranscriptionChunk.created_at.desc()).limit(50).all()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'chunks': [chunk.to_dict() for chunk in chunks],
            'count': len(chunks),
            'latest_timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get streaming results: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get results: {str(e)}'
        }), 500


@streaming_bp.route('/api/streaming/end-session', methods=['POST'])
def end_streaming_session():
    """End streaming transcription session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id is required'
            }), 400
        
        # Get session
        session = TranscriptionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # End streaming processor session
        processor = get_streaming_processor()
        analytics = processor.end_session(session_id)
        
        # Update database record
        session.ended_at = datetime.utcnow()
        session.status = 'completed'
        
        if session.started_at:
            session.duration_seconds = (session.ended_at - session.started_at).total_seconds()
        
        # Calculate final metrics from chunks
        chunks = TranscriptionChunk.query.filter_by(session_id=session_id).all()
        
        if chunks:
            # Processing metrics
            processing_times = [c.processing_time_ms for c in chunks if c.processing_time_ms]
            if processing_times:
                session.avg_latency_ms = sum(processing_times) / len(processing_times)
                session.max_latency_ms = max(processing_times)
                session.p95_latency_ms = sorted(processing_times)[int(len(processing_times) * 0.95)]
            
            # Quality metrics
            confidences = [c.confidence_score for c in chunks if c.confidence_score]
            if confidences:
                session.avg_confidence = sum(confidences) / len(confidences)
            
            # Counts
            session.successful_chunks = len([c for c in chunks if c.status == 'completed'])
            session.failed_chunks = len([c for c in chunks if c.status == 'failed'])
            session.total_words = sum(c.word_count for c in chunks)
            
            # Generate final transcript
            final_chunks = [c for c in chunks if c.transcript_text and c.status == 'completed']
            final_chunks.sort(key=lambda x: x.created_at)
            session.final_transcript = ' '.join(c.transcript_text for c in final_chunks)
        
        # Update analytics from processor
        if analytics:
            session.total_audio_duration_ms = analytics.get('speech_detected_ms', 0)
            session.silence_ratio = 1.0 - analytics.get('speech_ratio', 0)
        
        db.session.commit()
        
        logger.info(f"📊 Ended streaming session: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'analytics': session.to_dict(),
            'processor_analytics': analytics,
            'message': 'Session ended successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to end streaming session: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to end session: {str(e)}'
        }), 500


@streaming_bp.route('/api/streaming/session-status', methods=['GET'])
def get_session_status():
    """Get current session status and metrics"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id parameter is required'
            }), 400
        
        # Get session from database
        session = TranscriptionSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        # Get processor metrics
        processor = get_streaming_processor()
        processor_metrics = processor.get_metrics()
        
        # Get chunk statistics
        chunk_stats = db.session.query(
            db.func.count(TranscriptionChunk.id).label('total'),
            db.func.count(db.case((TranscriptionChunk.status == 'completed', 1))).label('completed'),
            db.func.count(db.case((TranscriptionChunk.status == 'failed', 1))).label('failed'),
            db.func.avg(TranscriptionChunk.processing_time_ms).label('avg_processing_ms'),
            db.func.sum(TranscriptionChunk.word_count).label('total_words')
        ).filter_by(session_id=session_id).first()
        
        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'chunk_statistics': {
                'total_chunks': chunk_stats.total or 0,
                'completed_chunks': chunk_stats.completed or 0,
                'failed_chunks': chunk_stats.failed or 0,
                'avg_processing_ms': float(chunk_stats.avg_processing_ms or 0),
                'total_words': chunk_stats.total_words or 0
            },
            'processor_metrics': processor_metrics
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to get session status: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Failed to get status: {str(e)}'
        }), 500


def handle_transcription_result(session_id: str, result: ProcessingResult):
    """Handle transcription result from streaming processor"""
    try:
        # Create chunk record
        chunk = TranscriptionChunk(
            session_id=session_id,
            chunk_id=result.chunk_id,
            processing_started_at=datetime.utcnow(),
            processing_completed_at=datetime.utcnow(),
            processing_time_ms=result.processing_time_ms,
            transcript_text=result.transcript,
            confidence_score=result.confidence,
            word_count=result.word_count,
            is_interim=result.is_interim,
            is_final=not result.is_interim,
            status='completed' if not result.error else 'failed',
            error_message=result.error,
            model_used='whisper-1'
        )
        
        db.session.add(chunk)
        db.session.commit()
        
        # Process with QA bridge for real-time metrics
        qa_bridge = get_qa_bridge()
        qa_result = {
            'text': result.transcript,
            'confidence': result.confidence,
            'processing_time_ms': result.processing_time_ms,
            'chunk_id': result.chunk_id,
            'is_final': not result.is_interim,
            'word_count': result.word_count
        }
        qa_metrics = qa_bridge.process_transcription_result(qa_result)
        
        logger.debug(f"✅ Saved transcription result: {result.chunk_id} | QA: WER={qa_metrics.wer:.1f}% Latency={qa_metrics.latency_ms:.0f}ms")
        
    except Exception as e:
        logger.error(f"❌ Failed to save transcription result: {e}", exc_info=True)


# Register error handlers
@streaming_bp.errorhandler(400)
def handle_bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request',
        'message': str(e.description)
    }), 400


@streaming_bp.errorhandler(404)
def handle_not_found(e):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'message': str(e.description)
    }), 404


@streaming_bp.errorhandler(500)
def handle_internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500