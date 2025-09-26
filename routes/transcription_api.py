"""
Working Live Transcription HTTP API
Provides HTTP endpoints for transcription functionality
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
import time
from datetime import datetime
from openai import OpenAI

# Import database models
from models import db, Session, Segment

# Create blueprint
transcription_api_bp = Blueprint('transcription_api', __name__)

# Initialize OpenAI client
try:
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if OPENAI_API_KEY:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)  # Explicit initialization
        print(f"[LIVE-API] ✅ OpenAI client initialized successfully")
    else:
        openai_client = None
        print(f"[LIVE-API] ❌ OpenAI API key not found")
except Exception as e:
    openai_client = None
    print(f"[LIVE-API] ❌ OpenAI initialization failed: {e}")

@transcription_api_bp.route('/api/transcribe_chunk_streaming', methods=['POST', 'GET', 'OPTIONS'])
def transcribe_chunk_streaming():
    """
    Main transcription endpoint that processes audio chunks
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
        
        if not audio_file:
            return jsonify({
                'error': 'No audio file provided',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'type': 'error'
            }), 400
        
        print(f"[LIVE-API] 📁 Processing audio file: {audio_file.filename}")
        print(f"[LIVE-API] 🔑 Session ID: {session_id}")
        print(f"[LIVE-API] 📊 Chunk ID: {chunk_id}")
        
        # Create or get existing session in database
        try:
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            if not session:
                session = Session(
                    external_id=session_id,
                    title="HTTP Transcription Session",
                    status="active",
                    started_at=datetime.utcnow()
                )
                db.session.add(session)
                db.session.commit()
                print(f"[LIVE-API] Created new session in DB: {session_id}")
        except Exception as e:
            print(f"[LIVE-API] Database error: {e}")
            # Continue without database persistence
            session = None
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_file:
            audio_file.save(tmp_file.name)
            audio_path = tmp_file.name
            
        try:
            # Transcribe using OpenAI Whisper
            with open(audio_path, 'rb') as audio_data:
                transcription = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    response_format="verbose_json"
                )
            
            text = transcription.text.strip() if transcription.text else ""
            confidence = getattr(transcription, 'confidence', 0.9)
            
            print(f"[LIVE-API] ✅ Transcription successful: '{text[:50]}...'")
            
            # Save segment to database
            if session and text:
                try:
                    segment = Segment(
                        session_id=session.id,
                        text=text,
                        start_time=0,
                        end_time=0,
                        confidence=confidence,
                        is_final=False,
                        segment_type="chunk"
                    )
                    db.session.add(segment)
                    db.session.commit()
                    print(f"[LIVE-API] Saved segment to database")
                except Exception as e:
                    print(f"[LIVE-API] Database error saving segment: {e}")
            
            processing_time = time.time() - start_time
            
            return jsonify({
                'text': text,
                'confidence': confidence,
                'processing_time': processing_time,
                'session_id': session_id,
                'chunk_id': chunk_id,
                'type': 'success'
            })
            
        except Exception as transcription_error:
            print(f"[LIVE-API] ❌ Transcription error: {transcription_error}")
            return jsonify({
                'error': f'Transcription failed: {str(transcription_error)}',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'type': 'error'
            }), 500
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(audio_path)
            except OSError:
                pass
                
    except Exception as e:
        print(f"[LIVE-API] ❌ Unexpected error: {e}")
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'text': '',
            'confidence': 0,
            'processing_time': time.time() - start_time,
            'type': 'error'
        }), 500

@transcription_api_bp.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'openai_configured': openai_client is not None,
        'timestamp': datetime.utcnow().isoformat()
    })