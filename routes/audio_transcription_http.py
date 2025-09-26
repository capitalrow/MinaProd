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
import io
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import openai
from pydub import AudioSegment

from models import Segment, Conversation
from models import db

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

@audio_bp.route('/api/transcribe_streaming', methods=['POST'])
def transcribe_audio_streaming():
    """
    🚀 STREAMING HTTP endpoint for real-time audio transcription.
    Processes chunks immediately and broadcasts via WebSocket.
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
        
        # Read audio data into memory
        audio_data = audio_file.read()
        original_filename = audio_file.filename or 'chunk.webm'
        
        # Get conversation from database (using current model structure)
        conversation = db.session.query(Conversation).filter_by(id=session_id).first()
        if not conversation:
            # Create new conversation if it doesn't exist
            conversation = Conversation(
                user_id=1,  # Default user for now
                title=f"Meeting {session_id}",
                created_at=datetime.utcnow()
            )
            db.session.add(conversation)
            db.session.commit()
            logger.info(f"Created new conversation: {session_id}")
        conversation_id = conversation.id
        
        # Convert webm to wav for better compatibility
        temp_dir = tempfile.gettempdir()
        wav_filename = f"audio_{session_id}_{int(time.time())}.wav"
        temp_path = os.path.join(temp_dir, wav_filename)
        
        try:
            # Convert webm to wav using pydub
            logger.info(f"Converting audio from {original_filename} to WAV format...")
            
            # Load audio from bytes
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format="webm" if original_filename.endswith('.webm') else None
            )
            
            # Convert to optimal format for Whisper
            audio_segment = audio_segment.set_frame_rate(16000)
            audio_segment = audio_segment.set_channels(1)
            audio_segment = audio_segment.set_sample_width(2)  # 16-bit
            
            # Export as WAV
            audio_segment.export(temp_path, format="wav")
            logger.info(f"Converted and saved audio file: {temp_path} ({os.path.getsize(temp_path)} bytes)")
            
        except Exception as conv_error:
            logger.error(f"Audio conversion failed: {conv_error}")
            # Fallback: save original file
            temp_path = os.path.join(temp_dir, original_filename)
            with open(temp_path, 'wb') as f:
                f.write(audio_data)
            logger.warning(f"Using original file format: {temp_path}")
        
        try:
            # 🚀 STREAMING INTEGRATION: Use real-time transcription service
            try:
                from services.realtime_transcription import realtime_service, StreamingChunk
            except ImportError as ie:
                logger.warning(f"⚠️ Streaming service not available: {ie}")
                # Fallback to original processing
                client = get_openai_client()
                
                # Use original transcription method as fallback
                with open(temp_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="verbose_json",
                        language="en",
                        temperature=0.2,
                    )
                
                # Handle fallback response
                text = response.text.strip()
                
                # Calculate basic confidence for fallback
                confidence = 0.8 if len(text) > 10 else 0.5
                
                processing_time = time.time() - start_time
                
                return jsonify({
                    "success": True,
                    "text": text,
                    "confidence": confidence,
                    "is_final": True,
                    "session_id": session_id,
                    "processing_time": processing_time,
                    "fallback_mode": True,
                    "message": "Using fallback transcription"
                })
            
            # Create streaming chunk
            chunk = StreamingChunk(
                audio_data=audio_data,
                session_id=session_id,
                chunk_id=int(time.time() * 1000),  # Unique chunk ID
                timestamp=time.time(),
                duration_ms=len(audio_data) // 32,  # Estimate duration
                is_final=request.form.get('is_final', 'false').lower() == 'true'
            )
            
            # Process chunk with streaming service
            import asyncio
            result = asyncio.run(realtime_service.process_streaming_chunk(chunk))
            
            if result:
                # Broadcast via WebSocket immediately
                from extensions import socketio
                socketio.emit('transcription_result', {
                    "type": "final_result" if result.is_final else "interim_result",
                    "session_id": result.session_id,
                    "text": result.text,
                    "confidence": result.confidence,
                    "is_final": result.is_final,
                    "latency_ms": result.latency_ms,
                    "timestamp": result.timestamp,
                    "chunk_id": result.chunk_id,
                    "words": result.words,
                    "performance_target_met": result.latency_ms < 500
                }, room=session_id)
                
                # Save to database for final results
                if result.is_final and result.text:
                    # Find the next segment index
                    max_idx = db.session.query(db.func.max(Segment.idx)).filter_by(conversation_id=conversation_id).scalar() or 0
                    
                    segment = Segment(
                        conversation_id=conversation_id,
                        idx=max_idx + 1,
                        start_ms=int(result.timestamp * 1000),
                        end_ms=int((result.timestamp + (result.latency_ms / 1000)) * 1000),
                        text=result.text,
                        is_final=result.is_final
                    )
                    db.session.add(segment)
                    db.session.commit()
                
                # Return streaming response
                processing_time = time.time() - start_time
                return jsonify({
                    "success": True,
                    "text": result.text,
                    "confidence": result.confidence,
                    "is_final": result.is_final,
                    "session_id": session_id,
                    "processing_time": processing_time,
                    "latency_ms": result.latency_ms,
                    "performance": {
                        "target_met": result.latency_ms < 500,
                        "target_latency_ms": 500,
                        "actual_latency_ms": result.latency_ms
                    },
                    "chunk_id": result.chunk_id,
                    "timestamp": result.timestamp
                })
            else:
                # No transcription result (filtered out)
                return jsonify({
                    "success": True,
                    "text": "",
                    "confidence": 0.0,
                    "is_final": chunk.is_final,
                    "session_id": session_id,
                    "processing_time": time.time() - start_time,
                    "message": "Chunk filtered (too small or low confidence)"
                })
            
            # FALLBACK: Enhanced original transcription code with error handling
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
                    # Determine the file format
                    file_format = "audio/wav" if temp_path.endswith('.wav') else "audio/webm"
                    file_name = os.path.basename(temp_path)
                    
                    logger.info(f"Sending audio to OpenAI Whisper API (format: {file_name}, type: {file_format})...")
                    
                    # Create file tuple with proper name and MIME type
                    audio_file_tuple = (file_name, audio_data, file_format)
                    
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
                
                # Find the next segment index
                max_idx = db.session.query(db.func.max(Segment.idx)).filter_by(conversation_id=conversation_id).scalar() or 0
                
                db_segment = Segment(
                    conversation_id=conversation_id,
                    idx=max_idx + i + 1,
                    text=segment_text,
                    start_ms=int(segment_start * 1000) if segment_start else 0,
                    end_ms=int(segment_end * 1000) if segment_end else 0,
                    is_final=True
                )
                db.session.add(db_segment)
            
            # Update conversation
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
        conversation = db.session.query(Conversation).filter_by(id=session_id).first()
        if not conversation:
            return jsonify({
                'error': 'Session not found',
                'success': False
            }), 404
        
        # Get segment count and latest activity
        segment_count = db.session.query(Segment).filter_by(conversation_id=conversation.id).count()
        latest_segment = db.session.query(Segment).filter_by(conversation_id=conversation.id).order_by(Segment.id.desc()).first()
        
        status_data = {
            'session_id': session_id,
            'status': 'active',
            'created_at': conversation.created_at.isoformat() if conversation.created_at else None,
            'last_activity': None,
            'total_segments': segment_count,
            'latest_segment_time': None,
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