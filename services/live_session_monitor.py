"""
Live Session Monitor - Real-time comprehensive monitoring for recording sessions
Tracks recording, transcription, quality, performance, and UI metrics in real-time
"""

import time
import logging
import threading
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import deque
import psutil

logger = logging.getLogger(__name__)

@dataclass
class LiveSessionMetrics:
    """Real-time session metrics tracking."""
    session_id: str
    start_time: float
    status: str = "initializing"
    
    # Recording metrics
    recording_duration: float = 0.0
    audio_chunks_received: int = 0
    audio_quality_scores: List[float] = field(default_factory=list)
    connection_stability: List[bool] = field(default_factory=list)
    
    # Transcription metrics
    segments_processed: int = 0
    words_transcribed: int = 0
    confidence_scores: List[float] = field(default_factory=list)
    response_times: List[float] = field(default_factory=list)
    
    # Quality metrics
    transcription_accuracy_estimate: float = 0.0
    real_time_factor: float = 0.0
    latency_ms: List[float] = field(default_factory=list)
    
    # UI/Performance metrics
    ui_updates_count: int = 0
    javascript_errors: List[str] = field(default_factory=list)
    memory_usage_mb: List[float] = field(default_factory=list)
    cpu_usage_percent: List[float] = field(default_factory=list)
    
    # Critical events
    events: List[Dict] = field(default_factory=list)

class LiveSessionMonitor:
    """Comprehensive real-time session monitoring."""
    
    def __init__(self):
        self.active_sessions: Dict[str, LiveSessionMetrics] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.is_monitoring = False
        
    def start_monitoring(self, session_id: str) -> LiveSessionMetrics:
        """🚀 Start comprehensive monitoring for a live session."""
        logger.info(f"🔍 Starting live monitoring for session {session_id}")
        
        # Initialize session metrics
        session_metrics = LiveSessionMetrics(
            session_id=session_id,
            start_time=time.time(),
            status="recording"
        )
        self.active_sessions[session_id] = session_metrics
        
        # Start monitoring thread
        monitor_thread = threading.Thread(
            target=self._monitor_session,
            args=(session_id,),
            daemon=True
        )
        monitor_thread.start()
        self.monitoring_threads[session_id] = monitor_thread
        
        # Log monitoring start
        self._log_event(session_id, "monitoring_started", {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        })
        
        return session_metrics
    
    def _monitor_session(self, session_id: str):
        """Monitor session in real-time."""
        metrics = self.active_sessions[session_id]
        self.is_monitoring = True
        
        while self.is_monitoring and session_id in self.active_sessions:
            try:
                # Update performance metrics
                self._update_performance_metrics(session_id)
                
                # Update recording metrics
                self._update_recording_metrics(session_id)
                
                # Check system health
                self._check_system_health(session_id)
                
                # Log real-time status
                self._log_real_time_status(session_id)
                
                time.sleep(1)  # Monitor every second
                
            except Exception as e:
                logger.error(f"Monitoring error for session {session_id}: {e}")
                self._log_event(session_id, "monitoring_error", {"error": str(e)})
    
    def _update_performance_metrics(self, session_id: str):
        """Update system performance metrics."""
        if session_id not in self.active_sessions:
            return
            
        metrics = self.active_sessions[session_id]
        
        # CPU and memory usage
        process = psutil.Process()
        cpu_percent = process.cpu_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        metrics.cpu_usage_percent.append(cpu_percent)
        metrics.memory_usage_mb.append(memory_mb)
        
        # Keep only last 60 measurements (1 minute)
        if len(metrics.cpu_usage_percent) > 60:
            metrics.cpu_usage_percent.pop(0)
        if len(metrics.memory_usage_mb) > 60:
            metrics.memory_usage_mb.pop(0)
    
    def _update_recording_metrics(self, session_id: str):
        """Update recording-specific metrics."""
        if session_id not in self.active_sessions:
            return
            
        metrics = self.active_sessions[session_id]
        metrics.recording_duration = time.time() - metrics.start_time
    
    def _check_system_health(self, session_id: str):
        """Check overall system health."""
        if session_id not in self.active_sessions:
            return
            
        metrics = self.active_sessions[session_id]
        
        # Check for performance issues
        if metrics.memory_usage_mb and metrics.memory_usage_mb[-1] > 100:
            self._log_event(session_id, "high_memory_usage", {
                "memory_mb": metrics.memory_usage_mb[-1]
            })
        
        if metrics.cpu_usage_percent and metrics.cpu_usage_percent[-1] > 80:
            self._log_event(session_id, "high_cpu_usage", {
                "cpu_percent": metrics.cpu_usage_percent[-1]
            })
    
    def _log_real_time_status(self, session_id: str):
        """Log real-time session status."""
        if session_id not in self.active_sessions:
            return
            
        metrics = self.active_sessions[session_id]
        
        status_update = {
            "session_id": session_id,
            "duration": metrics.recording_duration,
            "segments": metrics.segments_processed,
            "words": metrics.words_transcribed,
            "audio_chunks": metrics.audio_chunks_received,
            "avg_confidence": sum(metrics.confidence_scores) / max(1, len(metrics.confidence_scores)) if metrics.confidence_scores else 0,
            "memory_mb": metrics.memory_usage_mb[-1] if metrics.memory_usage_mb else 0,
            "cpu_percent": metrics.cpu_usage_percent[-1] if metrics.cpu_usage_percent else 0
        }
        
        logger.info(f"📊 Live Status [{session_id}]: {json.dumps(status_update)}")
    
    def record_audio_chunk(self, session_id: str, chunk_size: int, quality_score: float = 0.0):
        """Record incoming audio chunk."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            metrics.audio_chunks_received += 1
            if quality_score > 0:
                metrics.audio_quality_scores.append(quality_score)
            
            self._log_event(session_id, "audio_chunk_received", {
                "chunk_number": metrics.audio_chunks_received,
                "size": chunk_size,
                "quality": quality_score
            })
    
    def record_transcription_result(self, session_id: str, text: str, confidence: float, is_final: bool = True):
        """Record transcription result."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            
            if is_final:
                metrics.segments_processed += 1
                word_count = len(text.split()) if text else 0
                metrics.words_transcribed += word_count
            
            metrics.confidence_scores.append(confidence)
            
            # Calculate response time (from session start)
            response_time = time.time() - metrics.start_time
            metrics.response_times.append(response_time)
            
            self._log_event(session_id, "transcription_result", {
                "text": text,
                "confidence": confidence,
                "is_final": is_final,
                "word_count": len(text.split()) if text else 0,
                "response_time": response_time
            })
            
            logger.info(f"📝 Transcription [{session_id}]: '{text}' (confidence: {confidence:.2f})")
    
    def record_connection_event(self, session_id: str, event_type: str, is_connected: bool):
        """Record WebSocket connection event."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            metrics.connection_stability.append(is_connected)
            
            self._log_event(session_id, "connection_event", {
                "event_type": event_type,
                "connected": is_connected
            })
    
    def record_ui_update(self, session_id: str, update_type: str, data: Any = None):
        """Record UI update event."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            metrics.ui_updates_count += 1
            
            self._log_event(session_id, "ui_update", {
                "update_type": update_type,
                "data": data,
                "total_updates": metrics.ui_updates_count
            })
    
    def record_javascript_error(self, session_id: str, error_message: str, stack_trace: str = ""):
        """Record JavaScript error."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            metrics.javascript_errors.append(error_message)
            
            self._log_event(session_id, "javascript_error", {
                "error": error_message,
                "stack": stack_trace,
                "total_errors": len(metrics.javascript_errors)
            })
            
            logger.warning(f"🚨 JS Error [{session_id}]: {error_message}")
    
    def record_latency(self, session_id: str, latency_ms: float):
        """Record processing latency."""
        if session_id in self.active_sessions:
            metrics = self.active_sessions[session_id]
            metrics.latency_ms.append(latency_ms)
            
            # Keep only last 100 measurements
            if len(metrics.latency_ms) > 100:
                metrics.latency_ms.pop(0)
    
    def _log_event(self, session_id: str, event_type: str, data: Dict):
        """Log session event."""
        if session_id in self.active_sessions:
            event = {
                "timestamp": time.time(),
                "event_type": event_type,
                "data": data
            }
            self.active_sessions[session_id].events.append(event)
    
    def get_live_metrics(self, session_id: str) -> Optional[Dict]:
        """Get current live metrics for a session."""
        if session_id not in self.active_sessions:
            return None
        
        metrics = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "status": metrics.status,
            "duration": metrics.recording_duration,
            "audio_chunks": metrics.audio_chunks_received,
            "segments_processed": metrics.segments_processed,
            "words_transcribed": metrics.words_transcribed,
            "avg_confidence": sum(metrics.confidence_scores) / max(1, len(metrics.confidence_scores)) if metrics.confidence_scores else 0,
            "avg_latency_ms": sum(metrics.latency_ms) / max(1, len(metrics.latency_ms)) if metrics.latency_ms else 0,
            "current_memory_mb": metrics.memory_usage_mb[-1] if metrics.memory_usage_mb else 0,
            "current_cpu_percent": metrics.cpu_usage_percent[-1] if metrics.cpu_usage_percent else 0,
            "javascript_errors": len(metrics.javascript_errors),
            "connection_stability": sum(metrics.connection_stability) / max(1, len(metrics.connection_stability)) * 100 if metrics.connection_stability else 0,
            "ui_updates": metrics.ui_updates_count,
            "real_time_factor": self._calculate_real_time_factor(metrics)
        }
    
    def _calculate_real_time_factor(self, metrics: LiveSessionMetrics) -> float:
        """Calculate real-time processing factor."""
        if not metrics.response_times or metrics.recording_duration <= 0:
            return 0.0
        
        # Real-time factor = processing_time / audio_duration
        # Lower is better (< 1.0 means faster than real-time)
        avg_processing_time = sum(metrics.response_times) / len(metrics.response_times)
        return avg_processing_time / metrics.recording_duration
    
    def end_monitoring(self, session_id: str) -> Dict:
        """End monitoring and generate final report."""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        metrics = self.active_sessions[session_id]
        metrics.status = "completed"
        
        # Generate comprehensive report
        final_report = {
            "session_id": session_id,
            "start_time": datetime.fromtimestamp(metrics.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_duration": metrics.recording_duration,
            
            # Performance summary
            "performance": {
                "audio_chunks_received": metrics.audio_chunks_received,
                "segments_processed": metrics.segments_processed,
                "words_transcribed": metrics.words_transcribed,
                "avg_confidence": sum(metrics.confidence_scores) / max(1, len(metrics.confidence_scores)) if metrics.confidence_scores else 0,
                "avg_latency_ms": sum(metrics.latency_ms) / max(1, len(metrics.latency_ms)) if metrics.latency_ms else 0,
                "real_time_factor": self._calculate_real_time_factor(metrics),
                "words_per_minute": (metrics.words_transcribed / max(1, metrics.recording_duration / 60)) if metrics.recording_duration > 0 else 0
            },
            
            # Quality assessment
            "quality": {
                "transcription_confidence": sum(metrics.confidence_scores) / max(1, len(metrics.confidence_scores)) if metrics.confidence_scores else 0,
                "connection_stability": sum(metrics.connection_stability) / max(1, len(metrics.connection_stability)) * 100 if metrics.connection_stability else 0,
                "javascript_errors": len(metrics.javascript_errors),
                "ui_responsiveness": metrics.ui_updates_count
            },
            
            # Resource usage
            "resources": {
                "avg_memory_mb": sum(metrics.memory_usage_mb) / max(1, len(metrics.memory_usage_mb)) if metrics.memory_usage_mb else 0,
                "peak_memory_mb": max(metrics.memory_usage_mb) if metrics.memory_usage_mb else 0,
                "avg_cpu_percent": sum(metrics.cpu_usage_percent) / max(1, len(metrics.cpu_usage_percent)) if metrics.cpu_usage_percent else 0,
                "peak_cpu_percent": max(metrics.cpu_usage_percent) if metrics.cpu_usage_percent else 0
            },
            
            # Events summary
            "events_count": len(metrics.events),
            "status": "completed"
        }
        
        # Cleanup
        self.is_monitoring = False
        if session_id in self.monitoring_threads:
            del self.monitoring_threads[session_id]
        del self.active_sessions[session_id]
        
        logger.info(f"✅ Live monitoring completed for session {session_id}")
        logger.info(f"📊 Final Report: {json.dumps(final_report, indent=2)}")
        
        return final_report
    
    def get_all_active_sessions(self) -> List[str]:
        """Get list of all active monitoring sessions."""
        return list(self.active_sessions.keys())

# Global monitor instance
live_monitor = LiveSessionMonitor()