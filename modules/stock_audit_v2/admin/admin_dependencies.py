from fastapi import Depends
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin

def get_current_admin_user(admin: Admin = Depends(get_current_admin)) -> Admin:
    """Get current authenticated admin user"""
    return admin
