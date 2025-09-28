"""
🎯 UNIFIED TRANSCRIPTION API: Single robust endpoint for all transcription needs
Handles both FormData file uploads AND base64 audio data from frontend
"""

import os
import time
import base64
import tempfile
import logging
import struct
import subprocess
from flask import Blueprint, request, jsonify
from datetime import datetime
import openai
from pydub import AudioSegment
import io

# Import robust services
from services.circuit_breaker import get_openai_circuit_breaker, get_audio_processing_circuit_breaker, CircuitBreakerOpenError
from services.health_monitor import get_health_monitor

# Import enhanced services
from services.multi_model_transcription import get_multi_model_service, TranscriptionContext
from services.speaker_diarization_enhanced import get_speaker_diarization
from services.sentiment_analysis_service import get_sentiment_service
from services.meeting_insights_service import get_insights_service
from services.redis_cache_service import get_cache_service

logger = logging.getLogger(__name__)

# Create unified transcription blueprint
unified_api_bp = Blueprint('unified_transcription', __name__)

# Initialize OpenAI client
_openai_client = None

def get_openai_client():
    """Get or initialize OpenAI client with proper error handling"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        _openai_client = openai.OpenAI(api_key=api_key)
        logger.info("✅ OpenAI client initialized successfully")
    return _openai_client

@unified_api_bp.route('/api/transcribe-audio', methods=['POST'])
def unified_transcribe_audio():
    """
    🎯 ENHANCED UNIFIED TRANSCRIPTION ENDPOINT
    Handles BOTH base64 audio data AND file uploads
    Supports interim and final transcription modes
    Now with circuit breaker protection and health monitoring
    """
    request_start_time = time.time()
    health_monitor = get_health_monitor()
    success = False
    
    try:
        # Extract session info with defaults
        session_id = f'session_{int(time.time())}'
        chunk_id = '1' 
        is_interim = False
        
        # Determine request format and extract data
        audio_data = None
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle FormData file upload (from WebSocket relay)
            logger.info("📁 Processing FormData file upload")
            
            session_id = request.form.get('session_id', f'session_{int(time.time())}')
            chunk_id = request.form.get('chunk_id', '1')
            is_interim = request.form.get('is_interim', 'false').lower() == 'true'
            
            if 'audio' in request.files:
                audio_file = request.files['audio']
                if audio_file and audio_file.filename:
                    audio_data = audio_file.read()
                    content_type = audio_file.content_type or 'audio/webm'
                    logger.info(f"📦 File upload: {len(audio_data)} bytes, type: {content_type}, file: {audio_file.filename}")
                    
                    # Enhanced format validation
                    if len(audio_data) < 100:
                        logger.info(f"ℹ️ Audio chunk too small ({len(audio_data)} bytes) - skipping")
                        return jsonify({
                            'success': True,
                            'text': '',
                            'message': 'Audio chunk too small',
                            'processing_time': (time.time() - request_start_time) * 1000
                        })
            
        elif request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
            # Handle base64 audio data (current frontend format)
            logger.info("🔤 Processing base64 audio data")
            
            session_id = request.form.get('session_id', f'session_{int(time.time())}')
            chunk_id = request.form.get('chunk_id', '1')
            is_interim = request.form.get('is_interim', 'false').lower() == 'true'
            
            audio_data_b64 = request.form.get('audio_data')
            if audio_data_b64:
                try:
                    audio_data = base64.b64decode(audio_data_b64)
                    logger.info(f"📦 Base64 decoded: {len(audio_data)} bytes")
                except Exception as decode_error:
                    logger.error(f"❌ Base64 decode error: {decode_error}")
                    return jsonify({
                        'error': 'Invalid base64 audio data',
                        'success': False,
                        'session_id': session_id
                    }), 400
        
        else:
            # Try to handle JSON format as fallback
            try:
                json_data = request.get_json()
                if json_data:
                    session_id = json_data.get('session_id', f'session_{int(time.time())}')
                    chunk_id = json_data.get('chunk_id', '1')
                    is_interim = json_data.get('is_interim', False)
                    
                    audio_data_b64 = json_data.get('audio_data')
                    if audio_data_b64:
                        audio_data = base64.b64decode(audio_data_b64)
                        logger.info(f"📦 JSON base64 decoded: {len(audio_data)} bytes")
            except:
                pass
        
        # Validate we have audio data
        if not audio_data:
            logger.warning("⚠️ No audio data found in request")
            return jsonify({
                'error': 'No audio data provided. Expected either file upload or base64 audio_data field.',
                'success': False,
                'session_id': session_id or 'unknown',
                'processing_time': (time.time() - request_start_time) * 1000
            }), 400
        
        # Enhanced audio validation with different thresholds for interim vs final
        min_size_interim = 1000  # 1KB minimum for interim
        min_size_final = 500     # 500 bytes minimum for final
        
        required_size = min_size_interim if is_interim else min_size_final
        
        if len(audio_data) < required_size:
            logger.info(f"ℹ️ Audio too short ({len(audio_data)} bytes, need {required_size}) - returning empty result")
            return jsonify({
                'success': True,
                'text': '',
                'final_text': '',
                'confidence': 0.0,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'is_interim': is_interim,
                'is_final': not is_interim,
                'audio_duration_ms': 0,
                'word_count': 0,
                'timestamp': time.time(),
                'message': f'Audio too short for {"interim" if is_interim else "final"} transcription',
                'processing_time': (time.time() - request_start_time) * 1000
            })
        
        logger.info(f"🎵 Processing audio: session={session_id}, chunk={chunk_id}, interim={is_interim}, size={len(audio_data)} bytes")
        
        # 🔥 CRITICAL FIX: Use robust AudioProcessor service with format detection
        try:
            from services.audio_processor import AudioProcessor
            audio_processor = AudioProcessor()
            
            # Detect actual format instead of assuming WebM
            detected_format = detect_audio_format(audio_data)
            logger.info(f"🔍 Detected audio format: {detected_format} for {len(audio_data)} bytes")
            
            wav_audio = audio_processor.convert_to_wav(audio_data, detected_format)
            
            if not wav_audio or len(wav_audio) < 44:
                logger.error("❌ AudioProcessor conversion failed")
                # Fallback to basic conversion
                wav_audio = convert_audio_to_wav_enhanced(audio_data)
                
        except ImportError:
            logger.warning("⚠️ AudioProcessor service not available, using fallback")
            wav_audio = convert_audio_to_wav_enhanced(audio_data)
        except Exception as conversion_error:
            logger.error(f"❌ Audio conversion error: {conversion_error}")
            wav_audio = convert_audio_to_wav_enhanced(audio_data)
        
        if not wav_audio or len(wav_audio) < 44:
            logger.error("❌ All audio conversion methods failed")
            return jsonify({
                'error': 'Audio format not supported. Please ensure your browser is recording in a compatible format.',
                'details': 'WebM/Opus format conversion failed. Try refreshing the page or using a different browser.',
                'success': False,
                'session_id': session_id,
                'processing_time': (time.time() - request_start_time) * 1000
            }), 400
        
        # Transcribe using OpenAI Whisper with circuit breaker protection
        openai_breaker = get_openai_circuit_breaker()
        audio_breaker = get_audio_processing_circuit_breaker()
        
        def protected_transcription():
            client = get_openai_client()
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_audio)
                temp_file_path = temp_file.name
            
            try:
                # Call Whisper API with enhanced parameters and circuit breaker
                transcription_start = time.time()
                
                with open(temp_file_path, "rb") as audio_file:
                    # Enhanced Whisper parameters for robust transcription
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        temperature=0.0,  # Lower temperature for accuracy
                        # Add timestamp granularities for better analysis
                        timestamp_granularities=["word"]
                    )
                
                transcription_time = (time.time() - transcription_start) * 1000
                total_processing_time = (time.time() - request_start_time) * 1000
                
                # Extract text and confidence
                text = response.text.strip() if hasattr(response, 'text') else ''
                
                # Calculate confidence based on response
                confidence = 0.95  # Default high confidence for Whisper
                if hasattr(response, 'segments') and response.segments:
                    # Average confidence from segments if available
                    confidences = [seg.get('avg_logprob', 0.0) for seg in response.segments if isinstance(seg, dict)]
                    if confidences:
                        # Convert log probability to confidence percentage
                        confidence = max(0.0, min(1.0, sum(confidences) / len(confidences) + 1.0))
                
                logger.info(f"✅ Transcription successful: '{text[:50]}...' ({transcription_time:.0f}ms)")
                
                # Format response
                result = {
                    'success': True,
                    'text': text,
                    'final_text': text if not is_interim else '',
                    'confidence': confidence,
                    'session_id': session_id,
                    'chunk_id': chunk_id,
                    'is_interim': is_interim,
                    'is_final': not is_interim,
                    'processing_time': total_processing_time,
                    'transcription_time': transcription_time,
                    'word_count': len(text.split()) if text else 0,
                    'audio_duration_ms': len(audio_data) // 32,  # Rough estimate
                    'timestamp': time.time()
                }
                
                # Add processing details for debugging
                if os.getenv('DEBUG'):
                    result['debug'] = {
                        'audio_size': len(audio_data),
                        'wav_size': len(wav_audio),
                        'format_detected': 'webm',
                        'model_used': 'whisper-1'
                    }
                
                return result
                    
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
        
        try:
            # Execute transcription with circuit breaker protection
            result = openai_breaker.call(protected_transcription)
            success = True
            
            # Record successful transcription metrics
            total_processing_time = (time.time() - request_start_time) * 1000
            health_monitor.record_api_call('/api/transcribe-audio', total_processing_time, True)
            health_monitor.record_transcription_event(
                session_id, 
                total_processing_time / 1000, 
                True, 
                result.get('confidence', 0.95)
            )
            
            return jsonify(result)
                    
        except CircuitBreakerOpenError as cb_error:
            logger.warning(f"🔴 Circuit breaker protection activated: {cb_error}")
            processing_time = (time.time() - request_start_time) * 1000
            
            # Record the failed attempt
            health_monitor.record_api_call('/api/transcribe-audio', processing_time, False)
            
            return jsonify({
                'error': 'Transcription service temporarily unavailable due to high error rates',
                'success': False,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'is_interim': is_interim,
                'processing_time': processing_time,
                'retry_suggestion': 'Please wait a moment and try again - service is recovering',
                'service_status': 'circuit_breaker_open'
            }), 503
            
        except Exception as whisper_error:
            logger.error(f"❌ Whisper API error: {whisper_error}")
            processing_time = (time.time() - request_start_time) * 1000
            
            # Record the failed attempt
            health_monitor.record_api_call('/api/transcribe-audio', processing_time, False)
            
            error_message = str(whisper_error)
            status_code = 500
            
            # Handle specific OpenAI API errors gracefully
            if 'audio_too_short' in error_message.lower():
                logger.info(f"ℹ️ Audio too short for Whisper API (session: {session_id})")
                success = True  # This is not really a failure
                return jsonify({
                    'success': True,
                    'text': '',
                    'final_text': '',
                    'confidence': 0.0,
                    'session_id': session_id,
                    'chunk_id': chunk_id,
                    'is_interim': is_interim,
                    'is_final': not is_interim,
                    'message': 'Audio duration insufficient for transcription',
                    'processing_time': processing_time
                })
            elif 'rate_limit' in error_message.lower():
                status_code = 429
                error_message = 'Transcription service temporarily overloaded. Please try again.'
            elif 'quota' in error_message.lower() or 'billing' in error_message.lower():
                status_code = 402
                error_message = 'Transcription service quota exceeded. Please contact support.'
            elif 'invalid_request' in error_message.lower():
                status_code = 400
                error_message = 'Invalid audio format for transcription service.'
            
            return jsonify({
                'error': error_message,
                'success': False,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'is_interim': is_interim,
                'processing_time': processing_time,
                'retry_suggestion': 'Consider reducing audio quality or checking microphone permissions' if status_code == 400 else None
            }), status_code
            
    except Exception as e:
        logger.error(f"❌ Critical error in unified transcription API: {e}", exc_info=True)
        processing_time = (time.time() - request_start_time) * 1000
        
        # Record the critical error
        if 'health_monitor' in locals():
            health_monitor.record_api_call('/api/transcribe-audio', processing_time, False)
        
        # Enhanced error recovery with specific error handling
        error_details = {
            'type': type(e).__name__,
            'message': str(e),
            'processing_time': processing_time,
            'session_id': session_id or 'unknown',
            'success': False
        }
        
        # Add retry suggestions for recoverable errors
        if 'timeout' in str(e).lower() or 'connection' in str(e).lower():
            error_details['retry_suggestion'] = 'Network timeout - please try again in a moment'
            error_details['retryable'] = True
            status_code = 503
        elif 'memory' in str(e).lower() or 'allocation' in str(e).lower():
            error_details['retry_suggestion'] = 'System overloaded - try reducing audio quality'
            error_details['retryable'] = False
            status_code = 507
        else:
            error_details['retry_suggestion'] = 'Unexpected error - please refresh the page'
            error_details['retryable'] = True
            status_code = 500
        
        return jsonify(error_details), status_code

def detect_audio_format(audio_data):
    """
    Detect audio format using magic bytes instead of assuming WebM
    """
    if not audio_data or len(audio_data) < 12:
        return 'webm'  # Default fallback
    
    # Check for common audio format signatures
    if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
        return 'wav'
    elif audio_data[:4] == b'OggS':
        return 'ogg'
    elif audio_data[:4] == b'\x1a\x45\xdf\xa3':  # EBML signature for WebM
        return 'webm'
    elif audio_data[:8] == b'ftypmp4\x00' or audio_data[4:8] == b'ftyp':
        return 'mp4'
    else:
        # If no clear signature, check for WebM container patterns
        if b'webm' in audio_data[:100].lower():
            return 'webm'
        # Default to WebM for browser MediaRecorder
        return 'webm'

def convert_audio_to_wav_enhanced(audio_data):
    """Enhanced audio conversion with multiple fallback strategies"""
    
    if not audio_data or len(audio_data) < 100:
        logger.warning(f"⚠️ Invalid audio data: {len(audio_data) if audio_data else 0} bytes")
        return None
    
    # Strategy 1: PyDub with WebM/Opus
    try:
        from pydub import AudioSegment
        logger.info(f"🔧 Strategy 1: PyDub WebM conversion ({len(audio_data)} bytes)")
        
        audio_segment = AudioSegment.from_file(
            io.BytesIO(audio_data),
            format="webm"
        )
        
        # Optimize for Whisper
        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_sample_width(2)
        
        # Apply noise reduction for better transcription
        audio_segment = audio_segment.normalize()
        
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_data = wav_io.getvalue()
        
        logger.info(f"✅ Strategy 1 successful: {len(wav_data)} bytes WAV")
        return wav_data
        
    except Exception as e1:
        logger.warning(f"⚠️ Strategy 1 failed: {e1}")
    
    # Strategy 2: Try with Opus codec hint
    try:
        audio_segment = AudioSegment.from_file(
            io.BytesIO(audio_data),
            format="webm",
            codec="opus"
        )
        
        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_sample_width(2)
        audio_segment = audio_segment.normalize()
        
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        wav_data = wav_io.getvalue()
        
        logger.info(f"✅ Strategy 2 successful: {len(wav_data)} bytes WAV")
        return wav_data
        
    except Exception as e2:
        logger.warning(f"⚠️ Strategy 2 failed: {e2}")
    
    # Strategy 3: FFmpeg fallback using temporary files
    try:
        import subprocess
        import tempfile
        
        logger.info("🔧 Strategy 3: FFmpeg conversion")
        
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as webm_file:
            webm_file.write(audio_data)
            webm_path = webm_file.name
        
        wav_path = webm_path.replace('.webm', '.wav')
        
        # FFmpeg command optimized for Whisper
        cmd = [
            'ffmpeg', '-y', '-i', webm_path,
            '-ar', '16000',  # 16kHz
            '-ac', '1',      # Mono
            '-c:a', 'pcm_s16le',  # 16-bit PCM
            '-f', 'wav',
            '-loglevel', 'error',
            wav_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(wav_path):
            with open(wav_path, 'rb') as f:
                wav_data = f.read()
            
            # Cleanup
            for path in [webm_path, wav_path]:
                try:
                    os.unlink(path)
                except:
                    pass
            
            logger.info(f"✅ Strategy 3 successful: {len(wav_data)} bytes WAV")
            return wav_data
        else:
            logger.error(f"❌ FFmpeg failed: {result.stderr.decode()}")
            
    except Exception as e3:
        logger.warning(f"⚠️ Strategy 3 failed: {e3}")
    
    # Strategy 4: Assume it's raw PCM and create WAV header
    try:
        logger.info("🔧 Strategy 4: Raw PCM to WAV")
        wav_data = create_wav_from_pcm(audio_data, 16000, 1)
        
        if wav_data and len(wav_data) > 44:
            logger.info(f"✅ Strategy 4 successful: {len(wav_data)} bytes WAV")
            return wav_data
            
    except Exception as e4:
        logger.warning(f"⚠️ Strategy 4 failed: {e4}")
    
    logger.error("❌ All conversion strategies failed")
    return None

def create_wav_from_pcm(pcm_data, sample_rate=16000, channels=1):
    """Create WAV file from raw PCM data"""
    import struct
    
    # Calculate values
    byte_rate = sample_rate * channels * 2  # 16-bit = 2 bytes
    block_align = channels * 2
    data_size = len(pcm_data)
    file_size = 36 + data_size
    
    # Create WAV header
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', file_size, b'WAVE',
        b'fmt ', 16,           # PCM format
        1, channels,           # Format type, channels
        sample_rate, byte_rate, # Sample rate, byte rate
        block_align, 16,       # Block align, bits per sample
        b'data', data_size
    )
    
    return header + pcm_data

@unified_api_bp.route('/api/transcribe-health', methods=['GET'])
def transcription_health():
    """Health check for unified transcription API"""
    try:
        client = get_openai_client()
        
        # Enhanced health monitoring with circuit breakers and system metrics
        try:
            health_monitor = get_health_monitor()
            circuit_manager = __import__('services.circuit_breaker', fromlist=['circuit_manager']).circuit_manager
            
            system_health = health_monitor.get_current_health()
            circuit_health = circuit_manager.health_check()
            
            overall_status = 'healthy'
            if system_health.status == 'unhealthy' or circuit_health['overall_health'] == 'unhealthy':
                overall_status = 'unhealthy'
            elif system_health.status == 'degraded' or circuit_health['overall_health'] == 'degraded':
                overall_status = 'degraded'
        except Exception:
            # Fallback to basic health check if monitoring services fail
            overall_status = 'healthy'
            system_health = None
            circuit_health = None
        
        return jsonify({
            'status': overall_status,
            'openai_api_configured': True,
            'system_metrics': {
                'cpu_usage': system_health.cpu_usage if system_health else 0,
                'memory_usage': system_health.memory_usage if system_health else 0,
                'uptime_hours': round(system_health.uptime / 3600, 2) if system_health else 0,
                'error_rate': system_health.error_rate if system_health else 0
            },
            'circuit_breakers': {
                'status': circuit_health['overall_health'] if circuit_health else 'unknown',
                'open_breakers': circuit_health['open_breakers'] if circuit_health else 0,
                'total_breakers': circuit_health['total_breakers'] if circuit_health else 0
            },
            'services': {
                'openai_client': True,
                'audio_processing': True,
                'pydub_available': True,
                'health_monitor': system_health is not None,
                'circuit_breaker': circuit_health is not None
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'openai_api_configured': bool(os.getenv('OPENAI_API_KEY')),
            'timestamp': time.time()
        }), 503

# Additional robust health monitoring endpoints
@unified_api_bp.route('/api/health/metrics', methods=['GET'])
def detailed_health_metrics():
    """Get detailed health metrics and performance data"""
    try:
        health_monitor = get_health_monitor()
        circuit_manager = __import__('services.circuit_breaker', fromlist=['circuit_manager']).circuit_manager
        
        # Get time range from query params
        hours = int(request.args.get('hours', 1))
        
        return jsonify({
            'timestamp': time.time(),
            'metrics': {
                'cpu_usage': [
                    {'timestamp': m.timestamp, 'value': m.value, 'status': m.status}
                    for m in health_monitor.get_metric_history('cpu_usage', hours * 60)
                ],
                'memory_usage': [
                    {'timestamp': m.timestamp, 'value': m.value, 'status': m.status}
                    for m in health_monitor.get_metric_history('memory_usage', hours * 60)
                ],
                'api_response_time': [
                    {'timestamp': m.timestamp, 'value': m.value, 'status': m.status}
                    for m in health_monitor.get_metric_history('api_response_time', hours * 60)
                ]
            },
            'alerts': health_monitor.get_alerts(hours),
            'circuit_breakers': circuit_manager.get_all_stats(),
            'performance_summary': health_monitor.get_performance_summary()
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': time.time()
        }), 500

@unified_api_bp.route('/api/session/persist', methods=['POST'])
def persist_session():
    """Persist session state for recovery"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        state_data = data.get('state', {})
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        # Basic in-memory session persistence (production would use Redis/DB)
        session_store = getattr(persist_session, '_store', {})
        session_store[session_id] = {
            'state': state_data,
            'timestamp': time.time(),
            'last_activity': time.time()
        }
        persist_session._store = session_store
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'persisted_at': time.time()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@unified_api_bp.route('/api/session/recover/<session_id>', methods=['GET'])
def recover_session(session_id):
    """Recover persisted session state"""
    try:
        session_store = getattr(persist_session, '_store', {})
        
        if session_id not in session_store:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = session_store[session_id]
        
        # Check if session is still valid (within 24 hours)
        if time.time() - session_data['timestamp'] > 86400:
            del session_store[session_id]
            return jsonify({'error': 'Session expired'}), 410
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'state': session_data['state'],
            'last_activity': session_data['last_activity'],
            'age_hours': (time.time() - session_data['timestamp']) / 3600
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start health monitoring
try:
    health_monitor = get_health_monitor()
    health_monitor.start_monitoring(interval=30)  # Monitor every 30 seconds
    logger.info("🏥 Health monitoring started")
except Exception as e:
    logger.warning(f"⚠️ Failed to start health monitoring: {e}")

logger.info("✅ Enhanced Unified Transcription API initialized with robust monitoring")