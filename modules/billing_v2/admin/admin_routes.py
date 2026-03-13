from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.models import Admin
from typing import Optional
from modules.billing_v2.admin.admin_dependencies import get_admin_user
from modules.billing_v2.admin.admin_analytics_service import BillingAdminAnalytics
from app.utils.cache import dashboard_cache

router = APIRouter()

@router.get("/admin/analytics/dashboard")
def get_admin_dashboard(
    shop_id: Optional[int] = None,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_admin_user)
):
    """Get comprehensive billing analytics dashboard for admin"""
    cache_key = f"billing_admin_dashboard:{admin.organization_id}:{shop_id or 'all'}:{days}"
    cached = dashboard_cache.get(cache_key)
    if cached is not None:
        return cached

    analytics = BillingAdminAnalytics()
    data = analytics._gather_billing_data(db, admin.organization_id, shop_id, days)
    dashboard_cache.set(cache_key, data, ttl=60)
    return data

@router.get("/admin/analytics/ai-insights")
def get_ai_insights(
    shop_id: Optional[int] = None,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_admin_user)
):
    """Generate AI-powered insights for billing data"""
    cache_key = f"billing_admin_ai:{admin.organization_id}:{shop_id or 'all'}:{days}"
    cached = dashboard_cache.get(cache_key)
    if cached is not None:
        return cached

    analytics = BillingAdminAnalytics()
    result = analytics.generate_comprehensive_analysis(
        db, admin.organization_id, shop_id, days
    )
    dashboard_cache.set(cache_key, result, ttl=3600)
    return result
