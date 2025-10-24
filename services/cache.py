# services/cache.py
import os
from typing import Optional

try:
    import redis  # pip install redis
except Exception:  # redis not installed
    redis = None

class _NoopCache:
    def delete_prefix(self, prefix: str) -> int:
        return 0

class _RedisCache:
    def __init__(self, url: str):
        self._r = redis.from_url(url, decode_responses=True)

    def delete_prefix(self, prefix: str) -> int:
        # SCAN to avoid blocking
        count = 0
        cursor = 0
        pattern = f"{prefix}*"
        while True:
            cursor, keys = self._r.scan(cursor=cursor, match=pattern, count=500)
            if keys:
                count += self._r.delete(*keys)
            if cursor == 0:
                break
        return count

def _make_cache():
    url = os.getenv("REDIS_URL")
    if url and redis:
        return _RedisCache(url)
    return _NoopCache()

cache = _make_cache()
