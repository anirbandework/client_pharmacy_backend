import redis
import json
from typing import Optional, Any
from app.core.config import settings

class RedisService:
    def __init__(self):
        # Connection pool for handling multiple concurrent connections
        self.redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            max_connections=settings.redis_max_connections,
            retry_on_timeout=settings.redis_retry_on_timeout,
            socket_keepalive=settings.redis_socket_keepalive,
            socket_keepalive_options=settings.redis_socket_keepalive_options
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool, decode_responses=True)
    
    # Session Management
    async def set_session(self, session_id: str, data: dict, expire: int = 3600):
        """Store user session with expiration"""
        return self.redis_client.setex(f"session:{session_id}", expire, json.dumps(data))
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session data"""
        data = self.redis_client.get(f"session:{session_id}")
        return json.loads(data) if data else None
    
    # Cache frequently accessed data
    async def cache_shop_data(self, shop_code: str, data: dict, expire: int = 300):
        """Cache shop configuration and staff data"""
        return self.redis_client.setex(f"shop:{shop_code}", expire, json.dumps(data))
    
    async def get_shop_data(self, shop_code: str) -> Optional[dict]:
        data = self.redis_client.get(f"shop:{shop_code}")
        return json.loads(data) if data else None
    
    # Rate limiting
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if request is within rate limit"""
        current = self.redis_client.get(key)
        if current is None:
            self.redis_client.setex(key, window, 1)
            return True
        elif int(current) < limit:
            self.redis_client.incr(key)
            return True
        return False

redis_service = RedisService()