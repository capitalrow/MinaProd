"""
Redis Connection Manager with Failover and Retry Logic

Provides robust Redis connectivity with:
- Automatic connection retry
- Health monitoring
- Graceful fallback to in-memory cache
- Connection pool management
"""

import redis
import time
import logging
from typing import Optional, Any, Callable
from functools import wraps
import threading
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RedisConnectionState:
    """Redis connection states"""
    CONNECTED = 'connected'
    DISCONNECTED = 'disconnected'
    RECONNECTING = 'reconnecting'
    FALLBACK = 'fallback'


class RedisConnectionManager:
    """
    Manages Redis connections with automatic failover and retry
    
    Features:
    - Automatic reconnection with exponential backoff
    - Health check monitoring
    - Graceful fallback to in-memory cache
    - Connection pool management
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: int = 2,
        health_check_interval: int = 30,
        connection_timeout: int = 5
    ):
        self.redis_url = redis_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.health_check_interval = health_check_interval
        self.connection_timeout = connection_timeout
        
        self.client: Optional[redis.Redis] = None
        self.state = RedisConnectionState.DISCONNECTED
        self.last_error = None
        self.retry_count = 0
        self.fallback_cache = {}  # In-memory fallback
        self.health_check_thread = None
        self.running = False
        
        # Statistics
        self.total_operations = 0
        self.failed_operations = 0
        self.fallback_operations = 0
        self.last_health_check = None
        self.connection_errors = []
        
        # Connect on initialization
        if redis_url:
            self.connect()
    
    def connect(self) -> bool:
        """
        Establish Redis connection with retry logic
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not self.redis_url:
            logger.warning("No Redis URL configured. Using in-memory fallback.")
            self.state = RedisConnectionState.FALLBACK
            return False
        
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"Connecting to Redis (attempt {attempt}/{self.max_retries})...")
                
                self.client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=self.connection_timeout,
                    socket_keepalive=True,
                    health_check_interval=self.health_check_interval
                )
                
                # Test connection
                self.client.ping()
                
                self.state = RedisConnectionState.CONNECTED
                self.retry_count = 0
                self.last_error = None
                
                logger.info("✅ Redis connected successfully")
                
                # Start health check thread
                self._start_health_check()
                
                return True
                
            except (redis.ConnectionError, redis.TimeoutError) as e:
                self.last_error = str(e)
                self.connection_errors.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': str(e),
                    'attempt': attempt
                })
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.warning(
                        f"Redis connection failed (attempt {attempt}/{self.max_retries}). "
                        f"Retry in {delay}s. Error: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Redis connection failed after {self.max_retries} attempts. "
                        f"Falling back to in-memory cache. Error: {e}"
                    )
                    self.state = RedisConnectionState.FALLBACK
                    return False
            
            except Exception as e:
                logger.error(f"Unexpected Redis connection error: {e}")
                self.last_error = str(e)
                self.state = RedisConnectionState.FALLBACK
                return False
        
        return False
    
    def disconnect(self):
        """Disconnect from Redis"""
        self.running = False
        
        if self.client:
            try:
                self.client.close()
                logger.info("Redis disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting Redis: {e}")
        
        self.state = RedisConnectionState.DISCONNECTED
        self.client = None
    
    def reconnect(self) -> bool:
        """Manually trigger reconnection"""
        logger.info("Manual Redis reconnection triggered")
        self.disconnect()
        return self.connect()
    
    def _start_health_check(self):
        """Start background health check thread"""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return
        
        self.running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop,
            name="RedisHealthCheck",
            daemon=True
        )
        self.health_check_thread.start()
        logger.info("Redis health check thread started")
    
    def _health_check_loop(self):
        """Background health check loop"""
        while self.running:
            try:
                time.sleep(self.health_check_interval)
                
                if self.state == RedisConnectionState.CONNECTED:
                    # Ping Redis to verify connection
                    try:
                        self.client.ping()
                        self.last_health_check = datetime.utcnow()
                    except (redis.ConnectionError, redis.TimeoutError) as e:
                        logger.error(f"Redis health check failed: {e}")
                        self.state = RedisConnectionState.RECONNECTING
                        
                        # Attempt reconnection
                        if self.connect():
                            logger.info("Redis reconnected successfully")
                        else:
                            logger.error("Redis reconnection failed. Using fallback.")
                            self.state = RedisConnectionState.FALLBACK
                
                elif self.state == RedisConnectionState.FALLBACK:
                    # Periodically try to reconnect
                    logger.info("Attempting to restore Redis connection from fallback...")
                    if self.connect():
                        logger.info("✅ Redis connection restored")
                        # Optionally: sync fallback cache to Redis
                        self._sync_fallback_to_redis()
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    def _sync_fallback_to_redis(self):
        """Sync in-memory fallback cache to Redis after reconnection"""
        if not self.fallback_cache:
            return
        
        try:
            logger.info(f"Syncing {len(self.fallback_cache)} items from fallback to Redis...")
            for key, value in self.fallback_cache.items():
                self.client.set(key, value)
            
            self.fallback_cache.clear()
            logger.info("Fallback cache synced successfully")
        except Exception as e:
            logger.error(f"Error syncing fallback cache: {e}")
    
    def execute_with_fallback(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute Redis operation with automatic fallback
        
        Args:
            operation: Redis operation to execute (e.g., client.get, client.set)
            *args: Operation arguments
            **kwargs: Operation keyword arguments
        
        Returns:
            Operation result or fallback value
        """
        self.total_operations += 1
        
        if self.state == RedisConnectionState.CONNECTED:
            try:
                result = operation(*args, **kwargs)
                return result
            
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis operation failed: {e}. Using fallback.")
                self.failed_operations += 1
                self.state = RedisConnectionState.RECONNECTING
                
                # Trigger reconnection in background
                threading.Thread(target=self.connect, daemon=True).start()
                
                # Fall through to fallback
        
        # Use fallback (in-memory cache)
        self.fallback_operations += 1
        return self._fallback_operation(operation.__name__, *args, **kwargs)
    
    def _fallback_operation(self, operation_name: str, *args, **kwargs) -> Any:
        """Execute operation using in-memory fallback"""
        if operation_name == 'get':
            key = args[0]
            return self.fallback_cache.get(key)
        
        elif operation_name == 'set':
            key, value = args[0], args[1]
            self.fallback_cache[key] = value
            return True
        
        elif operation_name == 'delete':
            key = args[0]
            return self.fallback_cache.pop(key, None) is not None
        
        elif operation_name == 'exists':
            key = args[0]
            return key in self.fallback_cache
        
        elif operation_name == 'keys':
            pattern = args[0] if args else '*'
            # Simple pattern matching for fallback
            import fnmatch
            return [k for k in self.fallback_cache.keys() if fnmatch.fnmatch(k, pattern)]
        
        else:
            logger.warning(f"Fallback not implemented for operation: {operation_name}")
            return None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis with fallback"""
        if self.state == RedisConnectionState.CONNECTED:
            return self.execute_with_fallback(self.client.get, key)
        else:
            return self.fallback_cache.get(key)
    
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with fallback"""
        if self.state == RedisConnectionState.CONNECTED:
            return self.execute_with_fallback(self.client.set, key, value, ex=ex)
        else:
            self.fallback_cache[key] = value
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from Redis with fallback"""
        if self.state == RedisConnectionState.CONNECTED:
            return self.execute_with_fallback(self.client.delete, key) > 0
        else:
            return self.fallback_cache.pop(key, None) is not None
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis with fallback"""
        if self.state == RedisConnectionState.CONNECTED:
            return self.execute_with_fallback(self.client.exists, key) > 0
        else:
            return key in self.fallback_cache
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            'state': self.state,
            'total_operations': self.total_operations,
            'failed_operations': self.failed_operations,
            'fallback_operations': self.fallback_operations,
            'fallback_cache_size': len(self.fallback_cache),
            'success_rate': (
                (self.total_operations - self.failed_operations) / self.total_operations * 100
                if self.total_operations > 0 else 100
            ),
            'last_error': self.last_error,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'recent_errors': self.connection_errors[-5:] if self.connection_errors else []
        }


def redis_failover(fallback_value: Any = None):
    """
    Decorator for Redis operations with automatic fallback
    
    Usage:
        redis_manager = RedisConnectionManager(redis_url="redis://localhost:6379")
        
        @redis_failover(fallback_value={})
        def get_cached_data(key):
            return redis_manager.get(key)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis operation failed in {func.__name__}: {e}. Using fallback.")
                return fallback_value
        return wrapper
    return decorator


# Global Redis manager instance (initialized in app.py)
redis_manager: Optional[RedisConnectionManager] = None


def init_redis_manager(redis_url: Optional[str]) -> RedisConnectionManager:
    """Initialize global Redis manager"""
    global redis_manager
    redis_manager = RedisConnectionManager(redis_url=redis_url)
    return redis_manager


# Example usage:
if __name__ == "__main__":
    # Initialize manager
    manager = RedisConnectionManager(redis_url="redis://localhost:6379")
    
    # Test operations
    manager.set("test_key", "test_value")
    print("Get:", manager.get("test_key"))
    
    # Check stats
    print("\nStats:", manager.get_stats())
    
    # Simulate connection loss and test fallback
    manager.disconnect()
    manager.set("fallback_key", "fallback_value")  # Uses in-memory cache
    print("Fallback get:", manager.get("fallback_key"))
    
    # Stats after fallback
    print("\nStats after fallback:", manager.get_stats())
