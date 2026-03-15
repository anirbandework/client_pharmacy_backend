from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.services.redis_service import redis_service
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """User-type-based rate limiting optimized for 100k users"""
    
    # User type limits (requests per minute)
    USER_TYPE_LIMITS = {
        "super_admin": 500,
        "admin": 300,
        "staff": 300,  # Increased from 200 for stock operations
        "anonymous": 20
    }
    
    # Endpoint-specific overrides
    ENDPOINT_LIMITS = {
        # Auth endpoints
        "/api/auth/login": {"limit": 5, "window": 300},
        "/api/auth/register": {"limit": 3, "window": 3600},
        "/api/purchase-invoices/upload": {"limit": 10, "window": 60},
        
        # OTP endpoints - prevent SMS spam and brute force (Admin and Staff only)
        "/api/auth/otp/send": {"limit": 3, "window": 300},
        "/api/auth/otp/verify": {"limit": 5, "window": 300},
        "/api/auth/admin/send-otp": {"limit": 3, "window": 300},
        "/api/auth/admin/otp/verify": {"limit": 5, "window": 300},
        "/api/auth/staff/send-otp": {"limit": 3, "window": 300},
        "/api/auth/staff/otp/verify": {"limit": 5, "window": 300},
        
        # Stock audit operations - production-safe limits for bulk operations
        "/api/stock-audit/bulk-assign": {"limit": 1000, "window": 60},  # Allow bulk operations
        # Heavy query endpoints - prevent database overload
        "/api/invoice-analyzer/admin/ai-analytics": {"limit": 10, "window": 60},
        "/api/invoice-analyzer/admin/dashboard-analytics": {"limit": 10, "window": 60}
    }
    
    # High-frequency endpoints (lightweight rate limiting)
    HIGH_FREQUENCY_LIMITS = {
        "/api/attendance/wifi/heartbeat": {"limit": 2, "window": 60},  # 2/min = every 30s (matches heartbeat)
        "/api/attendance/wifi/status": {"limit": 30, "window": 60},    # 30/min = every 2s (reduced from 120)
        "/api/notifications/staff/unread-count": {"limit": 30, "window": 60}  # 30/min = every 2s (reduced from 120)
    }
    
    # Skip rate limiting entirely
    SKIP_RATE_LIMIT = [
        "/", "/health", "/modules",
        # SuperAdmin endpoints - no rate limits for superadmins
        "/api/auth/super-admin/send-otp",
        "/api/auth/super-admin/verify-otp",
        "/api/auth/super-admin/login",
        "/api/auth/super-admin/register",
        "/api/auth/super-admin/me",
        "/api/auth/super-admin/dashboard",
        "/api/auth/super-admin/analytics",
        "/api/auth/super-admin/admins",
        "/api/auth/super-admin/shops",
        "/api/auth/super-admin/staff",
        "/api/auth/super-admin/organizations",
        # Auth verification endpoints - needed for frontend auth checks
        "/api/auth/staff/me",
        "/api/auth/admin/me",
        "/api/rbac/my-permissions"
    ]
    
    # Skip rate limiting for specific patterns
    SKIP_PATTERNS = [
        # Remove blanket skip for stock audit - too risky for production
    ]
    
    def _create_rate_limit_response(self, retry_after: int):
        """Create a properly formatted 429 response with CORS headers"""
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "error": "Too many requests"},
            headers={
                "Retry-After": str(retry_after),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_RATE_LIMIT or request.method == "OPTIONS":
            return await call_next(request)
        
        # Check skip patterns
        for pattern in self.SKIP_PATTERNS:
            if pattern in request.url.path:
                return await call_next(request)
        
        # Extract user_type from JWT token directly (middleware order issue)
        user_type = 'anonymous'
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from modules.auth.service import AuthService
                token = auth_header.split(" ")[1]
                token_data = AuthService.decode_token(token)
                if token_data:
                    user_type = token_data.user_type
                    user_id = token_data.user_id
                    org_id = getattr(token_data, 'organization_id', None)
                else:
                    user_id = None
                    org_id = None
            except:
                user_id = None
                org_id = None
        else:
            user_id = getattr(request.state, 'user_id', None)
            org_id = getattr(request.state, 'organization_id', None)
        
        client_ip = request.client.host
        
        # Skip rate limiting for SuperAdmins entirely
        if user_type == 'super_admin':
            return await call_next(request)
        
        # High-frequency endpoints (lightweight limits)
        if request.url.path in self.HIGH_FREQUENCY_LIMITS:
            config = self.HIGH_FREQUENCY_LIMITS[request.url.path]
            key = f"rl:hf:{request.url.path}:{user_id or client_ip}"
            if not await redis_service.check_rate_limit(key, config["limit"], config["window"]):
                return self._create_rate_limit_response(config["window"])
            return await call_next(request)  # Skip other checks for performance
        
        # Endpoint-specific limits (use user_id if available, else IP)
        endpoint_path = request.url.path
        endpoint_config = None
        
        # Check exact match first
        if endpoint_path in self.ENDPOINT_LIMITS:
            endpoint_config = self.ENDPOINT_LIMITS[endpoint_path]
        else:
            # Stock audit operations - higher limits but still controlled
            if "/api/stock-audit/items/" in endpoint_path and "/assign-section" in endpoint_path:
                endpoint_config = {"limit": 500, "window": 60}  # 500/min for individual assignments
            elif "/api/stock-audit/bulk" in endpoint_path:
                endpoint_config = {"limit": 10, "window": 60}   # 10 bulk operations per minute
        
        if endpoint_config:
            key = f"rl:ep:{endpoint_path}:{user_id or client_ip}"
            if not await redis_service.check_rate_limit(key, endpoint_config["limit"], endpoint_config["window"]):
                return self._create_rate_limit_response(endpoint_config["window"])
        
        # User-level rate limit (authenticated users)
        if user_id:
            limit = self.USER_TYPE_LIMITS.get(user_type, 100)
            key = f"rl:u:{user_id}"
            if not await redis_service.check_rate_limit(key, limit, 60):
                return self._create_rate_limit_response(60)
        else:
            # Anonymous users - IP-based rate limit
            key = f"rl:anon:{client_ip}"
            if not await redis_service.check_rate_limit(key, self.USER_TYPE_LIMITS["anonymous"], 60):
                return self._create_rate_limit_response(60)
        
        # Organization-level rate limit
        if org_id:
            key = f"rl:org:{org_id}"
            if not await redis_service.check_rate_limit(key, 5000, 60):
                return self._create_rate_limit_response(60)
        
        return await call_next(request)
