"""
Simple in-memory cache for dashboard endpoints
Prevents database overload from frequent polling
"""
from datetime import datetime
from typing import Any, Optional

class SimpleCache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._ttls = {}

    def get(self, key: str, ttl_seconds: int = 60) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None

        effective_ttl = self._ttls.get(key, ttl_seconds)
        age = (datetime.now() - self._timestamps[key]).total_seconds()
        if age > effective_ttl:
            del self._cache[key]
            del self._timestamps[key]
            self._ttls.pop(key, None)
            return None

        return self._cache[key]

    def set(self, key: str, value: Any, ttl: int = 60):
        """Set cached value with current timestamp and TTL"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
        self._ttls[key] = ttl
    
    def clear(self, key: str = None):
        """Clear specific key or entire cache"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            self._ttls.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()
            self._ttls.clear()

    def clear_prefix(self, prefix: str):
        """Clear all keys that start with the given prefix"""
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_delete:
            self._cache.pop(k, None)
            self._timestamps.pop(k, None)
            self._ttls.pop(k, None)

dashboard_cache = SimpleCache()
