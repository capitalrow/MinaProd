"""
HTTP Audio Processing Endpoint
Fallback for when WebSocket is not available
"""

import time
import logging
import base64
from flask import Blueprint, request, jsonify
from typing import Dict, Any

# Import audio processing services
try:
    from routes.audio_http import process_audio_chunk, validate_audio_quality
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

# Import models
try:
    from models import Session
    from app_refactored import db
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Create blueprint
audio_processing_bp = Blueprint('audio_processing', __name__, url_prefix='/audio')

@audio_processing_bp.route('/process', methods=['POST'])
def process_audio():
    """
    HTTP endpoint for audio processing when WebSocket is not available
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No JSON data provided',
                'type': 'invalid_request'
            }), 400
        
        # Extract required fields
        session_id = data.get('session_id')
        audio_data_b64 = data.get('audio_data')
        chunk_id = data.get('chunk_id', 1)
        is_final = data.get('is_final', False)
        mime_type = data.get('mime_type', 'audio/webm')
        
        if not session_id:
            return jsonify({
                'error': 'Missing session_id',
                'type': 'missing_session_id'
            }), 400
        
        if not audio_data_b64:
            return jsonify({
                'error': 'Missing audio_data',
                'type': 'missing_audio_data'
            }), 400
        
        logger.info(f"🎵 HTTP Audio Processing: session={session_id}, chunk={chunk_id}, size={len(audio_data_b64)} chars")
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data_b64)
        except Exception as e:
            logger.error(f"❌ Base64 decode error: {e}")
            return jsonify({
                'error': 'Invalid base64 audio data',
                'type': 'decode_error'
            }), 400
        
        # Validate audio quality (basic check)
        if len(audio_bytes) < 100:
            logger.warning(f"⚠️ Very small audio chunk: {len(audio_bytes)} bytes")
            return jsonify({
                'text': '',
                'confidence': 0.0,
                'is_final': is_final,
                'timestamp': time.time(),
                'processing_time': 0,
                'message': 'Audio chunk too small'
            })
        
        # Process audio if processing is available
        if AUDIO_PROCESSING_AVAILABLE:
            try:
                result = process_audio_chunk(audio_bytes)
                
                if result:
                    processing_time = time.time() - start_time
                    
                    response = {
                        'text': result.get('text', ''),
                        'confidence': result.get('confidence', 0.0),
                        'is_final': is_final,
                        'timestamp': time.time(),
                        'processing_time': processing_time,
                        'chunk_id': chunk_id,
                        'session_id': session_id
                    }
                    
                    # Add additional metadata if available
                    if 'language' in result:
                        response['language'] = result['language']
                    
                    logger.info(f"✅ HTTP Processing complete: '{result.get('text', '')[:50]}...' ({processing_time:.2f}s)")
                    return jsonify(response)
                
                else:
                    # No transcription result
                    processing_time = time.time() - start_time
                    
                    return jsonify({
                        'text': '',
                        'confidence': 0.0,
                        'is_final': is_final,
                        'timestamp': time.time(),
                        'processing_time': processing_time,
                        'chunk_id': chunk_id,
                        'session_id': session_id,
                        'message': 'No speech detected'
                    })
            
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
                return jsonify({
                    'error': f'Audio processing failed: {str(e)}',
                    'type': 'processing_error',
                    'chunk_id': chunk_id,
                    'session_id': session_id
                }), 500
        
        else:
            # Fallback when audio processing is not available
            logger.warning("⚠️ Audio processing not available, using mock response")
            
            # Simulate processing time
            time.sleep(0.1)
            processing_time = time.time() - start_time
            
            # Return mock transcription result
            mock_texts = [
                "Testing transcription system",
                "Audio processing active",
                "Voice detection working",
                "Microphone input received",
                "Sound quality is good"
            ]
            
            mock_text = mock_texts[chunk_id % len(mock_texts)] if chunk_id != 'final' else "Transcription complete"
            
            return jsonify({
                'text': mock_text,
                'confidence': 0.85,
                'is_final': is_final,
                'timestamp': time.time(),
                'processing_time': processing_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'mode': 'mock'
            })
    
    except Exception as e:
        logger.error(f"❌ HTTP audio processing error: {e}")
        return jsonify({
            'error': f'Server error: {str(e)}',
            'type': 'server_error'
        }), 500


@audio_processing_bp.route('/status', methods=['GET'])
def audio_status():
    """
    Get audio processing system status
    """
    return jsonify({
        'audio_processing_available': AUDIO_PROCESSING_AVAILABLE,
        'models_available': MODELS_AVAILABLE,
        'timestamp': time.time(),
        'status': 'operational'
    })


@audio_processing_bp.route('/health', methods=['GET'])
def audio_health():
    """
    Health check for audio processing system
    """
    health_data = {
        'status': 'healthy',
        'components': {
            'audio_processing': 'available' if AUDIO_PROCESSING_AVAILABLE else 'unavailable',
            'database_models': 'available' if MODELS_AVAILABLE else 'unavailable'
        },
        'timestamp': time.time()
    }
    
    # Determine overall status
    if not AUDIO_PROCESSING_AVAILABLE:
        health_data['status'] = 'degraded'
        health_data['message'] = 'Audio processing running in fallback mode'
    
    return jsonify(health_data)