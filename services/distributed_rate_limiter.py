#!/usr/bin/env python3
"""
🔒 Production Feature: Distributed Rate Limiting

Implements comprehensive rate limiting using Redis backend for distributed scaling.
Prevents abuse and ensures fair resource allocation across all API endpoints.

Key Features:
- Redis-backed distributed rate limiting
- Per-IP, per-user, and per-endpoint limits
- Sliding window algorithm
- Burst protection and backoff
- Rate limit headers for clients
- Whitelist/blacklist support
"""

import logging
import time
import hashlib
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from flask import request, jsonify, current_app
import redis
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Global limits
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    
    # Burst protection
    burst_limit: int = 10  # Max requests in 1 second
    burst_window: int = 1  # seconds
    
    # WebSocket limits
    ws_connections_per_ip: int = 5
    ws_messages_per_minute: int = 300
    
    # API endpoint specific limits
    auth_attempts_per_minute: int = 5
    upload_requests_per_hour: int = 50
    transcription_requests_per_minute: int = 20
    
    # Advanced features
    enable_whitelist: bool = True
    enable_blacklist: bool = True
    enable_progressive_backoff: bool = True
    
    # Cleanup settings
    cleanup_interval: int = 3600  # 1 hour
    key_expiry: int = 86400  # 24 hours

class DistributedRateLimiter:
    """
    🚀 Production-grade distributed rate limiter.
    
    Uses Redis for shared state across multiple application instances.
    Implements multiple rate limiting strategies with enterprise features.
    """
    
    def __init__(self, redis_client: redis.Redis, config: Optional[RateLimitConfig] = None):
        self.redis_client = redis_client
        self.config = config or RateLimitConfig()
        
        # Rate limit keys
        self.key_prefix = "rate_limit"
        self.whitelist_key = f"{self.key_prefix}:whitelist"
        self.blacklist_key = f"{self.key_prefix}:blacklist"
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'blocked_requests': 0,
            'burst_blocks': 0,
            'rate_limit_blocks': 0
        }
        
        logger.info("🔒 Distributed Rate Limiter initialized")
    
    def get_client_identifier(self) -> str:
        """Get unique identifier for the client."""
        # Try to get real IP from headers (for reverse proxies)
        client_ip = request.headers.get('X-Forwarded-For', 
                    request.headers.get('X-Real-IP', 
                    request.remote_addr))
        
        # Take first IP if comma-separated
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Add user ID if authenticated
        user_id = getattr(request, 'user_id', None)
        if user_id:
            return f"user:{user_id}:{client_ip}"
        
        return f"ip:{client_ip}"
    
    def is_whitelisted(self, identifier: str) -> bool:
        """Check if client is whitelisted."""
        if not self.config.enable_whitelist:
            return False
        
        try:
            result = self.redis_client.sismember(self.whitelist_key, identifier)
            return bool(result)
        except Exception as e:
            logger.error(f"Whitelist check error: {e}")
            return False
    
    def is_blacklisted(self, identifier: str) -> bool:
        """Check if client is blacklisted."""
        if not self.config.enable_blacklist:
            return False
        
        try:
            result = self.redis_client.sismember(self.blacklist_key, identifier)
            return bool(result)
        except Exception as e:
            logger.error(f"Blacklist check error: {e}")
            return False
    
    def check_rate_limit(self, identifier: str, endpoint: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """
        Check rate limit using sliding window algorithm.
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        now = int(time.time())
        key = f"{self.key_prefix}:{identifier}:{endpoint}:{window}"
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, window + 60)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for current request
            
            rate_limit_info = {
                'limit': limit,
                'remaining': max(0, limit - current_count),
                'reset_time': now + window,
                'retry_after': window if current_count > limit else 0
            }
            
            is_allowed = current_count <= limit
            
            if not is_allowed:
                # Remove the request we just added since it's not allowed
                self.redis_client.zrem(key, str(now))
                self.stats['rate_limit_blocks'] += 1
                logger.warning(f"Rate limit exceeded for {identifier} on {endpoint}: {current_count}/{limit}")
            
            return is_allowed, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Fail open in case of Redis issues
            return True, {'limit': limit, 'remaining': limit, 'reset_time': now + window, 'retry_after': 0}
    
    def check_burst_protection(self, identifier: str) -> Tuple[bool, Dict]:
        """Check burst protection (short-term rate limiting)."""
        return self.check_rate_limit(
            identifier, 
            "burst", 
            self.config.burst_limit, 
            self.config.burst_window
        )
    
    def get_endpoint_limits(self, endpoint: str) -> Tuple[int, int]:
        """Get rate limits for specific endpoint."""
        endpoint_limits = {
            '/auth/login': (self.config.auth_attempts_per_minute, 60),
            '/auth/register': (self.config.auth_attempts_per_minute, 60),
            '/api/upload': (self.config.upload_requests_per_hour, 3600),
            '/api/transcribe': (self.config.transcription_requests_per_minute, 60),
            '/socket.io/': (self.config.ws_messages_per_minute, 60),
        }
        
        # Default limits
        return endpoint_limits.get(endpoint, (self.config.requests_per_minute, 60))
    
    def apply_progressive_backoff(self, identifier: str, violations: int) -> int:
        """Apply progressive backoff based on violation history."""
        if not self.config.enable_progressive_backoff:
            return 0
        
        # Exponential backoff: 2^violations minutes (max 60 minutes)
        backoff_minutes = min(2 ** violations, 60)
        backoff_key = f"{self.key_prefix}:backoff:{identifier}"
        
        try:
            self.redis_client.setex(backoff_key, backoff_minutes * 60, violations)
            logger.info(f"Applied {backoff_minutes}min backoff to {identifier} ({violations} violations)")
            return backoff_minutes * 60
        except Exception as e:
            logger.error(f"Backoff application error: {e}")
            return 0
    
    def is_in_backoff(self, identifier: str) -> Tuple[bool, int]:
        """Check if client is in backoff period."""
        backoff_key = f"{self.key_prefix}:backoff:{identifier}"
        
        try:
            ttl = self.redis_client.ttl(backoff_key)
            ttl = int(ttl) if ttl is not None else -1
            if ttl > 0:
                violations_val = self.redis_client.get(backoff_key)
                violations = int(violations_val) if violations_val else 0
                return True, ttl
            return False, 0
        except Exception as e:
            logger.error(f"Backoff check error: {e}")
            return False, 0
    
    def add_to_whitelist(self, identifier: str, ttl: Optional[int] = None):
        """Add client to whitelist."""
        try:
            self.redis_client.sadd(self.whitelist_key, identifier)
            if ttl:
                self.redis_client.expire(self.whitelist_key, ttl)
            logger.info(f"Added {identifier} to whitelist")
        except Exception as e:
            logger.error(f"Whitelist add error: {e}")
    
    def add_to_blacklist(self, identifier: str, ttl: Optional[int] = None):
        """Add client to blacklist."""
        try:
            self.redis_client.sadd(self.blacklist_key, identifier)
            if ttl:
                self.redis_client.expire(self.blacklist_key, ttl)
            logger.info(f"Added {identifier} to blacklist")
        except Exception as e:
            logger.error(f"Blacklist add error: {e}")
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        try:
            whitelist_count = int(self.redis_client.scard(self.whitelist_key) or 0)
            blacklist_count = int(self.redis_client.scard(self.blacklist_key) or 0)
            
            return {
                **self.stats,
                'whitelist_count': whitelist_count,
                'blacklist_count': blacklist_count,
                'block_rate': self.stats['blocked_requests'] / max(1, self.stats['total_requests'])
            }
        except Exception as e:
            logger.error(f"Stats retrieval error: {e}")
            return self.stats

def rate_limit(requests_per_minute: Optional[int] = None, 
               requests_per_hour: Optional[int] = None,
               endpoint_specific: bool = True):
    """
    Decorator for applying rate limits to Flask routes.
    
    Args:
        requests_per_minute: Override default per-minute limit
        requests_per_hour: Override default per-hour limit  
        endpoint_specific: Use endpoint-specific limits
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get rate limiter from app context
            rate_limiter = getattr(current_app, 'rate_limiter', None)
            if not rate_limiter:
                logger.warning("Rate limiter not configured - allowing request")
                return f(*args, **kwargs)
            
            # Update stats
            rate_limiter.stats['total_requests'] += 1
            
            # Get client identifier
            identifier = rate_limiter.get_client_identifier()
            
            # Check blacklist
            if rate_limiter.is_blacklisted(identifier):
                rate_limiter.stats['blocked_requests'] += 1
                return jsonify({
                    'error': 'Access denied',
                    'code': 'BLACKLISTED'
                }), 403
            
            # Check whitelist (bypass rate limits)
            if rate_limiter.is_whitelisted(identifier):
                return f(*args, **kwargs)
            
            # Check backoff period
            in_backoff, backoff_ttl = rate_limiter.is_in_backoff(identifier)
            if in_backoff:
                rate_limiter.stats['blocked_requests'] += 1
                return jsonify({
                    'error': 'Rate limit exceeded - backoff period active',
                    'retry_after': backoff_ttl,
                    'code': 'BACKOFF_ACTIVE'
                }), 429
            
            # Check burst protection
            burst_allowed, burst_info = rate_limiter.check_burst_protection(identifier)
            if not burst_allowed:
                rate_limiter.stats['burst_blocks'] += 1
                rate_limiter.stats['blocked_requests'] += 1
                return jsonify({
                    'error': 'Rate limit exceeded - too many requests',
                    'retry_after': burst_info['retry_after'],
                    'code': 'BURST_LIMIT'
                }), 429
            
            # Get endpoint limits
            endpoint = request.endpoint or request.path
            if endpoint_specific:
                limit, window = rate_limiter.get_endpoint_limits(endpoint)
            else:
                limit = requests_per_minute or rate_limiter.config.requests_per_minute
                window = 60
            
            # Check rate limit
            allowed, rate_info = rate_limiter.check_rate_limit(identifier, endpoint, limit, window)
            
            if not allowed:
                rate_limiter.stats['blocked_requests'] += 1
                
                # Track violations for progressive backoff
                violation_key = f"rate_limit:violations:{identifier}"
                try:
                    violations = int(rate_limiter.redis_client.get(violation_key) or 0) + 1
                    rate_limiter.redis_client.setex(violation_key, 3600, violations)  # 1 hour
                    
                    # Apply backoff if too many violations
                    if violations >= 3:
                        backoff_duration = rate_limiter.apply_progressive_backoff(identifier, violations)
                        rate_info['backoff_applied'] = backoff_duration
                except Exception as e:
                    logger.error(f"Violation tracking error: {e}")
                
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': rate_info['limit'],
                    'retry_after': rate_info['retry_after'],
                    'code': 'RATE_LIMIT_EXCEEDED'
                })
                
                # Add rate limit headers
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])
                response.headers['Retry-After'] = str(rate_info['retry_after'])
                
                return response, 429
            
            # Add rate limit headers to successful responses
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(rate_info['reset_time'])
            
            return response
        
        return decorated_function
    return decorator

# Initialize global rate limiter instance
rate_limiter = None

def init_rate_limiter(app, redis_client: redis.Redis, config: Optional[RateLimitConfig] = None):
    """Initialize rate limiter for Flask app."""
    global rate_limiter
    rate_limiter = DistributedRateLimiter(redis_client, config)
    app.rate_limiter = rate_limiter
    
    logger.info("🔒 Distributed rate limiter initialized for Flask app")
    return rate_limiter