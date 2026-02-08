from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from . import models, schemas
from .service import AuthService

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user (admin or staff)"""
    token = credentials.credentials
    token_data = AuthService.decode_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    if token_data.user_type == "admin":
        user = db.query(models.Admin).filter(models.Admin.id == token_data.user_id).first()
    elif token_data.user_type == "staff":
        user = db.query(models.Staff).filter(models.Staff.id == token_data.user_id).first()
    else:
        raise HTTPException(status_code=401, detail="Invalid user type")
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return {"user": user, "token_data": token_data}

def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Require admin authentication"""
    if current_user["token_data"].user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user["user"]

def get_current_staff(current_user: dict = Depends(get_current_user)):
    """Require staff authentication"""
    if current_user["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    return current_user["user"]

def get_shop_context(current_user: dict = Depends(get_current_user)):
    """Get shop context from authenticated user"""
    token_data = current_user["token_data"]
    
    if token_data.user_type == "staff":
        return token_data.shop_id
    
    # Admin doesn't have automatic shop context
    return None

def require_permission(permission: str):
    """Check if staff has specific permission"""
    def permission_checker(staff: models.Staff = Depends(get_current_staff)):
        if staff.role == "shop_manager":
            return staff  # Shop managers have all permissions
        
        if permission == "manage_staff" and not staff.can_manage_staff:
            raise HTTPException(status_code=403, detail="Permission denied: manage_staff")
        elif permission == "view_analytics" and not staff.can_view_analytics:
            raise HTTPException(status_code=403, detail="Permission denied: view_analytics")
        elif permission == "manage_inventory" and not staff.can_manage_inventory:
            raise HTTPException(status_code=403, detail="Permission denied: manage_inventory")
        elif permission == "manage_customers" and not staff.can_manage_customers:
            raise HTTPException(status_code=403, detail="Permission denied: manage_customers")
        
        return staff
    
    return permission_checker
