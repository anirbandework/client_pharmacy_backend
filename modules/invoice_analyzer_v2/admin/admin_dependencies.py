from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin

def get_admin_with_org(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
) -> tuple[Admin, int]:
    """Get current admin with organization context"""
    return admin, admin.organization_id
