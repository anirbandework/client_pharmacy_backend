from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Staff, Shop
from modules.auth.attendance.models import StaffDevice, AttendanceSettings

def get_current_user_with_geofence(user_dict: dict = Depends(get_user_dict), db: Session = Depends(get_db)) -> tuple[Staff, int]:
    """Extract staff user and verify they are within geofence"""
    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    staff = user_dict["user"]
    shop_code = user_dict["token_data"].shop_code
    
    if not shop_code:
        raise HTTPException(status_code=400, detail="Shop code not found in token")
    
    shop = db.query(Shop).filter(
        Shop.shop_code == shop_code,
        Shop.organization_id == staff.shop.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail=f"Shop not found with code: {shop_code}")
    
    # Check attendance settings
    settings = db.query(AttendanceSettings).filter(
        AttendanceSettings.shop_id == shop.id
    ).first()
    
    # If allow_any_network is enabled, skip geofence check
    if settings and settings.allow_any_network:
        return staff, shop.id
    
    # If WiFi enforcement is disabled, skip check
    if settings and not settings.require_wifi_for_modules:
        return staff, shop.id
    
    # Check if staff device is inside geofence
    staff_device = db.query(StaffDevice).filter(
        StaffDevice.staff_id == staff.id,
        StaffDevice.shop_id == shop.id,
        StaffDevice.is_active == True
    ).first()
    
    if not staff_device or not staff_device.is_inside_geofence:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. You must be inside the shop to access billing."
        )
    
    return staff, shop.id
