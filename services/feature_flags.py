from __future__ import annotations
import os
import logging
from functools import wraps
from typing import Optional
from flask import request, abort
from models.core_models import FeatureFlag
from extensions import db

logger = logging.getLogger(__name__)


class _Flags:
    def __init__(self):
        self._cache = None
        self.redis_client = None
        self.cache_ttl = 300
        self._init_redis()
    
    def _init_redis(self):
        redis_url = os.environ.get("REDIS_URL")
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                self.redis_client.ping()
                logger.info("✅ Feature flag Redis cache initialized")
            except Exception as e:
                logger.warning(f"⚠️ Redis connection failed for feature flags, using DB-only: {e}")
                self.redis_client = None
        else:
            logger.info("ℹ️ No REDIS_URL, feature flags using database-only mode")
    
    def get(self, key: str, default: bool = False) -> bool:
        cache_key = f"feature_flag:{key}"
        
        if self.redis_client:
            try:
                cached_value = self.redis_client.get(cache_key)
                if cached_value is not None:
                    return str(cached_value).lower() == 'true'
            except Exception as e:
                logger.warning(f"Redis cache read failed for {key}: {e}")
        
        if self._cache is None:
            self._cache = {f.key: f.enabled for f in FeatureFlag.query.all()}
        
        result = self._cache.get(key, default)
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    'true' if result else 'false'
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed for {key}: {e}")
        
        return result
    
    def set(self, key: str, enabled: bool, note: Optional[str] = None, updated_by: Optional[str] = None) -> bool:
        try:
            flag = FeatureFlag.query.filter_by(key=key).first()
            
            if flag is None:
                flag = FeatureFlag(key=key, enabled=enabled, note=note or f"Feature flag: {key}")  # type: ignore
                db.session.add(flag)
            else:
                flag.enabled = enabled
                if note:
                    flag.note = note
            
            db.session.commit()
            
            self.invalidate_cache(key)
            
            logger.info(f"✅ Feature flag updated: {key} = {enabled} (by {updated_by or 'system'})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set feature flag {key}: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def get_all(self):
        try:
            flags = FeatureFlag.query.all()
            return {
                'flags': [flag.to_dict() for flag in flags],
                'cache_backend': 'redis' if self.redis_client else 'database'
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch feature flags: {e}", exc_info=True)
            return {'flags': [], 'error': str(e)}
    
    def invalidate_cache(self, key: Optional[str] = None):
        self._cache = None
        
        if self.redis_client:
            try:
                if key:
                    cache_key = f"feature_flag:{key}"
                    self.redis_client.delete(cache_key)
                    logger.info(f"✅ Invalidated cache for flag: {key}")
                else:
                    pattern = "feature_flag:*"
                    cursor = 0
                    deleted_count = 0
                    while True:
                        cursor, keys_batch = self.redis_client.scan(cursor, match=pattern, count=100)  # type: ignore
                        if keys_batch:
                            self.redis_client.delete(*keys_batch)  # type: ignore
                            deleted_count += len(keys_batch)  # type: ignore
                        if cursor == 0:
                            break
                    if deleted_count > 0:
                        logger.info(f"✅ Invalidated {deleted_count} feature flag cache entries")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")


flags = _Flags()


def require_flag(key: str, default: bool = False):
    def deco(fn):
        @wraps(fn)
        def inner(*a, **kw):
            if not flags.get(key, default):
                abort(403, f"Feature '{key}' disabled")
            return fn(*a, **kw)
        return inner
    return deco


def require_flag_admin(fn):
    @wraps(fn)
    def inner(*a, **kw):
        try:
            from flask_login import current_user
            
            if not current_user.is_authenticated:
                abort(401, "Authentication required")
            
            if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
                abort(403, "Admin access required")
            
            return fn(*a, **kw)
        except ImportError:
            logger.error("Flask-Login not available for admin check")
            abort(500, "Authentication system unavailable")
    return inner


def check_feature_flag(key: str, default: bool = False) -> bool:
    return flags.get(key, default)
