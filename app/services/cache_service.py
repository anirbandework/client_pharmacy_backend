from app.services.redis_service import redis_service
import json
from typing import List, Dict, Any

class CacheService:
    """Service for caching frequently accessed data"""
    
    # Cache keys and TTL (Time To Live) in seconds
    CACHE_CONFIG = {
        "stock_items": 300,      # 5 minutes
        "shop_config": 600,      # 10 minutes  
        "staff_list": 300,       # 5 minutes
        "customer_data": 180,    # 3 minutes
        "daily_stats": 60,       # 1 minute
        "medicine_search": 120   # 2 minutes
    }
    
    @staticmethod
    async def cache_stock_items(shop_code: str, items: List[Dict]):
        """Cache stock items for quick medicine search"""
        key = f"stock:{shop_code}"
        await redis_service.redis_client.setex(
            key, 
            CacheService.CACHE_CONFIG["stock_items"], 
            json.dumps(items)
        )
    
    @staticmethod
    async def get_cached_stock(shop_code: str) -> List[Dict]:
        """Get cached stock items"""
        key = f"stock:{shop_code}"
        data = redis_service.redis_client.get(key)
        return json.loads(data) if data else []
    
    @staticmethod
    async def cache_daily_stats(shop_code: str, date: str, stats: Dict):
        """Cache daily business statistics"""
        key = f"daily_stats:{shop_code}:{date}"
        await redis_service.redis_client.setex(
            key,
            CacheService.CACHE_CONFIG["daily_stats"],
            json.dumps(stats)
        )
    
    @staticmethod
    async def invalidate_cache(pattern: str):
        """Invalidate cache by pattern"""
        keys = redis_service.redis_client.keys(pattern)
        if keys:
            redis_service.redis_client.delete(*keys)
    
    @staticmethod
    async def cache_customer_search(shop_code: str, phone: str, customer_data: Dict):
        """Cache customer data for quick lookup"""
        key = f"customer:{shop_code}:{phone}"
        await redis_service.redis_client.setex(
            key,
            CacheService.CACHE_CONFIG["customer_data"],
            json.dumps(customer_data)
        )

cache_service = CacheService()