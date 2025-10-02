"""
Performance monitoring service.
Tracks application performance metrics and integrates with monitoring platforms.
"""
import time
import logging
from functools import wraps
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Centralized performance monitoring service.
    Tracks latency, throughput, and custom metrics.
    """
    
    def __init__(self):
        self.metrics_buffer = []
        self.enabled = True
    
    def track_request(self, route: str, method: str, duration_ms: float, status_code: int):
        """Track HTTP request performance."""
        metric = {
            'type': 'http_request',
            'route': route,
            'method': method,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._record_metric(metric)
        
        if duration_ms > 1000:
            logger.warning(f"Slow request detected: {method} {route} took {duration_ms}ms")
    
    def track_database_query(self, query_type: str, duration_ms: float, table: Optional[str] = None):
        """Track database query performance."""
        metric = {
            'type': 'database_query',
            'query_type': query_type,
            'table': table,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._record_metric(metric)
        
        if duration_ms > 500:
            logger.warning(f"Slow query detected: {query_type} on {table} took {duration_ms}ms")
    
    def track_external_api_call(self, service: str, endpoint: str, duration_ms: float, success: bool):
        """Track external API call performance."""
        metric = {
            'type': 'external_api',
            'service': service,
            'endpoint': endpoint,
            'duration_ms': duration_ms,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._record_metric(metric)
    
    def track_websocket_latency(self, event: str, duration_ms: float):
        """Track WebSocket event latency."""
        metric = {
            'type': 'websocket',
            'event': event,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._record_metric(metric)
    
    def track_custom_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Track custom application metric."""
        metric = {
            'type': 'custom',
            'name': name,
            'value': value,
            'tags': tags or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._record_metric(metric)
    
    def _record_metric(self, metric: Dict[str, Any]):
        """Record metric to buffer and send to monitoring platforms."""
        if not self.enabled:
            return
        
        self.metrics_buffer.append(metric)
        
        logger.info(f"metric.{metric['type']}", extra=metric)
        
        if len(self.metrics_buffer) >= 100:
            self._flush_metrics()
    
    def _flush_metrics(self):
        """Flush metrics buffer to monitoring platforms."""
        if not self.metrics_buffer:
            return
        
        metrics_count = len(self.metrics_buffer)
        self.metrics_buffer.clear()
        
        logger.debug(f"Flushed {metrics_count} metrics")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        return {
            'metrics_buffered': len(self.metrics_buffer),
            'enabled': self.enabled
        }


performance_monitor = PerformanceMonitor()


def track_performance(operation_name: str):
    """
    Decorator to track function performance.
    
    Usage:
        @track_performance("user.create")
        def create_user(username, email):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                performance_monitor.track_custom_metric(
                    name=f"operation.{operation_name}.duration",
                    value=duration_ms,
                    tags={'success': str(success)}
                )
        
        return wrapper
    return decorator
