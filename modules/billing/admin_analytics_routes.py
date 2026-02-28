from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_user
from modules.auth.models import Admin
from typing import Optional
from .admin_analytics import BillingAdminAnalytics

router = APIRouter()

def get_admin_user(user_dict: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Verify user is admin"""
    if user_dict["token_data"].user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    admin = user_dict["user"]
    return admin

@router.get("/admin/analytics/dashboard")
def get_admin_dashboard(
    shop_id: Optional[int] = None,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_admin_user)
):
    """Get comprehensive billing analytics dashboard for admin"""
    analytics = BillingAdminAnalytics()
    data = analytics._gather_billing_data(db, admin.organization_id, shop_id, days)
    return data

@router.get("/admin/analytics/ai-insights")
def get_ai_insights(
    shop_id: Optional[int] = None,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_admin_user)
):
    """Generate AI-powered insights for billing data"""
    analytics = BillingAdminAnalytics()
    result = analytics.generate_comprehensive_analysis(
        db, admin.organization_id, shop_id, days
    )
    return result
