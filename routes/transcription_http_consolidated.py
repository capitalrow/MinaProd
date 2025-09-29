"""
🎙️ Consolidated Transcription HTTP API
Unified endpoint consolidating all transcription HTTP functionality to eliminate duplication.
Replaces: unified_transcription_api.py, enhanced_transcription_api.py, comprehensive_transcription_api.py, streaming_transcription_api.py
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import get_service
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Create consolidated blueprint
transcription_http_bp = Blueprint('transcription_http', __name__, url_prefix='/api/transcription')

@transcription_http_bp.route('/start', methods=['POST'])
@login_required
def start_transcription():
    """Start a new transcription session (unified endpoint)"""
    try:
        data = request.get_json() or {}
        
        # Get services via dependency injection
        transcription_service = get_service('transcription')
        business_metrics = get_service('business_metrics')
        
        # Extract configuration
        config = {
            'language': data.get('language', 'auto'),
            'model': data.get('model', 'whisper-1'),
            'enhanced_processing': data.get('enhanced_processing', True),
            'speaker_diarization': data.get('speaker_diarization', True),
            'real_time': data.get('real_time', True),
            'confidence_threshold': data.get('confidence_threshold', 0.7),
            'max_duration': data.get('max_duration', 3600)  # 1 hour default
        }
        
        # Create session
        session_id = transcription_service.create_session(
            user_id=current_user.id,
            config=config
        )
        
        # Track metrics
        business_metrics.start_transcription_session(
            user_id=current_user.id,
            session_id=session_id,
            config=config
        )
        
        logger.info(f"🎙️ Transcription session started: {session_id}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'config': config,
            'websocket_url': f'/socket.io',
            'websocket_namespace': '/transcription'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to start transcription: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to start transcription session'
        }), 500

@transcription_http_bp.route('/session/<session_id>/status', methods=['GET'])
@login_required
def get_session_status(session_id: str):
    """Get transcription session status"""
    try:
        transcription_service = get_service('transcription')
        
        session = transcription_service.get_session(session_id)
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
            
        # Check user authorization
        if session.user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        
        status_data = transcription_service.get_session_status(session_id)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'session_status': status_data['status'],
            'segments_count': status_data['segments_count'],
            'duration': status_data['duration'],
            'language_detected': status_data.get('language'),
            'confidence_avg': status_data.get('confidence_avg'),
            'processing_stats': status_data.get('processing_stats', {})
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve session status'
        }), 500

@transcription_http_bp.route('/session/<session_id>/transcript', methods=['GET'])
@login_required
def get_session_transcript(session_id: str):
    """Get transcription session transcript"""
    try:
        transcription_service = get_service('transcription')
        
        session = transcription_service.get_session(session_id)
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
            
        # Check user authorization
        if session.user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        
        # Get query parameters
        format_type = request.args.get('format', 'json')  # json, text, srt, vtt
        include_timestamps = request.args.get('timestamps', 'true').lower() == 'true'
        include_speakers = request.args.get('speakers', 'true').lower() == 'true'
        confidence_threshold = float(request.args.get('confidence_threshold', 0.0))
        
        transcript_data = transcription_service.get_transcript(
            session_id=session_id,
            format_type=format_type,
            include_timestamps=include_timestamps,
            include_speakers=include_speakers,
            confidence_threshold=confidence_threshold
        )
        
        if format_type == 'json':
            return jsonify({
                'status': 'success',
                'session_id': session_id,
                'transcript': transcript_data,
                'format': format_type
            }), 200
        else:
            # Return as text for non-JSON formats
            return transcript_data, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Failed to get transcript: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve transcript'
        }), 500

@transcription_http_bp.route('/session/<session_id>/stop', methods=['POST'])
@login_required
def stop_transcription(session_id: str):
    """Stop transcription session"""
    try:
        transcription_service = get_service('transcription')
        business_metrics = get_service('business_metrics')
        
        session = transcription_service.get_session(session_id)
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
            
        # Check user authorization
        if session.user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        
        # Stop the session
        final_stats = transcription_service.stop_session(session_id)
        
        # Track completion metrics
        business_metrics.complete_transcription_session(
            user_id=current_user.id,
            session_id=session_id,
            final_stats=final_stats
        )
        
        logger.info(f"🎙️ Transcription session stopped: {session_id}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'final_stats': final_stats,
            'message': 'Transcription session stopped successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to stop transcription: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to stop transcription session'
        }), 500

@transcription_http_bp.route('/session/<session_id>/audio', methods=['POST'])
@login_required
def upload_audio_chunk(session_id: str):
    """Upload audio chunk for processing (batch mode)"""
    try:
        transcription_service = get_service('transcription')
        
        session = transcription_service.get_session(session_id)
        if not session:
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
            
        # Check user authorization
        if session.user_id != current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Unauthorized'
            }), 403
        
        # Handle audio upload
        if 'audio' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No audio file provided'
            }), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No audio file selected'
            }), 400
        
        # Process audio chunk
        result = transcription_service.process_audio_chunk(
            session_id=session_id,
            audio_data=audio_file.read(),
            chunk_index=request.form.get('chunk_index', 0),
            is_final=request.form.get('is_final', 'false').lower() == 'true'
        )
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'chunk_processed': True,
            'segments': result.get('segments', []),
            'processing_time': result.get('processing_time'),
            'confidence': result.get('confidence')
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to process audio chunk: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process audio chunk'
        }), 500

@transcription_http_bp.route('/models', methods=['GET'])
def get_available_models():
    """Get available transcription models"""
    try:
        transcription_service = get_service('transcription')
        models = transcription_service.get_available_models()
        
        return jsonify({
            'status': 'success',
            'models': models
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve available models'
        }), 500

@transcription_http_bp.route('/languages', methods=['GET'])
def get_supported_languages():
    """Get supported languages"""
    try:
        transcription_service = get_service('transcription')
        languages = transcription_service.get_supported_languages()
        
        return jsonify({
            'status': 'success',
            'languages': languages
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get languages: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve supported languages'
        }), 500

@transcription_http_bp.route('/health', methods=['GET'])
def transcription_health():
    """Health check for transcription service"""
    try:
        transcription_service = get_service('transcription')
        health_status = transcription_service.health_check()
        
        return jsonify({
            'status': 'success',
            'service': 'transcription',
            'health': health_status
        }), 200
        
    except Exception as e:
        logger.error(f"Transcription health check failed: {e}")
        return jsonify({
            'status': 'error',
            'service': 'transcription',
            'message': 'Health check failed'
        }), 503

# Error handlers for this blueprint
@transcription_http_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'status': 'error',
        'message': 'Bad request'
    }), 400

@transcription_http_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'status': 'error',
        'message': 'Authentication required'
    }), 401

@transcription_http_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'status': 'error',
        'message': 'Insufficient permissions'
    }), 403

@transcription_http_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Resource not found'
    }), 404

@transcription_http_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500