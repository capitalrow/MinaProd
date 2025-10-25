"""
🔒 CIRCUIT BREAKER SERVICE: Robust API failure protection
Implements circuit breaker pattern to prevent cascading failures

UPGRADE (Wave 0-10): Redis-backed distributed state across Gunicorn workers
- Previous: Thread-local state (inconsistent across workers)
- Now: Redis-backed state (consistent across all workers)
- Backward compatible API
"""

import time
import logging
import threading
import redis
import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Callable, Any, Optional
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""
    failure_threshold: int = 5        # Failures to trip breaker
    recovery_timeout: int = 60        # Seconds before trying again
    success_threshold: int = 3        # Successes to close breaker
    request_timeout: int = 30         # Request timeout in seconds
    window_size: int = 10            # Rolling window for failure tracking

@dataclass
class CircuitBreakerStats:
    """Statistics for monitoring circuit breaker health"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_opens: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=10))

class CircuitBreaker:
    """
    Production-grade circuit breaker implementation with Redis-backed distributed state.
    
    Protects external services from cascade failures across all Gunicorn workers.
    
    State stored in Redis:
    - circuit_breaker:{name}:state → CLOSED/OPEN/HALF_OPEN
    - circuit_breaker:{name}:failures → failure count
    - circuit_breaker:{name}:last_failure_time → timestamp
    - circuit_breaker:{name}:metrics → JSON stats
    - circuit_breaker:{name}:history → last 100 events
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None, redis_url: Optional[str] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.lock = threading.RLock()
        
        # Connect to Redis for distributed state
        redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_enabled = True
            logger.debug(f"🔗 Circuit breaker '{name}' connected to Redis")
        except Exception as e:
            logger.warning(f"⚠️ Circuit breaker '{name}' failed to connect to Redis, falling back to local state: {e}")
            self.redis_enabled = False
            # Fallback to thread-local state
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self.last_attempt_time = 0
        
        # Redis keys
        self.state_key = f"circuit_breaker:{name}:state"
        self.failures_key = f"circuit_breaker:{name}:failures"
        self.last_failure_key = f"circuit_breaker:{name}:last_failure_time"
        self.metrics_key = f"circuit_breaker:{name}:metrics"
        self.history_key = f"circuit_breaker:{name}:history"
        
        # Initialize state if not exists
        if self.redis_enabled:
            if not self.redis_client.exists(self.state_key):
                self._initialize_redis_state()
        
        logger.info(f"🔒 Circuit breaker '{name}' initialized (Redis={self.redis_enabled}, config={self.config})")
    
    def _initialize_redis_state(self):
        """Initialize circuit breaker state in Redis."""
        if not self.redis_enabled:
            return
            
        self.redis_client.set(self.state_key, CircuitState.CLOSED.value)
        self.redis_client.set(self.failures_key, 0)
        self.redis_client.delete(self.last_failure_key)
        
        # Initialize metrics
        metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_opens": 0,
            "last_success_time": None,
            "last_failure_time": None,
            "created_at": datetime.utcnow().isoformat()
        }
        self.redis_client.set(self.metrics_key, json.dumps(metrics))
        logger.debug(f"✅ Redis state initialized for circuit breaker '{self.name}'")
    
    def _get_state_from_redis(self) -> CircuitState:
        """Get current state from Redis."""
        if not self.redis_enabled:
            return self.state
            
        state_str = self.redis_client.get(self.state_key)
        if not state_str:
            self._initialize_redis_state()
            return CircuitState.CLOSED
        return CircuitState(state_str)
    
    def _set_state_in_redis(self, new_state: CircuitState):
        """Set state in Redis with logging."""
        if not self.redis_enabled:
            old_state = self.state
            self.state = new_state
        else:
            old_state = self._get_state_from_redis()
            if old_state == new_state:
                return
            self.redis_client.set(self.state_key, new_state.value)
            
            # Update metrics
            metrics = self._get_metrics_from_redis()
            if new_state == CircuitState.OPEN:
                metrics["circuit_opens"] = metrics.get("circuit_opens", 0) + 1
            self.redis_client.set(self.metrics_key, json.dumps(metrics))
            
            # Record history
            self._record_history_event({
                "event": "state_transition",
                "from": old_state.value,
                "to": new_state.value,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        if old_state != new_state:
            logger.warning(f"⚠️ Circuit breaker '{self.name}' state: {old_state.value} → {new_state.value}")
    
    def _get_metrics_from_redis(self) -> Dict[str, Any]:
        """Get metrics from Redis."""
        if not self.redis_enabled:
            return {
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "circuit_opens": self.stats.circuit_opens,
                "last_success_time": self.stats.last_success_time,
                "last_failure_time": self.stats.last_failure_time
            }
            
        metrics_str = self.redis_client.get(self.metrics_key)
        if not metrics_str:
            return {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "circuit_opens": 0,
                "last_success_time": None,
                "last_failure_time": None
            }
        return json.loads(str(metrics_str))
    
    def _update_metrics_in_redis(self, updates: Dict[str, Any]):
        """Update metrics in Redis."""
        if not self.redis_enabled:
            for key, value in updates.items():
                if hasattr(self.stats, key):
                    setattr(self.stats, key, value)
            return
            
        metrics = self._get_metrics_from_redis()
        metrics.update(updates)
        self.redis_client.set(self.metrics_key, json.dumps(metrics))
    
    def _record_history_event(self, event: Dict[str, Any]):
        """Record event in history (keep last 100)."""
        if not self.redis_enabled:
            return
        self.redis_client.lpush(self.history_key, json.dumps(event))
        self.redis_client.ltrim(self.history_key, 0, 99)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to protect functions with circuit breaker"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self.lock:
            # Increment total requests
            metrics = self._get_metrics_from_redis()
            metrics["total_requests"] = metrics.get("total_requests", 0) + 1
            self._update_metrics_in_redis(metrics)
            
            # Check if circuit should remain open
            if self._should_reject_request():
                error_msg = f"Circuit breaker '{self.name}' is OPEN - rejecting request"
                logger.warning(error_msg)
                raise CircuitBreakerOpenError(error_msg)
            
            # If half-open, only allow limited requests
            current_state = self._get_state_from_redis()
            if current_state == CircuitState.HALF_OPEN:
                logger.info(f"🔍 Circuit breaker '{self.name}' testing recovery")
        
        try:
            # Execute the protected function
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Record success
            self._on_success(execution_time)
            return result
            
        except Exception as e:
            # Record failure
            self._on_failure(e)
            raise
    
    def _should_reject_request(self) -> bool:
        """Determine if request should be rejected based on circuit state"""
        current_state = self._get_state_from_redis()
        
        if current_state == CircuitState.CLOSED:
            return False
        
        if current_state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.redis_enabled:
                last_failure_time = self.redis_client.get(self.last_failure_key)
                if last_failure_time:
                    elapsed = time.time() - float(str(last_failure_time))
                    if elapsed >= self.config.recovery_timeout:
                        logger.info(f"🔄 Circuit breaker '{self.name}' timeout expired, entering HALF_OPEN (waited {elapsed:.1f}s)")
                        self._set_state_in_redis(CircuitState.HALF_OPEN)
                        return False
            else:
                if time.time() - self.last_attempt_time > self.config.recovery_timeout:
                    logger.info(f"🔄 Circuit breaker '{self.name}' entering HALF_OPEN state")
                    self._set_state_in_redis(CircuitState.HALF_OPEN)
                    return False
            return True
        
        # HALF_OPEN state - allow some requests through
        return False
    
    def _on_success(self, execution_time: float):
        """Handle successful request"""
        with self.lock:
            current_state = self._get_state_from_redis()
            
            # Update metrics
            metrics = self._get_metrics_from_redis()
            metrics["successful_requests"] = metrics.get("successful_requests", 0) + 1
            metrics["last_success_time"] = datetime.utcnow().isoformat()
            self._update_metrics_in_redis(metrics)
            
            # Record history
            self._record_history_event({
                "event": "success",
                "state": current_state.value,
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if current_state == CircuitState.HALF_OPEN:
                # Success in HALF_OPEN → close circuit
                logger.info(f"✅ Circuit breaker '{self.name}' recovered successfully")
                self._close_circuit()
            elif current_state == CircuitState.CLOSED:
                # Reset failure count on success
                if self.redis_enabled:
                    self.redis_client.set(self.failures_key, 0)
            
            logger.debug(f"✅ Circuit breaker '{self.name}' recorded success ({execution_time:.2f}s)")
    
    def _on_failure(self, exception: Exception):
        """Handle failed request"""
        with self.lock:
            current_state = self._get_state_from_redis()
            
            # Increment failure counter
            if self.redis_enabled:
                failures = self.redis_client.incr(self.failures_key)
                self.redis_client.set(self.last_failure_key, time.time())
            else:
                self.stats.failed_requests += 1
                self.stats.last_failure_time = time.time()
                self.stats.recent_failures.append(time.time())
                self.last_attempt_time = time.time()
                failures = self.stats.failed_requests
            
            # Update metrics
            metrics = self._get_metrics_from_redis()
            metrics["failed_requests"] = metrics.get("failed_requests", 0) + 1
            metrics["last_failure_time"] = datetime.utcnow().isoformat()
            metrics["last_failure_error"] = str(exception)
            self._update_metrics_in_redis(metrics)
            
            # Record history
            self._record_history_event({
                "event": "failure",
                "state": current_state.value,
                "failures": failures,
                "error": str(exception),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # State transitions
            if current_state == CircuitState.HALF_OPEN:
                # Failure in HALF_OPEN → back to OPEN
                logger.error(f"❌ Circuit breaker '{self.name}' recovery failed, reopening")
                self._open_circuit()
            elif current_state == CircuitState.CLOSED:
                # Check if threshold exceeded
                if int(failures) >= self.config.failure_threshold:
                    logger.error(f"🚨 Circuit breaker '{self.name}' threshold exceeded ({failures}/{self.config.failure_threshold})")
                    self._open_circuit()
            
            logger.warning(f"❌ Circuit breaker '{self.name}' recorded failure: {exception}")
    
    def _open_circuit(self):
        """Open circuit due to failures"""
        self._set_state_in_redis(CircuitState.OPEN)
        logger.warning(f"🔴 Circuit breaker '{self.name}' OPENED due to failures")
        
        # Send Slack alert (Wave 0-10-3)
        self._send_circuit_breaker_alert()
    
    def _close_circuit(self):
        """Close circuit after successful recovery"""
        self._set_state_in_redis(CircuitState.CLOSED)
        # Reset failure count
        if self.redis_enabled:
            self.redis_client.set(self.failures_key, 0)
        logger.info(f"🟢 Circuit breaker '{self.name}' CLOSED - service recovered")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self.lock:
            current_state = self._get_state_from_redis()
            metrics = self._get_metrics_from_redis()
            
            if self.redis_enabled:
                failures_val = self.redis_client.get(self.failures_key)
                current_failures = int(str(failures_val) if failures_val else 0)
            else:
                current_failures = self.stats.failed_requests
            
            total_requests = metrics.get("total_requests", 0)
            successful_requests = metrics.get("successful_requests", 0)
            
            return {
                'name': self.name,
                'state': current_state.value,
                'current_failures': current_failures,
                'failure_threshold': self.config.failure_threshold,
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': metrics.get("failed_requests", 0),
                'circuit_opens': metrics.get("circuit_opens", 0),
                'success_rate': (successful_requests / max(1, total_requests)) * 100,
                'last_failure_time': metrics.get("last_failure_time"),
                'last_success_time': metrics.get("last_success_time"),
                'last_failure_error': metrics.get("last_failure_error"),
                'recovery_timeout': self.config.recovery_timeout,
                'redis_enabled': self.redis_enabled
            }
    
    def get_history(self, limit: int = 20) -> list:
        """Get recent circuit breaker history"""
        if not self.redis_enabled:
            return []
        history = self.redis_client.lrange(self.history_key, 0, limit - 1)
        return [json.loads(str(event)) for event in (history if isinstance(history, list) else [])]
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        with self.lock:
            self._set_state_in_redis(CircuitState.CLOSED)
            
            if self.redis_enabled:
                self.redis_client.set(self.failures_key, 0)
                self.redis_client.delete(self.last_failure_key)
                self._record_history_event({
                    "event": "manual_reset",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                self.stats = CircuitBreakerStats()
                self.last_attempt_time = 0
            
            logger.info(f"🔄 Circuit breaker '{self.name}' manually reset")
    
    def _send_circuit_breaker_alert(self):
        """Send Slack alert when circuit breaker opens (Wave 0-10-3)."""
        try:
            # Import here to avoid circular dependency
            from services.slack_service import SlackService
            
            slack = SlackService()
            if not slack.is_available():
                logger.debug(f"Slack not configured, skipping alert for '{self.name}'")
                return
            
            # Get current metrics
            metrics = self._get_metrics_from_redis()
            current_failures = int(self.redis_client.get(self.failures_key) or 0) if self.redis_enabled else self.stats.failed_requests
            
            # Send alert
            slack.send_circuit_breaker_alert(
                service_name=self.name,
                state="OPEN",
                failure_count=current_failures,
                recovery_timeout=self.config.recovery_timeout,
                last_error=metrics.get("last_failure_error")
            )
        except Exception as e:
            logger.error(f"❌ Failed to send circuit breaker alert: {e}")


def get_all_circuit_breakers(redis_url: Optional[str] = None) -> list:
    """
    Get status of all circuit breakers in Redis.
    
    Returns:
        List of circuit breaker statistics
    """
    redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Scan for all circuit breaker state keys
        circuit_breakers = []
        for key in redis_client.scan_iter("circuit_breaker:*:state"):
            service_name = key.split(":")[1]
            cb = CircuitBreaker(service_name, redis_url=redis_url)
            circuit_breakers.append(cb.get_stats())
        
        return circuit_breakers
    except Exception as e:
        logger.error(f"❌ Failed to fetch circuit breakers from Redis: {e}")
        return []


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Centralized management of circuit breakers with Redis-backed state"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
        self.redis_url = redis_url
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker by name"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config, redis_url=self.redis_url)
            return self.breakers[name]
    
    def get_all_stats(self) -> Dict[str, dict]:
        """Get statistics for all circuit breakers (local + Redis)"""
        with self.lock:
            # Get stats from local instances
            local_stats = {name: breaker.get_stats() for name, breaker in self.breakers.items()}
            
            # Also scan Redis for any other circuit breakers
            all_breakers = get_all_circuit_breakers(self.redis_url)
            redis_stats = {cb['name']: cb for cb in all_breakers}
            
            # Merge (prefer local instances)
            local_stats.update(redis_stats)
            return local_stats
    
    def health_check(self) -> dict:
        """Overall health check for all circuit breakers"""
        stats = self.get_all_stats()
        
        total_breakers = len(stats)
        open_breakers = sum(1 for s in stats.values() if s['state'] == 'open')
        half_open_breakers = sum(1 for s in stats.values() if s['state'] == 'half_open')
        
        overall_health = "healthy" if open_breakers == 0 else "degraded" if open_breakers < total_breakers else "unhealthy"
        
        return {
            'overall_health': overall_health,
            'total_breakers': total_breakers,
            'open_breakers': open_breakers,
            'half_open_breakers': half_open_breakers,
            'breakers': stats
        }

# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()

# Pre-configured circuit breakers for common services
def get_openai_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for OpenAI API calls"""
    config = CircuitBreakerConfig(
        failure_threshold=3,    # More sensitive for API calls
        recovery_timeout=30,    # Shorter recovery time
        success_threshold=2,    # Require fewer successes
        request_timeout=45      # Longer timeout for transcription
    )
    return circuit_manager.get_breaker("openai_api", config)

def get_audio_processing_circuit_breaker() -> CircuitBreaker:
    """Get circuit breaker for audio processing operations"""
    config = CircuitBreakerConfig(
        failure_threshold=5,    # More tolerant for processing errors
        recovery_timeout=60,    # Standard recovery time
        success_threshold=3,    # Standard success threshold
        request_timeout=30      # Standard timeout
    )
    return circuit_manager.get_breaker("audio_processing", config)

logger.info("🔒 Circuit Breaker service initialized")