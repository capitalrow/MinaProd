#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE: Live Transcription Pipeline Profiler
Real-time analysis of chunk latency, queue metrics, and system performance.
"""

import time
import json
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
import psutil
import gc

logger = logging.getLogger(__name__)

@dataclass
class ChunkMetrics:
    """Metrics for individual audio chunk processing."""
    chunk_id: str
    session_id: str
    timestamp: float
    size_bytes: int
    processing_start: float
    processing_end: Optional[float] = None
    transcription_result: Optional[str] = None
    confidence: Optional[float] = None
    filtered: bool = False
    filter_reason: Optional[str] = None
    latency_ms: Optional[float] = None
    queue_depth: int = 0
    retry_count: int = 0

@dataclass
class PipelineMetrics:
    """Overall pipeline performance metrics."""
    session_id: str
    timestamp: str
    total_chunks: int
    successful_chunks: int
    filtered_chunks: int
    failed_chunks: int
    average_latency_ms: float
    max_latency_ms: float
    min_latency_ms: float
    queue_depth_avg: float
    queue_depth_max: int
    interim_final_ratio: float
    memory_usage_mb: float
    cpu_usage_percent: float
    dropped_chunks: int
    retries_total: int
    wer_estimate: float
    duplicate_rate: float

class PipelineProfiler:
    """
    🎯 ENHANCED: Comprehensive pipeline profiling with real-time metrics.
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.chunk_history = deque(maxlen=max_history)
        self.session_metrics = {}
        self.active_chunks = {}  # Track chunks in processing
        self.queue_depths = deque(maxlen=100)
        self.latencies = deque(maxlen=100)
        self.start_time = time.time()
        
        # Performance tracking
        self.interim_count = 0
        self.final_count = 0
        self.duplicate_texts = set()
        self.recent_texts = deque(maxlen=50)
        
        # Event loop monitoring
        self.event_loop_blocks = []
        self.last_event_time = time.time()
        
        logger.info("Pipeline profiler initialized")
    
    def start_chunk_processing(self, chunk_id: str, session_id: str, size_bytes: int, queue_depth: int = 0) -> ChunkMetrics:
        """Record start of chunk processing."""
        now = time.time()
        
        metrics = ChunkMetrics(
            chunk_id=chunk_id,
            session_id=session_id,
            timestamp=now,
            size_bytes=size_bytes,
            processing_start=now,
            queue_depth=queue_depth
        )
        
        self.active_chunks[chunk_id] = metrics
        self.queue_depths.append(queue_depth)
        
        # Detect event loop blocking
        time_since_last = now - self.last_event_time
        if time_since_last > 0.1:  # >100ms indicates blocking
            self.event_loop_blocks.append({
                'timestamp': now,
                'duration_ms': time_since_last * 1000,
                'context': 'chunk_processing_start'
            })
        
        self.last_event_time = now
        return metrics
    
    def complete_chunk_processing(self, chunk_id: str, result: Optional[str] = None, 
                                confidence: Optional[float] = None, filtered: bool = False,
                                filter_reason: Optional[str] = None, retry_count: int = 0):
        """Record completion of chunk processing."""
        if chunk_id not in self.active_chunks:
            logger.warning(f"Chunk {chunk_id} not found in active chunks")
            return
        
        now = time.time()
        metrics = self.active_chunks[chunk_id]
        
        # Update metrics
        metrics.processing_end = now
        metrics.transcription_result = result
        metrics.confidence = confidence
        metrics.filtered = filtered
        metrics.filter_reason = filter_reason
        metrics.retry_count = retry_count
        metrics.latency_ms = (now - metrics.processing_start) * 1000
        
        # Track interim vs final
        if result:
            if result.endswith('.') or result.endswith('!') or result.endswith('?'):
                self.final_count += 1
            else:
                self.interim_count += 1
            
            # Duplicate detection
            if result in self.recent_texts:
                self.duplicate_texts.add(result)
            self.recent_texts.append(result)
        
        # Store and cleanup
        self.chunk_history.append(metrics)
        self.latencies.append(metrics.latency_ms)
        del self.active_chunks[chunk_id]
        
        logger.debug(f"Chunk {chunk_id} completed: {metrics.latency_ms:.1f}ms, filtered={filtered}")
    
    def get_session_metrics(self, session_id: str) -> PipelineMetrics:
        """Generate comprehensive metrics for a session."""
        # Filter chunks for this session
        session_chunks = [c for c in self.chunk_history if c.session_id == session_id]
        
        if not session_chunks:
            return self._empty_metrics(session_id)
        
        # Calculate metrics
        total_chunks = len(session_chunks)
        successful_chunks = len([c for c in session_chunks if c.transcription_result and not c.filtered])
        filtered_chunks = len([c for c in session_chunks if c.filtered])
        failed_chunks = total_chunks - successful_chunks - filtered_chunks
        
        latencies = [c.latency_ms for c in session_chunks if c.latency_ms is not None]
        queue_depths = [c.queue_depth for c in session_chunks]
        
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0
        
        avg_queue_depth = sum(queue_depths) / len(queue_depths) if queue_depths else 0
        max_queue_depth = max(queue_depths) if queue_depths else 0
        
        interim_final_ratio = self.interim_count / max(self.final_count, 1)
        
        # System metrics
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        cpu_usage = psutil.cpu_percent()
        
        # Quality metrics
        dropped_chunks = len([c for c in session_chunks if c.processing_end is None])
        total_retries = sum(c.retry_count for c in session_chunks)
        
        # WER estimation (simplified)
        wer_estimate = self._estimate_wer(session_chunks)
        duplicate_rate = len(self.duplicate_texts) / max(len(self.recent_texts), 1) * 100
        
        return PipelineMetrics(
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            total_chunks=total_chunks,
            successful_chunks=successful_chunks,
            filtered_chunks=filtered_chunks,
            failed_chunks=failed_chunks,
            average_latency_ms=avg_latency,
            max_latency_ms=max_latency,
            min_latency_ms=min_latency,
            queue_depth_avg=avg_queue_depth,
            queue_depth_max=max_queue_depth,
            interim_final_ratio=interim_final_ratio,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            dropped_chunks=dropped_chunks,
            retries_total=total_retries,
            wer_estimate=wer_estimate,
            duplicate_rate=duplicate_rate
        )
    
    def detect_event_loop_blocking(self) -> List[Dict[str, Any]]:
        """Detect Flask-SocketIO event loop blocking issues."""
        # Keep only recent blocks (last 5 minutes)
        cutoff_time = time.time() - 300
        self.event_loop_blocks = [
            block for block in self.event_loop_blocks 
            if block['timestamp'] > cutoff_time
        ]
        
        return self.event_loop_blocks
    
    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time pipeline statistics."""
        now = time.time()
        
        # Recent performance
        recent_latencies = list(self.latencies)[-20:]  # Last 20 chunks
        recent_queue_depths = list(self.queue_depths)[-10:]  # Last 10 measurements
        
        event_loop_blocks = self.detect_event_loop_blocking()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': now - self.start_time,
            'active_chunks_count': len(self.active_chunks),
            'total_chunks_processed': len(self.chunk_history),
            'current_performance': {
                'avg_latency_ms': sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0,
                'current_queue_depth': recent_queue_depths[-1] if recent_queue_depths else 0,
                'avg_queue_depth': sum(recent_queue_depths) / len(recent_queue_depths) if recent_queue_depths else 0
            },
            'quality_metrics': {
                'interim_final_ratio': self.interim_count / max(self.final_count, 1),
                'duplicate_rate_percent': len(self.duplicate_texts) / max(len(self.recent_texts), 1) * 100,
                'recent_duplicates': len(self.duplicate_texts)
            },
            'system_health': {
                'memory_usage_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_usage_percent': psutil.cpu_percent(),
                'gc_objects': len(gc.get_objects())
            },
            'event_loop_health': {
                'recent_blocks_count': len(event_loop_blocks),
                'max_block_duration_ms': max([b['duration_ms'] for b in event_loop_blocks], default=0),
                'avg_block_duration_ms': sum([b['duration_ms'] for b in event_loop_blocks]) / len(event_loop_blocks) if event_loop_blocks else 0
            }
        }
    
    def _estimate_wer(self, chunks: List[ChunkMetrics]) -> float:
        """Estimate Word Error Rate based on filtering and confidence."""
        if not chunks:
            return 0.0
        
        # Simple WER estimation based on filtering rate and confidence
        filtered_rate = len([c for c in chunks if c.filtered]) / len(chunks)
        avg_confidence = sum([c.confidence for c in chunks if c.confidence]) / len([c for c in chunks if c.confidence]) if any(c.confidence for c in chunks) else 0.8
        
        # Higher filtering rate and lower confidence suggest higher WER
        estimated_wer = (filtered_rate * 0.3) + ((1 - avg_confidence) * 0.2)
        return min(estimated_wer, 1.0)
    
    def _empty_metrics(self, session_id: str) -> PipelineMetrics:
        """Return empty metrics for sessions with no data."""
        return PipelineMetrics(
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            total_chunks=0,
            successful_chunks=0,
            filtered_chunks=0,
            failed_chunks=0,
            average_latency_ms=0,
            max_latency_ms=0,
            min_latency_ms=0,
            queue_depth_avg=0,
            queue_depth_max=0,
            interim_final_ratio=0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            dropped_chunks=0,
            retries_total=0,
            wer_estimate=0,
            duplicate_rate=0
        )
    
    def log_metrics_summary(self, session_id: str):
        """Log comprehensive metrics summary."""
        metrics = self.get_session_metrics(session_id)
        realtime = self.get_realtime_stats()
        
        logger.info(f"📊 PIPELINE METRICS [{session_id[:8]}]: "
                   f"Chunks: {metrics.total_chunks} | "
                   f"Success: {metrics.successful_chunks} | "
                   f"Filtered: {metrics.filtered_chunks} | "
                   f"Avg Latency: {metrics.average_latency_ms:.1f}ms | "
                   f"Queue Depth: {metrics.queue_depth_avg:.1f} | "
                   f"WER Est: {metrics.wer_estimate:.2%} | "
                   f"Duplicates: {metrics.duplicate_rate:.1f}%")
        
        if realtime['event_loop_health']['recent_blocks_count'] > 0:
            logger.warning(f"⚠️ EVENT LOOP BLOCKING: {realtime['event_loop_health']['recent_blocks_count']} blocks, "
                          f"max {realtime['event_loop_health']['max_block_duration_ms']:.1f}ms")
    
    def export_metrics(self, session_id: str, filename: Optional[str] = None) -> str:
        """Export detailed metrics to JSON file."""
        metrics = self.get_session_metrics(session_id)
        realtime = self.get_realtime_stats()
        
        export_data = {
            'session_metrics': asdict(metrics),
            'realtime_stats': realtime,
            'chunk_details': [asdict(c) for c in self.chunk_history if c.session_id == session_id],
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        if filename is None:
            filename = f"pipeline_metrics_{session_id[:8]}_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Metrics exported to {filename}")
        return filename

# Global profiler instance
pipeline_profiler = PipelineProfiler()

def profile_chunk_start(chunk_id: str, session_id: str, size_bytes: int, queue_depth: int = 0) -> ChunkMetrics:
    """Profile start of chunk processing."""
    return pipeline_profiler.start_chunk_processing(chunk_id, session_id, size_bytes, queue_depth)

def profile_chunk_complete(chunk_id: str, result: Optional[str] = None, 
                         confidence: Optional[float] = None, filtered: bool = False,
                         filter_reason: Optional[str] = None, retry_count: int = 0):
    """Profile completion of chunk processing."""
    pipeline_profiler.complete_chunk_processing(chunk_id, result, confidence, filtered, filter_reason, retry_count)

def get_session_metrics(session_id: str) -> PipelineMetrics:
    """Get comprehensive session metrics."""
    return pipeline_profiler.get_session_metrics(session_id)

def get_realtime_stats() -> Dict[str, Any]:
    """Get real-time pipeline statistics."""
    return pipeline_profiler.get_realtime_stats()

if __name__ == "__main__":
    # Demo/testing
    print("🔍 Pipeline Profiler Demo")
    stats = get_realtime_stats()
    print(json.dumps(stats, indent=2))