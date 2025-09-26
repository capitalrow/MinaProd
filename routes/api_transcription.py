# routes/api_transcription.py
"""
HTTP POST chunked audio transcription endpoint
Based on proven working implementation for reliable live transcription
"""

from flask import Blueprint, request, jsonify, current_app
import os
import tempfile
import time
from datetime import datetime
from openai import OpenAI
from extensions import socketio

# Create blueprint
transcription_bp = Blueprint('transcription', __name__)

# Initialize OpenAI client using the proven pattern from services/openai_whisper_client.py
import httpx

def _make_http_client() -> httpx.Client:
    """Build an httpx client that ignores environment proxies"""
    return httpx.Client(
        timeout=30.0,
        http2=True,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        verify=True,
        trust_env=False,  # critical: do not load HTTP(S)_PROXY from env
    )

# Initialize OpenAI client
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai_client = OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=_make_http_client()  # bypasses SDK's default client creation
        )
        print(f"[LIVE-API] ✅ OpenAI client initialized successfully")
    else:
        openai_client = None
        print(f"[LIVE-API] ❌ OpenAI API key not found")
except Exception as e:
    openai_client = None
    print(f"[LIVE-API] ❌ OpenAI initialization failed: {e}")

@transcription_bp.route('/api/transcribe_chunk_streaming', methods=['POST', 'GET', 'OPTIONS'])
def transcribe_chunk_streaming():
    """
    The main transcription endpoint that actually works
    Processes audio chunks and returns real transcription results
    """
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight successful'}), 200
    
    # Handle GET request for testing
    if request.method == 'GET':
        return jsonify({
            'message': 'Transcription streaming endpoint is operational',
            'methods': ['POST', 'GET', 'OPTIONS'],
            'openai_configured': openai_client is not None,
            'endpoint': '/api/transcribe_chunk_streaming',
            'status': 'ready'
        })
    
    start_time = time.time()
    
    try:
        print(f"[LIVE-API] 🎵 Received transcription request")
        
        # Check if OpenAI is available
        if not openai_client:
            return jsonify({
                'error': 'OpenAI API not configured',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'type': 'error'
            }), 500
        
        # Get form data
        audio_file = request.files.get('audio')
        session_id = request.form.get('session_id', f'session_{int(time.time())}')
        chunk_id = request.form.get('chunk_id', '1')
        
        print(f"[LIVE-API] 📊 Request details: audio_file={bool(audio_file)}, session_id={session_id}, chunk_id={chunk_id}")
        
        # Enhanced request logging
        if audio_file:
            print(f"[LIVE-API] 🎵 Audio file: {audio_file.filename}, size: {audio_file.content_length or 'unknown'}")
        
        # Log all form data for debugging
        print(f"[LIVE-API] 📋 Form data: {dict(request.form)}")
        print(f"[LIVE-API] 📂 Files: {list(request.files.keys())}")
        
        if not audio_file:
            return jsonify({
                'error': 'No audio file provided',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'type': 'error'
            }), 400
        
        print(f"[LIVE-API] 📁 Processing chunk {chunk_id}: {audio_file.filename} ({audio_file.content_length} bytes)")
        
        # Validate file size (minimum 1KB, maximum 25MB)
        if hasattr(audio_file, 'content_length') and audio_file.content_length:
            if audio_file.content_length < 1000:
                print(f"[LIVE-API] ⚠️ Chunk {chunk_id} too small: {audio_file.content_length} bytes")
                return jsonify({
                    'text': '',
                    'confidence': 0,
                    'processing_time': time.time() - start_time,
                    'chunk_id': chunk_id,
                    'type': 'partial',
                    'message': 'Audio chunk too small'
                })
            
            if audio_file.content_length > 25 * 1024 * 1024:  # 25MB limit
                return jsonify({
                    'error': 'Audio file too large (max 25MB)',
                    'text': '',
                    'confidence': 0,
                    'processing_time': time.time() - start_time,
                    'chunk_id': chunk_id,
                    'type': 'error'
                }), 413
        
        # Create temporary file for OpenAI processing  
        # Fix: Read the file data directly instead of saving to path
        audio_data = audio_file.read()
        print(f"[LIVE-API] 📏 Raw audio data size: {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            return jsonify({
                'error': 'Empty audio file received',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'type': 'error'
            }), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            temp_file_path = temp_file.name
            print(f"[LIVE-API] 💾 Temp file created: {temp_file_path}, size: {len(audio_data)} bytes")
        
        try:
            # Call OpenAI Whisper API
            print(f"[LIVE-API] 🤖 Sending chunk {chunk_id} to OpenAI Whisper...")
            
            with open(temp_file_path, 'rb') as audio_data:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    response_format="verbose_json",
                    language="en"  # Can be made dynamic
                )
            
            # Extract text and confidence
            text = transcription.text.strip() if transcription.text else ""
            
            # Calculate confidence from segments if available
            confidence = 0.0
            if hasattr(transcription, 'segments') and getattr(transcription, 'segments', None):
                confidences = []
                for segment in transcription.segments:
                    if hasattr(segment, 'avg_logprob'):
                        # Convert log probability to confidence (0-1)
                        conf = min(1.0, max(0.0, (segment.avg_logprob + 1.5) / 1.5))
                        confidences.append(conf)
                
                if confidences:
                    confidence = sum(confidences) / len(confidences)
                else:
                    confidence = 0.5 if text else 0.0
            else:
                confidence = 0.5 if text else 0.0
            
            processing_time = time.time() - start_time
            
            print(f"[LIVE-API] ✅ Chunk {chunk_id} transcribed successfully:")
            print(f"[LIVE-API]    Text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            print(f"[LIVE-API]    Confidence: {confidence:.3f}")
            print(f"[LIVE-API]    Processing time: {processing_time:.3f}s")
            
            # Prepare response
            response_data = {
                'text': text,
                'confidence': confidence,
                'processing_time': processing_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'success' if text else 'partial',
                'segments': []
            }
            
            # Add segment data if available
            segments = getattr(transcription, 'segments', None)
            if segments:
                for segment in segments:
                    response_data['segments'].append({
                        'start': getattr(segment, 'start', 0),
                        'end': getattr(segment, 'end', 0),
                        'text': getattr(segment, 'text', ''),
                        'confidence': min(1.0, max(0.0, (getattr(segment, 'avg_logprob', -1) + 1.5) / 1.5))
                    })
            
            # Emit to WebSocket for real-time updates (if client connected)
            try:
                if text and confidence > 0.1:  # Only emit meaningful results
                    socketio.emit('transcription_result', response_data)
                    print(f"[LIVE-API] 📡 Emitted transcription result via WebSocket")
            except Exception as e:
                print(f"[LIVE-API] ⚠️ WebSocket emit failed: {e}")
            
            return jsonify(response_data)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"[LIVE-API] ⚠️ Failed to delete temp file: {e}")
    
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        chunk_id = request.form.get('chunk_id', 'unknown')
        
        print(f"[LIVE-API] ❌ Transcription error for chunk {chunk_id}: {error_msg}")
        
        # Handle specific OpenAI errors
        if "rate_limit" in error_msg.lower():
            return jsonify({
                'error': 'Rate limit exceeded. Please wait a moment.',
                'text': '',
                'confidence': 0,
                'processing_time': processing_time,
                'chunk_id': chunk_id,
                'type': 'rate_limit'
            }), 429
        
        elif "quota" in error_msg.lower():
            return jsonify({
                'error': 'API quota exceeded. Please check your OpenAI account.',
                'text': '',
                'confidence': 0,
                'processing_time': processing_time,
                'chunk_id': chunk_id,
                'type': 'quota_exceeded'
            }), 402
        
        else:
            return jsonify({
                'error': f'Transcription failed: {error_msg}',
                'text': '',
                'confidence': 0,
                'processing_time': processing_time,
                'chunk_id': chunk_id,
                'type': 'error'
            }), 500

@transcription_bp.route('/api/transcription/health', methods=['GET'])
def transcription_health():
    """Health check for transcription service"""
    try:
        health_data = {
            'status': 'healthy',
            'openai_configured': openai_client is not None,
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
        
        # Test OpenAI connection if available
        if openai_client:
            try:
                # Quick test - list models (doesn't count against quota)
                models = openai_client.models.list()
                health_data['openai_status'] = 'connected'
                health_data['available_models'] = [m.id for m in models.data if 'whisper' in m.id]
            except Exception as e:
                health_data['openai_status'] = f'error: {str(e)}'
        
        return jsonify(health_data)
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Test endpoint for debugging
@transcription_bp.route('/api/transcription/test', methods=['GET', 'POST'])
def transcription_test():
    """Test endpoint for debugging transcription issues"""
    if request.method == 'GET':
        return jsonify({
            'message': 'Transcription test endpoint is working',
            'openai_configured': openai_client is not None,
            'methods': ['GET', 'POST'],
            'timestamp': datetime.utcnow().isoformat()
        })
    
    else:  # POST
        return jsonify({
            'message': 'Test POST received',
            'form_data': dict(request.form),
            'files': list(request.files.keys()),
            'openai_ready': openai_client is not None
        })