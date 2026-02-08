from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from modules.auth.service import AuthService

class ShopContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject shop context into request state"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            token_data = AuthService.decode_token(token)
            
            if token_data:
                request.state.user_id = token_data.user_id
                request.state.user_type = token_data.user_type
                request.state.shop_id = token_data.shop_id
            else:
                request.state.user_id = None
                request.state.user_type = None
                request.state.shop_id = None
        else:
            request.state.user_id = None
            request.state.user_type = None
            request.state.shop_id = None
        
        response = await call_next(request)
        return response
