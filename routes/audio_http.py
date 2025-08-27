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
    """Synchronous audio transcription using OpenAI Whisper API"""
    try:
        if len(audio_data) < 100:
            return None
            
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Call OpenAI Whisper API
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("No OpenAI API key found")
                return None
                
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            with open(temp_file_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                    'model': (None, 'whisper-1'),
                    'response_format': (None, 'text'),
                    'language': (None, 'en')
                }
                
                response = requests.post(url, headers=headers, files=files, timeout=10)
            
            os.unlink(temp_file_path)
            
            if response.status_code == 200:
                text = response.text.strip()
                logger.info(f"✅ Transcribed: {text[:50]}...")
                return text
            else:
                logger.error(f"OpenAI API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            logger.error(f"Transcription error: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        return None