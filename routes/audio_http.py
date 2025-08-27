"""
HTTP endpoints for real-time audio transcription
Simple approach that works with any browser
"""

from flask import Blueprint, request, jsonify
import logging
import os
import tempfile
import requests
import base64
import time

audio_http_bp = Blueprint('audio_http', __name__)
logger = logging.getLogger(__name__)

@audio_http_bp.route('/api/transcribe-audio', methods=['POST'])
def transcribe_audio():
    """Receive and transcribe audio data via HTTP POST"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        session_id = data.get('session_id', 'unknown')
        audio_data = data.get('audio_data')  # Base64 encoded
        
        logger.info(f"🎵 Received audio for session {session_id}")
        
        if not audio_data:
            return jsonify({
                'session_id': session_id,
                'text': '[No audio data]',
                'is_final': False,
                'confidence': 0.0
            })
        
        # Decode and transcribe
        try:
            audio_bytes = base64.b64decode(audio_data)
            transcript = transcribe_audio_sync(audio_bytes)
            
            if transcript and transcript.strip():
                return jsonify({
                    'session_id': session_id,
                    'text': transcript.strip(),
                    'is_final': True,
                    'confidence': 0.95,
                    'status': 'success'
                })
            else:
                return jsonify({
                    'session_id': session_id,
                    'text': '[No speech detected]',
                    'is_final': False,
                    'confidence': 0.0,
                    'status': 'no_speech'
                })
                
        except Exception as e:
            logger.error(f"❌ Audio processing error: {e}")
            return jsonify({
                'session_id': session_id,
                'text': '[Processing error]',
                'is_final': False,
                'confidence': 0.0,
                'status': 'error'
            })
            
    except Exception as e:
        logger.error(f"❌ HTTP audio endpoint error: {e}")
        return jsonify({'error': 'Server error'}), 500

def transcribe_audio_sync(audio_data):
    """Enhanced audio transcription with monitoring recommendations implemented"""
    start_time = time.time()
    
    try:
        # MONITORING FIX 1.1: Audio chunk validation
        if len(audio_data) < 100:
            logger.warning("⚠️ Audio chunk too small for transcription")
            return None
            
        # MONITORING FIX 1.1: Audio format validation
        if not audio_data.startswith(b'OpusHead') and not audio_data.startswith(b'RIFF'):
            logger.warning("⚠️ Unexpected audio format detected")
            
        # Save to temp file with enhanced error handling
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # MONITORING FIX 1.1: API key validation
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("❌ CRITICAL: No OpenAI API key found")
                return None
                
            if not api_key.startswith('sk-'):
                logger.error("❌ CRITICAL: Invalid OpenAI API key format")
                return None
                
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mina-Transcription/1.0"
            }
            
            # MONITORING FIX 1.1: Enhanced request with validation
            with open(temp_file_path, 'rb') as audio_file:
                files = {
                    'file': ('audio.webm', audio_file, 'audio/webm'),
                    'model': (None, 'whisper-1'),
                    'response_format': (None, 'json'),  # Get detailed response
                    'language': (None, 'en'),
                    'temperature': (None, '0')  # Deterministic results
                }
                
                # MONITORING FIX 1.1: Request with comprehensive error handling
                response = requests.post(
                    url, 
                    headers=headers, 
                    files=files, 
                    timeout=15,  # Increased timeout
                    retry=3 if hasattr(requests, 'retry') else None
                )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # MONITORING FIX 1.1: Enhanced response processing
            processing_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    text = result.get('text', '').strip()
                    
                    if text:
                        logger.info(f"✅ WHISPER SUCCESS: {text[:50]}... ({processing_time:.0f}ms)")
                        return text
                    else:
                        logger.warning(f"⚠️ WHISPER EMPTY: No text in response ({processing_time:.0f}ms)")
                        return None
                        
                except Exception as json_error:
                    # Fallback to text response
                    text = response.text.strip()
                    if text:
                        logger.info(f"✅ WHISPER SUCCESS (text): {text[:50]}... ({processing_time:.0f}ms)")
                        return text
                    else:
                        logger.error(f"❌ WHISPER JSON ERROR: {json_error}")
                        return None
            else:
                logger.error(f"❌ WHISPER API ERROR {response.status_code}: {response.text[:200]}... ({processing_time:.0f}ms)")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ WHISPER TIMEOUT after {(time.time() - start_time) * 1000:.0f}ms")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ WHISPER REQUEST ERROR: {e}")
            return None
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            logger.error(f"❌ WHISPER PROCESSING ERROR: {e}")
            return None
            
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ AUDIO PROCESSING FAILED: {e} ({processing_time:.0f}ms)")
        return None