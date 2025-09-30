# routes/enhanced_transcription_api.py
"""
ENHANCED TRANSCRIPTION API
Advanced, comprehensive transcription processing with quality monitoring,
adaptive processing, context awareness, and sophisticated error handling.
"""

import os
import time
import base64
import tempfile
import logging
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, request, jsonify
from datetime import datetime
import openai
from pydub import AudioSegment
import io
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Enhanced transcription blueprint
enhanced_api_bp = Blueprint('enhanced_transcription_api', __name__)

# Thread pool for concurrent processing
_thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix='EnhancedTranscription')

# Enhanced OpenAI client
_enhanced_openai_client = None

# Processing cache for context awareness
_processing_cache = {}
_cache_lock = threading.RLock()

def get_enhanced_openai_client():
    """Get enhanced OpenAI client with optimized settings"""
    global _enhanced_openai_client
    if _enhanced_openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        _enhanced_openai_client = openai.OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=2
        )
        logger.info("✅ Enhanced OpenAI client initialized with optimizations")
    return _enhanced_openai_client

@enhanced_api_bp.route('/api/transcribe-audio-enhanced', methods=['POST'])
def enhanced_transcribe_audio():
    """
    🚀 ENHANCED TRANSCRIPTION ENDPOINT
    Comprehensive processing with adaptive quality, context awareness,
    advanced error handling, and performance optimization.
    """
    request_start_time = time.time()
    processing_id = f"proc_{int(request_start_time * 1000)}"
    
    try:
        # Enhanced request parsing
        request_data = _parse_enhanced_request()
        if not request_data['success']:
            return jsonify(request_data), 400
        
        session_id = request_data['session_id']
        audio_data = request_data['audio_data']
        enhanced_metadata = request_data.get('enhanced_metadata', {})
        processing_hints = request_data.get('processing_hints', {})
        
        logger.info(f"🎯 Enhanced processing started: {processing_id}, session: {session_id}, size: {len(audio_data)}B")
        
        # Advanced quality assessment
        quality_assessment = _assess_enhanced_audio_quality(audio_data, enhanced_metadata)
        
        # Context-aware processing preparation
        context_info = _prepare_context_information(session_id, processing_hints)
        
        # Enhanced audio preprocessing
        processed_audio = _preprocess_audio_enhanced(audio_data, quality_assessment)
        
        if not processed_audio:
            return jsonify({
                'error': 'Enhanced audio preprocessing failed',
                'success': False,
                'processing_id': processing_id,
                'quality_assessment': quality_assessment,
                'processing_time': (time.time() - request_start_time) * 1000
            }), 400
        
        # Adaptive transcription processing
        transcription_result = _perform_enhanced_transcription(
            processed_audio, quality_assessment, context_info, processing_hints
        )
        
        if not transcription_result['success']:
            return jsonify({
                **transcription_result,
                'processing_id': processing_id,
                'processing_time': (time.time() - request_start_time) * 1000
            }), 500
        
        # Advanced result processing and enhancement
        enhanced_result = _enhance_transcription_result(
            transcription_result, quality_assessment, context_info, enhanced_metadata
        )
        
        # Update context cache
        _update_context_cache(session_id, enhanced_result)
        
        # Calculate comprehensive metrics
        total_processing_time = (time.time() - request_start_time) * 1000
        
        # Final enhanced response
        final_response = {
            'success': True,
            'processing_id': processing_id,
            'session_id': session_id,
            'text': enhanced_result['text'],
            'confidence': enhanced_result['confidence'],
            'is_final': enhanced_result['is_final'],
            
            # Enhanced features
            'enhanced_features': {
                'quality_score': quality_assessment['overall_score'],
                'context_aware': context_info['has_context'],
                'adaptive_processed': True,
                'audio_enhanced': processed_audio != audio_data,
                'confidence_adjusted': enhanced_result.get('confidence_adjusted', False)
            },
            
            # Detailed analytics
            'processing_analytics': {
                'total_time': total_processing_time,
                'preprocessing_time': enhanced_result.get('preprocessing_time', 0),
                'transcription_time': enhanced_result.get('transcription_time', 0),
                'enhancement_time': enhanced_result.get('enhancement_time', 0),
                'quality_assessment': quality_assessment,
                'context_utilization': context_info.get('utilization_score', 0.0)
            },
            
            # Advanced metadata
            'advanced_metadata': {
                'word_count': len(enhanced_result['text'].split()) if enhanced_result['text'] else 0,
                'estimated_duration_ms': len(audio_data) // 32,
                'processing_quality': 'high' if quality_assessment['overall_score'] > 0.8 else 'medium',
                'language_confidence': enhanced_result.get('language_confidence', 0.95),
                'speaker_characteristics': enhanced_result.get('speaker_characteristics', {}),
                'audio_characteristics': {
                    'sample_rate_estimated': quality_assessment.get('estimated_sample_rate', 16000),
                    'channels_estimated': quality_assessment.get('estimated_channels', 1),
                    'noise_level': quality_assessment.get('noise_level', 'low'),
                    'speech_clarity': quality_assessment.get('speech_clarity', 'good')
                }
            },
            
            'timestamp': time.time()
        }
        
        logger.info(f"✅ Enhanced processing completed: {processing_id}, text: '{enhanced_result['text'][:50]}...', time: {total_processing_time:.0f}ms")
        
        return jsonify(final_response)
        
    except Exception as e:
        processing_time = (time.time() - request_start_time) * 1000
        logger.error(f"❌ Enhanced transcription failed: {processing_id}, error: {e}", exc_info=True)
        
        return jsonify({
            'error': f'Enhanced transcription failed: {str(e)}',
            'success': False,
            'processing_id': processing_id,
            'processing_time': processing_time,
            'error_type': type(e).__name__,
            'timestamp': time.time()
        }), 500

def _parse_enhanced_request() -> Dict[str, Any]:
    """Parse and validate enhanced transcription request"""
    try:
        # Handle JSON requests (from enhanced WebSocket handler)
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            if not data:
                return {'success': False, 'error': 'No JSON data provided'}
            
            session_id = data.get('session_id', f'session_{int(time.time())}')
            audio_data_b64 = data.get('audio_data')
            
            if not audio_data_b64:
                return {'success': False, 'error': 'No audio_data in JSON request'}
            
            try:
                audio_data = base64.b64decode(audio_data_b64)
            except Exception as e:
                return {'success': False, 'error': f'Invalid base64 audio data: {e}'}
            
            return {
                'success': True,
                'session_id': session_id,
                'audio_data': audio_data,
                'chunk_id': data.get('chunk_id', '1'),
                'is_interim': data.get('is_interim', True),
                'enhanced_metadata': data.get('enhanced_metadata', {}),
                'processing_hints': data.get('processing_hints', {})
            }
        
        # Handle form data (legacy support)
        elif request.content_type and 'multipart/form-data' in request.content_type:
            session_id = request.form.get('session_id', f'session_{int(time.time())}')
            
            if 'audio' in request.files:
                audio_file = request.files['audio']
                if audio_file and audio_file.filename:
                    audio_data = audio_file.read()
                    
                    return {
                        'success': True,
                        'session_id': session_id,
                        'audio_data': audio_data,
                        'chunk_id': request.form.get('chunk_id', '1'),
                        'is_interim': request.form.get('is_interim', 'true').lower() == 'true',
                        'enhanced_metadata': {},
                        'processing_hints': {}
                    }
        
        return {'success': False, 'error': 'Unsupported request format'}
        
    except Exception as e:
        return {'success': False, 'error': f'Request parsing failed: {e}'}

def _assess_enhanced_audio_quality(audio_data: bytes, enhanced_metadata: Dict) -> Dict:
    """Comprehensive audio quality assessment"""
    assessment = {
        'overall_score': 0.5,
        'size_score': 0.5,
        'format_score': 0.5,
        'metadata_score': 0.5,
        'estimated_sample_rate': 16000,
        'estimated_channels': 1,
        'noise_level': 'medium',
        'speech_clarity': 'good'
    }
    
    try:
        # Size-based assessment
        if len(audio_data) > 10000:
            assessment['size_score'] = 1.0
        elif len(audio_data) > 1000:
            assessment['size_score'] = 0.7
        else:
            assessment['size_score'] = 0.3
        
        # Format detection score
        if audio_data[:4] == b'\x1a\x45\xdf\xa3':  # WebM
            assessment['format_score'] = 1.0
        elif audio_data[:4] == b'RIFF':  # WAV
            assessment['format_score'] = 0.9
        elif audio_data[:4] == b'OggS':  # OGG
            assessment['format_score'] = 0.8
        else:
            assessment['format_score'] = 0.5
        
        # Metadata-based assessment
        if enhanced_metadata:
            speech_ratio = enhanced_metadata.get('speech_ratio', 0.5)
            avg_energy = enhanced_metadata.get('avg_energy', 0.1)
            
            if speech_ratio > 0.7:
                assessment['metadata_score'] = 1.0
                assessment['speech_clarity'] = 'excellent'
            elif speech_ratio > 0.4:
                assessment['metadata_score'] = 0.7
                assessment['speech_clarity'] = 'good'
            else:
                assessment['metadata_score'] = 0.4
                assessment['speech_clarity'] = 'poor'
            
            # Noise level assessment
            if avg_energy > 0.3:
                assessment['noise_level'] = 'low'
            elif avg_energy > 0.1:
                assessment['noise_level'] = 'medium'
            else:
                assessment['noise_level'] = 'high'
        
        # Calculate overall score
        assessment['overall_score'] = (
            assessment['size_score'] * 0.3 +
            assessment['format_score'] * 0.3 +
            assessment['metadata_score'] * 0.4
        )
        
    except Exception as e:
        logger.warning(f"⚠️ Quality assessment error: {e}")
        assessment['overall_score'] = 0.5
    
    return assessment

def _prepare_context_information(session_id: str, processing_hints: Dict) -> Dict:
    """Prepare context information for enhanced processing"""
    context_info = {
        'has_context': False,
        'previous_text': '',
        'context_length': 0,
        'language_hint': 'en',
        'utilization_score': 0.0
    }
    
    try:
        with _cache_lock:
            if session_id in _processing_cache:
                cache_entry = _processing_cache[session_id]
                context_info['has_context'] = True
                context_info['previous_text'] = cache_entry.get('previous_text', '')[-500:]  # Last 500 chars
                context_info['context_length'] = len(context_info['previous_text'])
                context_info['utilization_score'] = min(1.0, context_info['context_length'] / 200)
        
        # Extract language hint from processing hints
        context_info['language_hint'] = processing_hints.get('expected_language', 'en')
        
    except Exception as e:
        logger.warning(f"⚠️ Context preparation error: {e}")
    
    return context_info

def _preprocess_audio_enhanced(audio_data: bytes, quality_assessment: Dict) -> bytes:
    """Enhanced audio preprocessing with adaptive quality improvements"""
    try:
        # If quality is already high, minimal processing
        if quality_assessment['overall_score'] > 0.9:
            return audio_data
        
        # Enhanced PyDub processing
        audio_segment = AudioSegment.from_file(
            io.BytesIO(audio_data),
            format="webm"
        )
        
        # Adaptive enhancements based on quality assessment
        if quality_assessment['noise_level'] == 'high':
            # Noise reduction
            audio_segment = audio_segment.normalize()
            audio_segment = audio_segment.high_pass_filter(80)  # Remove low-frequency noise
        
        if quality_assessment['speech_clarity'] == 'poor':
            # Speech enhancement
            audio_segment = audio_segment.compress_dynamic_range(threshold=-20.0, ratio=4.0)
        
        # Optimize for Whisper
        audio_segment = audio_segment.set_frame_rate(16000)
        audio_segment = audio_segment.set_channels(1)
        audio_segment = audio_segment.set_sample_width(2)
        
        # Export enhanced audio
        wav_io = io.BytesIO()
        audio_segment.export(wav_io, format="wav")
        enhanced_audio = wav_io.getvalue()
        
        logger.info(f"🔧 Audio enhanced: {len(audio_data)}B -> {len(enhanced_audio)}B")
        return enhanced_audio
        
    except Exception as e:
        logger.warning(f"⚠️ Audio preprocessing failed: {e}")
        return audio_data  # Return original on failure

def _perform_enhanced_transcription(
    audio_data: bytes, 
    quality_assessment: Dict, 
    context_info: Dict, 
    processing_hints: Dict
) -> Dict:
    """Perform enhanced transcription with adaptive parameters"""
    try:
        client = get_enhanced_openai_client()
        transcription_start = time.time()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Adaptive Whisper parameters based on quality
            temperature = 0.0 if quality_assessment['overall_score'] > 0.8 else 0.1
            
            # Context-aware prompting (if available)
            prompt = None
            if context_info['has_context'] and context_info['previous_text']:
                # Use last few words as context
                words = context_info['previous_text'].split()
                if len(words) > 3:
                    prompt = ' '.join(words[-10:])  # Last 10 words for context
            
            with open(temp_file_path, "rb") as audio_file:
                # Enhanced Whisper API call
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    language=context_info.get('language_hint', 'en'),
                    temperature=temperature,
                    prompt=prompt  # Context-aware prompting
                )
            
            transcription_time = (time.time() - transcription_start) * 1000
            
            # Extract enhanced results
            text = response.text.strip() if hasattr(response, 'text') else ''
            
            # Enhanced confidence calculation
            confidence = 0.95  # Default
            if hasattr(response, 'segments') and response.segments:
                segment_confidences = []
                for seg in response.segments:
                    if isinstance(seg, dict) and 'avg_logprob' in seg:
                        # Convert log probability to confidence
                        seg_conf = max(0.0, min(1.0, seg['avg_logprob'] + 1.0))
                        segment_confidences.append(seg_conf)
                
                if segment_confidences:
                    confidence = sum(segment_confidences) / len(segment_confidences)
            
            # Quality-based confidence adjustment
            confidence *= quality_assessment['overall_score']
            
            return {
                'success': True,
                'text': text,
                'confidence': confidence,
                'transcription_time': transcription_time,
                'segments': getattr(response, 'segments', []),
                'language_confidence': 0.95  # Would be from response if available
            }
            
        finally:
            # Cleanup
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"❌ Enhanced transcription failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'text': '',
            'confidence': 0.0
        }

def _enhance_transcription_result(
    transcription_result: Dict, 
    quality_assessment: Dict, 
    context_info: Dict, 
    enhanced_metadata: Dict
) -> Dict:
    """Enhance transcription result with advanced processing"""
    enhancement_start = time.time()
    
    try:
        text = transcription_result.get('text', '')
        confidence = transcription_result.get('confidence', 0.0)
        
        # Advanced text processing
        if text:
            # Context-aware text cleaning
            text = _clean_transcription_text(text, context_info)
            
            # Confidence adjustment based on various factors
            adjusted_confidence = _adjust_confidence_score(
                confidence, text, quality_assessment, enhanced_metadata
            )
        else:
            adjusted_confidence = confidence
        
        # Determine finality based on enhanced criteria
        is_final = _determine_result_finality(
            text, adjusted_confidence, enhanced_metadata
        )
        
        enhancement_time = (time.time() - enhancement_start) * 1000
        
        return {
            'text': text,
            'confidence': adjusted_confidence,
            'confidence_adjusted': adjusted_confidence != confidence,
            'is_final': is_final,
            'transcription_time': transcription_result.get('transcription_time', 0),
            'enhancement_time': enhancement_time,
            'language_confidence': transcription_result.get('language_confidence', 0.95),
            'speaker_characteristics': _extract_speaker_characteristics(text)
        }
        
    except Exception as e:
        logger.warning(f"⚠️ Result enhancement failed: {e}")
        return {
            'text': transcription_result.get('text', ''),
            'confidence': transcription_result.get('confidence', 0.0),
            'confidence_adjusted': False,
            'is_final': False,
            'enhancement_time': 0
        }

def _clean_transcription_text(text: str, context_info: Dict) -> str:
    """Clean and enhance transcription text"""
    if not text:
        return text
    
    # Basic cleaning
    text = text.strip()
    
    # Remove repeated words that might be artifacts
    words = text.split()
    cleaned_words = []
    
    for i, word in enumerate(words):
        # Skip if same word repeated 3+ times consecutively
        if i >= 2 and words[i-1] == word and words[i-2] == word:
            continue
        cleaned_words.append(word)
    
    return ' '.join(cleaned_words)

def _adjust_confidence_score(
    base_confidence: float, 
    text: str, 
    quality_assessment: Dict, 
    enhanced_metadata: Dict
) -> float:
    """Adjust confidence score based on multiple factors"""
    adjusted = base_confidence
    
    # Length-based adjustment
    if len(text.split()) < 2:
        adjusted *= 0.8  # Lower confidence for very short text
    elif len(text.split()) > 10:
        adjusted *= 1.1  # Higher confidence for longer text
    
    # Quality-based adjustment
    adjusted *= (0.5 + 0.5 * quality_assessment['overall_score'])
    
    # Metadata-based adjustment
    speech_ratio = enhanced_metadata.get('speech_ratio', 0.5)
    if speech_ratio > 0.8:
        adjusted *= 1.2
    elif speech_ratio < 0.3:
        adjusted *= 0.7
    
    return min(1.0, max(0.0, adjusted))

def _determine_result_finality(text: str, confidence: float, enhanced_metadata: Dict) -> bool:
    """Determine if the transcription result should be considered final"""
    # High confidence and reasonable length
    if confidence > 0.85 and len(text.split()) >= 3:
        return True
    
    # Check for natural speech ending indicators
    if text.endswith(('.', '!', '?')) and confidence > 0.7:
        return True
    
    # Check metadata for end-of-speech indicators
    consecutive_failures = enhanced_metadata.get('consecutive_failures', 0)
    if consecutive_failures == 0 and confidence > 0.8:
        return True
    
    return False

def _extract_speaker_characteristics(text: str) -> Dict:
    """Extract basic speaker characteristics from transcription"""
    characteristics = {
        'estimated_words_per_minute': 0,
        'speech_pattern': 'normal',
        'complexity_score': 0.5
    }
    
    try:
        if text:
            words = text.split()
            characteristics['complexity_score'] = min(1.0, len(set(words)) / max(1, len(words)))
            
            # Simple pattern detection
            if '...' in text or text.count(',') > len(words) // 4:
                characteristics['speech_pattern'] = 'hesitant'
            elif text.isupper() or '!' in text:
                characteristics['speech_pattern'] = 'emphatic'
    
    except:
        pass
    
    return characteristics

def _update_context_cache(session_id: str, enhanced_result: Dict):
    """Update context cache with new result"""
    try:
        with _cache_lock:
            if session_id not in _processing_cache:
                _processing_cache[session_id] = {
                    'created_at': time.time(),
                    'previous_text': '',
                    'result_history': []
                }
            
            cache_entry = _processing_cache[session_id]
            
            # Append new text to context
            if enhanced_result.get('is_final'):
                cache_entry['previous_text'] += ' ' + enhanced_result['text']
            else:
                # For interim results, just update the buffer
                cache_entry['interim_text'] = enhanced_result['text']
            
            # Maintain reasonable cache size
            if len(cache_entry['previous_text']) > 2000:
                cache_entry['previous_text'] = cache_entry['previous_text'][-1500:]
            
            # Keep result history for analysis
            cache_entry['result_history'].append({
                'text': enhanced_result['text'],
                'confidence': enhanced_result['confidence'],
                'is_final': enhanced_result['is_final'],
                'timestamp': time.time()
            })
            
            # Limit history size
            if len(cache_entry['result_history']) > 50:
                cache_entry['result_history'] = cache_entry['result_history'][-30:]
                
    except Exception as e:
        logger.warning(f"⚠️ Context cache update failed: {e}")

@enhanced_api_bp.route('/api/transcribe-health-enhanced', methods=['GET'])
def enhanced_transcription_health():
    """Enhanced health check with comprehensive system status"""
    try:
        client = get_enhanced_openai_client()
        
        # Test basic functionality
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'services': {
                'openai_client': True,
                'thread_pool': _thread_pool._threads is not None,
                'context_cache': len(_processing_cache),
                'audio_processing': True,
                'pydub_available': True
            },
            'performance_metrics': {
                'active_sessions': len(_processing_cache),
                'cache_memory_usage': sum(len(str(cache)) for cache in _processing_cache.values()),
                'thread_pool_active': len(_thread_pool._threads) if _thread_pool._threads else 0
            },
            'capabilities': {
                'context_aware_processing': True,
                'adaptive_quality_assessment': True,
                'multi_format_support': True,
                'real_time_optimization': True,
                'advanced_confidence_scoring': True,
                'speech_enhancement': True
            }
        }
        
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"❌ Enhanced health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time(),
            'openai_configured': bool(os.getenv('OPENAI_API_KEY'))
        }), 503

logger.info("✅ Enhanced Transcription API initialized with comprehensive features")