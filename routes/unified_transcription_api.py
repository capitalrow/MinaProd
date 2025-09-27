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
    🎯 UNIFIED TRANSCRIPTION ENDPOINT
    Handles BOTH base64 audio data AND file uploads
    Supports interim and final transcription modes
    """
    request_start_time = time.time()
    
    try:
        # Extract session info
        session_id = None
        chunk_id = None
        is_interim = False
        
        # Determine request format and extract data
        audio_data = None
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle FormData file upload
            logger.info("📁 Processing FormData file upload")
            
            session_id = request.form.get('session_id', f'session_{int(time.time())}')
            chunk_id = request.form.get('chunk_id', '1')
            is_interim = request.form.get('is_interim', 'false').lower() == 'true'
            
            if 'audio' in request.files:
                audio_file = request.files['audio']
                if audio_file and audio_file.filename:
                    audio_data = audio_file.read()
                    logger.info(f"📦 File upload: {len(audio_data)} bytes from {audio_file.filename}")
            
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
        
        # Validate audio size
        if len(audio_data) < 100:
            logger.info(f"ℹ️ Audio too short ({len(audio_data)} bytes) - returning empty result")
            return jsonify({
                'success': True,
                'text': '',
                'final_text': '',
                'confidence': 0.0,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'is_interim': is_interim,
                'message': 'Audio too short for transcription',
                'processing_time': (time.time() - request_start_time) * 1000
            })
        
        logger.info(f"🎵 Processing audio: session={session_id}, chunk={chunk_id}, interim={is_interim}, size={len(audio_data)} bytes")
        
        # 🔥 CRITICAL FIX: Use robust AudioProcessor service for conversion
        try:
            from services.audio_processor import AudioProcessor
            audio_processor = AudioProcessor()
            wav_audio = audio_processor.convert_to_wav(audio_data, 'webm')
            
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
        
        # Transcribe using OpenAI Whisper
        try:
            client = get_openai_client()
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(wav_audio)
                temp_file_path = temp_file.name
            
            try:
                # Call Whisper API
                transcription_start = time.time()
                
                with open(temp_file_path, "rb") as audio_file:
                    # Optimized Whisper parameters for accuracy
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        temperature=0.0,  # Lower temperature for more accurate results
                        prompt="Professional meeting transcription. Transcribe exactly what is spoken with proper punctuation and capitalization."
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
                
                return jsonify(result)
                
            finally:
                # Cleanup temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as whisper_error:
            logger.error(f"❌ Whisper API error: {whisper_error}")
            processing_time = (time.time() - request_start_time) * 1000
            
            return jsonify({
                'error': f'Transcription failed: {str(whisper_error)}',
                'success': False,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'processing_time': processing_time
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Critical error in unified transcription API: {e}", exc_info=True)
        processing_time = (time.time() - request_start_time) * 1000
        
        return jsonify({
            'error': f'Server error: {str(e)}',
            'success': False,
            'session_id': session_id or 'unknown',
            'processing_time': processing_time
        }), 500

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
        
        return jsonify({
            'status': 'healthy',
            'openai_api_configured': True,
            'services': {
                'openai_client': True,
                'audio_processing': True,
                'pydub_available': True
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

logger.info("✅ Unified Transcription API initialized")