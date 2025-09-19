"""
🎯 OBSERVER SERVICE - Comprehensive Performance & Quality Observability

This service implements the OBSERVER-SYS and OBSERVER-LING specifications:
- System performance metrics: latencies, throughput, resource usage
- Linguistic quality metrics: WER, confidence, transcript refinement
- Structured persistence: Database + JSONL files
- Internal API endpoints for metrics access

Integrates with existing PerformanceMonitor and QAPipeline services.
"""

import json
import time
import logging
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

from models.session import Session
from models.segment import Segment  
from models.metrics import ChunkMetric, SessionMetric
from services.performance_monitor import PerformanceMonitor, TranscriptionMetrics
from services.qa_pipeline import QAPipeline, TranscriptQualityMetrics
from app_refactored import db
import os

logger = logging.getLogger(__name__)


@dataclass
class ChunkTimestamps:
    """Comprehensive timestamp tracking for a single chunk."""
    chunk_id: str
    session_id: str
    
    # Client-side timestamps
    t_client_chunk_start: Optional[int] = None
    t_client_chunk_end: Optional[int] = None
    t_client_tx: Optional[int] = None
    t_client_render_interim: Optional[int] = None
    t_client_render_final: Optional[int] = None
    
    # Server-side timestamps  
    t_ws_rx: Optional[int] = None
    t_decode_start: Optional[int] = None
    t_decode_done: Optional[int] = None
    t_api_start: Optional[int] = None
    t_api_done: Optional[int] = None
    t_emit_interim: Optional[int] = None
    t_emit_final: Optional[int] = None


@dataclass
class ChunkQualityMetrics:
    """Linguistic and semantic quality metrics for a chunk."""
    chunk_id: str
    interim_updates_count: int = 0
    transcript_change_rate: float = 0.0
    avg_confidence_score: float = 0.0
    word_count: int = 0
    interim_text: str = ""
    final_text: str = ""


class ObserverService:
    """
    🔍 Comprehensive observability service for live transcription.
    
    Implements OBSERVER-SYS and OBSERVER-LING specifications:
    - Tracks detailed performance metrics per chunk and session
    - Computes linguistic quality metrics including WER and confidence
    - Persists metrics to both database and structured logs
    - Provides internal API for metrics access
    """
    
    def __init__(self, metrics_storage_path: str = "/tmp/mina_metrics"):
        self.storage_path = Path(metrics_storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        
        # Active tracking
        self.chunk_timestamps: Dict[str, ChunkTimestamps] = {}
        self.chunk_quality: Dict[str, ChunkQualityMetrics] = {}
        self.session_context: Dict[str, Dict] = {}
        
        # Integration with existing services
        self.performance_monitor = PerformanceMonitor()
        self.qa_pipeline = QAPipeline()
        
        # JSONL file for structured logging
        self.metrics_log = self.storage_path / "metrics.jsonl"
        
        logger.info("🎯 OBSERVER: Comprehensive observability service initialized")
    
    def start_chunk_tracking(self, session_id: str, chunk_id: str) -> ChunkTimestamps:
        """Initialize timestamp tracking for a new chunk."""
        timestamps = ChunkTimestamps(chunk_id=chunk_id, session_id=session_id)
        self.chunk_timestamps[chunk_id] = timestamps
        self.chunk_quality[chunk_id] = ChunkQualityMetrics(chunk_id=chunk_id)
        return timestamps
    
    def record_timestamp(self, chunk_id: str, timestamp_name: str, value: int):
        """Record a specific timestamp for a chunk."""
        if chunk_id in self.chunk_timestamps:
            timestamps = self.chunk_timestamps[chunk_id]
            setattr(timestamps, timestamp_name, value)
    
    def record_client_timestamps(self, chunk_id: str, client_data: Dict[str, Any]):
        """Record client-side timestamps from WebSocket message."""
        if chunk_id in self.chunk_timestamps:
            timestamps = self.chunk_timestamps[chunk_id]
            timestamps.t_client_chunk_start = client_data.get('chunk_start')
            timestamps.t_client_chunk_end = client_data.get('chunk_end') 
            timestamps.t_client_tx = client_data.get('transmission_time')
            timestamps.t_client_render_interim = client_data.get('render_interim')
            timestamps.t_client_render_final = client_data.get('render_final')
    
    def update_quality_metrics(self, chunk_id: str, interim_text: str = "", 
                             final_text: str = "", confidence: float = 0.0):
        """Update linguistic quality metrics for a chunk."""
        if chunk_id not in self.chunk_quality:
            return
            
        quality = self.chunk_quality[chunk_id]
        
        if interim_text:
            quality.interim_text = interim_text
            quality.interim_updates_count += 1
            
        if final_text:
            quality.final_text = final_text
            quality.word_count = len(final_text.split())
            
            # Calculate transcript change rate
            if quality.interim_text:
                quality.transcript_change_rate = self._calculate_change_rate(
                    quality.interim_text, final_text
                )
        
        if confidence > 0:
            quality.avg_confidence_score = confidence
    
    def _calculate_change_rate(self, interim: str, final: str) -> float:
        """Calculate edit distance ratio between interim and final transcripts."""
        if not interim or not final:
            return 0.0
            
        # Simple word-level edit distance calculation
        interim_words = interim.split()
        final_words = final.split()
        
        if not final_words:
            return 0.0
            
        # Levenshtein distance at word level
        edit_distance = self._word_levenshtein_distance(interim_words, final_words)
        return edit_distance / len(final_words)
    
    def _word_levenshtein_distance(self, words1: List[str], words2: List[str]) -> int:
        """Calculate Levenshtein distance between two word lists."""
        m, n = len(words1), len(words2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
            
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if words1[i-1] == words2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
                    
        return dp[m][n]
    
    def finalize_chunk_metrics(self, chunk_id: str) -> bool:
        """Finalize and persist metrics for a completed chunk."""
        if chunk_id not in self.chunk_timestamps:
            logger.warning(f"🎯 OBSERVER: No timestamps found for chunk {chunk_id}")
            return False
            
        timestamps = self.chunk_timestamps[chunk_id]
        quality = self.chunk_quality.get(chunk_id, ChunkQualityMetrics(chunk_id))
        
        try:
            # Compute derived metrics
            computed_metrics = self._compute_chunk_metrics(timestamps, quality)
            
            # Persist to database
            self._persist_chunk_metrics(timestamps, quality, computed_metrics)
            
            # Log to JSONL
            self._log_chunk_metrics(timestamps, quality, computed_metrics)
            
            # Cleanup
            del self.chunk_timestamps[chunk_id]
            if chunk_id in self.chunk_quality:
                del self.chunk_quality[chunk_id]
                
            return True
            
        except Exception as e:
            logger.error(f"🎯 OBSERVER ERROR: Failed to finalize chunk {chunk_id}: {e}")
            return False
    
    def _compute_chunk_metrics(self, timestamps: ChunkTimestamps, 
                              quality: ChunkQualityMetrics) -> Dict[str, Any]:
        """Compute derived performance metrics from timestamps."""
        metrics = {}
        
        # End-to-end latency: client_render_final - client_chunk_end
        if timestamps.t_client_render_final and timestamps.t_client_chunk_end:
            metrics['end_to_end_latency'] = timestamps.t_client_render_final - timestamps.t_client_chunk_end
        
        # Partial result latency: client_render_interim - client_chunk_start  
        if timestamps.t_client_render_interim and timestamps.t_client_chunk_start:
            metrics['partial_result_latency'] = timestamps.t_client_render_interim - timestamps.t_client_chunk_start
            
        # Finalization latency: client_render_final - end_of_speech
        # Note: Using client_chunk_end as proxy for end_of_speech
        if timestamps.t_client_render_final and timestamps.t_client_chunk_end:
            metrics['finalization_latency'] = timestamps.t_client_render_final - timestamps.t_client_chunk_end
            
        # Real-time factor: processing_time / audio_duration
        if timestamps.t_api_done and timestamps.t_api_start:
            processing_time = (timestamps.t_api_done - timestamps.t_api_start) / 1000.0  # Convert to seconds
            # Assuming chunk duration is ~1 second for real-time processing
            chunk_duration = 1.0
            metrics['real_time_factor'] = processing_time / chunk_duration
            
        # Throughput: audio_seconds_processed / wall_time_seconds
        if timestamps.t_client_chunk_end and timestamps.t_client_chunk_start:
            wall_time = (timestamps.t_client_chunk_end - timestamps.t_client_chunk_start) / 1000.0
            audio_duration = 1.0  # Assuming ~1 second audio chunks
            metrics['throughput'] = audio_duration / wall_time if wall_time > 0 else 0.0
            
        return metrics
    
    def _persist_chunk_metrics(self, timestamps: ChunkTimestamps, 
                              quality: ChunkQualityMetrics, 
                              computed_metrics: Dict[str, Any]):
        """Persist chunk metrics to database."""
        try:
            # Get session ID from session external_id if needed
            session = db.session.query(Session).filter_by(external_id=timestamps.session_id).first()
            if not session:
                logger.error(f"🎯 OBSERVER: Session not found: {timestamps.session_id}")
                return
                
            chunk_metric = ChunkMetric(
                    session_id=session.id,
                    chunk_id=timestamps.chunk_id,
                    
                    # Timestamps
                    t_client_chunk_start=timestamps.t_client_chunk_start,
                    t_client_chunk_end=timestamps.t_client_chunk_end,
                    t_client_tx=timestamps.t_client_tx,
                    t_ws_rx=timestamps.t_ws_rx,
                    t_decode_start=timestamps.t_decode_start,
                    t_decode_done=timestamps.t_decode_done,
                    t_api_start=timestamps.t_api_start,
                    t_api_done=timestamps.t_api_done,
                    t_emit_interim=timestamps.t_emit_interim,
                    t_emit_final=timestamps.t_emit_final,
                    t_client_render_interim=timestamps.t_client_render_interim,
                    t_client_render_final=timestamps.t_client_render_final,
                    
                    # Computed metrics
                    end_to_end_latency=computed_metrics.get('end_to_end_latency'),
                    partial_result_latency=computed_metrics.get('partial_result_latency'),
                    finalization_latency=computed_metrics.get('finalization_latency'),
                    real_time_factor=computed_metrics.get('real_time_factor'),
                    throughput=computed_metrics.get('throughput'),
                    
                    # Quality metrics
                    interim_updates_count=quality.interim_updates_count,
                    transcript_change_rate=quality.transcript_change_rate,
                    avg_confidence_score=quality.avg_confidence_score,
                    word_count=quality.word_count,
                    
                    # TODO: Add resource usage from system monitoring
                    # cpu_usage=...,
                    # memory_usage=...,
                    
                    status='completed'
                )
            
            db.session.add(chunk_metric)
            db.session.commit()
                
            logger.debug(f"🎯 OBSERVER: Persisted chunk metrics for {timestamps.chunk_id}")
                
        except Exception as e:
            logger.error(f"🎯 OBSERVER ERROR: Failed to persist chunk metrics: {e}")
    
    def _log_chunk_metrics(self, timestamps: ChunkTimestamps, 
                          quality: ChunkQualityMetrics, 
                          computed_metrics: Dict[str, Any]):
        """Log chunk metrics to JSONL file."""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'type': 'chunk_metrics',
                'session_id': timestamps.session_id,
                'chunk_id': timestamps.chunk_id,
                'timestamps': asdict(timestamps),
                'quality': asdict(quality),
                'computed_metrics': computed_metrics
            }
            
            with open(self.metrics_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            logger.error(f"🎯 OBSERVER ERROR: Failed to log chunk metrics: {e}")
    
    def compute_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Compute and persist aggregated session-level metrics."""
        try:
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            if not session:
                logger.error(f"🎯 OBSERVER: Session not found: {session_id}")
                return {}
                
            # Get all chunk metrics for this session
            chunk_metrics = db.session.query(ChunkMetric).filter_by(session_id=session.id).all()
            
            if not chunk_metrics:
                logger.warning(f"🎯 OBSERVER: No chunk metrics found for session {session_id}")
                return {}
            
            # Aggregate metrics
            aggregated = self._aggregate_chunk_metrics(chunk_metrics)
                
            # Create or update session metrics
            session_metric = db.session.query(SessionMetric).filter_by(session_id=session.id).first()
            if not session_metric:
                session_metric = SessionMetric(session_id=session.id)
                db.session.add(session_metric)
            
            # Update aggregated values
            for key, value in aggregated.items():
                setattr(session_metric, key, value)
            
            db.session.commit()
            
            logger.info(f"🎯 OBSERVER: Computed session metrics for {session_id}")
            return aggregated
                
        except Exception as e:
            logger.error(f"🎯 OBSERVER ERROR: Failed to compute session metrics: {e}")
            return {}
    
    def _aggregate_chunk_metrics(self, chunk_metrics: List[ChunkMetric]) -> Dict[str, Any]:
        """Aggregate chunk-level metrics into session-level metrics."""
        if not chunk_metrics:
            return {}
        
        # Extract valid metrics
        end_to_end_latencies = [m.end_to_end_latency for m in chunk_metrics if m.end_to_end_latency]
        partial_latencies = [m.partial_result_latency for m in chunk_metrics if m.partial_result_latency]
        finalization_latencies = [m.finalization_latency for m in chunk_metrics if m.finalization_latency]
        real_time_factors = [m.real_time_factor for m in chunk_metrics if m.real_time_factor]
        throughputs = [m.throughput for m in chunk_metrics if m.throughput]
        confidence_scores = [m.avg_confidence_score for m in chunk_metrics if m.avg_confidence_score]
        change_rates = [m.transcript_change_rate for m in chunk_metrics if m.transcript_change_rate]
        
        aggregated = {}
        aggregated['total_chunks'] = len(chunk_metrics)
        aggregated['successful_chunks'] = len([m for m in chunk_metrics if m.status == 'completed'])
        aggregated['error_count'] = len([m for m in chunk_metrics if m.status == 'error'])
        aggregated['total_interim_updates'] = sum(m.interim_updates_count or 0 for m in chunk_metrics)
        aggregated['total_words'] = sum(m.word_count or 0 for m in chunk_metrics)
        
        # Compute averages and percentiles
        if end_to_end_latencies:
            aggregated['avg_end_to_end_latency'] = statistics.mean(end_to_end_latencies)
            aggregated['p95_end_to_end_latency'] = statistics.quantiles(end_to_end_latencies, n=20)[18]  # 95th percentile
            aggregated['p99_end_to_end_latency'] = statistics.quantiles(end_to_end_latencies, n=100)[98] # 99th percentile
        
        if partial_latencies:
            aggregated['avg_partial_result_latency'] = statistics.mean(partial_latencies)
            
        if finalization_latencies:
            aggregated['avg_finalization_latency'] = statistics.mean(finalization_latencies)
            
        if real_time_factors:
            aggregated['avg_real_time_factor'] = statistics.mean(real_time_factors)
            
        if throughputs:
            aggregated['avg_throughput'] = statistics.mean(throughputs)
            
        if confidence_scores:
            aggregated['avg_confidence_score'] = statistics.mean(confidence_scores)
            
        if change_rates:
            aggregated['avg_transcript_change_rate'] = statistics.mean(change_rates)
        
        # Quality-delay tradeoff assessment
        if end_to_end_latencies and confidence_scores:
            avg_latency = statistics.mean(end_to_end_latencies)
            avg_confidence = statistics.mean(confidence_scores)
            quality_delay_tradeoff = {
                'latency_ms': avg_latency,
                'quality_proxy': avg_confidence,
                'tradeoff_score': avg_confidence / (avg_latency / 1000.0)  # Confidence per second of latency
            }
            aggregated['quality_delay_tradeoff'] = json.dumps(quality_delay_tradeoff)
        
        return aggregated
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive metrics for a session (for internal API)."""
        try:
            session = db.session.query(Session).filter_by(external_id=session_id).first()
            if not session:
                return {'error': 'Session not found'}
                
            # Get session metrics
            session_metric = db.session.query(SessionMetric).filter_by(session_id=session.id).first()
                
            if not session_metric:
                # Compute metrics if not exists
                self.compute_session_metrics(session_id)
                session_metric = db.session.query(SessionMetric).filter_by(session_id=session.id).first()
            
            if not session_metric:
                return {'error': 'No metrics available'}
            
            # Format for API response
            return {
                    'session_id': session_id,
                    'system_performance': {
                        'end_to_end_latency': session_metric.avg_end_to_end_latency,
                        'partial_result_latency': session_metric.avg_partial_result_latency,
                        'finalization_latency': session_metric.avg_finalization_latency,
                        'real_time_factor': session_metric.avg_real_time_factor,
                        'throughput': session_metric.avg_throughput,
                        'p95_latency': session_metric.p95_end_to_end_latency,
                        'p99_latency': session_metric.p99_end_to_end_latency,
                    },
                    'resource_usage': {
                        'cpu_usage': session_metric.avg_cpu_usage,
                        'memory_usage': session_metric.avg_memory_usage,
                        'network_usage': session_metric.total_network_usage,
                    },
                    'linguistic_quality': {
                        'word_error_rate': session_metric.word_error_rate,
                        'sentence_error_rate': session_metric.sentence_error_rate,
                        'avg_confidence_score': session_metric.avg_confidence_score,
                        'avg_transcript_change_rate': session_metric.avg_transcript_change_rate,
                        'quality_delay_tradeoff': json.loads(session_metric.quality_delay_tradeoff) if session_metric.quality_delay_tradeoff else None,
                    },
                    'session_summary': {
                        'total_chunks': session_metric.total_chunks,
                        'successful_chunks': session_metric.successful_chunks,
                        'error_count': session_metric.error_count,
                        'timeout_count': session_metric.timeout_count,
                        'total_words': session_metric.total_words,
                        'total_duration_sec': session_metric.total_duration_sec,
                        'total_interim_updates': session_metric.total_interim_updates,
                    }
                }
                
        except Exception as e:
            logger.error(f"🎯 OBSERVER ERROR: Failed to get session metrics: {e}")
            return {'error': str(e)}


# Global observer instance
observer_service = ObserverService()