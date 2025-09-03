"""
Enhanced Transcription Service - Google Recorder Level Integration
Integrates all advanced components for Google Recorder-level transcription performance.
Orchestrates advanced audio processing, context correlation, VAD, and progressive interim display.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
import threading
from collections import deque

# Import our advanced components
from .advanced_audio_processor import AdvancedAudioProcessor, AudioChunk, AudioEnhancementConfig
from .context_correlation_engine import ContextCorrelationEngine, TranscriptionChunk, ContextCorrelation
from .enhanced_vad_service import EnhancedVADService, VADResult
from .progressive_interim_system import ProgressiveInterimSystem, InterimUpdate
from .latency_optimization_engine import LatencyOptimizationEngine, PipelineStage

# Import existing services
from .whisper_streaming import WhisperStreamingService, TranscriptionConfig
from .transcription_service import TranscriptionServiceConfig

logger = logging.getLogger(__name__)

@dataclass
class GoogleRecorderConfig:
    """Configuration for Google Recorder-level performance."""
    # Performance targets
    target_latency_ms: float = 400.0
    target_wer: float = 0.05  # 5% Word Error Rate
    target_confidence: float = 0.85
    
    # Advanced audio processing
    enable_spectral_enhancement: bool = True
    enable_adaptive_noise_reduction: bool = True
    enable_speech_enhancement: bool = True
    overlap_duration_ms: int = 500
    
    # Context correlation
    enable_context_correlation: bool = True
    max_context_chunks: int = 5
    context_stability_threshold: float = 0.8
    
    # Progressive interim display
    enable_progressive_interim: bool = True
    interim_stability_threshold: float = 0.75
    interim_confirmation_delay: float = 1.0
    
    # VAD enhancement
    enable_advanced_vad: bool = True
    vad_aggressiveness: int = 2
    vad_fusion_mode: str = "adaptive"  # webrtc, energy, spectral, feature, adaptive
    
    # Quality assurance
    enable_hallucination_detection: bool = True
    enable_adaptive_quality: bool = True
    min_quality_threshold: float = 0.7

class EnhancedTranscriptionService:
    """
    🎯 Google Recorder-level transcription service.
    
    Integrates all advanced components for enterprise-grade transcription performance:
    - Advanced audio preprocessing with spectral enhancement
    - Context correlation for seamless chunk continuity
    - Enhanced VAD with multi-algorithm fusion
    - Progressive interim display system
    - Latency optimization engine
    - Adaptive quality monitoring
    """
    
    def __init__(self, config: Optional[GoogleRecorderConfig] = None):
        self.config = config or GoogleRecorderConfig()
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_contexts: Dict[str, ContextCorrelationEngine] = {}
        self.session_interim_systems: Dict[str, ProgressiveInterimSystem] = {}
        
        # Initialize advanced components
        self._initialize_advanced_components()
        
        # Initialize original Whisper service
        transcription_config = TranscriptionConfig(
            language="en",
            confidence_threshold=self.config.target_confidence
        )
        self.whisper_service = WhisperStreamingService(transcription_config)
        
        # Performance tracking
        self.performance_metrics = {
            'total_chunks_processed': 0,
            'avg_latency_ms': 0.0,
            'avg_confidence': 0.0,
            'avg_quality_score': 0.0,
            'wer_estimate': 0.0
        }
        
        # Threading for continuous optimization
        self.optimization_thread = None
        self.running = False
        
        logger.info("🎯 Enhanced Transcription Service initialized with Google Recorder-level components")
    
    def _initialize_advanced_components(self):
        """🔧 Initialize all advanced components."""
        try:
            # 1. Advanced Audio Processor
            audio_config = AudioEnhancementConfig(
                enable_spectral_enhancement=self.config.enable_spectral_enhancement,
                enable_adaptive_noise_reduction=self.config.enable_adaptive_noise_reduction,
                enable_speech_enhancement=self.config.enable_speech_enhancement,
                overlap_duration_ms=self.config.overlap_duration_ms
            )
            self.audio_processor = AdvancedAudioProcessor(audio_config)
            
            # 2. Enhanced VAD Service
            self.vad_service = EnhancedVADService(
                sample_rate=16000,
                aggressiveness=self.config.vad_aggressiveness
            )
            
            # 3. Latency Optimization Engine
            self.latency_optimizer = LatencyOptimizationEngine(
                target_latency_ms=self.config.target_latency_ms
            )
            
            # 4. Initialize pipeline stages
            self._setup_optimized_pipeline()
            
            logger.info("🔧 Advanced components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Advanced component initialization failed: {e}")
            raise
    
    def _setup_optimized_pipeline(self):
        """⚡ Setup optimized processing pipeline."""
        try:
            pipeline_stages = [
                PipelineStage(
                    name="audio_preprocessing",
                    processor=self._stage_audio_preprocessing,
                    parallel=True,
                    max_workers=2,
                    timeout=0.3,
                    priority=0
                ),
                PipelineStage(
                    name="vad_analysis",
                    processor=self._stage_vad_analysis,
                    parallel=True,
                    max_workers=2,
                    timeout=0.2,
                    priority=1
                ),
                PipelineStage(
                    name="transcription",
                    processor=self._stage_transcription,
                    parallel=False,  # Sequential with Whisper
                    max_workers=1,
                    timeout=2.0,
                    priority=2
                ),
                PipelineStage(
                    name="context_correlation",
                    processor=self._stage_context_correlation,
                    parallel=True,
                    max_workers=2,
                    timeout=0.1,
                    priority=3
                ),
                PipelineStage(
                    name="interim_processing",
                    processor=self._stage_interim_processing,
                    parallel=True,
                    max_workers=2,
                    timeout=0.1,
                    priority=4
                )
            ]
            
            self.latency_optimizer.initialize_pipeline(pipeline_stages)
            
            logger.info("⚡ Optimized pipeline initialized with 5 stages")
            
        except Exception as e:
            logger.error(f"❌ Pipeline setup failed: {e}")
            raise
    
    async def start_session(self, session_id: str, **kwargs) -> Dict[str, Any]:
        """🚀 Start enhanced transcription session."""
        try:
            # Initialize session context
            session_context = {
                'session_id': session_id,
                'start_time': time.time(),
                'chunk_count': 0,
                'total_latency': 0.0,
                'total_confidence': 0.0,
                'processing_stats': {}
            }
            
            self.active_sessions[session_id] = session_context
            
            # Initialize context correlation engine
            if self.config.enable_context_correlation:
                self.session_contexts[session_id] = ContextCorrelationEngine(
                    max_context_chunks=self.config.max_context_chunks
                )
            
            # Initialize progressive interim system
            if self.config.enable_progressive_interim:
                interim_system = ProgressiveInterimSystem(
                    stability_threshold=self.config.interim_stability_threshold,
                    confirmation_delay=self.config.interim_confirmation_delay
                )
                interim_system.start_processing()
                self.session_interim_systems[session_id] = interim_system
            
            # Start latency optimization
            if not self.running:
                self.latency_optimizer.start_optimization()
                self.running = True
            
            logger.info(f"🚀 Enhanced session {session_id} started")
            
            return {
                'success': True,
                'session_id': session_id,
                'enhanced_features': {
                    'advanced_audio_processing': True,
                    'context_correlation': self.config.enable_context_correlation,
                    'progressive_interim': self.config.enable_progressive_interim,
                    'latency_optimization': True,
                    'target_latency_ms': self.config.target_latency_ms
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Session start failed for {session_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    async def process_audio_chunk(self, session_id: str, audio_data: bytes, 
                                is_final: bool = False, 
                                timestamp: Optional[float] = None) -> Dict[str, Any]:
        """
        🎯 Process audio chunk with Google Recorder-level optimization.
        
        Args:
            session_id: Session identifier
            audio_data: Raw audio bytes
            is_final: Whether this is a final chunk
            timestamp: Optional timestamp
            
        Returns:
            Enhanced processing result with latency metrics
        """
        if session_id not in self.active_sessions:
            return {'success': False, 'error': 'Session not found'}
        
        if timestamp is None:
            timestamp = time.time()
        
        try:
            session_context = self.active_sessions[session_id]
            chunk_id = session_context['chunk_count']
            session_context['chunk_count'] += 1
            
            # === OPTIMIZED PIPELINE EXECUTION ===
            
            # Process through latency-optimized pipeline
            result = await self.latency_optimizer.process_chunk_optimized(
                audio_chunk={
                    'data': audio_data,
                    'session_id': session_id,
                    'chunk_id': chunk_id,
                    'timestamp': timestamp,
                    'is_final': is_final
                },
                session_id=session_id,
                chunk_id=chunk_id
            )
            
            # Update session statistics
            if result['success']:
                session_context['total_latency'] += result['latency_ms']
                
                # Extract transcription result
                transcription_result = result['result'].get('transcription', {})
                
                if transcription_result.get('success', False):
                    session_context['total_confidence'] += transcription_result.get('confidence', 0.0)
                    
                    # Update global performance metrics
                    self._update_performance_metrics(result, transcription_result)
                    
                    return {
                        'success': True,
                        'transcript': transcription_result.get('transcript', ''),
                        'confidence': transcription_result.get('confidence', 0.0),
                        'is_final': is_final,
                        'latency_ms': result['latency_ms'],
                        'meets_target': result['meets_target'],
                        'quality_score': transcription_result.get('quality_score', 0.0),
                        'context_correlation': transcription_result.get('context_correlation', {}),
                        'interim_update': transcription_result.get('interim_update', {}),
                        'vad_result': transcription_result.get('vad_result', {}),
                        'chunk_id': chunk_id,
                        'session_stats': self._get_session_stats(session_id)
                    }
            
            return {
                'success': False,
                'error': result.get('error', 'Processing failed'),
                'latency_ms': result.get('latency_ms', 0),
                'chunk_id': chunk_id
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced audio processing failed for session {session_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'chunk_id': chunk_id if 'chunk_id' in locals() else 0
            }
    
    def _stage_audio_preprocessing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🎵 Pipeline stage: Advanced audio preprocessing."""
        try:
            audio_chunk_data = context['audio_chunk']
            
            # Process with advanced audio processor
            enhanced_chunk = self.audio_processor.process_audio_chunk_advanced(
                audio_data=audio_chunk_data['data'],
                session_id=audio_chunk_data['session_id'],
                chunk_id=audio_chunk_data['chunk_id'],
                timestamp=audio_chunk_data['timestamp']
            )
            
            return {
                'success': True,
                'enhanced_chunk': enhanced_chunk,
                'quality_score': enhanced_chunk.quality_score,
                'speech_probability': enhanced_chunk.speech_probability,
                'noise_level': enhanced_chunk.noise_level
            }
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing stage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _stage_vad_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🎤 Pipeline stage: Enhanced VAD analysis."""
        try:
            if not self.config.enable_advanced_vad:
                return {'success': True, 'vad_result': None}
            
            audio_chunk_data = context['audio_chunk']
            
            # Analyze voice activity with enhanced VAD
            vad_result = self.vad_service.analyze_voice_activity(
                audio_data=audio_chunk_data['data'],
                timestamp=audio_chunk_data['timestamp']
            )
            
            return {
                'success': True,
                'vad_result': vad_result,
                'is_speech': vad_result.is_speech,
                'confidence': vad_result.confidence
            }
            
        except Exception as e:
            logger.error(f"❌ VAD analysis stage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _stage_transcription(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🗣️ Pipeline stage: Whisper transcription."""
        try:
            audio_chunk_data = context['audio_chunk']
            
            # Check if VAD indicates speech
            vad_result = context.get('stage_results', {}).get('vad_analysis', {})
            if vad_result and not vad_result.get('is_speech', True):
                return {
                    'success': True,
                    'transcript': '',
                    'confidence': 0.0,
                    'skipped_reason': 'no_speech_detected'
                }
            
            # Get enhanced audio from preprocessing stage
            preprocessing_result = context.get('stage_results', {}).get('audio_preprocessing', {})
            
            if preprocessing_result and 'enhanced_chunk' in preprocessing_result:
                enhanced_chunk = preprocessing_result['enhanced_chunk']
                # Convert enhanced audio back to bytes for Whisper
                enhanced_audio_bytes = (enhanced_chunk.data * 32768.0).astype(np.int16).tobytes()
            else:
                enhanced_audio_bytes = audio_chunk_data['data']
            
            # Transcribe with Whisper
            transcription_result = asyncio.run(
                self.whisper_service.transcribe_audio(
                    audio_data=enhanced_audio_bytes,
                    session_id=audio_chunk_data['session_id'],
                    chunk_id=audio_chunk_data['chunk_id']
                )
            )
            
            return {
                'success': transcription_result.get('success', False),
                'transcript': transcription_result.get('transcript', ''),
                'confidence': transcription_result.get('confidence', 0.0),
                'segments': transcription_result.get('segments', []),
                'processing_time': transcription_result.get('processing_time', 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription stage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _stage_context_correlation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """🧠 Pipeline stage: Context correlation."""
        try:
            if not self.config.enable_context_correlation:
                return {'success': True, 'correlation_result': None}
            
            audio_chunk_data = context['audio_chunk']
            session_id = audio_chunk_data['session_id']
            
            # Get transcription result
            transcription_result = context.get('stage_results', {}).get('transcription', {})
            if not transcription_result.get('success', False):
                return {'success': True, 'correlation_result': None}
            
            # Get context correlation engine for session
            if session_id not in self.session_contexts:
                return {'success': True, 'correlation_result': None}
            
            context_engine = self.session_contexts[session_id]
            
            # Create transcription chunk
            transcription_chunk = TranscriptionChunk(
                chunk_id=audio_chunk_data['chunk_id'],
                session_id=session_id,
                text=transcription_result['transcript'],
                timestamp=audio_chunk_data['timestamp'],
                confidence=transcription_result['confidence'],
                audio_hash=f"chunk_{audio_chunk_data['chunk_id']}",
                is_interim=not audio_chunk_data.get('is_final', False)
            )
            
            # Process context correlation
            correlation_result = context_engine.add_transcription_chunk(transcription_chunk)
            
            return {
                'success': True,
                'correlation_result': correlation_result,
                'text_update': correlation_result.get('text_update', {}),
                'context_score': correlation_result.get('context_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Context correlation stage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _stage_interim_processing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """📝 Pipeline stage: Progressive interim processing."""
        try:
            if not self.config.enable_progressive_interim:
                return {'success': True, 'interim_result': None}
            
            audio_chunk_data = context['audio_chunk']
            session_id = audio_chunk_data['session_id']
            
            # Get interim system for session
            if session_id not in self.session_interim_systems:
                return {'success': True, 'interim_result': None}
            
            interim_system = self.session_interim_systems[session_id]
            
            # Get transcription and context results
            transcription_result = context.get('stage_results', {}).get('transcription', {})
            context_result = context.get('stage_results', {}).get('context_correlation', {})
            
            if not transcription_result.get('success', False):
                return {'success': True, 'interim_result': None}
            
            # Use context-correlated text if available
            text_update = context_result.get('text_update', {})
            final_text = text_update.get('display_text', transcription_result['transcript'])
            
            # Create interim update
            interim_update = InterimUpdate(
                text=final_text,
                confidence=transcription_result['confidence'],
                chunk_id=audio_chunk_data['chunk_id'],
                timestamp=audio_chunk_data['timestamp'],
                is_final=audio_chunk_data.get('is_final', False)
            )
            
            # Process interim update
            interim_result = interim_system.add_interim_update(interim_update)
            
            return {
                'success': True,
                'interim_result': interim_result,
                'display_text': interim_result.get('display_text', ''),
                'stability_score': interim_result.get('stability_score', 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Interim processing stage failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _update_performance_metrics(self, pipeline_result: Dict[str, Any], 
                                  transcription_result: Dict[str, Any]):
        """📊 Update global performance metrics."""
        try:
            self.performance_metrics['total_chunks_processed'] += 1
            
            # Update latency
            total_chunks = self.performance_metrics['total_chunks_processed']
            current_avg_latency = self.performance_metrics['avg_latency_ms']
            new_latency = pipeline_result['latency_ms']
            
            self.performance_metrics['avg_latency_ms'] = (
                (current_avg_latency * (total_chunks - 1) + new_latency) / total_chunks
            )
            
            # Update confidence
            current_avg_confidence = self.performance_metrics['avg_confidence']
            new_confidence = transcription_result.get('confidence', 0.0)
            
            self.performance_metrics['avg_confidence'] = (
                (current_avg_confidence * (total_chunks - 1) + new_confidence) / total_chunks
            )
            
            # Update quality score if available
            quality_score = transcription_result.get('quality_score', 0.0)
            if quality_score > 0:
                current_avg_quality = self.performance_metrics['avg_quality_score']
                self.performance_metrics['avg_quality_score'] = (
                    (current_avg_quality * (total_chunks - 1) + quality_score) / total_chunks
                )
            
        except Exception as e:
            logger.warning(f"⚠️ Performance metrics update failed: {e}")
    
    def _get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """📊 Get session-specific statistics."""
        try:
            if session_id not in self.active_sessions:
                return {}
            
            session_context = self.active_sessions[session_id]
            chunk_count = session_context['chunk_count']
            
            if chunk_count == 0:
                return {'chunk_count': 0}
            
            avg_latency = session_context['total_latency'] / chunk_count
            avg_confidence = session_context['total_confidence'] / chunk_count
            
            return {
                'chunk_count': chunk_count,
                'avg_latency_ms': avg_latency,
                'avg_confidence': avg_confidence,
                'session_duration': time.time() - session_context['start_time']
            }
            
        except Exception as e:
            logger.warning(f"⚠️ Session stats calculation failed: {e}")
            return {}
    
    async def stop_session(self, session_id: str) -> Dict[str, Any]:
        """⏹️ Stop enhanced transcription session."""
        try:
            if session_id not in self.active_sessions:
                return {'success': False, 'error': 'Session not found'}
            
            # Stop progressive interim system
            if session_id in self.session_interim_systems:
                self.session_interim_systems[session_id].stop_processing()
                del self.session_interim_systems[session_id]
            
            # Clean up context correlation
            if session_id in self.session_contexts:
                del self.session_contexts[session_id]
            
            # Get final session stats
            final_stats = self._get_session_stats(session_id)
            
            # Clean up session
            del self.active_sessions[session_id]
            
            logger.info(f"⏹️ Enhanced session {session_id} stopped")
            
            return {
                'success': True,
                'session_id': session_id,
                'final_stats': final_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Session stop failed for {session_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """📊 Get comprehensive performance report."""
        try:
            # Get latency optimizer report
            latency_report = self.latency_optimizer.get_performance_report()
            
            # Get audio processor stats
            audio_stats = self.audio_processor.get_performance_stats()
            
            # Get VAD stats
            vad_stats = self.vad_service.get_performance_stats()
            
            return {
                'overall_performance': self.performance_metrics,
                'latency_optimization': latency_report,
                'audio_processing': audio_stats,
                'vad_performance': vad_stats,
                'active_sessions': len(self.active_sessions),
                'google_recorder_compliance': {
                    'target_latency_ms': self.config.target_latency_ms,
                    'current_avg_latency_ms': self.performance_metrics['avg_latency_ms'],
                    'latency_target_met': self.performance_metrics['avg_latency_ms'] <= self.config.target_latency_ms,
                    'target_confidence': self.config.target_confidence,
                    'current_avg_confidence': self.performance_metrics['avg_confidence'],
                    'confidence_target_met': self.performance_metrics['avg_confidence'] >= self.config.target_confidence
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Performance report generation failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def shutdown(self):
        """🔄 Shutdown enhanced transcription service."""
        try:
            # Stop all active sessions
            for session_id in list(self.active_sessions.keys()):
                asyncio.run(self.stop_session(session_id))
            
            # Stop latency optimization
            self.latency_optimizer.stop_optimization()
            self.running = False
            
            logger.info("🔄 Enhanced Transcription Service shutdown complete")
            
        except Exception as e:
            logger.error(f"❌ Shutdown failed: {e}")


# Import numpy for audio processing
import numpy as np