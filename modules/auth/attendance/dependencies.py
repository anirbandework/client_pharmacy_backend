"""
Attendance Module - Custom Authentication Dependencies
Supports both Admin and Staff access with proper shop-level isolation
"""
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from ..models import Staff, Shop, Admin
from ..dependencies import get_current_user
from typing import Optional

def get_current_attendance_user(
    user_dict: dict = Depends(get_current_user),
    shop_code: Optional[str] = Query(None, description="Shop code (required for admin)"),
    db: Session = Depends(get_db)
) -> tuple:
    """
    Extract user (staff/admin) and resolve shop_id from token or query param.
    
    - Staff: shop_code from JWT token (automatic)
    - Admin: shop_code from query parameter (must select shop)
    
    Returns:
        tuple: (user_object, shop_id, user_type)
    
    Raises:
        HTTPException: If shop not found or unauthorized
    """
    
    token_data = user_dict["token_data"]
    user = user_dict["user"]
    user_type = token_data.user_type
    
    # Admin access - needs shop_code in query param
    if user_type == "admin":
        if not shop_code:
            raise HTTPException(status_code=400, detail="shop_code query parameter required for admin")
        
        shop = db.query(Shop).filter(
            Shop.shop_code == shop_code,
            Shop.organization_id == token_data.organization_id
        ).first()
        
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found or not in your organization")
        
        return user, shop.id, "admin"
    
    # Staff access - shop_code from token
    elif user_type == "staff":
        staff_shop_code = token_data.shop_code
        if not staff_shop_code:
            raise HTTPException(status_code=400, detail="Shop code not found in token")
        
        shop = db.query(Shop).filter(
            Shop.shop_code == staff_shop_code,
            Shop.organization_id == user.shop.organization_id
        ).first()
        
        if not shop:
            raise HTTPException(status_code=404, detail="Shop not found")
        
        return user, shop.id, "staff"
    
    else:
        raise HTTPException(status_code=403, detail="Admin or Staff access required")
