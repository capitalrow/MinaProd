# services/enhanced_transcription_integration.py
"""
Enhanced Transcription Integration Service
Integrates all enhanced systems: streaming processor, neural audio enhancement,
intelligent chunk manager, conversation analytics, and advanced result emission.
"""

import logging
import time
import threading
import asyncio
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import uuid
import numpy as np

# Import enhanced services
from services.enhanced_streaming_processor import (
    get_enhanced_streaming_processor, StreamingConfig, StreamingResult
)
from services.neural_audio_enhancement import get_neural_audio_enhancer
from services.intelligent_chunk_manager import (
    get_intelligent_chunk_manager, IntelligentChunk, ChunkPriority
)
from services.conversation_analytics import get_conversation_analytics

logger = logging.getLogger(__name__)

@dataclass
class EnhancedTranscriptionConfig:
    """Configuration for enhanced transcription system"""
    # Streaming configuration
    streaming_config: Optional[StreamingConfig] = None
    
    # Chunk management
    max_cache_size_mb: int = 200
    worker_threads: int = 6
    
    # Audio enhancement
    enable_neural_enhancement: bool = True
    enable_voice_fingerprinting: bool = True
    enable_emotion_detection: bool = True
    
    # Analytics
    enable_conversation_analytics: bool = True
    enable_action_item_extraction: bool = True
    enable_insight_generation: bool = True
    
    # Performance
    max_processing_latency_ms: float = 500
    enable_performance_monitoring: bool = True
    
    # Quality thresholds
    min_confidence_threshold: float = 0.6
    min_voice_activity_threshold: float = 0.3

class EnhancedTranscriptionIntegration:
    """Main integration service for enhanced transcription system"""
    
    def __init__(self, config: Optional[EnhancedTranscriptionConfig] = None):
        self.config = config or EnhancedTranscriptionConfig()
        
        # Initialize all components
        self._initialize_components()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_callbacks: Dict[str, List[Callable]] = {}
        
        # Performance monitoring
        self.performance_metrics = {
            'total_sessions': 0,
            'total_chunks_processed': 0,
            'total_results_emitted': 0,
            'avg_processing_latency': 0.0,
            'avg_enhancement_quality': 0.0,
            'system_uptime': time.time()
        }
        
        self.lock = threading.Lock()
        
        logger.info("🚀 Enhanced Transcription Integration System initialized")
    
    def _initialize_components(self):
        """Initialize all enhanced components"""
        try:
            # Initialize streaming processor
            self.streaming_processor = get_enhanced_streaming_processor(self.config.streaming_config)
            logger.info("✅ Enhanced streaming processor initialized")
            
            # Initialize neural audio enhancer
            if self.config.enable_neural_enhancement:
                self.neural_enhancer = get_neural_audio_enhancer()
                logger.info("✅ Neural audio enhancer initialized")
            else:
                self.neural_enhancer = None
            
            # Initialize chunk manager
            self.chunk_manager = get_intelligent_chunk_manager(
                max_cache_size_mb=self.config.max_cache_size_mb,
                worker_threads=self.config.worker_threads
            )
            logger.info("✅ Intelligent chunk manager initialized")
            
            # Initialize conversation analytics
            if self.config.enable_conversation_analytics:
                self.analytics_engine = get_conversation_analytics()
                logger.info("✅ Conversation analytics initialized")
            else:
                self.analytics_engine = None
            
            # Set up processing callbacks
            self._setup_processing_callbacks()
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            raise
    
    def _setup_processing_callbacks(self):
        """Set up callbacks between components"""
        # Add chunk processing callback
        def chunk_processing_callback(chunk: IntelligentChunk):
            try:
                self._process_chunk_callback(chunk)
            except Exception as e:
                logger.error(f"❌ Chunk processing callback failed: {e}")
        
        self.chunk_manager.add_processing_callback(chunk_processing_callback)
        
        # Add quality filter
        def quality_filter(chunk: IntelligentChunk) -> bool:
            return (
                chunk.metrics.quality_score >= self.config.min_confidence_threshold and
                chunk.metrics.voice_activity >= self.config.min_voice_activity_threshold
            )
        
        self.chunk_manager.add_quality_filter(quality_filter)
    
    def create_enhanced_session(self, session_id: str, **metadata) -> Dict[str, Any]:
        """Create new enhanced transcription session"""
        with self.lock:
            session_info = {
                'id': session_id,
                'created_at': time.time(),
                'metadata': metadata,
                'status': 'active',
                'components': {
                    'streaming_processor': None,
                    'chunk_manager': None,
                    'analytics': None,
                    'neural_enhancer': None
                },
                'performance': {
                    'chunks_processed': 0,
                    'results_emitted': 0,
                    'avg_latency': 0.0,
                    'quality_scores': [],
                    'errors': 0
                },
                'callbacks': []
            }
            
            # Initialize components for session
            session_info['components']['streaming_processor'] = self.streaming_processor.create_session(
                session_id, **metadata
            )
            
            session_info['components']['chunk_manager'] = self.chunk_manager.create_session(
                session_id, **metadata
            )
            
            if self.analytics_engine:
                session_info['components']['analytics'] = self.analytics_engine.create_session(
                    session_id, **metadata
                )
            
            self.active_sessions[session_id] = session_info
            self.session_callbacks[session_id] = []
            
            # Update global metrics
            self.performance_metrics['total_sessions'] += 1
            
            logger.info(f"🎯 Created enhanced transcription session: {session_id}")
            return session_info
    
    def process_audio_chunk(self, session_id: str, audio_data: np.ndarray, 
                           sample_rate: int = 16000, **chunk_metadata) -> Dict[str, Any]:
        """Process audio chunk through enhanced pipeline"""
        if session_id not in self.active_sessions:
            self.create_enhanced_session(session_id)
        
        start_time = time.time()
        processing_results = {
            'session_id': session_id,
            'chunk_id': str(uuid.uuid4()),
            'timestamp': start_time,
            'processing_stages': {}
        }
        
        try:
            # Stage 1: Neural Audio Enhancement
            enhancement_result = None
            if self.neural_enhancer:
                enhancement_result = self.neural_enhancer.process_audio(
                    audio_data, sample_rate, session_id
                )
                processing_results['processing_stages']['neural_enhancement'] = {
                    'completed': True,
                    'processing_time_ms': enhancement_result.get('processing_time_ms', 0),
                    'quality_score': enhancement_result.get('enhancement_quality', 0)
                }
            
            # Stage 2: Create Intelligent Chunk
            chunk = IntelligentChunk(
                id=processing_results['chunk_id'],
                session_id=session_id,
                data=audio_data,
                timestamp=start_time,
                sequence_number=self.active_sessions[session_id]['performance']['chunks_processed'],
                chunk_type='audio',
                priority=self._determine_chunk_priority(audio_data, enhancement_result),
                metadata={
                    **chunk_metadata,
                    'sample_rate': sample_rate,
                    'enhancement_result': enhancement_result,
                    'audio_length_seconds': len(audio_data) / sample_rate
                }
            )
            
            # Update chunk metrics from enhancement
            if enhancement_result:
                chunk.metrics.voice_activity = enhancement_result.get('voice_features', {}).get('voice_activity', 0)
                chunk.metrics.quality_score = enhancement_result.get('enhancement_quality', 0)
                chunk.metrics.noise_level = enhancement_result.get('acoustic_scene', {}).get('noise_level', 0)
                
                # Speaker identification
                speaker_info = enhancement_result.get('speaker_identification', {})
                if speaker_info.get('speaker_id'):
                    chunk.metadata['speaker_id'] = speaker_info['speaker_id']
                    chunk.metadata['speaker_confidence'] = speaker_info.get('confidence', 0)
                
                # Emotion detection
                emotions = enhancement_result.get('emotions', {})
                if emotions:
                    chunk.metadata['emotions'] = emotions
                    chunk.metrics.emotion_intensity = max(emotions.values()) if emotions else 0
            
            # Stage 3: Add to Chunk Manager
            chunk_added = self.chunk_manager.add_chunk(chunk)
            processing_results['processing_stages']['chunk_management'] = {
                'completed': chunk_added,
                'chunk_id': chunk.id,
                'priority': chunk.priority.value if hasattr(chunk.priority, 'value') else str(chunk.priority)
            }
            
            # Stage 4: Update session performance
            self._update_session_performance(session_id, processing_results, start_time)
            
            # Stage 5: Trigger callbacks
            self._trigger_session_callbacks(session_id, 'chunk_processed', {
                'chunk': chunk,
                'enhancement_result': enhancement_result,
                'processing_results': processing_results
            })
            
            return processing_results
            
        except Exception as e:
            logger.error(f"❌ Audio chunk processing failed: {e}")
            processing_results['error'] = str(e)
            self.active_sessions[session_id]['performance']['errors'] += 1
            return processing_results
    
    def process_transcription_result(self, session_id: str, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process transcription result through enhanced streaming pipeline"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        start_time = time.time()
        
        try:
            # Process through streaming processor
            enhanced_result = self.streaming_processor.process_streaming_result(session_id, raw_result)
            
            if not enhanced_result:
                return {'status': 'buffered', 'message': 'Result buffered for optimization'}
            
            # Add to conversation analytics
            if self.analytics_engine and enhanced_result:
                analytics_segment = {
                    'id': enhanced_result.id,
                    'text': enhanced_result.text,
                    'speaker': enhanced_result.speaker_id,
                    'timestamp': enhanced_result.timestamp,
                    'confidence': enhanced_result.confidence,
                    'emotions': enhanced_result.emotions,
                    'keywords': enhanced_result.keywords,
                    'duration': enhanced_result.end_time - enhanced_result.start_time if enhanced_result.end_time and enhanced_result.start_time else 3.0
                }
                
                analytics_result = self.analytics_engine.add_segment(session_id, analytics_segment)
            else:
                analytics_result = {}
            
            # Prepare enhanced response
            response = {
                'session_id': session_id,
                'result': enhanced_result.to_dict() if enhanced_result else None,
                'analytics': analytics_result,
                'processing_latency_ms': (time.time() - start_time) * 1000,
                'timestamp': time.time()
            }
            
            # Update session performance
            session = self.active_sessions[session_id]
            session['performance']['results_emitted'] += 1
            
            # Calculate running average latency
            latency = response['processing_latency_ms']
            current_avg = session['performance']['avg_latency']
            count = session['performance']['results_emitted']
            session['performance']['avg_latency'] = (current_avg * (count - 1) + latency) / count
            
            # Update quality scores
            if enhanced_result:
                session['performance']['quality_scores'].append(enhanced_result.confidence)
                if len(session['performance']['quality_scores']) > 100:
                    session['performance']['quality_scores'].pop(0)
            
            # Trigger callbacks
            self._trigger_session_callbacks(session_id, 'result_processed', response)
            
            # Update global metrics
            self.performance_metrics['total_results_emitted'] += 1
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Transcription result processing failed: {e}")
            return {'error': str(e), 'session_id': session_id}
    
    def _process_chunk_callback(self, chunk: IntelligentChunk):
        """Callback for when chunk is processed"""
        session_id = chunk.session_id
        
        if session_id not in self.active_sessions:
            return
        
        # Update session metrics
        session = self.active_sessions[session_id]
        session['performance']['chunks_processed'] += 1
        
        # Log processing completion
        logger.debug(f"✅ Chunk processed: {chunk.id} for session {session_id}")
        
        # Trigger session callbacks
        self._trigger_session_callbacks(session_id, 'chunk_completed', {
            'chunk_id': chunk.id,
            'processing_time': chunk.metrics.processing_time_ms,
            'quality_score': chunk.metrics.quality_score
        })
    
    def _determine_chunk_priority(self, audio_data: np.ndarray, 
                                 enhancement_result: Optional[Dict[str, Any]]) -> ChunkPriority:
        """Determine processing priority for audio chunk"""
        # Base priority
        priority = ChunkPriority.NORMAL
        
        if enhancement_result:
            # High voice activity = higher priority
            voice_activity = enhancement_result.get('voice_features', {}).get('voice_activity', 0)
            if voice_activity > 0.8:
                priority = ChunkPriority.HIGH
            
            # Low noise = higher priority
            noise_level = enhancement_result.get('acoustic_scene', {}).get('noise_level', 0.5)
            if noise_level < 0.2 and voice_activity > 0.6:
                priority = ChunkPriority.HIGH
            
            # Strong emotions = higher priority
            emotions = enhancement_result.get('emotions', {})
            if emotions and max(emotions.values()) > 0.7:
                priority = ChunkPriority.HIGH
        
        # Check audio characteristics
        energy = np.mean(audio_data ** 2)
        if energy > 0.1:  # High energy
            if priority == ChunkPriority.NORMAL:
                priority = ChunkPriority.HIGH
        elif energy < 0.01:  # Very low energy
            priority = ChunkPriority.LOW
        
        return priority
    
    def _update_session_performance(self, session_id: str, processing_results: Dict[str, Any], start_time: float):
        """Update session performance metrics"""
        session = self.active_sessions[session_id]
        
        # Calculate total processing time
        total_latency = (time.time() - start_time) * 1000
        processing_results['total_processing_latency_ms'] = total_latency
        
        # Update session averages
        perf = session['performance']
        perf['chunks_processed'] += 1
        
        # Running average latency
        current_avg = perf['avg_latency']
        count = perf['chunks_processed']
        perf['avg_latency'] = (current_avg * (count - 1) + total_latency) / count
        
        # Update global metrics
        self.performance_metrics['total_chunks_processed'] += 1
        
        # Global average latency
        global_avg = self.performance_metrics['avg_processing_latency']
        global_count = self.performance_metrics['total_chunks_processed']
        self.performance_metrics['avg_processing_latency'] = (
            global_avg * (global_count - 1) + total_latency
        ) / global_count
    
    def _trigger_session_callbacks(self, session_id: str, event_type: str, data: Dict[str, Any]):
        """Trigger callbacks for session events"""
        if session_id not in self.session_callbacks:
            return
        
        for callback in self.session_callbacks[session_id]:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.warning(f"⚠️ Session callback failed: {e}")
    
    def add_session_callback(self, session_id: str, callback: Callable):
        """Add callback for session events"""
        if session_id not in self.session_callbacks:
            self.session_callbacks[session_id] = []
        
        self.session_callbacks[session_id].append(callback)
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session analytics"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        analytics = {}
        
        # Get streaming processor analytics
        streaming_analytics = self.streaming_processor.get_session_analytics(session_id)
        
        # Get chunk manager analytics
        chunk_analytics = self.chunk_manager.get_session_analytics(session_id)
        
        # Get conversation analytics
        if self.analytics_engine:
            conversation_analytics = self.analytics_engine.get_session_summary(session_id)
        else:
            conversation_analytics = {}
        
        # Get neural enhancement summary
        enhancement_summary = {}
        if self.neural_enhancer:
            enhancement_summary = self.neural_enhancer.get_session_summary(session_id)
        
        # Combine all analytics
        analytics = {
            'session_info': session,
            'streaming_analytics': streaming_analytics,
            'chunk_analytics': chunk_analytics,
            'conversation_analytics': conversation_analytics,
            'enhancement_summary': enhancement_summary,
            'integration_metrics': {
                'total_processing_time': time.time() - session['created_at'],
                'components_active': len([c for c in session['components'].values() if c]),
                'callbacks_registered': len(self.session_callbacks.get(session_id, [])),
                'performance_score': self._calculate_session_performance_score(session)
            }
        }
        
        return analytics
    
    def _calculate_session_performance_score(self, session: Dict[str, Any]) -> float:
        """Calculate overall performance score for session"""
        perf = session['performance']
        
        # Start with base score
        score = 0.5
        
        # Low latency bonus
        if perf['avg_latency'] < self.config.max_processing_latency_ms:
            score += 0.2
        
        # High quality bonus
        if perf['quality_scores']:
            avg_quality = np.mean(perf['quality_scores'])
            score += avg_quality * 0.2
        
        # Low error rate bonus
        error_rate = perf['errors'] / max(perf['chunks_processed'], 1)
        score += (1.0 - error_rate) * 0.1
        
        # High throughput bonus
        duration = time.time() - session['created_at']
        chunks_per_second = perf['chunks_processed'] / max(duration, 1)
        if chunks_per_second > 1.0:  # More than 1 chunk per second
            score += 0.1
        
        return min(1.0, score)
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics"""
        uptime = time.time() - self.performance_metrics['system_uptime']
        
        # Get component performance
        component_performance = {}
        
        if hasattr(self.streaming_processor, 'get_performance_metrics'):
            # Get streaming processor performance if available
            if hasattr(self.streaming_processor, 'get_performance_metrics'):
                component_performance['streaming_processor'] = self.streaming_processor.get_performance_metrics()
            else:
                component_performance['streaming_processor'] = {'status': 'active'}
        
        if hasattr(self.chunk_manager, 'get_system_performance'):
            component_performance['chunk_manager'] = self.chunk_manager.get_system_performance()
        
        return {
            'system_metrics': {
                **self.performance_metrics,
                'uptime_seconds': uptime,
                'chunks_per_second': self.performance_metrics['total_chunks_processed'] / max(uptime, 1),
                'results_per_second': self.performance_metrics['total_results_emitted'] / max(uptime, 1),
                'active_sessions': len(self.active_sessions)
            },
            'component_performance': component_performance,
            'session_summaries': {
                session_id: {
                    'duration': time.time() - session['created_at'],
                    'chunks_processed': session['performance']['chunks_processed'],
                    'avg_latency': session['performance']['avg_latency'],
                    'performance_score': self._calculate_session_performance_score(session)
                }
                for session_id, session in self.active_sessions.items()
            }
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End enhanced transcription session"""
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        
        # Get final analytics from all components
        final_analytics = {}
        
        # Streaming processor
        if self.streaming_processor:
            final_analytics['streaming'] = self.streaming_processor.end_session(session_id)
        
        # Chunk manager
        if self.chunk_manager:
            final_analytics['chunk_management'] = self.chunk_manager.end_session(session_id)
        
        # Conversation analytics
        if self.analytics_engine:
            final_analytics['conversation'] = self.analytics_engine.end_session(session_id)
        
        # Neural enhancement summary
        if self.neural_enhancer:
            final_analytics['enhancement'] = self.neural_enhancer.get_session_summary(session_id)
        
        # Session summary
        session_summary = {
            'session_id': session_id,
            'duration_seconds': time.time() - session['created_at'],
            'final_performance': session['performance'],
            'performance_score': self._calculate_session_performance_score(session),
            'components_used': list(session['components'].keys()),
            'total_callbacks_triggered': len(self.session_callbacks.get(session_id, []))
        }
        
        # Cleanup
        with self.lock:
            del self.active_sessions[session_id]
            self.session_callbacks.pop(session_id, None)
        
        logger.info(f"🏁 Ended enhanced transcription session: {session_id}")
        
        return {
            'session_summary': session_summary,
            'component_analytics': final_analytics
        }

# Global integration instance
_integration_service = None
_integration_lock = threading.Lock()

def get_enhanced_transcription_integration(config: Optional[EnhancedTranscriptionConfig] = None) -> EnhancedTranscriptionIntegration:
    """Get global enhanced transcription integration instance"""
    global _integration_service
    
    with _integration_lock:
        if _integration_service is None:
            _integration_service = EnhancedTranscriptionIntegration(config)
        return _integration_service

logger.info("✅ Enhanced Transcription Integration module initialized")