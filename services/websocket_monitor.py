"""
🔌 WebSocket Connection Health Monitor
Monitors WebSocket connections, message flow, and connection quality for 100% observability.
"""
import logging
import time
import threading
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """Metrics for a single WebSocket connection"""
    connection_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    connected_at: float
    last_activity: float
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    ping_latency: Optional[float] = None
    status: str = "active"  # active, idle, disconnected
    errors: List[str] = field(default_factory=list)

@dataclass
class WebSocketHealth:
    """Overall WebSocket health metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_messages: int = 0
    messages_per_second: float = 0.0
    average_latency: float = 0.0
    error_rate: float = 0.0
    peak_connections: int = 0
    uptime: float = 0.0
    last_updated: float = field(default_factory=time.time)

class WebSocketMonitor:
    """Comprehensive WebSocket connection monitoring"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionMetrics] = {}
        self.health_history: deque = deque(maxlen=1000)
        self.lock = threading.RLock()
        self.start_time = time.time()
        
        # Monitoring intervals and thresholds
        self.idle_threshold = 300  # 5 minutes
        self.stale_threshold = 900  # 15 minutes  
        self.max_connections = 200
        self.max_error_rate = 5.0  # 5% error rate
        
        # Message tracking for throughput calculation
        self.message_timestamps = deque(maxlen=1000)
        
        logger.info("🔌 WebSocket monitor initialized")
    
    def register_connection(self, connection_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Register new WebSocket connection"""
        with self.lock:
            metrics = ConnectionMetrics(
                connection_id=connection_id,
                user_id=user_id,
                session_id=session_id,
                connected_at=time.time(),
                last_activity=time.time()
            )
            self.connections[connection_id] = metrics
            
            logger.info(f"🔌 WebSocket connected: {connection_id} (user: {user_id}, session: {session_id})")
            self._update_health_metrics()
    
    def unregister_connection(self, connection_id: str, reason: str = "normal_close"):
        """Unregister WebSocket connection"""
        with self.lock:
            if connection_id in self.connections:
                metrics = self.connections[connection_id]
                metrics.status = "disconnected"
                
                # Log connection stats
                duration = time.time() - metrics.connected_at
                logger.info(f"🔌 WebSocket disconnected: {connection_id} "
                           f"(duration: {duration:.1f}s, messages: {metrics.messages_sent + metrics.messages_received}, "
                           f"reason: {reason})")
                
                del self.connections[connection_id]
                self._update_health_metrics()
    
    def record_message_sent(self, connection_id: str, message_size: int):
        """Record sent message"""
        self._record_message_activity(connection_id, sent=True, size=message_size)
    
    def record_message_received(self, connection_id: str, message_size: int):
        """Record received message"""
        self._record_message_activity(connection_id, sent=False, size=message_size)
    
    def _record_message_activity(self, connection_id: str, sent: bool, size: int):
        """Record message activity for connection"""
        with self.lock:
            if connection_id in self.connections:
                metrics = self.connections[connection_id]
                metrics.last_activity = time.time()
                
                if sent:
                    metrics.messages_sent += 1
                    metrics.bytes_sent += size
                else:
                    metrics.messages_received += 1
                    metrics.bytes_received += size
                
                # Track message timestamps for throughput
                self.message_timestamps.append(time.time())
    
    def record_ping_latency(self, connection_id: str, latency_ms: float):
        """Record ping latency for connection"""
        with self.lock:
            if connection_id in self.connections:
                self.connections[connection_id].ping_latency = latency_ms
    
    def record_error(self, connection_id: str, error: str):
        """Record error for connection"""
        with self.lock:
            if connection_id in self.connections:
                metrics = self.connections[connection_id]
                metrics.errors.append(f"{time.time()}: {error}")
                
                # Keep only last 10 errors per connection
                if len(metrics.errors) > 10:
                    metrics.errors = metrics.errors[-10:]
                
                logger.warning(f"🔌 WebSocket error on {connection_id}: {error}")
    
    def get_health_metrics(self) -> WebSocketHealth:
        """Get current WebSocket health metrics"""
        with self.lock:
            current_time = time.time()
            
            # Count connection states
            total_connections = len(self.connections)
            active_connections = 0
            idle_connections = 0
            
            total_latency = 0
            latency_count = 0
            total_errors = 0
            
            for metrics in self.connections.values():
                # Classify connection state
                time_since_activity = current_time - metrics.last_activity
                if time_since_activity > self.idle_threshold:
                    idle_connections += 1
                else:
                    active_connections += 1
                
                # Aggregate latency
                if metrics.ping_latency:
                    total_latency += metrics.ping_latency
                    latency_count += 1
                
                # Count errors
                total_errors += len(metrics.errors)
            
            # Calculate messages per second (last 60 seconds)
            recent_messages = [t for t in self.message_timestamps if current_time - t <= 60]
            messages_per_second = len(recent_messages) / 60.0
            
            # Calculate averages
            average_latency = total_latency / latency_count if latency_count > 0 else 0.0
            error_rate = (total_errors / total_connections * 100) if total_connections > 0 else 0.0
            
            # Get peak connections from history
            peak_connections = max([h.total_connections for h in self.health_history], default=total_connections)
            peak_connections = max(peak_connections, total_connections)
            
            health = WebSocketHealth(
                total_connections=total_connections,
                active_connections=active_connections,
                idle_connections=idle_connections,
                total_messages=sum(len(self.message_timestamps)),
                messages_per_second=messages_per_second,
                average_latency=average_latency,
                error_rate=error_rate,
                peak_connections=peak_connections,
                uptime=current_time - self.start_time
            )
            
            # Store in history
            self.health_history.append(health)
            
            return health
    
    def _update_health_metrics(self):
        """Update health metrics and check for alerts"""
        health = self.get_health_metrics()
        
        # Check for alert conditions
        if health.total_connections > self.max_connections:
            logger.warning(f"🚨 High WebSocket connections: {health.total_connections}")
        
        if health.error_rate > self.max_error_rate:
            logger.warning(f"🚨 High WebSocket error rate: {health.error_rate}%")
        
        # Clean up stale connections
        self._cleanup_stale_connections()
    
    def _cleanup_stale_connections(self):
        """Clean up stale connections that haven't been properly closed"""
        current_time = time.time()
        stale_connections = []
        
        for connection_id, metrics in self.connections.items():
            if current_time - metrics.last_activity > self.stale_threshold:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.warning(f"🔌 Cleaning up stale WebSocket connection: {connection_id}")
            self.unregister_connection(connection_id, "stale_cleanup")
    
    def get_connection_details(self, connection_id: str) -> Optional[ConnectionMetrics]:
        """Get detailed metrics for specific connection"""
        with self.lock:
            return self.connections.get(connection_id)
    
    def get_connections_by_session(self, session_id: str) -> List[ConnectionMetrics]:
        """Get all connections for a session"""
        with self.lock:
            return [m for m in self.connections.values() if m.session_id == session_id]
    
    def get_summary(self) -> Dict:
        """Get summary for monitoring dashboard"""
        health = self.get_health_metrics()
        
        return {
            'status': 'healthy' if health.total_connections < self.max_connections and health.error_rate < self.max_error_rate else 'warning',
            'total_connections': health.total_connections,
            'active_connections': health.active_connections, 
            'messages_per_second': health.messages_per_second,
            'average_latency': health.average_latency,
            'error_rate': health.error_rate,
            'uptime': health.uptime
        }

# Global WebSocket monitor instance
_websocket_monitor = None

def get_websocket_monitor() -> WebSocketMonitor:
    """Get global WebSocket monitor instance"""
    global _websocket_monitor
    if _websocket_monitor is None:
        _websocket_monitor = WebSocketMonitor()
    return _websocket_monitor