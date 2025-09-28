#!/usr/bin/env python3
"""
Real-time Performance Monitor for Mina Live Transcription System
Provides structured logging and performance tracking
"""

import json
import time
import logging
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict, deque
import psutil
import os

# Enhanced logging configuration
class StructuredLogger:
    """Structured JSON logger for performance tracking"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for structured logs
        file_handler = logging.FileHandler('mina_performance.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def log_request(self, request_id: str, session_id: str, action: str, 
                   latency_ms: float, success: bool, **kwargs):
        """Log structured request data"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_id,
            'session_id': session_id,
            'action': action,
            'latency_ms': round(latency_ms, 2),
            'success': success,
            **kwargs
        }
        
        self.logger.info(f"REQUEST: {json.dumps(log_data)}")
    
    def log_session_metrics(self, session_id: str, metrics: Dict):
        """Log session-level metrics"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'type': 'session_metrics',
            **metrics
        }
        
        self.logger.info(f"SESSION: {json.dumps(log_data)}")
    
    def log_system_metrics(self, metrics: Dict):
        """Log system resource metrics"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'type': 'system_metrics',
            **metrics
        }
        
        self.logger.info(f"SYSTEM: {json.dumps(log_data)}")

@dataclass
class RequestMetrics:
    """Individual request performance metrics"""
    request_id: str
    session_id: str
    timestamp: datetime
    action: str
    latency_ms: float
    success: bool
    audio_size_bytes: int = 0
    transcribed_words: int = 0
    confidence_score: float = 0.0
    error_message: str = ""

@dataclass
class SessionMetrics:
    """Session-level performance metrics"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    total_audio_bytes: int = 0
    total_words: int = 0
    average_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    error_count: int = 0
    last_activity: Optional[datetime] = None

class PerformanceMonitor:
    """Real-time performance monitoring system"""
    
    def __init__(self):
        self.logger = StructuredLogger('MinaPerformance')
        self.sessions: Dict[str, SessionMetrics] = {}
        self.request_history: deque = deque(maxlen=1000)  # Keep last 1000 requests
        self.system_metrics_history: deque = deque(maxlen=100)  # Keep last 100 system snapshots
        
        # Performance tracking
        self.latency_buckets = defaultdict(int)  # For latency distribution
        self.error_patterns = defaultdict(int)
        
        # Start background monitoring
        self.monitoring_active = True
        self.system_monitor_thread = threading.Thread(target=self._monitor_system_resources, daemon=True)
        self.system_monitor_thread.start()
        
        self.logger.logger.info("🚀 Performance Monitor initialized")
    
    def start_request(self, request_id: str, session_id: str, action: str) -> float:
        """Start tracking a request and return start time"""
        start_time = time.time()
        
        # Ensure session exists
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionMetrics(
                session_id=session_id,
                start_time=datetime.now()
            )
        
        return start_time
    
    def end_request(self, request_id: str, session_id: str, action: str, 
                   start_time: float, success: bool, **kwargs):
        """End request tracking and log metrics"""
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Create request metrics
        request_metrics = RequestMetrics(
            request_id=request_id,
            session_id=session_id,
            timestamp=datetime.now(),
            action=action,
            latency_ms=latency_ms,
            success=success,
            **kwargs
        )
        
        # Add to history
        self.request_history.append(request_metrics)
        
        # Update session metrics
        self._update_session_metrics(session_id, request_metrics)
        
        # Update latency distribution
        latency_bucket = self._get_latency_bucket(latency_ms)
        self.latency_buckets[latency_bucket] += 1
        
        # Track error patterns
        if not success and kwargs.get('error_message'):
            self.error_patterns[kwargs['error_message']] += 1
        
        # Log structured data
        self.logger.log_request(
            request_id=request_id,
            session_id=session_id,
            action=action,
            latency_ms=latency_ms,
            success=success,
            **kwargs
        )
        
        return request_metrics
    
    def _update_session_metrics(self, session_id: str, request_metrics: RequestMetrics):
        """Update session-level metrics"""
        session = self.sessions[session_id]
        
        session.total_requests += 1
        session.last_activity = request_metrics.timestamp
        
        if request_metrics.success:
            session.successful_requests += 1
        else:
            session.error_count += 1
        
        # Update latency metrics
        latency = request_metrics.latency_ms
        session.max_latency_ms = max(session.max_latency_ms, latency)
        session.min_latency_ms = min(session.min_latency_ms, latency)
        
        # Calculate rolling average latency
        recent_successful = [r for r in self.request_history 
                           if r.session_id == session_id and r.success]
        if recent_successful:
            session.average_latency_ms = sum(r.latency_ms for r in recent_successful) / len(recent_successful)
        
        # Update totals
        session.total_audio_bytes += request_metrics.audio_size_bytes
        session.total_words += request_metrics.transcribed_words
    
    def _get_latency_bucket(self, latency_ms: float) -> str:
        """Categorize latency into buckets for distribution analysis"""
        if latency_ms < 500:
            return "<500ms"
        elif latency_ms < 1000:
            return "500-1000ms"
        elif latency_ms < 2000:
            return "1-2s"
        elif latency_ms < 5000:
            return "2-5s"
        else:
            return ">5s"
    
    def _monitor_system_resources(self):
        """Background thread to monitor system resources"""
        while self.monitoring_active:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking CPU sampling
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get process-specific metrics
                process = psutil.Process(os.getpid())
                process_memory = process.memory_info().rss / 1024 / 1024  # MB
                process_cpu = process.cpu_percent()
                
                system_metrics = {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available_gb': memory.available / 1024 / 1024 / 1024,
                    'disk_free_gb': disk.free / 1024 / 1024 / 1024,
                    'process_memory_mb': process_memory,
                    'process_cpu_percent': process_cpu,
                    'active_sessions': len(self.sessions),
                    'requests_last_minute': len([r for r in self.request_history 
                                               if (datetime.now() - r.timestamp).seconds < 60])
                }
                
                self.system_metrics_history.append({
                    'timestamp': datetime.now(),
                    **system_metrics
                })
                
                # Log system metrics every 30 seconds
                if len(self.system_metrics_history) % 6 == 0:  # Every 6th sample (30 seconds)
                    self.logger.log_system_metrics(system_metrics)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.logger.error(f"System monitoring error: {e}")
                time.sleep(10)  # Wait longer on error
    
    def get_session_summary(self, session_id: str) -> Optional[Dict]:
        """Get comprehensive session summary"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Calculate session duration
        end_time = session.end_time or session.last_activity or datetime.now()
        duration_seconds = (end_time - session.start_time).total_seconds()
        
        # Get session requests
        session_requests = [r for r in self.request_history if r.session_id == session_id]
        
        # Calculate success rate
        success_rate = (session.successful_requests / session.total_requests * 100) if session.total_requests > 0 else 0
        
        summary = {
            'session_id': session_id,
            'duration_seconds': duration_seconds,
            'total_requests': session.total_requests,
            'successful_requests': session.successful_requests,
            'success_rate_percent': round(success_rate, 2),
            'total_words': session.total_words,
            'total_audio_mb': round(session.total_audio_bytes / 1024 / 1024, 2),
            'average_latency_ms': round(session.average_latency_ms, 2),
            'min_latency_ms': round(session.min_latency_ms, 2) if session.min_latency_ms != float('inf') else 0,
            'max_latency_ms': round(session.max_latency_ms, 2),
            'words_per_minute': round((session.total_words / duration_seconds * 60), 2) if duration_seconds > 0 else 0,
            'requests_per_minute': round((session.total_requests / duration_seconds * 60), 2) if duration_seconds > 0 else 0,
            'error_count': session.error_count,
            'start_time': session.start_time.isoformat(),
            'last_activity': session.last_activity.isoformat() if session.last_activity else None
        }
        
        return summary
    
    def get_system_health(self) -> Dict:
        """Get current system health metrics"""
        if not self.system_metrics_history:
            return {'status': 'no_data'}
        
        latest = self.system_metrics_history[-1]
        
        # Calculate health status
        health_score = 100
        issues = []
        
        if latest['cpu_percent'] > 80:
            health_score -= 20
            issues.append('High CPU usage')
        
        if latest['memory_percent'] > 90:
            health_score -= 25
            issues.append('High memory usage')
        
        if latest['process_memory_mb'] > 1000:  # 1GB
            health_score -= 15
            issues.append('High process memory usage')
        
        # Check recent error rate
        recent_requests = [r for r in self.request_history 
                         if (datetime.now() - r.timestamp).seconds < 300]  # Last 5 minutes
        if recent_requests:
            error_rate = len([r for r in recent_requests if not r.success]) / len(recent_requests) * 100
            if error_rate > 10:
                health_score -= 30
                issues.append(f'High error rate: {error_rate:.1f}%')
        
        status = 'healthy' if health_score >= 80 else 'degraded' if health_score >= 60 else 'unhealthy'
        
        return {
            'status': status,
            'health_score': max(0, health_score),
            'issues': issues,
            'system_metrics': {k: v for k, v in latest.items() if k != 'timestamp'},
            'timestamp': latest['timestamp'].isoformat()
        }
    
    def get_performance_summary(self) -> Dict:
        """Get overall performance summary"""
        if not self.request_history:
            return {'status': 'no_data'}
        
        recent_requests = list(self.request_history)[-100:]  # Last 100 requests
        successful_requests = [r for r in recent_requests if r.success]
        
        # Calculate metrics
        total_requests = len(recent_requests)
        success_rate = len(successful_requests) / total_requests * 100 if total_requests > 0 else 0
        
        latencies = [r.latency_ms for r in successful_requests]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Get P95 latency (approximation)
        sorted_latencies = sorted(latencies)
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0
        
        return {
            'recent_requests_analyzed': total_requests,
            'success_rate_percent': round(success_rate, 2),
            'average_latency_ms': round(avg_latency, 2),
            'p95_latency_ms': round(p95_latency, 2),
            'active_sessions': len(self.sessions),
            'latency_distribution': dict(self.latency_buckets),
            'top_errors': dict(list(self.error_patterns.items())[:5]),
            'timestamp': datetime.now().isoformat()
        }
    
    def finalize_session(self, session_id: str):
        """Mark session as completed and log final metrics"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.end_time = datetime.now()
            
            summary = self.get_session_summary(session_id)
            if summary:
                self.logger.log_session_metrics(session_id, summary)
    
    def shutdown(self):
        """Gracefully shutdown the performance monitor"""
        self.monitoring_active = False
        if self.system_monitor_thread.is_alive():
            self.system_monitor_thread.join(timeout=5)
        
        self.logger.logger.info("📊 Performance Monitor shutdown complete")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Decorator for easy request tracking
def track_performance(action: str):
    """Decorator to automatically track request performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import uuid
            
            request_id = str(uuid.uuid4())[:8]
            session_id = kwargs.get('session_id', 'unknown')
            
            start_time = performance_monitor.start_request(request_id, session_id, action)
            
            try:
                result = func(*args, **kwargs)
                
                # Extract metrics from result if available
                metrics = {}
                if isinstance(result, dict):
                    metrics.update({
                        'audio_size_bytes': kwargs.get('audio_size', 0),
                        'transcribed_words': len(result.get('text', '').split()) if result.get('text') else 0,
                        'confidence_score': result.get('confidence', 0.0)
                    })
                
                performance_monitor.end_request(
                    request_id, session_id, action, start_time, True, **metrics
                )
                
                return result
                
            except Exception as e:
                performance_monitor.end_request(
                    request_id, session_id, action, start_time, False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test the performance monitor
    print("🧪 Testing Performance Monitor...")
    
    import time
    import random
    
    # Simulate some requests
    for i in range(10):
        request_id = f"test_{i}"
        session_id = f"session_{random.randint(1, 3)}"
        
        start_time = performance_monitor.start_request(request_id, session_id, "transcribe")
        
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))
        
        success = random.choice([True, True, True, False])  # 75% success rate
        
        performance_monitor.end_request(
            request_id, session_id, "transcribe", start_time, success,
            audio_size_bytes=random.randint(1000, 5000),
            transcribed_words=random.randint(0, 10) if success else 0,
            confidence_score=random.uniform(0.8, 0.99) if success else 0.0,
            error_message="Test error" if not success else ""
        )
    
    # Print summary
    print("\n📊 Performance Summary:")
    summary = performance_monitor.get_performance_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n🏥 System Health:")
    health = performance_monitor.get_system_health()
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    performance_monitor.shutdown()