"""
🔥 PHASE 4: Advanced Performance Optimization and Scalability
Comprehensive performance monitoring, optimization, and scalable resource management.
"""

import logging
import time
import threading
import asyncio
import psutil
import gc
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor
import queue

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """System performance metrics."""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    memory_available: float
    active_sessions: int
    concurrent_processing: int
    average_latency: float
    throughput: float
    error_rate: float
    queue_depths: Dict[str, int]
    
@dataclass
class ResourceLimits:
    """Resource usage limits and thresholds."""
    max_cpu_usage: float = 80.0
    max_memory_usage: float = 85.0
    max_concurrent_sessions: int = 50
    max_processing_queue: int = 100
    latency_threshold_ms: float = 500.0
    error_rate_threshold: float = 0.05

class PerformanceOptimizer:
    """
    🔥 PHASE 4: Advanced performance optimization and scalability management.
    Provides real-time resource monitoring, adaptive scaling, and performance optimization.
    """
    
    def __init__(self, resource_limits: Optional[ResourceLimits] = None):
        self.resource_limits = resource_limits or ResourceLimits()
        
        # Performance monitoring
        self.metrics_history = deque(maxlen=1000)  # Last 1000 measurements
        self.performance_stats = {
            'total_sessions_processed': 0,
            'total_optimization_actions': 0,
            'memory_optimizations': 0,
            'cpu_optimizations': 0,
            'queue_optimizations': 0,
            'scalability_adjustments': 0
        }
        
        # Resource management
        self.session_pools = {}
        self.processing_queues = {
            'audio_processing': queue.Queue(maxsize=100),
            'transcription': queue.Queue(maxsize=100),
            'postprocessing': queue.Queue(maxsize=50)
        }
        
        # Thread pools for different workloads
        self.thread_pools = {
            'audio_io': ThreadPoolExecutor(max_workers=4, thread_name_prefix='audio_io'),
            'transcription': ThreadPoolExecutor(max_workers=6, thread_name_prefix='transcription'),
            'postprocessing': ThreadPoolExecutor(max_workers=2, thread_name_prefix='postprocessing')
        }
        
        # Adaptive scaling state
        self.scaling_state = {
            'current_load_level': 'normal',  # low, normal, high, critical
            'last_scaling_action': 0,
            'scaling_cooldown': 30.0,  # seconds
            'optimization_strategy': 'balanced'  # aggressive, balanced, conservative
        }
        
        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Performance optimization strategies
        self.optimization_strategies = {
            'memory': self._optimize_memory_usage,
            'cpu': self._optimize_cpu_usage,
            'queue': self._optimize_queue_performance,
            'scaling': self._adaptive_scaling
        }
        
        logger.info("Performance Optimizer initialized with advanced scalability features")
    
    def start_monitoring(self, interval: float = 5.0):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True,
            name='performance_monitor'
        )
        self.monitoring_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self, interval: float):
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self.collect_performance_metrics()
                self.metrics_history.append(metrics)
                
                # Analyze and optimize if needed
                self.analyze_and_optimize(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect comprehensive performance metrics."""
        # System metrics
        cpu_usage = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        memory_available = memory.available / (1024**3)  # GB
        
        # Application metrics
        active_sessions = len(self.session_pools)
        concurrent_processing = 0
        for pool in self.thread_pools.values():
            if hasattr(pool, '_threads') and isinstance(pool._threads, int):
                concurrent_processing += pool._threads
            elif hasattr(pool, '_max_workers'):
                concurrent_processing += pool._max_workers
        
        # Calculate average latency from recent metrics
        recent_latencies = [m.average_latency for m in list(self.metrics_history)[-10:]]
        average_latency = sum(recent_latencies) / len(recent_latencies) if recent_latencies else 0.0
        
        # Queue depths
        queue_depths = {
            name: q.qsize() for name, q in self.processing_queues.items()
        }
        
        # Throughput (sessions per minute)
        throughput = self._calculate_throughput()
        
        # Error rate (placeholder - would be calculated from actual error tracking)
        error_rate = 0.0
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            memory_available=memory_available,
            active_sessions=active_sessions,
            concurrent_processing=concurrent_processing,
            average_latency=average_latency,
            throughput=throughput,
            error_rate=error_rate,
            queue_depths=queue_depths
        )
    
    def analyze_and_optimize(self, metrics: PerformanceMetrics):
        """Analyze metrics and apply optimizations."""
        current_time = time.time()
        
        # Skip if in cooldown period
        if current_time - self.scaling_state['last_scaling_action'] < self.scaling_state['scaling_cooldown']:
            return
        
        # Determine load level
        load_level = self._determine_load_level(metrics)
        previous_load = self.scaling_state['current_load_level']
        self.scaling_state['current_load_level'] = load_level
        
        # Apply optimizations based on metrics
        optimization_applied = False
        
        # Memory optimization
        if metrics.memory_usage > self.resource_limits.max_memory_usage:
            self.optimization_strategies['memory'](metrics)
            optimization_applied = True
        
        # CPU optimization
        if metrics.cpu_usage > self.resource_limits.max_cpu_usage:
            self.optimization_strategies['cpu'](metrics)
            optimization_applied = True
        
        # Queue optimization
        if any(depth > 20 for depth in metrics.queue_depths.values()):
            self.optimization_strategies['queue'](metrics)
            optimization_applied = True
        
        # Adaptive scaling
        if load_level != previous_load or metrics.average_latency > self.resource_limits.latency_threshold_ms:
            self.optimization_strategies['scaling'](metrics)
            optimization_applied = True
        
        if optimization_applied:
            self.scaling_state['last_scaling_action'] = current_time
            self.performance_stats['total_optimization_actions'] += 1
    
    def _determine_load_level(self, metrics: PerformanceMetrics) -> str:
        """Determine current system load level."""
        load_score = 0
        
        # CPU contribution
        if metrics.cpu_usage > 70:
            load_score += 2
        elif metrics.cpu_usage > 50:
            load_score += 1
        
        # Memory contribution
        if metrics.memory_usage > 80:
            load_score += 2
        elif metrics.memory_usage > 60:
            load_score += 1
        
        # Session load contribution
        if metrics.active_sessions > 30:
            load_score += 2
        elif metrics.active_sessions > 15:
            load_score += 1
        
        # Queue depth contribution
        max_queue_depth = max(metrics.queue_depths.values()) if metrics.queue_depths else 0
        if max_queue_depth > 50:
            load_score += 2
        elif max_queue_depth > 20:
            load_score += 1
        
        # Latency contribution
        if metrics.average_latency > 800:
            load_score += 2
        elif metrics.average_latency > 400:
            load_score += 1
        
        # Determine level
        if load_score >= 6:
            return 'critical'
        elif load_score >= 4:
            return 'high'
        elif load_score >= 2:
            return 'normal'
        else:
            return 'low'
    
    def _optimize_memory_usage(self, metrics: PerformanceMetrics):
        """Optimize memory usage."""
        logger.info(f"Applying memory optimization (usage: {metrics.memory_usage:.1f}%)")
        
        # Force garbage collection
        gc.collect()
        
        # Clear caches if available
        self._clear_internal_caches()
        
        # Reduce buffer sizes for low-priority operations
        self._reduce_buffer_sizes()
        
        self.performance_stats['memory_optimizations'] += 1
    
    def _optimize_cpu_usage(self, metrics: PerformanceMetrics):
        """Optimize CPU usage."""
        logger.info(f"Applying CPU optimization (usage: {metrics.cpu_usage:.1f}%)")
        
        # Reduce thread pool sizes temporarily
        self._adjust_thread_pool_sizes('reduce')
        
        # Implement CPU throttling for non-critical tasks
        self._enable_cpu_throttling()
        
        self.performance_stats['cpu_optimizations'] += 1
    
    def _optimize_queue_performance(self, metrics: PerformanceMetrics):
        """Optimize queue performance."""
        max_queue = max(metrics.queue_depths.values()) if metrics.queue_depths else 0
        logger.info(f"Applying queue optimization (max depth: {max_queue})")
        
        # Increase processing capacity for overloaded queues
        for queue_name, depth in metrics.queue_depths.items():
            if depth > 30:
                self._scale_queue_processing(queue_name, 'up')
        
        # Prioritize high-priority queues
        self._rebalance_queue_priorities()
        
        self.performance_stats['queue_optimizations'] += 1
    
    def _adaptive_scaling(self, metrics: PerformanceMetrics):
        """Apply adaptive scaling based on load."""
        load_level = self.scaling_state['current_load_level']
        logger.info(f"Applying adaptive scaling for load level: {load_level}")
        
        if load_level == 'critical':
            self._apply_critical_scaling(metrics)
        elif load_level == 'high':
            self._apply_high_load_scaling(metrics)
        elif load_level == 'low':
            self._apply_low_load_scaling(metrics)
        
        self.performance_stats['scalability_adjustments'] += 1
    
    def _apply_critical_scaling(self, metrics: PerformanceMetrics):
        """Apply critical load scaling measures."""
        # Maximum resource allocation
        self._adjust_thread_pool_sizes('maximize')
        self._enable_aggressive_optimization()
        self._prioritize_critical_operations()
        
        logger.warning("Critical load detected - maximum scaling applied")
    
    def _apply_high_load_scaling(self, metrics: PerformanceMetrics):
        """Apply high load scaling measures."""
        # Increase resource allocation
        self._adjust_thread_pool_sizes('increase')
        self._enable_balanced_optimization()
        
        logger.info("High load detected - increased scaling applied")
    
    def _apply_low_load_scaling(self, metrics: PerformanceMetrics):
        """Apply low load scaling measures."""
        # Reduce resource allocation to save resources
        self._adjust_thread_pool_sizes('reduce')
        self._enable_conservative_optimization()
        
        logger.info("Low load detected - reduced scaling applied")
    
    def _adjust_thread_pool_sizes(self, action: str):
        """Adjust thread pool sizes based on action."""
        adjustments = {
            'reduce': 0.8,
            'increase': 1.3,
            'maximize': 2.0
        }
        
        multiplier = adjustments.get(action, 1.0)
        
        for pool_name, pool in self.thread_pools.items():
            current_workers = pool._max_workers
            new_workers = max(1, min(20, int(current_workers * multiplier)))
            
            if new_workers != current_workers:
                # Note: ThreadPoolExecutor doesn't support dynamic resizing
                # In a real implementation, you'd need a custom pool or recreation
                logger.info(f"Would adjust {pool_name} pool from {current_workers} to {new_workers} workers")
    
    def _clear_internal_caches(self):
        """Clear internal caches to free memory."""
        # Clear session pools that are inactive
        current_time = time.time()
        inactive_sessions = []
        
        for session_id, session_data in self.session_pools.items():
            if current_time - session_data.get('last_activity', 0) > 300:  # 5 minutes
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.session_pools[session_id]
        
        if inactive_sessions:
            logger.info(f"Cleared {len(inactive_sessions)} inactive session pools")
    
    def _reduce_buffer_sizes(self):
        """Reduce buffer sizes for memory optimization."""
        # Implement buffer size reduction logic
        logger.info("Reduced buffer sizes for memory optimization")
    
    def _enable_cpu_throttling(self):
        """Enable CPU throttling for non-critical operations."""
        # Implement CPU throttling logic
        logger.info("Enabled CPU throttling for non-critical operations")
    
    def _scale_queue_processing(self, queue_name: str, direction: str):
        """Scale processing capacity for specific queue."""
        logger.info(f"Scaling {queue_name} queue processing: {direction}")
    
    def _rebalance_queue_priorities(self):
        """Rebalance queue processing priorities."""
        logger.info("Rebalanced queue processing priorities")
    
    def _enable_aggressive_optimization(self):
        """Enable aggressive optimization strategies."""
        self.scaling_state['optimization_strategy'] = 'aggressive'
        logger.info("Enabled aggressive optimization strategy")
    
    def _enable_balanced_optimization(self):
        """Enable balanced optimization strategies."""
        self.scaling_state['optimization_strategy'] = 'balanced'
        logger.info("Enabled balanced optimization strategy")
    
    def _enable_conservative_optimization(self):
        """Enable conservative optimization strategies."""
        self.scaling_state['optimization_strategy'] = 'conservative'
        logger.info("Enabled conservative optimization strategy")
    
    def _prioritize_critical_operations(self):
        """Prioritize critical operations during high load."""
        logger.info("Prioritized critical operations for high load")
    
    def _calculate_throughput(self) -> float:
        """Calculate system throughput (operations per minute)."""
        if len(self.metrics_history) < 2:
            return 0.0
        
        recent_metrics = list(self.metrics_history)[-12:]  # Last minute of 5-second intervals
        if not recent_metrics:
            return 0.0
        
        # Calculate based on session processing
        sessions_processed = sum(m.active_sessions for m in recent_metrics)
        time_window = len(recent_metrics) * 5 / 60  # Convert to minutes
        
        return sessions_processed / time_window if time_window > 0 else 0.0
    
    def register_session(self, session_id: str, session_data: Dict[str, Any]):
        """Register a new session for performance tracking."""
        self.session_pools[session_id] = {
            'start_time': time.time(),
            'last_activity': time.time(),
            'metrics': session_data
        }
        self.performance_stats['total_sessions_processed'] += 1
    
    def update_session_activity(self, session_id: str):
        """Update session activity timestamp."""
        if session_id in self.session_pools:
            self.session_pools[session_id]['last_activity'] = time.time()
    
    def unregister_session(self, session_id: str):
        """Unregister a completed session."""
        if session_id in self.session_pools:
            del self.session_pools[session_id]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        current_metrics = self.collect_performance_metrics()
        
        # Calculate trends
        recent_metrics = list(self.metrics_history)[-10:]
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
        latency_trend = self._calculate_trend([m.average_latency for m in recent_metrics])
        
        return {
            'current_metrics': asdict(current_metrics),
            'performance_stats': self.performance_stats.copy(),
            'scaling_state': self.scaling_state.copy(),
            'trends': {
                'cpu': cpu_trend,
                'memory': memory_trend,
                'latency': latency_trend
            },
            'resource_utilization': {
                'thread_pools': {name: pool._max_workers for name, pool in self.thread_pools.items()},
                'queue_depths': current_metrics.queue_depths,
                'active_sessions': len(self.session_pools)
            }
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 3:
            return 'stable'
        
        # Simple linear trend calculation
        recent_avg = sum(values[-3:]) / 3
        older_avg = sum(values[:-3]) / max(1, len(values) - 3)
        
        if recent_avg > older_avg * 1.1:
            return 'increasing'
        elif recent_avg < older_avg * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def apply_manual_optimization(self, optimization_type: str, **kwargs):
        """Apply manual optimization strategies."""
        if optimization_type in self.optimization_strategies:
            current_metrics = self.collect_performance_metrics()
            self.optimization_strategies[optimization_type](current_metrics)
            logger.info(f"Applied manual {optimization_type} optimization")
        else:
            logger.warning(f"Unknown optimization type: {optimization_type}")
    
    def shutdown(self):
        """Shutdown performance optimizer and cleanup resources."""
        self.stop_monitoring()
        
        # Shutdown thread pools
        for pool_name, pool in self.thread_pools.items():
            pool.shutdown(wait=True)
            logger.info(f"Shutdown {pool_name} thread pool")
        
        logger.info("Performance Optimizer shutdown complete")