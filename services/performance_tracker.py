# 🚀 **FIX PACK 2: Performance Optimization Components**

import time
import threading
import queue
import psutil
import gc
from collections import defaultdict, deque
from contextlib import contextmanager
from typing import Dict, Any, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Advanced performance monitoring and optimization system."""
    
    def __init__(self):
        self.operation_metrics = defaultdict(list)
        self.latency_percentiles = {}
        self.memory_samples = deque(maxlen=1000)
        self.cpu_samples = deque(maxlen=1000)
        self.lock = threading.RLock()
        
    @contextmanager
    def track_operation(self, operation_name: str, context_id: str):
        """Track performance metrics for a specific operation."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = (end_time - start_time) * 1000  # Convert to ms
            memory_delta = end_memory - start_memory
            
            with self.lock:
                self.operation_metrics[operation_name].append({
                    'duration_ms': duration,
                    'memory_delta_bytes': memory_delta,
                    'timestamp': end_time,
                    'context_id': context_id
                })
                
                # Keep only recent metrics (last 1000)
                if len(self.operation_metrics[operation_name]) > 1000:
                    self.operation_metrics[operation_name].pop(0)
                
                # Update percentiles every 100 operations
                if len(self.operation_metrics[operation_name]) % 100 == 0:
                    self._update_percentiles(operation_name)
    
    def _update_percentiles(self, operation_name: str):
        """Update latency percentiles for an operation."""
        durations = [m['duration_ms'] for m in self.operation_metrics[operation_name][-1000:]]
        durations.sort()
        
        n = len(durations)
        self.latency_percentiles[operation_name] = {
            'p50': durations[int(n * 0.5)] if n > 0 else 0,
            'p90': durations[int(n * 0.9)] if n > 0 else 0,
            'p95': durations[int(n * 0.95)] if n > 0 else 0,
            'p99': durations[int(n * 0.99)] if n > 0 else 0,
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        with self.lock:
            summary = {}
            for operation, metrics in self.operation_metrics.items():
                if not metrics:
                    continue
                    
                recent_metrics = metrics[-100:]  # Last 100 operations
                avg_duration = sum(m['duration_ms'] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m['memory_delta_bytes'] for m in recent_metrics) / len(recent_metrics)
                
                summary[operation] = {
                    'avg_duration_ms': avg_duration,
                    'avg_memory_delta_bytes': avg_memory,
                    'total_operations': len(metrics),
                    'percentiles': self.latency_percentiles.get(operation, {}),
                    'recent_operations': len(recent_metrics)
                }
            
            return {
                'operations': summary,
                'system_memory_mb': psutil.Process().memory_info().rss / (1024 * 1024),
                'system_cpu_percent': psutil.cpu_percent(),
                'timestamp': time.time()
            }

class AdaptiveConfigManager:
    """Adaptive configuration management based on performance metrics."""
    
    def __init__(self, base_config: Dict[str, Any]):
        self.base_config = base_config.copy()
        self.current_config = base_config.copy()
        self.performance_history = deque(maxlen=100)
        self.adjustment_cooldown = {}
        
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """Update performance metrics and potentially adjust configuration."""
        self.performance_history.append({
            'timestamp': time.time(),
            'metrics': metrics
        })
        
        # Auto-adjust configuration based on performance
        self._auto_adjust_config(metrics)
    
    def _auto_adjust_config(self, metrics: Dict[str, Any]):
        """Automatically adjust configuration based on performance metrics."""
        current_time = time.time()
        
        # Adjust interim throttling based on processing latency
        if 'audio_processing' in metrics.get('operations', {}):
            processing_metrics = metrics['operations']['audio_processing']
            avg_latency = processing_metrics.get('avg_duration_ms', 0)
            
            # Increase throttling if processing is slow
            if avg_latency > 2000 and self._can_adjust('interim_throttle', current_time):
                self.current_config['interim_throttle_ms'] = min(
                    self.current_config.get('interim_throttle_ms', 400) + 100,
                    1000  # Max 1 second
                )
                logger.info(f"Increased interim throttling to {self.current_config['interim_throttle_ms']}ms due to high latency")
                self.adjustment_cooldown['interim_throttle'] = current_time
            
            # Decrease throttling if processing is fast
            elif avg_latency < 500 and self._can_adjust('interim_throttle', current_time):
                self.current_config['interim_throttle_ms'] = max(
                    self.current_config.get('interim_throttle_ms', 400) - 50,
                    200  # Min 200ms
                )
                logger.info(f"Decreased interim throttling to {self.current_config['interim_throttle_ms']}ms due to low latency")
                self.adjustment_cooldown['interim_throttle'] = current_time
        
        # Adjust confidence threshold based on queue depth
        queue_depth = metrics.get('system_queue_depth', 0)
        if queue_depth > 5 and self._can_adjust('confidence', current_time):
            self.current_config['min_confidence'] = min(
                self.current_config.get('min_confidence', 0.4) + 0.1,
                0.8  # Max 0.8
            )
            logger.info(f"Increased confidence threshold to {self.current_config['min_confidence']} due to high queue depth")
            self.adjustment_cooldown['confidence'] = current_time
    
    def _can_adjust(self, setting: str, current_time: float) -> bool:
        """Check if we can adjust a setting (respect cooldown)."""
        last_adjustment = self.adjustment_cooldown.get(setting, 0)
        return current_time - last_adjustment > 60  # 60 second cooldown

class ResourceManager:
    """Advanced resource management with monitoring and cleanup."""
    
    def __init__(self, memory_threshold_mb: int = 100):
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # Convert to bytes
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        self.active_sessions = {}
        
    def monitor_resources(self) -> Dict[str, Any]:
        """Monitor system resources and trigger cleanup if needed."""
        current_memory = psutil.Process().memory_info().rss
        current_time = time.time()
        
        resource_info = {
            'memory_mb': current_memory / (1024 * 1024),
            'memory_threshold_mb': self.memory_threshold / (1024 * 1024),
            'memory_usage_percent': (current_memory / self.memory_threshold) * 100,
            'cleanup_needed': current_memory > self.memory_threshold,
            'time_since_cleanup': current_time - self.last_cleanup
        }
        
        if resource_info['cleanup_needed'] or (current_time - self.last_cleanup) > self.cleanup_interval:
            cleanup_stats = self.trigger_cleanup()
            resource_info['cleanup_stats'] = cleanup_stats
            
        return resource_info
    
    def trigger_cleanup(self) -> Dict[str, Any]:
        """Trigger comprehensive resource cleanup."""
        start_memory = psutil.Process().memory_info().rss
        start_time = time.time()
        
        # Clean expired sessions
        current_time = time.time()
        expired_sessions = []
        for session_id, session_data in list(self.active_sessions.items()):
            if current_time - session_data.get('last_activity', 0) > 1800:  # 30 minutes
                expired_sessions.append(session_id)
                self.cleanup_session(session_id)
        
        # Force garbage collection
        collected = gc.collect()
        
        # Update last cleanup time
        self.last_cleanup = current_time
        
        end_memory = psutil.Process().memory_info().rss
        cleanup_time = (time.time() - start_time) * 1000
        
        cleanup_stats = {
            'memory_freed_mb': (start_memory - end_memory) / (1024 * 1024),
            'sessions_cleaned': len(expired_sessions),
            'gc_objects_collected': collected,
            'cleanup_duration_ms': cleanup_time,
            'timestamp': current_time
        }
        
        logger.info(f"Resource cleanup completed: {cleanup_stats}")
        return cleanup_stats
    
    def cleanup_session(self, session_id: str):
        """Clean up a specific session's resources."""
        if session_id in self.active_sessions:
            # Clear any session-specific buffers, connections, etc.
            del self.active_sessions[session_id]
    
    def register_session(self, session_id: str, session_data: Dict[str, Any]):
        """Register a new session for resource tracking."""
        self.active_sessions[session_id] = {
            **session_data,
            'registered_at': time.time(),
            'last_activity': time.time()
        }
    
    def update_session_activity(self, session_id: str):
        """Update last activity time for a session."""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_activity'] = time.time()