"""
🤖 MULTI-MODEL TRANSCRIPTION SERVICE: Intelligent transcription with fallback strategies
Provides advanced multi-model support, context-aware processing, and intelligent quality optimization
"""

import os
import time
import logging
import tempfile
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import deque
import hashlib
import json
import numpy as np

from services.circuit_breaker import get_openai_circuit_breaker, CircuitBreakerOpenError
from services.health_monitor import get_health_monitor
from services.advanced_audio_processor import AdvancedAudioProcessor

logger = logging.getLogger(__name__)

class TranscriptionModel(Enum):
    """Available transcription models with priorities"""
    WHISPER_1 = "whisper-1"
    WHISPER_LARGE = "whisper-large-v3"  # Future model
    WHISPER_TURBO = "whisper-turbo"     # Future model

@dataclass
class ModelConfig:
    """Configuration for individual transcription models"""
    name: str
    temperature: float = 0.0
    language: Optional[str] = None
    prompt: Optional[str] = None
    response_format: str = "verbose_json"
    timestamp_granularities: List[str] = field(default_factory=lambda: ["word"])
    max_retries: int = 3
    timeout: float = 45.0
    priority: int = 1  # Lower number = higher priority

@dataclass
class TranscriptionContext:
    """Context information for intelligent transcription"""
    session_id: str
    chunk_id: int
    previous_segments: List[str] = field(default_factory=list)
    speaker_context: Optional[str] = None
    domain_context: Optional[str] = None
    language_hints: List[str] = field(default_factory=list)
    custom_vocabulary: List[str] = field(default_factory=list)
    meeting_type: Optional[str] = None
    quality_threshold: float = 0.8

@dataclass
class TranscriptionResult:
    """Comprehensive transcription result with metadata"""
    text: str
    confidence: float
    segments: List[Dict] = field(default_factory=list)
    language: Optional[str] = None
    model_used: str = ""
    processing_time_ms: float = 0.0
    audio_quality_score: float = 0.0
    context_applied: List[str] = field(default_factory=list)
    fallback_used: bool = False
    enhancement_applied: List[str] = field(default_factory=list)
    word_timestamps: List[Dict] = field(default_factory=list)
    speaker_segments: List[Dict] = field(default_factory=list)

class MultiModelTranscriptionService:
    """
    Advanced multi-model transcription service with intelligent fallback and optimization
    """
    
    def __init__(self):
        self.models = self._initialize_models()
        self.context_cache = {}
        self.performance_stats = {
            'model_usage': {},
            'success_rates': {},
            'avg_processing_times': {},
            'fallback_frequency': 0
        }
        self.cache_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="MultiModel")
        
        # Context management
        self.session_contexts = {}
        self.vocabulary_cache = {}
        
        logger.info("🤖 Multi-Model Transcription Service initialized")
    
    def _initialize_models(self) -> Dict[str, ModelConfig]:
        """Initialize available transcription models with configurations"""
        models = {
            TranscriptionModel.WHISPER_1.value: ModelConfig(
                name=TranscriptionModel.WHISPER_1.value,
                temperature=0.0,
                language="en",
                priority=1,
                max_retries=3,
                timeout=45.0
            ),
            # Future models (commented for now)
            # TranscriptionModel.WHISPER_LARGE.value: ModelConfig(
            #     name=TranscriptionModel.WHISPER_LARGE.value,
            #     temperature=0.1,
            #     priority=2,
            #     max_retries=2,
            #     timeout=60.0
            # ),
            # TranscriptionModel.WHISPER_TURBO.value: ModelConfig(
            #     name=TranscriptionModel.WHISPER_TURBO.value,
            #     temperature=0.0,
            #     priority=3,
            #     max_retries=4,
            #     timeout=30.0
            # )
        }
        
        return models
    
    async def transcribe_with_intelligence(self, 
                                         audio_data: bytes,
                                         context: TranscriptionContext,
                                         enhance_audio: bool = True) -> TranscriptionResult:
        """
        Intelligent transcription with multi-model fallback and context awareness
        """
        start_time = time.time()
        health_monitor = get_health_monitor()
        
        try:
            # Step 1: Audio enhancement (if enabled)
            enhanced_audio_data = audio_data
            enhancement_applied = []
            audio_quality_score = 0.5
            
            if enhance_audio:
                audio_processor = AdvancedAudioProcessor()
                try:
                    # Process audio chunk for enhancement
                    audio_chunk = audio_processor.process_audio_chunk_advanced(
                        audio_data,
                        context.session_id,
                        context.chunk_id
                    )
                    
                    if audio_chunk and audio_chunk.quality_score > 0.5:
                        # Convert back to bytes for transcription
                        import struct
                        audio_int16 = (audio_chunk.data * 32767).astype(np.int16)
                        enhanced_audio_data = audio_int16.tobytes()
                        audio_quality_score = audio_chunk.quality_score
                        enhancement_applied = ["advanced_processing"]
                        logger.info(f"🎵 Audio enhanced: quality {audio_quality_score:.2f}")
                except Exception as e:
                    logger.warning(f"⚠️ Audio enhancement failed: {e}")
            
            # Step 2: Context preparation
            prepared_context = self._prepare_transcription_context(context)
            
            # Step 3: Model selection based on context and quality
            selected_models = self._select_optimal_models(context, audio_quality_score)
            
            # Step 4: Attempt transcription with selected models
            result = await self._attempt_transcription_with_fallback(
                enhanced_audio_data, 
                prepared_context, 
                selected_models
            )
            
            # Step 5: Post-processing and context enhancement
            enhanced_result = self._enhance_result_with_context(result, context)
            
            # Step 6: Update performance statistics
            total_time = (time.time() - start_time) * 1000
            self._update_performance_stats(result.model_used, total_time, result.confidence > 0.8)
            
            # Step 7: Record metrics
            health_monitor.record_transcription_event(
                context.session_id,
                total_time / 1000,
                result.confidence > 0.5,
                result.confidence
            )
            
            # Final result preparation
            enhanced_result.processing_time_ms = total_time
            enhanced_result.audio_quality_score = audio_quality_score
            enhanced_result.enhancement_applied = enhancement_applied
            
            logger.info(f"🎯 Transcription completed: model={result.model_used}, "
                       f"confidence={result.confidence:.2f}, time={total_time:.0f}ms")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"❌ Multi-model transcription failed: {e}")
            processing_time = (time.time() - start_time) * 1000
            health_monitor.record_transcription_event(context.session_id, processing_time / 1000, False)
            
            return TranscriptionResult(
                text="",
                confidence=0.0,
                model_used="error",
                processing_time_ms=processing_time,
                context_applied=["error_fallback"]
            )
    
    def _prepare_transcription_context(self, context: TranscriptionContext) -> Dict[str, Any]:
        """Prepare intelligent context for transcription"""
        prepared = {
            'session_id': context.session_id,
            'chunk_id': context.chunk_id
        }
        
        # Build context prompt from previous segments
        if context.previous_segments:
            recent_context = " ".join(context.previous_segments[-3:])  # Last 3 segments
            prepared['prompt'] = f"Previous context: {recent_context}. Continue:"
        
        # Add custom vocabulary
        if context.custom_vocabulary:
            vocab_hint = ", ".join(context.custom_vocabulary[:10])  # Limit to 10 terms
            if 'prompt' in prepared:
                prepared['prompt'] += f" Key terms: {vocab_hint}"
            else:
                prepared['prompt'] = f"Key terms: {vocab_hint}"
        
        # Add domain context
        if context.domain_context:
            domain_prompts = {
                'medical': "Medical consultation with clinical terminology.",
                'legal': "Legal discussion with legal terminology.",
                'technical': "Technical meeting with specialized terminology.",
                'business': "Business meeting with corporate terminology.",
                'education': "Educational content with academic terminology."
            }
            
            domain_prompt = domain_prompts.get(context.domain_context, "")
            if domain_prompt:
                if 'prompt' in prepared:
                    prepared['prompt'] = f"{domain_prompt} {prepared['prompt']}"
                else:
                    prepared['prompt'] = domain_prompt
        
        # Language hints
        if context.language_hints:
            prepared['language'] = context.language_hints[0]  # Use primary language hint
        
        return prepared
    
    def _select_optimal_models(self, context: TranscriptionContext, audio_quality: float) -> List[ModelConfig]:
        """Select optimal models based on context and audio quality"""
        available_models = list(self.models.values())
        
        # Sort by priority
        available_models.sort(key=lambda m: m.priority)
        
        # For now, we only have whisper-1, but this logic will scale
        selected = []
        
        # Primary model selection
        primary_model = available_models[0]  # whisper-1
        
        # Adjust model configuration based on context
        if audio_quality < 0.5:
            # Lower quality audio - use more conservative settings
            primary_model.temperature = 0.0
            primary_model.max_retries = 4
        elif context.domain_context:
            # Domain-specific content - use lower temperature for consistency
            primary_model.temperature = 0.0
        else:
            # Standard settings
            primary_model.temperature = 0.1
        
        selected.append(primary_model)
        
        # Add fallback models (when available)
        # for model in available_models[1:]:
        #     selected.append(model)
        
        return selected
    
    async def _attempt_transcription_with_fallback(self, 
                                                  audio_data: bytes,
                                                  context: Dict[str, Any],
                                                  models: List[ModelConfig]) -> TranscriptionResult:
        """Attempt transcription with intelligent fallback"""
        circuit_breaker = get_openai_circuit_breaker()
        
        for i, model_config in enumerate(models):
            try:
                logger.debug(f"🎯 Attempting transcription with {model_config.name}")
                
                # Create transcription parameters
                params = {
                    'model': model_config.name,
                    'temperature': model_config.temperature,
                    'response_format': model_config.response_format,
                    'timestamp_granularities': model_config.timestamp_granularities
                }
                
                # Add context if available
                if 'language' in context:
                    params['language'] = context['language']
                
                if 'prompt' in context and context['prompt']:
                    params['prompt'] = context['prompt'][:200]  # Limit prompt length
                
                # Execute transcription with circuit breaker protection
                def protected_transcription():
                    return self._execute_single_transcription(audio_data, params, model_config.timeout)
                
                result = circuit_breaker.call(protected_transcription)
                
                # Process successful result
                if result and result.get('text', '').strip():
                    transcription_result = self._process_transcription_response(result, model_config.name)
                    transcription_result.fallback_used = i > 0
                    return transcription_result
                
                logger.warning(f"⚠️ Empty result from {model_config.name}, trying next model")
                
            except CircuitBreakerOpenError:
                logger.warning(f"🔴 Circuit breaker open for {model_config.name}")
                self.performance_stats['fallback_frequency'] += 1
                continue
                
            except Exception as e:
                logger.warning(f"⚠️ Model {model_config.name} failed: {e}")
                if i == len(models) - 1:  # Last model
                    raise
                continue
        
        # If all models fail, return empty result
        return TranscriptionResult(
            text="",
            confidence=0.0,
            model_used="all_failed",
            fallback_used=True
        )
    
    def _execute_single_transcription(self, audio_data: bytes, params: Dict, timeout: float) -> Dict:
        """Execute single transcription request"""
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file.flush()
            
            try:
                with open(temp_file.name, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        file=audio_file,
                        **params
                    )
                
                return response.model_dump() if hasattr(response, 'model_dump') else response.__dict__
                
            finally:
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    def _process_transcription_response(self, response: Dict, model_name: str) -> TranscriptionResult:
        """Process transcription response into standardized result"""
        text = response.get('text', '').strip()
        
        # Extract confidence from segments if available
        segments = response.get('segments', [])
        confidences = []
        word_timestamps = []
        
        for segment in segments:
            if 'confidence' in segment:
                confidences.append(segment['confidence'])
            
            # Extract word-level timestamps
            words = segment.get('words', [])
            for word in words:
                word_timestamps.append({
                    'word': word.get('word', ''),
                    'start': word.get('start', 0),
                    'end': word.get('end', 0),
                    'confidence': word.get('confidence', 0)
                })
        
        # Calculate overall confidence
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.8
        
        # Detect language
        detected_language = response.get('language', 'en')
        
        return TranscriptionResult(
            text=text,
            confidence=overall_confidence,
            segments=segments,
            language=detected_language,
            model_used=model_name,
            word_timestamps=word_timestamps
        )
    
    def _enhance_result_with_context(self, result: TranscriptionResult, context: TranscriptionContext) -> TranscriptionResult:
        """Enhance transcription result with contextual information"""
        enhancements = []
        
        # Post-processing corrections based on custom vocabulary
        if context.custom_vocabulary and result.text:
            corrected_text = self._apply_vocabulary_corrections(result.text, context.custom_vocabulary)
            if corrected_text != result.text:
                result.text = corrected_text
                enhancements.append("vocabulary_correction")
        
        # Capitalize sentences and proper nouns
        if result.text:
            result.text = self._apply_capitalization(result.text)
            enhancements.append("capitalization")
        
        # Add punctuation intelligence
        if result.text and not result.text.endswith(('.', '!', '?')):
            # Simple sentence ending detection
            if len(result.text.split()) > 5:  # Longer segments likely need punctuation
                result.text += "."
                enhancements.append("punctuation")
        
        result.context_applied = enhancements
        return result
    
    def _apply_vocabulary_corrections(self, text: str, vocabulary: List[str]) -> str:
        """Apply custom vocabulary corrections"""
        corrected = text
        
        for term in vocabulary:
            # Simple case-insensitive replacement
            import re
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            corrected = pattern.sub(term, corrected)
        
        return corrected
    
    def _apply_capitalization(self, text: str) -> str:
        """Apply intelligent capitalization"""
        if not text:
            return text
        
        # Capitalize first letter
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Capitalize after sentence endings
        import re
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        return text
    
    def _update_performance_stats(self, model_name: str, processing_time: float, success: bool):
        """Update performance statistics"""
        with self.cache_lock:
            # Model usage tracking
            if model_name not in self.performance_stats['model_usage']:
                self.performance_stats['model_usage'][model_name] = 0
            self.performance_stats['model_usage'][model_name] += 1
            
            # Success rate tracking
            if model_name not in self.performance_stats['success_rates']:
                self.performance_stats['success_rates'][model_name] = {'success': 0, 'total': 0}
            
            self.performance_stats['success_rates'][model_name]['total'] += 1
            if success:
                self.performance_stats['success_rates'][model_name]['success'] += 1
            
            # Processing time tracking
            if model_name not in self.performance_stats['avg_processing_times']:
                self.performance_stats['avg_processing_times'][model_name] = deque(maxlen=100)
            
            self.performance_stats['avg_processing_times'][model_name].append(processing_time)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        with self.cache_lock:
            stats = {}
            
            for model_name in self.performance_stats['model_usage']:
                model_stats = {
                    'usage_count': self.performance_stats['model_usage'][model_name],
                    'success_rate': 0.0,
                    'avg_processing_time': 0.0
                }
                
                # Calculate success rate
                if model_name in self.performance_stats['success_rates']:
                    sr = self.performance_stats['success_rates'][model_name]
                    if sr['total'] > 0:
                        model_stats['success_rate'] = sr['success'] / sr['total']
                
                # Calculate average processing time
                if model_name in self.performance_stats['avg_processing_times']:
                    times = list(self.performance_stats['avg_processing_times'][model_name])
                    if times:
                        model_stats['avg_processing_time'] = sum(times) / len(times)
                
                stats[model_name] = model_stats
            
            stats['fallback_frequency'] = self.performance_stats['fallback_frequency']
            
            return stats
    
    def update_session_context(self, context: TranscriptionContext):
        """Update session context for improved transcription"""
        self.session_contexts[context.session_id] = context
    
    def clear_session_context(self, session_id: str):
        """Clear session context"""
        if session_id in self.session_contexts:
            del self.session_contexts[session_id]

# Global service instance
_global_service = None
_service_lock = threading.Lock()

def get_multi_model_service() -> MultiModelTranscriptionService:
    """Get global multi-model transcription service"""
    global _global_service
    
    if _global_service is None:
        with _service_lock:
            if _global_service is None:
                _global_service = MultiModelTranscriptionService()
    
    return _global_service

logger.info("🤖 Multi-Model Transcription Service initialized")