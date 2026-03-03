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
    
    def get(self, key: str, ttl_seconds: int = 60) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None
        
        if key in self._timestamps:
            age = (datetime.now() - self._timestamps[key]).total_seconds()
            if age > ttl_seconds:
                del self._cache[key]
                del self._timestamps[key]
                return None
        
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        """Set cached value with current timestamp"""
        self._cache[key] = value
        self._timestamps[key] = datetime.now()
    
    def clear(self, key: str = None):
        """Clear specific key or entire cache"""
        if key:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._cache.clear()
            self._timestamps.clear()

dashboard_cache = SimpleCache()
