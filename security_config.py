"""
Production security configuration for Mina
Implements security best practices for production deployment
"""
import os
import logging
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, abort, current_app
import redis
import time

logger = logging.getLogger(__name__)

class SecurityConfig:
    """Production security configuration and middleware."""
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client or self._get_redis_client()
        
        # Security settings
        self.rate_limits = {
            'api': {'requests': 100, 'window': 300},  # 100 requests per 5 minutes
            'websocket': {'requests': 50, 'window': 300},  # 50 connections per 5 minutes
            'transcription': {'requests': 20, 'window': 300}  # 20 transcriptions per 5 minutes
        }
        
        self.blocked_ips = set()
        self.trusted_proxies = ['127.0.0.1', '::1']
        
        if app:
            self.init_app(app)
    
    def _get_redis_client(self):
        """Get Redis client for rate limiting."""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            return redis.from_url(redis_url)
        except Exception as e:
            logger.warning(f"Redis not available for rate limiting: {e}")
            return None
    
    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.before_request(self.before_request_security_check)
        app.after_request(self.after_request_security_headers)
    
    def get_client_ip(self) -> str:
        """Get real client IP, handling proxies."""
        # Check for X-Forwarded-For header (from load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(',')[0].strip()
        
        # Check for X-Real-IP header (from reverse proxies)
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to remote_addr
        return request.remote_addr or 'unknown'
    
    def is_rate_limited(self, client_ip: str, rate_type: str = 'api') -> bool:
        """Check if client is rate limited using Redis."""
        if not self.redis_client:
            return False  # Skip rate limiting if Redis unavailable
        
        try:
            limits = self.rate_limits.get(rate_type, self.rate_limits['api'])
            key = f"rate_limit:{rate_type}:{client_ip}"
            window = limits['window']
            max_requests = limits['requests']
            
            current_time = int(time.time())
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, window)
            
            results = pipe.execute()
            request_count = results[1]
            
            return request_count >= max_requests
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return False  # Fail open on errors
    
    def validate_audio_content(self, content: bytes) -> bool:
        """Validate audio content for security threats."""
        # Check file size
        max_size = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size:
            return False
        
        # Basic content validation
        if len(content) < 100:  # Too small to be valid audio
            return False
        
        # Check for suspicious patterns (basic malware detection)
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'data:text/html',
            b'<?xml',
            b'<!DOCTYPE'
        ]
        
        content_lower = content.lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                logger.warning(f"Suspicious pattern detected in audio content: {pattern}")
                return False
        
        return True
    
    def before_request_security_check(self):
        """Security checks before processing requests."""
        client_ip = self.get_client_ip()
        
        # Check blocked IPs
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            abort(403)
        
        # Rate limiting
        endpoint = request.endpoint or 'unknown'
        if 'api' in request.path:
            if self.is_rate_limited(client_ip, 'api'):
                logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
                abort(429)
        elif 'socket.io' in request.path:
            if self.is_rate_limited(client_ip, 'websocket'):
                logger.warning(f"WebSocket rate limit exceeded for {client_ip}")
                abort(429)
        
        # Content type validation for API endpoints
        if request.method in ['POST', 'PUT', 'PATCH'] and '/api/' in request.path:
            content_type = request.headers.get('Content-Type', '')
            if 'application/json' not in content_type and 'multipart/form-data' not in content_type:
                if not content_type.startswith('audio/'):
                    logger.warning(f"Invalid content type from {client_ip}: {content_type}")
                    abort(400)
    
    def after_request_security_headers(self, response):
        """Add security headers to all responses."""
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS header for HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # CSP header
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.socket.io; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' wss: ws:; "
            "media-src 'self' blob:; "
            "img-src 'self' data:;"
        )
        response.headers['Content-Security-Policy'] = csp
        
        return response
    
    def block_ip(self, ip: str, reason: str = "Security violation"):
        """Block an IP address."""
        self.blocked_ips.add(ip)
        logger.warning(f"Blocked IP {ip}: {reason}")
        
        # Store in Redis for persistence across restarts
        if self.redis_client:
            try:
                self.redis_client.sadd('blocked_ips', ip)
                self.redis_client.expire('blocked_ips', 86400 * 7)  # 7 days
            except Exception as e:
                logger.error(f"Failed to store blocked IP in Redis: {e}")
    
    def unblock_ip(self, ip: str):
        """Unblock an IP address."""
        self.blocked_ips.discard(ip)
        
        if self.redis_client:
            try:
                self.redis_client.srem('blocked_ips', ip)
            except Exception as e:
                logger.error(f"Failed to remove blocked IP from Redis: {e}")
    
    def load_blocked_ips(self):
        """Load blocked IPs from Redis."""
        if self.redis_client:
            try:
                blocked_raw = self.redis_client.smembers('blocked_ips')
                if blocked_raw:
                    self.blocked_ips = {ip.decode() if isinstance(ip, bytes) else str(ip) for ip in blocked_raw}
                else:
                    self.blocked_ips = set()
                logger.info(f"Loaded {len(self.blocked_ips)} blocked IPs from Redis")
            except Exception as e:
                logger.error(f"Failed to load blocked IPs from Redis: {e}")
                self.blocked_ips = set()

def require_api_key(f):
    """Decorator to require API key for sensitive endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = os.getenv('API_SECRET_KEY')
        
        if not expected_key:
            logger.error("API_SECRET_KEY not configured")
            abort(500)
        
        if not api_key or api_key != expected_key:
            logger.warning(f"Invalid API key from {request.remote_addr}")
            abort(401)
        
        return f(*args, **kwargs)
    return decorated_function

def validate_session_token(f):
    """Decorator to validate session tokens."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            abort(401)
        
        # Add token validation logic here
        # This would integrate with your session management system
        
        return f(*args, **kwargs)
    return decorated_function