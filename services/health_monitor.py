"""
🏥 HEALTH MONITOR SERVICE: Comprehensive system health tracking
Monitors all aspects of transcription pipeline health and performance
"""

import time
import psutil
import logging
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """Individual health metric with timestamp"""
    name: str
    value: Any
    timestamp: float
    status: str = "healthy"  # healthy, warning, critical
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: str = "healthy"  # healthy, degraded, unhealthy
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    active_sessions: int = 0
    api_response_time: float = 0.0
    error_rate: float = 0.0
    uptime: float = 0.0
    last_updated: float = field(default_factory=time.time)

class HealthMonitor:
    """
    Comprehensive health monitoring for transcription service
    Tracks system resources, API performance, and service health
    """
    
    def __init__(self):
        self.metrics: Dict[str, deque] = {}
        self.alerts: List[Dict] = []
        self.start_time = time.time()
        self.lock = threading.RLock()
        self.monitoring_active = False
        self.monitor_thread = None
        
        # CPU sampling optimization - rolling average without blocking
        self.cpu_samples = deque(maxlen=10)  # Keep last 10 samples for rolling average
        self.last_cpu_sample_time = 0
        
        # Thresholds for health checks
        self.thresholds = {
            'cpu_usage': {'warning': 80.0, 'critical': 90.0},
            'memory_usage': {'warning': 80.0, 'critical': 95.0},
            'disk_usage': {'warning': 85.0, 'critical': 95.0},
            'api_response_time': {'warning': 5000.0, 'critical': 10000.0},  # milliseconds
            'error_rate': {'warning': 5.0, 'critical': 15.0},  # percentage
            'memory_growth_rate': {'warning': 10.0, 'critical': 25.0},  # MB/minute
            'active_sessions': {'warning': 100, 'critical': 200},  # concurrent sessions
            'buffer_memory': {'warning': 100.0, 'critical': 200.0},  # MB total buffer memory
        }
        
        # Initialize metric storage
        for metric_name in self.thresholds.keys():
            self.metrics[metric_name] = deque(maxlen=100)  # Keep last 100 readings
        
        self.metrics['active_sessions'] = deque(maxlen=100)
        self.metrics['transcription_count'] = deque(maxlen=100)
        self.metrics['audio_quality'] = deque(maxlen=100)
        self.metrics['memory_growth_rate'] = deque(maxlen=100)
        self.metrics['buffer_memory'] = deque(maxlen=100)
        
        # Memory leak detection
        self.baseline_memory = None
        self.memory_samples = deque(maxlen=20)  # Track last 20 memory samples
        self.last_memory_check = time.time()
        
        logger.info("🏥 Health Monitor initialized")
    
    def start_monitoring(self, interval: int = 30):
        """Start continuous health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info(f"🏥 Health monitoring started (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🏥 Health monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                self._check_thresholds()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"❌ Error in health monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        current_time = time.time()
        
        try:
            # CPU usage - non-blocking with rolling average
            cpu_usage = self._get_cpu_usage_optimized(current_time)
            if cpu_usage is not None:
                self.record_metric('cpu_usage', cpu_usage, current_time)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            self.record_metric('memory_usage', memory_usage, current_time)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            self.record_metric('disk_usage', disk_usage, current_time)
            
            # Memory leak detection
            self._detect_memory_leaks(current_time)
            
            # Session and buffer monitoring
            self._monitor_session_resources(current_time)
            
        except Exception as e:
            logger.error(f"❌ Error collecting system metrics: {e}")
    
    def _get_cpu_usage_optimized(self, current_time: float) -> Optional[float]:
        """Get CPU usage with non-blocking optimized sampling and rolling average"""
        # Only sample every 2 seconds to avoid blocking
        if current_time - self.last_cpu_sample_time < 2.0:
            # Return rolling average if we have recent samples
            if self.cpu_samples:
                return sum(self.cpu_samples) / len(self.cpu_samples)
            return None
        
        try:
            # Non-blocking CPU sample
            cpu_sample = psutil.cpu_percent(interval=None)
            
            # Only use the sample if it's reasonable (not first call or after pause)
            if cpu_sample > 0:
                self.cpu_samples.append(cpu_sample)
                self.last_cpu_sample_time = current_time
                
                # Return rolling average
                return sum(self.cpu_samples) / len(self.cpu_samples)
            
            return None
        except Exception as e:
            logger.error(f"❌ Error getting optimized CPU usage: {e}")
            return None
    
    def record_metric(self, name: str, value: Any, timestamp: Optional[float] = None):
        """Record a metric value"""
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = deque(maxlen=100)
            
            metric = HealthMetric(
                name=name,
                value=value,
                timestamp=timestamp,
                status=self._determine_status(name, value)
            )
            
            self.metrics[name].append(metric)
        
        logger.debug(f"📊 Recorded metric {name}: {value}")
    
    def _determine_status(self, name: str, value: float) -> str:
        """Determine health status based on thresholds"""
        if name not in self.thresholds:
            return "healthy"
        
        thresholds = self.thresholds[name]
        
        if value >= thresholds.get('critical', float('inf')):
            return "critical"
        elif value >= thresholds.get('warning', float('inf')):
            return "warning"
        else:
            return "healthy"
    
    def _check_thresholds(self):
        """Check all metrics against thresholds and generate alerts"""
        current_time = time.time()
        
        with self.lock:
            for name, metric_queue in self.metrics.items():
                if not metric_queue or name not in self.thresholds:
                    continue
                
                latest_metric = metric_queue[-1]
                
                if latest_metric.status in ['warning', 'critical']:
                    self._generate_alert(latest_metric, current_time)
    
    def _generate_alert(self, metric: HealthMetric, timestamp: float):
        """Generate alert for threshold breach"""
        alert = {
            'metric': metric.name,
            'value': metric.value,
            'status': metric.status,
            'timestamp': timestamp,
            'message': f"{metric.name} is {metric.status}: {metric.value}"
        }
        
        # Avoid duplicate alerts (only alert if status changed)
        if not self.alerts or self.alerts[-1]['metric'] != metric.name or self.alerts[-1]['status'] != metric.status:
            self.alerts.append(alert)
            logger.warning(f"🚨 Health Alert: {alert['message']}")
            
            # Keep only last 50 alerts
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]
    
    def get_current_health(self) -> SystemHealth:
        """Get current overall system health"""
        with self.lock:
            health = SystemHealth(uptime=time.time() - self.start_time)
            
            # Get latest values for each metric
            for name, metric_queue in self.metrics.items():
                if metric_queue:
                    latest = metric_queue[-1]
                    setattr(health, name, latest.value)
            
            # Determine overall status
            critical_count = sum(1 for queue in self.metrics.values() 
                               for metric in list(queue)[-1:] 
                               if metric.status == 'critical')
            
            warning_count = sum(1 for queue in self.metrics.values() 
                              for metric in list(queue)[-1:] 
                              if metric.status == 'warning')
            
            if critical_count > 0:
                health.status = "unhealthy"
            elif warning_count > 0:
                health.status = "degraded"
            else:
                health.status = "healthy"
            
            health.last_updated = time.time()
            
            return health
    
    def get_metric_history(self, name: str, minutes: int = 60) -> List[HealthMetric]:
        """Get metric history for specified time period"""
        cutoff_time = time.time() - (minutes * 60)
        
        with self.lock:
            if name not in self.metrics:
                return []
            
            return [metric for metric in self.metrics[name] 
                   if metric.timestamp >= cutoff_time]
    
    def get_alerts(self, hours: int = 24) -> List[Dict]:
        """Get alerts from specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.lock:
            return [alert for alert in self.alerts 
                   if alert['timestamp'] >= cutoff_time]
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary statistics"""
        with self.lock:
            summary = {
                'uptime_hours': (time.time() - self.start_time) / 3600,
                'metrics_count': len(self.metrics),
                'total_alerts': len(self.alerts),
                'recent_alerts': len(self.get_alerts(1)),  # Last hour
                'health_status': self.get_current_health().status
            }
            
            # Add metric averages for last hour
            for name in ['cpu_usage', 'memory_usage', 'api_response_time']:
                history = self.get_metric_history(name, 60)
                if history:
                    avg_value = sum(m.value for m in history) / len(history)
                    summary[f'{name}_avg_1h'] = round(avg_value, 2)
            
            return summary
    
    def record_api_call(self, endpoint: str, response_time: float, success: bool):
        """Record API call metrics"""
        current_time = time.time()
        
        # Record response time
        self.record_metric('api_response_time', response_time, current_time)
        
        # Record for error rate calculation
        self.record_metric('api_call_success', 1 if success else 0, current_time)
        
        # Calculate error rate over last 100 calls
        recent_calls = list(self.metrics.get('api_call_success', []))[-100:]
        if recent_calls:
            error_rate = (1 - sum(m.value for m in recent_calls) / len(recent_calls)) * 100
            self.record_metric('error_rate', error_rate, current_time)
    
    def record_transcription_event(self, session_id: str, duration: float, success: bool, confidence: Optional[float] = None):
        """Record transcription-specific metrics"""
        current_time = time.time()
        
        self.record_metric('transcription_count', 1, current_time)
        
        if confidence is not None:
            self.record_metric('audio_quality', confidence, current_time)
        
        # Update active sessions count (simplified)
        # In production, you'd track this more accurately
        current_sessions = len(set(session_id for _ in range(1)))  # Placeholder
        self.record_metric('active_sessions', current_sessions, current_time)
    
    def _detect_memory_leaks(self, current_time: float):
        """Detect memory leaks by analyzing memory growth patterns"""
        try:
            # Get current PROCESS memory usage in MB (not system memory)
            process = psutil.Process()
            current_memory_mb = process.memory_info().rss / (1024 * 1024)
            
            # Store baseline memory on first run
            if self.baseline_memory is None:
                self.baseline_memory = current_memory_mb
                logger.info(f"📊 Baseline memory set: {self.baseline_memory:.2f} MB")
                return
            
            # Add to memory samples
            self.memory_samples.append(current_memory_mb)
            
            # Calculate memory growth rate (MB per minute)
            if len(self.memory_samples) >= 2:
                time_diff = current_time - self.last_memory_check
                if time_diff > 60:  # Check every minute
                    # Get oldest sample safely
                    oldest_sample = list(self.memory_samples)[0]
                    memory_diff = current_memory_mb - oldest_sample
                    growth_rate = memory_diff / (time_diff / 60.0)  # MB per minute
                    
                    self.record_metric('memory_growth_rate', growth_rate, current_time)
                    self.last_memory_check = current_time
                    
                    # Log concerning growth
                    if growth_rate > 5.0:  # More than 5MB/minute growth
                        logger.warning(f"🚨 High memory growth detected: {growth_rate:.2f} MB/min")
                        
                    # Reset samples if we have enough data
                    if len(self.memory_samples) > 10:
                        # Convert to list first, then slice, then back to deque
                        recent_samples = list(self.memory_samples)[-5:]
                        self.memory_samples = deque(recent_samples, maxlen=20)
            
        except Exception as e:
            logger.error(f"❌ Memory leak detection failed: {e}")
    
    def _monitor_session_resources(self, current_time: float):
        """Monitor session and buffer memory usage"""
        try:
            # Import here to avoid circular imports
            from services.session_buffer_manager import buffer_registry
            
            # Get active session count and buffer memory
            metrics = buffer_registry.get_all_metrics()
            active_sessions = metrics.get('total_sessions', 0)
            
            # Calculate total buffer memory (approximate)
            total_buffer_memory = 0
            for session_metrics in metrics.get('sessions', {}).values():
                buffer_bytes = session_metrics.get('buffer_bytes', 0)
                total_buffer_memory += buffer_bytes
            
            buffer_memory_mb = total_buffer_memory / (1024 * 1024)
            
            # Record metrics
            self.record_metric('active_sessions', active_sessions, current_time)
            self.record_metric('buffer_memory', buffer_memory_mb, current_time)
            
            # Log warnings for resource usage
            if active_sessions > 50:
                logger.warning(f"⚠️ High session count: {active_sessions}")
            if buffer_memory_mb > 50:
                logger.warning(f"⚠️ High buffer memory usage: {buffer_memory_mb:.2f} MB")
                
        except Exception as e:
            logger.error(f"❌ Session resource monitoring failed: {e}")

# Global health monitor instance
health_monitor = HealthMonitor()

def get_health_monitor() -> HealthMonitor:
    """Get the global health monitor instance"""
    return health_monitor

logger.info("🏥 Health Monitor service initialized")