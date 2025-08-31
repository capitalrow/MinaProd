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
        
        # Save audio file temporarily
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(audio_file.filename) or f"audio_{int(time.time())}.webm"
        temp_path = os.path.join(temp_dir, filename)
        
        audio_file.save(temp_path)
        logger.info(f"Saved audio file: {temp_path} ({os.path.getsize(temp_path)} bytes)")
        
        try:
            # Transcribe with OpenAI Whisper API
            client = get_openai_client()
            
            with open(temp_path, 'rb') as audio_data:
                logger.info(f"Sending audio to OpenAI Whisper API...")
                
                transcript_response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_data,
                    response_format="verbose_json",  # Get detailed response with timestamps
                    language="en"  # Can be made configurable
                )
                
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
                    confidence=segment_confidence,
                    start_time=segment_start,
                    end_time=segment_end,
                    speaker_id=segment_speaker,
                    sequence_number=i,
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
                        'text': seg.get('text', ''),
                        'start': seg.get('start', 0.0),
                        'end': seg.get('end', 0.0),
                        'confidence': seg.get('avg_logprob', 0.0)
                    }
                    for seg in segments
                ],
                'session_id': session_id,
                'processing_time': processing_time,
                'audio_duration': segments[-1].get('end', 0.0) if segments else 0.0,
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