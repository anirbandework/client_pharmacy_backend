from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.redis_service import redis_service
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with different limits for different endpoints"""
    
    RATE_LIMITS = {
        # Authentication endpoints - stricter limits
        "/api/auth/login": {"limit": 5, "window": 300},  # 5 attempts per 5 minutes
        "/api/auth/register": {"limit": 3, "window": 3600},  # 3 per hour
        
        # Billing endpoints - moderate limits
        "/api/billing": {"limit": 100, "window": 60},  # 100 per minute
        
        # Customer tracking - moderate limits  
        "/api/customer-tracking": {"limit": 50, "window": 60},
        
        # Stock operations - higher limits
        "/api/stock-audit": {"limit": 200, "window": 60},
        
        # Default for all other endpoints
        "default": {"limit": 1000, "window": 60}  # 1000 per minute
    }
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/", "/health", "/modules"]:
            return await call_next(request)
        
        # Get client identifier (IP + user_id if authenticated)
        client_ip = request.client.host
        user_id = getattr(request.state, 'user_id', None)
        client_key = f"{client_ip}:{user_id}" if user_id else client_ip
        
        # Determine rate limit for this endpoint
        endpoint_config = self._get_rate_limit_config(request.url.path)
        rate_limit_key = f"rate_limit:{request.url.path}:{client_key}"
        
        # Check rate limit
        if not await redis_service.check_rate_limit(
            rate_limit_key, 
            endpoint_config["limit"], 
            endpoint_config["window"]
        ):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {endpoint_config['limit']} requests per {endpoint_config['window']} seconds"
            )
        
        return await call_next(request)
    
    def _get_rate_limit_config(self, path: str) -> dict:
        """Get rate limit configuration for a specific path"""
        for endpoint, config in self.RATE_LIMITS.items():
            if endpoint != "default" and path.startswith(endpoint):
                return config
        return self.RATE_LIMITS["default"]