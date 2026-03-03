"""
WiFi Enforcement Middleware
Restricts access to modules (stock_audit, billing, etc.) based on WiFi connection
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from modules.auth.service import AuthService
from modules.auth.models import Shop, Staff
from modules.auth.attendance.models import AttendanceSettings, AttendanceRecord, StaffDevice, ShopWiFi
from datetime import datetime, date

class WiFiEnforcementMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce WiFi requirement for staff accessing protected modules.
    
    Protected modules: stock_audit, billing, profit_analysis, customer_tracking
    Exempt modules: auth, attendance, notifications, feedback
    """
    
    PROTECTED_MODULES = [
        "/api/stock-audit",
        "/api/billing",
        "/api/profit",
        "/api/customer-tracking",
        "/api/purchase-invoices"
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if request is for a protected module
        path = request.url.path
        is_protected = any(path.startswith(module) for module in self.PROTECTED_MODULES)
        
        if not is_protected:
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await call_next(request)  # Let auth dependency handle it
        
        token = auth_header.split(" ")[1]
        token_data = AuthService.decode_token(token)
        
        # Exempt admin and super_admin from WiFi checks
        if not token_data or token_data.user_type in ["admin", "super_admin"]:
            return await call_next(request)
        
        # Only enforce for staff
        if token_data.user_type != "staff":
            return await call_next(request)
        
        # Check WiFi requirement
        db = SessionLocal()
        try:
            # Get shop from token
            shop = db.query(Shop).filter(Shop.shop_code == token_data.shop_code).first()
            if not shop:
                return await call_next(request)
            
            # Get attendance settings
            settings = db.query(AttendanceSettings).filter(
                AttendanceSettings.shop_id == shop.id
            ).first()
            
            # If allow_any_network is enabled, bypass WiFi check
            if settings and settings.allow_any_network:
                return await call_next(request)
            
            # If WiFi enforcement is disabled, bypass check
            if settings and not settings.require_wifi_for_modules:
                return await call_next(request)
            
            # Check if staff device is currently connected to shop WiFi
            staff_device = db.query(StaffDevice).filter(
                StaffDevice.staff_id == token_data.user_id,
                StaffDevice.shop_id == shop.id,
                StaffDevice.is_active == True
            ).first()
            
            if not staff_device or not staff_device.is_inside_geofence:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="WiFi connection required. Please connect to shop WiFi to access this module."
                )
            
            return await call_next(request)
            
        finally:
            db.close()
