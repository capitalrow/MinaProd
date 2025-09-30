#!/usr/bin/env python3
"""
🔍 Mina Live Transcription Pipeline Profiler
Comprehensive analysis of transcription pipeline performance, latency, and quality metrics.
"""

import time
import json
import psutil
import logging
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np

@dataclass
class PipelineMetrics:
    """Real-time pipeline performance metrics."""
    # Latency metrics
    chunk_latency_ms: List[float]
    e2e_latency_ms: List[float]  # End-to-end: audio capture → transcript display
    
    # Queue and throughput
    queue_length_samples: List[int]
    chunks_processed: int
    chunks_dropped: int
    chunks_retried: int
    
    # Transcription quality
    interim_events: int
    final_events: int
    interim_to_final_ratio: float
    avg_confidence: float
    
    # System resources
    cpu_usage_pct: List[float]
    memory_usage_mb: List[float]
    
    # Error tracking
    websocket_errors: int
    transcription_errors: int
    session_errors: int
    
    # Quality filters
    dedupe_hits: int
    low_conf_suppressed: int
    repetitive_filtered: int

class PipelineProfiler:
    """Live pipeline performance profiler."""
    
    def __init__(self):
        self.metrics = PipelineMetrics(
            chunk_latency_ms=[],
            e2e_latency_ms=[],
            queue_length_samples=[],
            chunks_processed=0,
            chunks_dropped=0,
            chunks_retried=0,
            interim_events=0,
            final_events=0,
            interim_to_final_ratio=0.0,
            avg_confidence=0.0,
            cpu_usage_pct=[],
            memory_usage_mb=[],
            websocket_errors=0,
            transcription_errors=0,
            session_errors=0,
            dedupe_hits=0,
            low_conf_suppressed=0,
            repetitive_filtered=0
        )
        
        self.session_start_times = {}  # session_id -> start_time
        self.chunk_start_times = {}   # chunk_id -> start_time
        self.confidence_samples = deque(maxlen=100)
        
        self.monitoring = False
        self.monitor_thread = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start real-time system monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._system_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.logger.info("🔍 Pipeline profiler started")
    
    def stop_monitoring(self):
        """Stop monitoring and generate report."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        self.logger.info("⏹️ Pipeline profiler stopped")
        return self.generate_report()
    
    def _system_monitor_loop(self):
        """Monitor system resources continuously."""
        while self.monitoring:
            try:
                # CPU usage
                cpu_pct = psutil.cpu_percent(interval=0.1)
                self.metrics.cpu_usage_pct.append(cpu_pct)
                
                # Memory usage  
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)
                self.metrics.memory_usage_mb.append(memory_mb)
                
                # Keep rolling window
                if len(self.metrics.cpu_usage_pct) > 300:  # 30 seconds at 0.1s intervals
                    self.metrics.cpu_usage_pct.pop(0)
                if len(self.metrics.memory_usage_mb) > 300:
                    self.metrics.memory_usage_mb.pop(0)
                    
                time.sleep(0.1)  # 100ms monitoring interval
                
            except Exception as e:
                self.logger.error(f"System monitoring error: {e}")
                time.sleep(1)
    
    # Event tracking methods
    def track_chunk_start(self, chunk_id: str, session_id: str):
        """Track start of audio chunk processing."""
        self.chunk_start_times[chunk_id] = time.time()
    
    def track_chunk_complete(self, chunk_id: str, queue_length: int):
        """Track completion of chunk processing."""
        if chunk_id in self.chunk_start_times:
            latency_ms = (time.time() - self.chunk_start_times[chunk_id]) * 1000
            self.metrics.chunk_latency_ms.append(latency_ms)
            del self.chunk_start_times[chunk_id]
        
        self.metrics.queue_length_samples.append(queue_length)
        self.metrics.chunks_processed += 1
    
    def track_chunk_dropped(self):
        """Track dropped chunk."""
        self.metrics.chunks_dropped += 1
    
    def track_chunk_retry(self):
        """Track chunk retry."""
        self.metrics.chunks_retried += 1
    
    def track_interim_event(self, confidence: float):
        """Track interim transcript event."""
        self.metrics.interim_events += 1
        self.confidence_samples.append(confidence)
        self._update_confidence_avg()
    
    def track_final_event(self, confidence: float):
        """Track final transcript event."""
        self.metrics.final_events += 1
        self.confidence_samples.append(confidence)
        self._update_confidence_avg()
        
        # Update interim-to-final ratio
        if self.metrics.final_events > 0:
            self.metrics.interim_to_final_ratio = self.metrics.interim_events / self.metrics.final_events
    
    def track_websocket_error(self):
        """Track WebSocket error."""
        self.metrics.websocket_errors += 1
    
    def track_transcription_error(self):
        """Track transcription processing error."""
        self.metrics.transcription_errors += 1
    
    def track_session_error(self):
        """Track session management error."""
        self.metrics.session_errors += 1
    
    def track_quality_filter(self, filter_type: str):
        """Track quality filter application."""
        if filter_type == 'dedupe':
            self.metrics.dedupe_hits += 1
        elif filter_type == 'low_confidence':
            self.metrics.low_conf_suppressed += 1
        elif filter_type == 'repetitive':
            self.metrics.repetitive_filtered += 1
    
    def _update_confidence_avg(self):
        """Update rolling average confidence."""
        if self.confidence_samples:
            self.metrics.avg_confidence = sum(self.confidence_samples) / len(self.confidence_samples)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            'timestamp': time.time(),
            'summary': self._generate_summary(),
            'performance': self._analyze_performance(),
            'quality': self._analyze_quality(),
            'errors': self._analyze_errors(),
            'recommendations': self._generate_recommendations(),
            'raw_metrics': asdict(self.metrics)
        }
        
        return report
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate high-level summary."""
        total_events = self.metrics.interim_events + self.metrics.final_events
        
        return {
            'total_chunks_processed': self.metrics.chunks_processed,
            'total_transcription_events': total_events,
            'interim_events': self.metrics.interim_events,
            'final_events': self.metrics.final_events,
            'success_rate': (self.metrics.chunks_processed / max(1, self.metrics.chunks_processed + self.metrics.chunks_dropped)) * 100,
            'avg_confidence': round(self.metrics.avg_confidence, 3),
            'interim_to_final_ratio': round(self.metrics.interim_to_final_ratio, 2)
        }
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics."""
        chunk_latencies = self.metrics.chunk_latency_ms
        queue_lengths = self.metrics.queue_length_samples
        cpu_usage = self.metrics.cpu_usage_pct
        memory_usage = self.metrics.memory_usage_mb
        
        return {
            'latency': {
                'chunk_p50_ms': np.percentile(chunk_latencies, 50) if chunk_latencies else 0,
                'chunk_p95_ms': np.percentile(chunk_latencies, 95) if chunk_latencies else 0,
                'chunk_p99_ms': np.percentile(chunk_latencies, 99) if chunk_latencies else 0,
                'avg_chunk_latency_ms': np.mean(chunk_latencies) if chunk_latencies else 0
            },
            'throughput': {
                'chunks_per_second': self.metrics.chunks_processed / max(1, len(chunk_latencies) * 0.3),  # Estimate
                'queue_p95_length': np.percentile(queue_lengths, 95) if queue_lengths else 0,
                'avg_queue_length': np.mean(queue_lengths) if queue_lengths else 0
            },
            'resources': {
                'avg_cpu_pct': np.mean(cpu_usage) if cpu_usage else 0,
                'peak_cpu_pct': np.max(cpu_usage) if cpu_usage else 0,
                'avg_memory_mb': np.mean(memory_usage) if memory_usage else 0,
                'peak_memory_mb': np.max(memory_usage) if memory_usage else 0
            }
        }
    
    def _analyze_quality(self) -> Dict[str, Any]:
        """Analyze transcription quality metrics."""
        total_filtered = self.metrics.dedupe_hits + self.metrics.low_conf_suppressed + self.metrics.repetitive_filtered
        total_chunks = self.metrics.chunks_processed
        
        return {
            'filtering': {
                'total_filtered': total_filtered,
                'filter_rate_pct': (total_filtered / max(1, total_chunks)) * 100,
                'dedupe_hits': self.metrics.dedupe_hits,
                'low_conf_suppressed': self.metrics.low_conf_suppressed,
                'repetitive_filtered': self.metrics.repetitive_filtered
            },
            'confidence': {
                'avg_confidence': self.metrics.avg_confidence,
                'confidence_samples': len(self.confidence_samples)
            },
            'flow': {
                'interim_events': self.metrics.interim_events,
                'final_events': self.metrics.final_events,
                'interim_to_final_ratio': self.metrics.interim_to_final_ratio
            }
        }
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns."""
        total_errors = self.metrics.websocket_errors + self.metrics.transcription_errors + self.metrics.session_errors
        
        return {
            'total_errors': total_errors,
            'websocket_errors': self.metrics.websocket_errors,
            'transcription_errors': self.metrics.transcription_errors,
            'session_errors': self.metrics.session_errors,
            'dropped_chunks': self.metrics.chunks_dropped,
            'retried_chunks': self.metrics.chunks_retried
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Latency analysis
        if self.metrics.chunk_latency_ms:
            avg_latency = np.mean(self.metrics.chunk_latency_ms)
            if avg_latency > 2000:  # >2s latency
                recommendations.append("🚨 High chunk latency detected (>2s). Consider optimizing Whisper API calls or reducing chunk size.")
        
        # Queue length analysis
        if self.metrics.queue_length_samples:
            avg_queue = np.mean(self.metrics.queue_length_samples)
            if avg_queue > 5:
                recommendations.append("⚠️ High queue length detected. Consider increasing processing concurrency.")
        
        # Error rate analysis
        if self.metrics.chunks_dropped > 0:
            drop_rate = self.metrics.chunks_dropped / max(1, self.metrics.chunks_processed) * 100
            if drop_rate > 5:
                recommendations.append(f"🚨 High chunk drop rate ({drop_rate:.1f}%). Check network stability and API rate limits.")
        
        # Quality filter analysis
        total_filtered = self.metrics.dedupe_hits + self.metrics.low_conf_suppressed + self.metrics.repetitive_filtered
        if total_filtered > 0:
            filter_rate = total_filtered / max(1, self.metrics.chunks_processed) * 100
            if filter_rate > 20:
                recommendations.append(f"⚠️ High quality filter rate ({filter_rate:.1f}%). Review confidence thresholds and deduplication logic.")
        
        # Interim/final ratio analysis
        if self.metrics.interim_to_final_ratio > 10:
            recommendations.append("⚠️ High interim-to-final ratio. Consider adjusting interim throttling.")
        elif self.metrics.interim_to_final_ratio < 2:
            recommendations.append("ℹ️ Low interim-to-final ratio. Users may experience less responsive transcription.")
        
        # Resource usage
        if self.metrics.cpu_usage_pct:
            avg_cpu = np.mean(self.metrics.cpu_usage_pct)
            if avg_cpu > 80:
                recommendations.append("🚨 High CPU usage detected. Consider optimizing audio processing or scaling horizontally.")
        
        if not recommendations:
            recommendations.append("✅ Pipeline performance looks healthy.")
        
        return recommendations

# Global profiler instance
profiler = PipelineProfiler()

def start_profiling():
    """Start pipeline profiling."""
    profiler.start_monitoring()

def stop_profiling_and_report():
    """Stop profiling and return report."""
    return profiler.stop_monitoring()

def track_event(event_type: str, **kwargs):
    """Track pipeline event."""
    if event_type == 'chunk_start':
        profiler.track_chunk_start(kwargs.get('chunk_id'), kwargs.get('session_id'))
    elif event_type == 'chunk_complete':
        profiler.track_chunk_complete(kwargs.get('chunk_id'), kwargs.get('queue_length', 0))
    elif event_type == 'chunk_dropped':
        profiler.track_chunk_dropped()
    elif event_type == 'interim':
        profiler.track_interim_event(kwargs.get('confidence', 0.0))
    elif event_type == 'final':
        profiler.track_final_event(kwargs.get('confidence', 0.0))
    elif event_type == 'websocket_error':
        profiler.track_websocket_error()
    elif event_type == 'transcription_error':
        profiler.track_transcription_error()
    elif event_type == 'session_error':
        profiler.track_session_error()
    elif event_type == 'quality_filter':
        profiler.track_quality_filter(kwargs.get('filter_type'))

if __name__ == '__main__':
    # Demo/test mode
    print("🔍 Mina Pipeline Profiler - Demo Mode")
    
    profiler = PipelineProfiler()
    profiler.start_monitoring()
    
    # Simulate some events
    import random
    for i in range(10):
        chunk_id = f"chunk_{i}"
        profiler.track_chunk_start(chunk_id, "test_session")
        time.sleep(random.uniform(0.1, 0.5))  # Simulate processing
        profiler.track_chunk_complete(chunk_id, random.randint(0, 3))
        
        if random.random() < 0.3:  # 30% interim events
            profiler.track_interim_event(random.uniform(0.4, 0.9))
        if random.random() < 0.1:  # 10% final events
            profiler.track_final_event(random.uniform(0.6, 0.95))
    
    time.sleep(2)
    
    report = profiler.stop_monitoring()
    print(json.dumps(report, indent=2))