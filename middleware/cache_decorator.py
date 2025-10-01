"""
Cache Decorator Middleware
Provides Flask route decorators for Redis caching with automatic cache invalidation.
"""

import logging
import hashlib
import json
from functools import wraps
from typing import Callable, Optional, Any
from flask import request, g
from flask_login import current_user
from services.redis_cache_service import get_cache_service

logger = logging.getLogger(__name__)


def cache_response(ttl: int = 300, prefix: str = 'analytics', 
                   key_func: Optional[Callable] = None,
                   vary_on_user: bool = True):
    """
    Decorator to cache Flask route responses in Redis.
    
    Args:
        ttl: Time-to-live in seconds (default: 300 = 5 minutes)
        prefix: Cache key prefix (analytics, session, transcription, etc.)
        key_func: Optional function to generate custom cache key
        vary_on_user: Include user ID in cache key (default: True)
    
    Usage:
        @cache_response(ttl=600, prefix='analytics')
        @login_required
        def get_analytics():
            return jsonify({'data': expensive_computation()})
    
    Example with custom key:
        def custom_key():
            return f"dashboard:{request.args.get('days', 7)}"
        
        @cache_response(ttl=1800, key_func=custom_key)
        def get_dashboard():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_service = get_cache_service()
            
            # Skip caching if Redis not available or request method is not GET
            if not cache_service.is_available() or request.method != 'GET':
                return f(*args, **kwargs)
            
            try:
                # Generate cache key
                if key_func:
                    cache_key = key_func()
                else:
                    cache_key = _generate_cache_key(
                        route=request.endpoint or '',
                        args=args,
                        kwargs=kwargs,
                        query_params=request.args.to_dict(),
                        vary_on_user=vary_on_user
                    )
                
                # Try to get from cache
                cached_response = cache_service.get(cache_key, prefix=prefix)
                if cached_response is not None:
                    logger.debug(f"🎯 Cache HIT: {prefix}:{cache_key}")
                    
                    # Add cache header for debugging
                    response_data = cached_response
                    if isinstance(response_data, tuple):
                        # Handle (response, status_code) tuples
                        return response_data
                    return response_data
                
                # Cache miss - execute function
                logger.debug(f"💨 Cache MISS: {prefix}:{cache_key}")
                result = f(*args, **kwargs)
                
                # Cache the result
                cache_service.set(cache_key, result, ttl=ttl, prefix=prefix)
                logger.debug(f"💾 Cached response: {prefix}:{cache_key} (TTL: {ttl}s)")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Cache decorator error: {e}")
                # Fall back to executing function without cache
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def invalidate_cache(prefix: str, pattern: Optional[str] = None):
    """
    Decorator to invalidate cache entries after write operations.
    
    Args:
        prefix: Cache prefix to invalidate (e.g., 'analytics', 'session')
        pattern: Optional pattern to match specific keys (e.g., 'meeting:123:*')
    
    Usage:
        @invalidate_cache(prefix='analytics', pattern='dashboard:*')
        @login_required
        def update_meeting():
            # Update meeting
            return jsonify({'success': True})
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            # Invalidate cache after successful execution
            try:
                cache_service = get_cache_service()
                if cache_service.is_available():
                    if pattern:
                        keys_to_delete = cache_service.get_keys_by_pattern(pattern, prefix=prefix)
                        for key in keys_to_delete:
                            cache_service.delete(key, prefix=prefix)
                        logger.info(f"🗑️ Invalidated {len(keys_to_delete)} cache entries: {prefix}:{pattern}")
                    else:
                        # Clear entire prefix
                        deleted = cache_service.clear_prefix(prefix)
                        logger.info(f"🗑️ Cleared cache prefix: {prefix} ({deleted} keys)")
            except Exception as e:
                logger.error(f"❌ Cache invalidation error: {e}")
            
            return result
        
        return decorated_function
    return decorator


def invalidate_meeting_cache(meeting_id: int):
    """
    Invalidate all cache entries related to a specific meeting.
    
    Args:
        meeting_id: Meeting ID to invalidate cache for
    """
    try:
        cache_service = get_cache_service()
        if cache_service.is_available():
            # Invalidate analytics cache for this meeting
            cache_service.delete(f"meeting:{meeting_id}", prefix='analytics')
            
            # Invalidate dashboard cache (contains meeting data)
            cache_service.clear_prefix('analytics')
            
            # Invalidate session cache if exists
            cache_service.delete(str(meeting_id), prefix='session')
            
            logger.info(f"🗑️ Invalidated cache for meeting {meeting_id}")
    except Exception as e:
        logger.error(f"❌ Error invalidating meeting cache: {e}")


def invalidate_user_cache(user_id: Optional[int] = None):
    """
    Invalidate cache entries for a specific user.
    
    Args:
        user_id: User ID to invalidate cache for (defaults to current_user)
    """
    try:
        if user_id is None and hasattr(current_user, 'id'):
            user_id = current_user.id
        
        if user_id is None:
            return
        
        cache_service = get_cache_service()
        if cache_service.is_available():
            # Invalidate user-specific analytics
            pattern = f"*:user:{user_id}:*"
            keys = cache_service.get_keys_by_pattern(pattern, prefix='analytics')
            for key in keys:
                cache_service.delete(key, prefix='analytics')
            
            logger.info(f"🗑️ Invalidated cache for user {user_id}")
    except Exception as e:
        logger.error(f"❌ Error invalidating user cache: {e}")


def _generate_cache_key(route: str, args: tuple, kwargs: dict, 
                        query_params: dict, vary_on_user: bool = True) -> str:
    """
    Generate a cache key based on route, arguments, and query parameters.
    
    Returns:
        Cache key string
    """
    key_parts = [route]
    
    # Add user ID if vary_on_user is True
    if vary_on_user and hasattr(current_user, 'id'):
        key_parts.append(f"user:{current_user.id}")
    
    # Add route arguments (e.g., meeting_id from URL)
    if args:
        key_parts.append(":".join(str(arg) for arg in args))
    if kwargs:
        key_parts.append(":".join(f"{k}={v}" for k, v in sorted(kwargs.items())))
    
    # Add query parameters (sorted for consistent keys)
    if query_params:
        query_str = ":".join(f"{k}={v}" for k, v in sorted(query_params.items()))
        key_parts.append(query_str)
    
    # Join all parts
    cache_key = ":".join(key_parts)
    
    # Hash if too long (Redis key limit is 512MB but shorter is better)
    if len(cache_key) > 200:
        cache_key = hashlib.md5(cache_key.encode()).hexdigest()
    
    return cache_key


# Convenience cache invalidation helpers
def invalidate_analytics_cache():
    """Clear all analytics cache entries."""
    cache_service = get_cache_service()
    if cache_service.is_available():
        deleted = cache_service.clear_prefix('analytics')
        logger.info(f"🗑️ Cleared analytics cache ({deleted} keys)")


def invalidate_session_cache_by_id(session_id: str):
    """Invalidate cache for a specific session."""
    from services.redis_cache_service import invalidate_session_cache
    invalidate_session_cache(session_id)


logger.info("✅ Cache decorator middleware loaded")
