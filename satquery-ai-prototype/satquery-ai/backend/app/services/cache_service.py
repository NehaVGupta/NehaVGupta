"""Cache abstraction: Redis when reachable, otherwise in-process memory (never fatal)."""
import json
import logging

log = logging.getLogger("satquery.cache")


class MemoryCache:
    backend = "memory"

    def __init__(self):
        self._d = {}

    def get(self, key):
        return self._d.get(key)

    def set(self, key, value, ttl=3600):
        self._d[key] = value


class RedisCache:
    backend = "redis"

    def __init__(self, url):
        import redis

        self._r = redis.Redis.from_url(url, socket_connect_timeout=0.5)
        self._r.ping()

    def get(self, key):
        v = self._r.get("satquery:" + key)
        return json.loads(v) if v else None

    def set(self, key, value, ttl=3600):
        self._r.setex("satquery:" + key, ttl, json.dumps(value))


def make_cache(redis_url=""):
    if redis_url:
        try:
            return RedisCache(redis_url)
        except Exception as e:  # noqa: BLE001
            log.warning("Redis unavailable (%s); using in-memory cache.", e)
    return MemoryCache()
