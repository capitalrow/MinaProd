"""
Performance Monitoring Service for Mina Live Transcription
Tracks pipeline metrics, latency, memory, and quality indicators
"""

import time
import psutil
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque, defaultdict
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionMetrics:
    """Real-time transcription performance metrics."""
    session_id: str
    chunk_latency_ms: List[float] = field(default_factory=list)
    queue_lengths: List[int] = field(default_factory=list)
    dropped_chunks: int = 0
    retry_count: int = 0
    interim_to_final_ratio: float = 0.0
    memory_usage_mb: List[float] = field(default_factory=list)
    cpu_usage_percent: List[float] = field(default_factory=list)
    wer_score: Optional[float] = None
    confidence_scores: List[float] = field(default_factory=list)
    dedup_effectiveness: float = 0.0
    quality_scores: List[float] = field(default_factory=list)
    text_segments: List[Dict[str, Any]] = field(default_factory=list)
    
class PerformanceMonitor:
    """Comprehensive performance monitoring for live transcription."""
    
    def __init__(self):
        self.metrics: Dict[str, TranscriptionMetrics] = {}
        self.global_metrics = {
            'total_sessions': 0,
            'active_sessions': 0,
            'avg_latency_ms': 0.0,
            'avg_queue_length': 0.0,
            'total_dropped_chunks': 0,
            'system_memory_usage': 0.0,
            'system_cpu_usage': 0.0
        }
        self.monitoring_active = True
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system resource monitoring."""
        def monitor():
            while self.monitoring_active:
                try:
                    # System metrics
                    memory = psutil.virtual_memory()
                    cpu = psutil.cpu_percent(interval=1)
                    
                    self.global_metrics.update({
                        'system_memory_usage': memory.percent,
                        'system_cpu_usage': cpu,
                        'active_sessions': len([m for m in self.metrics.values() if m])
                    })
                    
                    # Per-session memory tracking
                    for session_id, metrics in self.metrics.items():
                        if len(metrics.memory_usage_mb) < 100:  # Keep last 100 samples
                            metrics.memory_usage_mb.append(memory.percent)
                            metrics.cpu_usage_percent.append(cpu)
                        
                except Exception as e:
                    logger.error(f"Error in system monitoring: {e}")
                
                time.sleep(5)  # Monitor every 5 seconds
        
        monitoring_thread = threading.Thread(target=monitor, daemon=True)
        monitoring_thread.start()
    
    def start_session_monitoring(self, session_id: str):
        """Initialize monitoring for a new session."""
        self.metrics[session_id] = TranscriptionMetrics(session_id=session_id)
        self.global_metrics['total_sessions'] += 1
        logger.info(f"Started performance monitoring for session {session_id}")
    
    def record_chunk_latency(self, session_id: str, latency_ms: float):
        """Record processing latency for an audio chunk."""
        if session_id in self.metrics:
            metrics = self.metrics[session_id]
            metrics.chunk_latency_ms.append(latency_ms)
            
            # Keep rolling window of last 50 measurements
            if len(metrics.chunk_latency_ms) > 50:
                metrics.chunk_latency_ms.pop(0)
            
            # Update global average
            all_latencies = []
            for m in self.metrics.values():
                all_latencies.extend(m.chunk_latency_ms)
            
            if all_latencies:
                self.global_metrics['avg_latency_ms'] = sum(all_latencies) / len(all_latencies)
    
    def record_queue_length(self, session_id: str, queue_length: int):
        """Record current processing queue length."""
        if session_id in self.metrics:
            self.metrics[session_id].queue_lengths.append(queue_length)
            
            # Update global average
            all_queues = []
            for m in self.metrics.values():
                all_queues.extend(m.queue_lengths)
            
            if all_queues:
                self.global_metrics['avg_queue_length'] = sum(all_queues) / len(all_queues)
    
    def record_dropped_chunk(self, session_id: str):
        """Record a dropped/failed chunk."""
        if session_id in self.metrics:
            self.metrics[session_id].dropped_chunks += 1
            self.global_metrics['total_dropped_chunks'] += 1
    
    def record_retry(self, session_id: str):
        """Record an API retry attempt."""
        if session_id in self.metrics:
            self.metrics[session_id].retry_count += 1
    
    def record_transcription_result(self, session_id: str, success: bool, confidence: float = 0.0, text: str = ""):
        """🔥 ENHANCED: Record transcription result with comprehensive QA metrics."""
        try:
            if session_id not in self.metrics:
                self.start_session_monitoring(session_id)
            
            metrics = self.metrics[session_id]
            if success and confidence > 0:
                metrics.confidence_scores.append(confidence)
                
                # 🔥 ENHANCED: Text quality analysis
                if text:
                    quality_score = self._calculate_text_quality_score(text, confidence)
                    metrics.quality_scores.append(quality_score)
                    
                    # Store text segments for potential WER calculation
                    metrics.text_segments.append({
                        'text': text,
                        'timestamp': time.time(),
                        'confidence': confidence,
                        'quality_score': quality_score
                    })
                    
        except Exception as e:
            logger.error(f"Error recording transcription result: {e}")
    
    def _calculate_text_quality_score(self, text: str, confidence: float) -> float:
        """🔥 NEW: Calculate quality score based on text characteristics."""
        try:
            # Base score from confidence
            score = confidence
            
            # Penalize very short text (likely noise)
            words = text.split()
            if len(words) < 2:
                score *= 0.7
            
            # Penalize excessive repetition
            if len(words) > 1:
                unique_ratio = len(set(words)) / len(words)
                if unique_ratio < 0.5:  # Too much repetition
                    score *= 0.8
            
            # Bonus for proper sentence structure
            if text.strip().endswith(('.', '!', '?')):
                score = min(1.0, score * 1.05)
            
            # Penalize all caps (likely error)
            if text.isupper() and len(text) > 5:
                score *= 0.9
                
            return max(0.0, min(1.0, score))
            
        except Exception:
            return confidence
    
    def record_transcription_result(self, session_id: str, is_final: bool, confidence: float):
        """Record transcription result metrics."""
        if session_id in self.metrics:
            metrics = self.metrics[session_id]
            metrics.confidence_scores.append(confidence)
            
            # Calculate interim to final ratio
            if is_final:
                total_results = len(metrics.confidence_scores)
                # Estimate interim vs final based on typical patterns
                metrics.interim_to_final_ratio = max(0, (total_results - 1) / total_results) if total_results > 0 else 0
    
    def calculate_wer(self, session_id: str, reference_text: str, hypothesis_text: str) -> float:
        """Calculate Word Error Rate between reference and hypothesis."""
        try:
            from difflib import SequenceMatcher
            
            ref_words = reference_text.lower().split()
            hyp_words = hypothesis_text.lower().split()
            
            if not ref_words:
                return 0.0 if not hyp_words else 1.0
            
            # Simple WER approximation using sequence matching
            matcher = SequenceMatcher(None, ref_words, hyp_words)
            similarity = matcher.ratio()
            wer = 1.0 - similarity
            
            if session_id in self.metrics:
                self.metrics[session_id].wer_score = wer
            
            return wer
            
        except Exception as e:
            logger.error(f"Error calculating WER: {e}")
            return 0.0
    
    def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive performance report for a session."""
        if session_id not in self.metrics:
            return {"error": f"No metrics found for session {session_id}"}
        
        metrics = self.metrics[session_id]
        
        return {
            "session_id": session_id,
            "performance": {
                "avg_chunk_latency_ms": sum(metrics.chunk_latency_ms) / len(metrics.chunk_latency_ms) if metrics.chunk_latency_ms else 0,
                "max_chunk_latency_ms": max(metrics.chunk_latency_ms) if metrics.chunk_latency_ms else 0,
                "avg_queue_length": sum(metrics.queue_lengths) / len(metrics.queue_lengths) if metrics.queue_lengths else 0,
                "dropped_chunks": metrics.dropped_chunks,
                "retry_count": metrics.retry_count,
                "interim_to_final_ratio": metrics.interim_to_final_ratio
            },
            "quality": {
                "avg_confidence": sum(metrics.confidence_scores) / len(metrics.confidence_scores) if metrics.confidence_scores else 0,
                "wer_score": metrics.wer_score,
                "dedup_effectiveness": metrics.dedup_effectiveness
            },
            "resources": {
                "avg_memory_usage_mb": sum(metrics.memory_usage_mb) / len(metrics.memory_usage_mb) if metrics.memory_usage_mb else 0,
                "avg_cpu_usage_percent": sum(metrics.cpu_usage_percent) / len(metrics.cpu_usage_percent) if metrics.cpu_usage_percent else 0
            },
            "total_transcriptions": len(metrics.confidence_scores)
        }
    
    def get_global_dashboard(self) -> Dict[str, Any]:
        """Generate global performance dashboard data."""
        active_sessions = [s for s in self.metrics.keys() if s in self.metrics]
        
        return {
            "overview": self.global_metrics,
            "active_sessions": len(active_sessions),
            "session_details": {sid: self.get_session_report(sid) for sid in active_sessions[:10]},  # Latest 10 sessions
            "alerts": self._generate_alerts(),
            "timestamp": time.time()
        }
    
    def _generate_alerts(self) -> List[Dict[str, str]]:
        """Generate performance alerts based on thresholds."""
        alerts = []
        
        if self.global_metrics['avg_latency_ms'] > 2000:  # >2s latency
            alerts.append({
                "level": "warning",
                "message": f"High latency detected: {self.global_metrics['avg_latency_ms']:.1f}ms"
            })
        
        if self.global_metrics['avg_queue_length'] > 10:  # Queue backing up
            alerts.append({
                "level": "warning", 
                "message": f"Processing queue backing up: {self.global_metrics['avg_queue_length']:.1f} items"
            })
        
        if self.global_metrics['total_dropped_chunks'] > 0:
            alerts.append({
                "level": "error",
                "message": f"Chunks being dropped: {self.global_metrics['total_dropped_chunks']} total"
            })
        
        if self.global_metrics['system_memory_usage'] > 80:
            alerts.append({
                "level": "critical",
                "message": f"High memory usage: {self.global_metrics['system_memory_usage']:.1f}%"
            })
        
        return alerts
    
    def end_session_monitoring(self, session_id: str):
        """Clean up monitoring for ended session."""
        if session_id in self.metrics:
            # Archive the final report before cleanup
            final_report = self.get_session_report(session_id)
            logger.info(f"Session {session_id} final performance report: {json.dumps(final_report, indent=2)}")
            
            # Keep metrics for a short while for analysis
            # Could be moved to persistent storage here
            del self.metrics[session_id]
    
    def shutdown(self):
        """Shutdown performance monitoring."""
        self.monitoring_active = False
        logger.info("Performance monitoring shutdown complete")

# Global instance
performance_monitor = PerformanceMonitor()