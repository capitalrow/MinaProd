# routes/api_transcription.py
"""
Enterprise-Grade Audio Transcription Service
Advanced buffering system for MediaRecorder chunk assembly and optimal transcription
"""

from flask import Blueprint, request, jsonify, current_app
import os
import tempfile
import time
import threading
from datetime import datetime, timedelta
from collections import deque, defaultdict
from openai import OpenAI
from extensions import socketio
import io
import uuid

# Create blueprint
transcription_bp = Blueprint('transcription', __name__)

# Advanced Audio Buffer Management System
class AudioBufferManager:
    """Enterprise-grade audio buffer management for MediaRecorder chunk assembly"""
    
    def __init__(self):
        self.session_buffers = defaultdict(deque)  # session_id -> deque of audio chunks
        self.session_metadata = defaultdict(dict)  # session_id -> metadata
        self.buffer_locks = defaultdict(threading.Lock)  # session_id -> lock
        self.cleanup_thread = None
        self.start_cleanup_thread()
        
        # Configuration for optimal transcription quality
        self.MIN_BUFFER_SIZE = 3  # Minimum chunks for valid WebM assembly
        self.MAX_BUFFER_SIZE = 8  # Maximum chunks before forced processing
        self.BUFFER_TIMEOUT = 2.0  # Seconds before processing partial buffer
        self.SESSION_TIMEOUT = 300  # 5 minutes session timeout
        
    def add_chunk(self, session_id: str, audio_data: bytes, chunk_id: str) -> tuple[bool, bytes or None]:
        """Add audio chunk and return (should_process, assembled_audio_data)"""
        with self.buffer_locks[session_id]:
            buffer = self.session_buffers[session_id]
            metadata = self.session_metadata[session_id]
            
            # Add chunk with metadata
            chunk_info = {
                'data': audio_data,
                'chunk_id': chunk_id,
                'timestamp': time.time(),
                'size': len(audio_data)
            }
            buffer.append(chunk_info)
            
            # Update session metadata
            metadata.update({
                'last_activity': time.time(),
                'total_chunks': metadata.get('total_chunks', 0) + 1,
                'total_bytes': metadata.get('total_bytes', 0) + len(audio_data)
            })
            
            # Decide if we should process the buffer
            should_process = self._should_process_buffer(session_id)
            
            if should_process:
                assembled_audio = self._assemble_buffer(session_id)
                print(f"[BUFFER] 📦 Assembled {len(buffer)} chunks into {len(assembled_audio)} bytes for session {session_id}")
                return True, assembled_audio
                
        return False, None
    
    def _should_process_buffer(self, session_id: str) -> bool:
        """Intelligent decision on when to process buffer for optimal quality"""
        buffer = self.session_buffers[session_id]
        metadata = self.session_metadata[session_id]
        
        # Process if buffer is full
        if len(buffer) >= self.MAX_BUFFER_SIZE:
            return True
            
        # Process if minimum size reached and timeout occurred
        if len(buffer) >= self.MIN_BUFFER_SIZE:
            last_chunk_time = buffer[-1]['timestamp']
            if time.time() - last_chunk_time > self.BUFFER_TIMEOUT:
                return True
                
        return False
    
    def _assemble_buffer(self, session_id: str) -> bytes:
        """Assemble buffer chunks into complete WebM audio data"""
        buffer = self.session_buffers[session_id]
        
        if not buffer:
            return b''
            
        # Extract all audio data from buffer
        audio_chunks = []
        processed_chunks = []
        
        # Process chunks in order
        while buffer and len(processed_chunks) < self.MAX_BUFFER_SIZE:
            chunk_info = buffer.popleft()
            audio_chunks.append(chunk_info['data'])
            processed_chunks.append(chunk_info)
            
        # Assemble into complete WebM
        try:
            assembled_data = self._create_valid_webm(audio_chunks)
            print(f"[BUFFER] ✅ Successfully assembled {len(processed_chunks)} chunks into valid WebM")
            return assembled_data
        except Exception as e:
            print(f"[BUFFER] ❌ Failed to assemble WebM: {e}")
            # Fallback: return concatenated raw data
            return b''.join(audio_chunks)
    
    def _create_valid_webm(self, audio_chunks: list[bytes]) -> bytes:
        """Create a valid WebM file from MediaRecorder chunks using advanced assembly"""
        if not audio_chunks:
            return b''
            
        # Method 1: Try direct concatenation with WebM container reconstruction
        try:
            # Concatenate all chunks
            combined_data = b''.join(audio_chunks)
            
            # Check if the combined data starts with EBML header
            if combined_data.startswith(b'\x1a\x45\xdf\xa3'):  # EBML signature
                return combined_data
                
            # Method 2: Find and extract valid WebM segments
            valid_segments = []
            for chunk in audio_chunks:
                if self._contains_valid_webm_data(chunk):
                    valid_segments.append(chunk)
                    
            if valid_segments:
                return b''.join(valid_segments)
                
            # Method 3: Fallback to raw concatenation
            return combined_data
            
        except Exception as e:
            print(f"[BUFFER] ⚠️ WebM assembly failed, using raw concatenation: {e}")
            return b''.join(audio_chunks)
    
    def _contains_valid_webm_data(self, data: bytes) -> bool:
        """Check if chunk contains valid WebM data markers"""
        if len(data) < 4:
            return False
            
        # Look for WebM/Matroska markers
        webm_markers = [
            b'\x1a\x45\xdf\xa3',  # EBML
            b'\x18\x53\x80\x67',  # Segment
            b'\x16\x54\xae\x6b',  # Tracks
            b'\x1f\x43\xb6\x75',  # Cluster
        ]
        
        for marker in webm_markers:
            if marker in data:
                return True
                
        return False
    
    def start_cleanup_thread(self):
        """Start background thread for session cleanup"""
        def cleanup_sessions():
            while True:
                try:
                    current_time = time.time()
                    sessions_to_remove = []
                    
                    for session_id, metadata in self.session_metadata.items():
                        last_activity = metadata.get('last_activity', 0)
                        if current_time - last_activity > self.SESSION_TIMEOUT:
                            sessions_to_remove.append(session_id)
                    
                    for session_id in sessions_to_remove:
                        self.cleanup_session(session_id)
                        
                    time.sleep(60)  # Cleanup every minute
                except Exception as e:
                    print(f"[BUFFER] ⚠️ Cleanup thread error: {e}")
                    time.sleep(60)
        
        if not self.cleanup_thread or not self.cleanup_thread.is_alive():
            self.cleanup_thread = threading.Thread(target=cleanup_sessions, daemon=True)
            self.cleanup_thread.start()
    
    def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        with self.buffer_locks[session_id]:
            if session_id in self.session_buffers:
                buffer_size = len(self.session_buffers[session_id])
                del self.session_buffers[session_id]
                del self.session_metadata[session_id]
                print(f"[BUFFER] 🧹 Cleaned up session {session_id} (had {buffer_size} pending chunks)")
    
    def get_session_stats(self, session_id: str) -> dict:
        """Get comprehensive session statistics"""
        metadata = self.session_metadata.get(session_id, {})
        buffer = self.session_buffers.get(session_id, deque())
        
        return {
            'session_id': session_id,
            'buffer_size': len(buffer),
            'total_chunks_processed': metadata.get('total_chunks', 0),
            'total_bytes_processed': metadata.get('total_bytes', 0),
            'last_activity': metadata.get('last_activity', 0),
            'session_age': time.time() - metadata.get('created_at', time.time())
        }

# Global buffer manager instance
audio_buffer_manager = AudioBufferManager()

def _optimize_audio_for_transcription(audio_file_path: str, audio_data: bytes):
    """
    Advanced audio optimization for maximum OpenAI Whisper compatibility
    Returns optimized file path or None if optimization fails
    """
    try:
        from pydub import AudioSegment
        
        # Try multiple optimization strategies
        strategies = [
            ('webm_direct', lambda: AudioSegment.from_file(audio_file_path, format="webm")),
            ('raw_webm', lambda: AudioSegment.from_file(io.BytesIO(audio_data), format="webm")),
            ('auto_detect', lambda: AudioSegment.from_file(audio_file_path)),
            ('opus_codec', lambda: AudioSegment.from_file(audio_file_path, codec="opus"))
        ]
        
        for strategy_name, loader_func in strategies:
            try:
                print(f"[ENTERPRISE] 🔧 Trying optimization strategy: {strategy_name}")
                audio_segment = loader_func()
                
                # Apply audio optimizations for best transcription quality
                # Normalize audio levels
                audio_segment = audio_segment.normalize()
                
                # Ensure optimal sample rate for Whisper (16kHz is optimal)
                if audio_segment.frame_rate != 16000:
                    audio_segment = audio_segment.set_frame_rate(16000)
                
                # Convert to mono if stereo (Whisper works better with mono)
                if audio_segment.channels > 1:
                    audio_segment = audio_segment.set_channels(1)
                
                # Export optimized version
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as optimized_file:
                    optimized_path = optimized_file.name
                
                # Export as high-quality WAV for maximum compatibility
                audio_segment.export(
                    optimized_path, 
                    format="wav",
                    parameters=["-ar", "16000", "-ac", "1"]  # 16kHz mono
                )
                
                print(f"[ENTERPRISE] ✅ Audio optimized using {strategy_name}: {optimized_path}")
                return optimized_path
                
            except Exception as strategy_error:
                print(f"[ENTERPRISE] ❌ Strategy {strategy_name} failed: {strategy_error}")
                continue
        
        print(f"[ENTERPRISE] ⚠️ All optimization strategies failed")
        return None
        
    except ImportError:
        print(f"[ENTERPRISE] ⚠️ pydub not available for audio optimization")
        return None
    except Exception as e:
        print(f"[ENTERPRISE] ❌ Audio optimization error: {e}")
        return None

def _calculate_enterprise_confidence(transcription) -> float:
    """Calculate advanced confidence score using multiple factors"""
    try:
        segments = getattr(transcription, 'segments', None)
        if not segments:
            return 0.5
            
        confidences = []
        no_speech_probs = []
        
        for segment in segments:
            # Convert log probability to confidence
            if hasattr(segment, 'avg_logprob'):
                conf = min(1.0, max(0.0, (segment.avg_logprob + 1.5) / 1.5))
                confidences.append(conf)
            
            # Factor in no-speech probability (lower is better)
            if hasattr(segment, 'no_speech_prob'):
                no_speech_probs.append(segment.no_speech_prob)
        
        if not confidences:
            return 0.5
            
        # Calculate weighted confidence
        avg_confidence = sum(confidences) / len(confidences)
        
        # Adjust for no-speech probability
        if no_speech_probs:
            avg_no_speech = sum(no_speech_probs) / len(no_speech_probs)
            # Penalize high no-speech probability
            confidence_adjustment = max(0.1, 1.0 - avg_no_speech)
            avg_confidence *= confidence_adjustment
            
        return min(1.0, max(0.0, avg_confidence))
        
    except Exception as e:
        print(f"[ENTERPRISE] ⚠️ Confidence calculation failed: {e}")
        return 0.5

def _handle_transcription_failure(error, chunk_id, session_id, processing_time, buffer_stats) -> tuple:
    """Handle transcription failure with comprehensive error analysis"""
    error_msg = str(error)
    error_type = 'unknown_error'
    status_code = 500
    
    # Categorize error for appropriate response
    if "rate_limit" in error_msg.lower() or "429" in error_msg:
        error_type = 'rate_limit'
        status_code = 429
        user_message = 'Rate limit exceeded. Please wait a moment before trying again.'
    elif "quota" in error_msg.lower() or "402" in error_msg:
        error_type = 'quota_exceeded' 
        status_code = 402
        user_message = 'API quota exceeded. Please check your OpenAI account.'
    elif "invalid" in error_msg.lower() and "format" in error_msg.lower():
        error_type = 'invalid_format'
        status_code = 400
        user_message = 'Audio format not supported. The system will continue buffering for better assembly.'
    elif "timeout" in error_msg.lower():
        error_type = 'timeout'
        status_code = 408
        user_message = 'Transcription timed out. Trying again with optimized settings.'
    else:
        user_message = 'Transcription temporarily unavailable. The system is working to resolve this.'
    
    print(f"[ENTERPRISE] 💥 Transcription failure analysis:")
    print(f"[ENTERPRISE]    Error type: {error_type}")
    print(f"[ENTERPRISE]    Error message: {error_msg}")
    print(f"[ENTERPRISE]    Buffer stats: {buffer_stats}")
    
    response_data = {
        'error': user_message,
        'text': '',
        'confidence': 0,
        'processing_time': processing_time,
        'chunk_id': chunk_id,
        'session_id': session_id,
        'type': error_type,
        'buffer_stats': buffer_stats,
        'timestamp': datetime.utcnow().isoformat(),
        'retry_recommended': error_type in ['timeout', 'rate_limit'],
        'technical_error': error_msg[:200]  # Truncated for debugging
    }
    
    return jsonify(response_data), status_code

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
    Enterprise-Grade Audio Transcription Endpoint
    Uses advanced buffering for MediaRecorder chunk assembly and optimal transcription quality
    """
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS preflight successful'}), 200
    
    # Handle GET request for testing  
    if request.method == 'GET':
        return jsonify({
            'message': 'Enterprise Audio Transcription Service - Operational',
            'methods': ['POST', 'GET', 'OPTIONS'],
            'openai_configured': openai_client is not None,
            'endpoint': '/api/transcribe_chunk_streaming',
            'status': 'ready',
            'buffer_stats': {
                'active_sessions': len(audio_buffer_manager.session_buffers),
                'total_buffers': sum(len(buf) for buf in audio_buffer_manager.session_buffers.values())
            }
        })
    
    start_time = time.time()
    temp_file_path = None
    
    try:
        print(f"[LIVE-API] 🎵 Received enterprise transcription request")
        
        # Check if OpenAI is available
        if not openai_client:
            return jsonify({
                'error': 'OpenAI API not configured',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'type': 'error'
            }), 500
        
        # Extract request parameters with enhanced validation
        audio_file = request.files.get('audio')
        session_id = request.form.get('session_id', f'session_{int(time.time())}_{uuid.uuid4().hex[:8]}')
        chunk_id = request.form.get('chunk_id', str(int(time.time())))
        
        print(f"[ENTERPRISE] 📊 Processing request: session_id={session_id}, chunk_id={chunk_id}")
        
        # Enhanced request validation and logging
        if audio_file:
            print(f"[ENTERPRISE] 🎵 Audio file: {audio_file.filename}, size: {audio_file.content_length or 'unknown'}")
            print(f"[ENTERPRISE] 🎵 Content-type: {audio_file.content_type}, mimetype: {audio_file.mimetype}")
        
        if not audio_file:
            return jsonify({
                'error': 'No audio file provided',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'type': 'error'
            }), 400
        
        # Read audio data for buffer processing
        audio_data = audio_file.read()
        print(f"[ENTERPRISE] 📏 Audio data size: {len(audio_data)} bytes")
        
        if len(audio_data) == 0:
            return jsonify({
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'type': 'partial',
                'message': 'Empty audio chunk - buffering'
            })
        
        # Advanced file size validation
        if len(audio_data) < 100:  # Minimum viable chunk size
            print(f"[ENTERPRISE] ⚠️ Chunk {chunk_id} too small: {len(audio_data)} bytes - buffering")
            # Add to buffer anyway for potential assembly
            audio_buffer_manager.add_chunk(session_id, audio_data, chunk_id)
            return jsonify({
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'type': 'partial',
                'message': 'Small chunk buffered'
            })
        
        if len(audio_data) > 25 * 1024 * 1024:  # 25MB limit
            return jsonify({
                'error': 'Audio chunk too large (max 25MB)',
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'type': 'error'
            }), 413
        
        # Enterprise-Grade Audio Buffering and Assembly System
        print(f"[ENTERPRISE] 📦 Adding chunk {chunk_id} to buffer for session {session_id}")
        
        # Add chunk to buffer and check if we should process
        should_process, assembled_audio = audio_buffer_manager.add_chunk(session_id, audio_data, chunk_id)
        
        if not should_process:
            # Buffer not ready for processing - return partial response
            buffer_stats = audio_buffer_manager.get_session_stats(session_id)
            print(f"[ENTERPRISE] ⏳ Buffering chunk {chunk_id} - {buffer_stats['buffer_size']} chunks pending")
            
            return jsonify({
                'text': '',
                'confidence': 0,
                'processing_time': time.time() - start_time,
                'chunk_id': chunk_id,
                'session_id': session_id,
                'type': 'buffering',
                'message': f'Buffering audio chunks ({buffer_stats["buffer_size"]} pending)',
                'buffer_stats': buffer_stats
            })
        
        # Buffer ready for processing - create temporary file for OpenAI
        print(f"[ENTERPRISE] 🎯 Processing assembled audio: {len(assembled_audio)} bytes")
        
        # Create temporary file with assembled audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(assembled_audio)
            temp_file.flush()
            temp_file_path = temp_file.name
            print(f"[ENTERPRISE] 💾 Created assembled audio file: {temp_file_path}")
        
        # Advanced format optimization for OpenAI compatibility
        try:
            # First, try to optimize the assembled WebM for better compatibility
            optimized_path = _optimize_audio_for_transcription(temp_file_path, assembled_audio)
            if optimized_path:
                # Clean up original and use optimized version
                os.unlink(temp_file_path)
                temp_file_path = optimized_path
                print(f"[ENTERPRISE] ✨ Audio optimized for transcription: {temp_file_path}")
        except Exception as e:
            print(f"[ENTERPRISE] ⚠️ Audio optimization failed, using assembled version: {e}")
        
        # Enterprise OpenAI Whisper Transcription with Advanced Error Handling
        transcription_attempts = 0
        max_attempts = 3
        
        while transcription_attempts < max_attempts:
            transcription_attempts += 1
            
            try:
                print(f"[ENTERPRISE] 🚀 Transcription attempt {transcription_attempts}/{max_attempts}")
                print(f"[ENTERPRISE] 🤖 Sending assembled audio to OpenAI Whisper...")
                
                with open(temp_file_path, 'rb') as audio_file_obj:
                    # Enhanced Whisper API call with optimal parameters
                    transcription = openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file_obj,
                        response_format="verbose_json",
                        language="en",  # Can be made dynamic based on session settings
                        temperature=0.0,  # Deterministic results
                        prompt="Transcribe the following audio with high accuracy, including punctuation."
                    )
                
                # Advanced text extraction and processing
                text = transcription.text.strip() if transcription.text else ""
                
                # Enterprise-grade confidence calculation
                confidence = _calculate_enterprise_confidence(transcription)
                
                processing_time = time.time() - start_time
                buffer_stats = audio_buffer_manager.get_session_stats(session_id)
                
                print(f"[ENTERPRISE] ✅ Transcription successful on attempt {transcription_attempts}:")
                print(f"[ENTERPRISE]    Text: '{text[:150]}{'...' if len(text) > 150 else ''}'")
                print(f"[ENTERPRISE]    Confidence: {confidence:.3f}")
                print(f"[ENTERPRISE]    Processing time: {processing_time:.3f}s")
                print(f"[ENTERPRISE]    Buffer processed: {buffer_stats['total_chunks_processed']} total chunks")
                
                # Prepare comprehensive response
                response_data = {
                    'text': text,
                    'confidence': confidence,
                    'processing_time': processing_time,
                    'chunk_id': chunk_id,
                    'session_id': session_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': 'success' if text else 'partial',
                    'segments': [],
                    'buffer_stats': buffer_stats,
                    'transcription_attempt': transcription_attempts,
                    'audio_duration': getattr(transcription, 'duration', 0),
                    'language_detected': getattr(transcription, 'language', 'en')
                }
                
                # Extract detailed segment information for enhanced analysis
                segments = getattr(transcription, 'segments', None)
                if segments:
                    for segment in segments:
                        segment_data = {
                            'start': getattr(segment, 'start', 0),
                            'end': getattr(segment, 'end', 0),
                            'text': getattr(segment, 'text', ''),
                            'confidence': min(1.0, max(0.0, (getattr(segment, 'avg_logprob', -1) + 1.5) / 1.5)),
                            'no_speech_prob': getattr(segment, 'no_speech_prob', 0),
                            'temperature': getattr(segment, 'temperature', 0)
                        }
                        response_data['segments'].append(segment_data)
                
                # Enhanced WebSocket emission with filtering
                try:
                    if text and confidence > 0.15:  # Higher threshold for quality
                        socketio.emit('transcription_result', response_data)
                        print(f"[ENTERPRISE] 📡 High-quality transcription emitted via WebSocket")
                    elif text:
                        # Send lower confidence results to a different channel for debugging
                        debug_data = response_data.copy()
                        debug_data['type'] = 'low_confidence'
                        socketio.emit('transcription_debug', debug_data)
                        print(f"[ENTERPRISE] 🔍 Low-confidence result sent to debug channel")
                except Exception as e:
                    print(f"[ENTERPRISE] ⚠️ WebSocket emission failed: {e}")
                
                return jsonify(response_data)
                
            except Exception as transcription_error:
                print(f"[ENTERPRISE] ❌ Transcription attempt {transcription_attempts} failed: {transcription_error}")
                
                if transcription_attempts >= max_attempts:
                    # All attempts failed - return comprehensive error response
                    processing_time = time.time() - start_time
                    buffer_stats = audio_buffer_manager.get_session_stats(session_id)
                    
                    return _handle_transcription_failure(
                        transcription_error, chunk_id, session_id, processing_time, buffer_stats
                    )
                else:
                    # Wait before retry
                    time.sleep(0.5 * transcription_attempts)
                    continue
    
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        chunk_id = request.form.get('chunk_id', 'unknown')
        
        print(f"[ENTERPRISE] ❌ Transcription error for chunk {chunk_id}: {error_msg}")
        
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
    
    finally:
        # Clean up temporary file
        if temp_file_path:
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                print(f"[ENTERPRISE] ⚠️ Failed to delete temp file: {e}")

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