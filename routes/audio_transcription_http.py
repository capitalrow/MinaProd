#!/usr/bin/env python3
"""
🎤 HTTP-based Audio Transcription API
Reliable endpoint for audio transcription without WebSocket dependencies
"""

import os
import json
import time
import tempfile
import logging
import traceback
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import openai

from models import Session, Segment
from app import db

logger = logging.getLogger(__name__)

# Create blueprint for audio transcription routes
audio_bp = Blueprint('audio_transcription', __name__)

# Initialize OpenAI client
openai_client = None

def get_openai_client():
    """Get or initialize OpenAI client."""
    global openai_client
    if openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        openai_client = openai.OpenAI(api_key=api_key)
    return openai_client

@audio_bp.route('/api/transcribe', methods=['POST'])
def transcribe_audio():
    """
    HTTP endpoint for audio transcription.
    Accepts audio files and returns transcription results.
    """
    try:
        start_time = time.time()
        
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({
                'error': 'No audio file provided',
                'success': False,
                'timestamp': time.time()
            }), 400
        
        audio_file = request.files['audio']
        session_id = request.form.get('session_id', 'default')
        
        if audio_file.filename == '':
            return jsonify({
                'error': 'No audio file selected',
                'success': False,
                'timestamp': time.time()
            }), 400
        
        # Get session from database
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if not session:
            # Create new session if it doesn't exist
            session = Session(
                external_id=session_id,
                started_at=datetime.utcnow(),
                status='active'
            )
            db.session.add(session)
            db.session.commit()
            logger.info(f"Created new session: {session_id}")
        
        # Save audio file temporarily with proper extension
        temp_dir = tempfile.gettempdir()
        original_filename = audio_file.filename or ''
        
        # Ensure proper extension for OpenAI API
        if original_filename:
            filename = secure_filename(original_filename)
            # If no extension or not a supported format, default to webm
            if not filename or '.' not in filename:
                filename = f"audio_{int(time.time())}.webm"
        else:
            filename = f"audio_{int(time.time())}.webm"
        
        # Ensure webm extension for browser recordings
        if not filename.endswith(('.wav', '.webm', '.mp3', '.m4a', '.mp4')):
            filename = filename.rsplit('.', 1)[0] + '.webm' if '.' in filename else filename + '.webm'
            
        temp_path = os.path.join(temp_dir, filename)
        
        audio_file.save(temp_path)
        logger.info(f"Saved audio file: {temp_path} ({os.path.getsize(temp_path)} bytes)")
        
        try:
            # Transcribe with OpenAI Whisper API
            client = get_openai_client()
            
            # Add retry logic with exponential backoff
            from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
            import openai
            
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError))
            )
            def transcribe_with_retry():
                with open(temp_path, 'rb') as audio_data:
                    logger.info(f"Sending audio to OpenAI Whisper API (format: {filename})...")
                    
                    # Create file tuple with proper name for OpenAI
                    audio_file_tuple = (filename, audio_data, 'audio/webm')
                    
                    return client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_tuple,
                        response_format="verbose_json",  # Get detailed response with timestamps
                        language="en"  # Can be made configurable
                    )
            
            # Call with retry logic
            transcript_response = transcribe_with_retry()
                
            # Process transcription response
            transcript_text = transcript_response.text
            segments = getattr(transcript_response, 'segments', [])
            
            logger.info(f"Transcription completed: {len(transcript_text)} characters, {len(segments)} segments")
            
            # Save transcription segments to database
            for i, segment in enumerate(segments):
                # Handle both dict and object formats
                if hasattr(segment, 'text'):
                    # It's an object with attributes
                    segment_text = getattr(segment, 'text', '')
                    segment_confidence = getattr(segment, 'avg_logprob', 0.0) if hasattr(segment, 'avg_logprob') else 0.0
                    segment_start = getattr(segment, 'start', 0.0)
                    segment_end = getattr(segment, 'end', 0.0)
                    segment_speaker = getattr(segment, 'speaker', 'unknown') if hasattr(segment, 'speaker') else 'unknown'
                else:
                    # It's a dictionary
                    segment_text = segment.get('text', '')
                    segment_confidence = segment.get('avg_logprob', 0.0)
                    segment_start = segment.get('start', 0.0)
                    segment_end = segment.get('end', 0.0)
                    segment_speaker = segment.get('speaker', 'unknown')
                
                db_segment = Segment(
                    session_id=session.id,  # Use session.id not session_id string
                    text=segment_text,
                    kind='final',  # Mark as final transcription
                    avg_confidence=segment_confidence if segment_confidence else None,
                    start_ms=int(segment_start * 1000) if segment_start else None,  # Convert to milliseconds
                    end_ms=int(segment_end * 1000) if segment_end else None,  # Convert to milliseconds
                    created_at=datetime.utcnow()
                )
                db.session.add(db_segment)
            
            # Update session
            if not session.started_at:
                session.started_at = datetime.utcnow()
            session.total_segments = len(segments)
            db.session.commit()
            
            # Calculate performance metrics
            processing_time = time.time() - start_time
            
            response_data = {
                'success': True,
                'transcript': transcript_text,
                'segments': [
                    {
                        'text': getattr(seg, 'text', ''),
                        'start': getattr(seg, 'start', 0.0),
                        'end': getattr(seg, 'end', 0.0),
                        'confidence': getattr(seg, 'avg_logprob', 0.0)
                    }
                    for seg in segments
                ],
                'session_id': session_id,
                'processing_time': processing_time,
                'audio_duration': getattr(segments[-1], 'end', 0.0) if segments else 0.0,
                'segment_count': len(segments),
                'timestamp': time.time(),
                'api_latency': processing_time
            }
            
            logger.info(f"✅ Transcription successful: {len(transcript_text)} chars in {processing_time:.2f}s")
            return jsonify(response_data)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup {temp_path}: {cleanup_error}")
        
    except ValueError as ve:
        # Missing API key or configuration error
        logger.error(f"Configuration error: {ve}")
        return jsonify({
            'error': 'Service configuration error. Please check API credentials.',
            'success': False,
            'timestamp': time.time(),
            'details': str(ve)
        }), 500
        
    except Exception as e:
        # General processing error
        logger.error(f"Transcription error: {e}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Transcription service error. Please try again.',
            'success': False,
            'timestamp': time.time(),
            'details': str(e) if current_app.debug else 'Internal server error'
        }), 500

@audio_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for transcription service."""
    try:
        # Check OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        api_key_status = 'configured' if api_key else 'missing'
        
        # Check database connectivity
        try:
            db.session.execute('SELECT 1')
            db_status = 'connected'
        except Exception:
            db_status = 'error'
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'api_key_status': api_key_status,
            'database_status': db_status,
            'transcription_mode': 'http',
            'version': '2.0.0'
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@audio_bp.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get status and metrics for a specific session."""
    try:
        session = db.session.query(Session).filter_by(external_id=session_id).first()
        if not session:
            return jsonify({
                'error': 'Session not found',
                'success': False
            }), 404
        
        # Get segment count and latest activity
        segment_count = db.session.query(Segment).filter_by(session_id=session.id).count()
        latest_segment = db.session.query(Segment).filter_by(session_id=session.id).order_by(Segment.created_at.desc()).first()
        
        status_data = {
            'session_id': session_id,
            'status': session.status,
            'created_at': session.started_at.isoformat() if session.started_at else None,
            'last_activity': session.completed_at.isoformat() if session.completed_at else None,
            'total_segments': segment_count,
            'latest_segment_time': latest_segment.created_at.isoformat() if latest_segment else None,
            'success': True
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Session status error: {e}")
        return jsonify({
            'error': 'Failed to get session status',
            'success': False,
            'details': str(e)
        }), 500