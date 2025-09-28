"""
🔒 CIRCUIT BREAKER SERVICE: Robust API failure protection
Implements circuit breaker pattern to prevent cascading failures
"""

import time
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Callable, Any, Optional
from collections import deque

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
    Production-grade circuit breaker implementation
    Protects external services from cascade failures
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.lock = threading.RLock()
        self.last_attempt_time = 0
        
        logger.info(f"🔒 Circuit breaker '{name}' initialized with config: {self.config}")
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to protect functions with circuit breaker"""
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self.lock:
            self.stats.total_requests += 1
            
            # Check if circuit should remain open
            if self._should_reject_request():
                error_msg = f"Circuit breaker '{self.name}' is OPEN - rejecting request"
                logger.warning(error_msg)
                raise CircuitBreakerOpenError(error_msg)
            
            # If half-open, only allow limited requests
            if self.state == CircuitState.HALF_OPEN:
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
        if self.state == CircuitState.CLOSED:
            return False
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_attempt_time > self.config.recovery_timeout:
                logger.info(f"🔄 Circuit breaker '{self.name}' entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                return False
            return True
        
        # HALF_OPEN state - allow some requests through
        return False
    
    def _on_success(self, execution_time: float):
        """Handle successful request"""
        with self.lock:
            self.stats.successful_requests += 1
            self.stats.last_success_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Check if we have enough successes to close circuit
                recent_successes = self._count_recent_successes()
                if recent_successes >= self.config.success_threshold:
                    self._close_circuit()
            
            logger.debug(f"✅ Circuit breaker '{self.name}' recorded success ({execution_time:.2f}s)")
    
    def _on_failure(self, exception: Exception):
        """Handle failed request"""
        with self.lock:
            self.stats.failed_requests += 1
            self.stats.last_failure_time = time.time()
            self.stats.recent_failures.append(time.time())
            self.last_attempt_time = time.time()
            
            # Check if we should open the circuit
            if self._should_open_circuit():
                self._open_circuit()
            
            logger.warning(f"❌ Circuit breaker '{self.name}' recorded failure: {exception}")
    
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened due to failures"""
        if self.state == CircuitState.OPEN:
            return False
        
        # Count recent failures within window
        current_time = time.time()
        recent_failures = sum(1 for failure_time in self.stats.recent_failures 
                            if current_time - failure_time < 60)  # Last minute
        
        return recent_failures >= self.config.failure_threshold
    
    def _open_circuit(self):
        """Open circuit due to failures"""
        self.state = CircuitState.OPEN
        self.stats.circuit_opens += 1
        logger.warning(f"🔴 Circuit breaker '{self.name}' OPENED due to failures")
    
    def _close_circuit(self):
        """Close circuit after successful recovery"""
        self.state = CircuitState.CLOSED
        logger.info(f"🟢 Circuit breaker '{self.name}' CLOSED - service recovered")
    
    def _count_recent_successes(self) -> int:
        """Count recent successful requests"""
        # For simplicity, we'll use a basic counter
        # In production, you'd want a more sophisticated sliding window
        return min(self.stats.successful_requests, self.config.success_threshold)
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'total_requests': self.stats.total_requests,
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'circuit_opens': self.stats.circuit_opens,
                'success_rate': (self.stats.successful_requests / max(1, self.stats.total_requests)) * 100,
                'last_failure_time': self.stats.last_failure_time,
                'last_success_time': self.stats.last_success_time,
                'recent_failures_count': len(self.stats.recent_failures)
            }
    
    def reset(self):
        """Reset circuit breaker to initial state"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.stats = CircuitBreakerStats()
            self.last_attempt_time = 0
            logger.info(f"🔄 Circuit breaker '{self.name}' reset")

class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreakerManager:
    """Centralized management of circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.RLock()
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker by name"""
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(name, config)
            return self.breakers[name]
    
    def get_all_stats(self) -> Dict[str, dict]:
        """Get statistics for all circuit breakers"""
        with self.lock:
            return {name: breaker.get_stats() for name, breaker in self.breakers.items()}
    
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