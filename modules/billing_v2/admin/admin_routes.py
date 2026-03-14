from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from modules.auth.models import Admin, Shop
from typing import Optional
from datetime import datetime, date, timedelta
from io import BytesIO
import json, math
from pydantic import BaseModel
from modules.auth.dependencies import get_current_admin
from modules.billing_v2 import models
from modules.billing_v2.admin.admin_analytics_service import BillingAdminAnalytics
from app.utils.cache import dashboard_cache
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

router = APIRouter()

# ─── ANALYTICS ────────────────────────────────────────────────────────────────

@router.get("/admin/analytics/dashboard")
def get_admin_dashboard(
    shop_id: Optional[int] = None,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
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
    admin: Admin = Depends(get_current_admin)
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

# ─── BILL MANAGEMENT ──────────────────────────────────────────────────────────

@router.get("/admin/bills")
def get_admin_bills(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_phone: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """List bills for admin (org-scoped, paginated, with optional shop filter)"""
    query = (
        db.query(models.Bill)
        .join(Shop, models.Bill.shop_id == Shop.id)
        .filter(Shop.organization_id == admin.organization_id)
    )
    if shop_id:
        query = query.filter(models.Bill.shop_id == shop_id)
    if start_date:
        query = query.filter(models.Bill.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(models.Bill.created_at <= datetime.combine(end_date, datetime.max.time()))
    if customer_phone:
        query = query.filter(models.Bill.customer_phone == customer_phone)

    total = query.count()
    bills = query.order_by(models.Bill.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": bills,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total > 0 else 1
    }

@router.get("/admin/bills/{bill_id}")
def get_admin_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get a single bill by ID (org-scoped)"""
    bill = (
        db.query(models.Bill)
        .join(Shop, models.Bill.shop_id == Shop.id)
        .filter(models.Bill.id == bill_id, Shop.organization_id == admin.organization_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.get("/admin/shop/{shop_id}/bill-config")
def get_admin_shop_bill_config(
    shop_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get bill config for a specific shop (for printing bills in admin view)"""
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.organization_id == admin.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.bill_config:
        try:
            return {"config": json.loads(shop.bill_config)}
        except Exception:
            pass
    return {"config": None}

class AdminBillConfigUpdate(BaseModel):
    storeName: str
    logo: str
    dlNumbers: dict
    flNumber: str
    address: dict
    phone: str
    gstIn: str

@router.put("/admin/shop/{shop_id}/bill-config")
def update_admin_shop_bill_config(
    shop_id: int,
    config: AdminBillConfigUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin updates bill config for a specific shop (org-scoped)"""
    shop = db.query(Shop).filter(
        Shop.id == shop_id,
        Shop.organization_id == admin.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop.bill_config = json.dumps(config.dict())
    db.commit()
    return {"message": "Bill configuration updated successfully"}

# ─── REPORTS ──────────────────────────────────────────────────────────────────

@router.get("/admin/top-selling")
def get_admin_top_selling(
    shop_id: Optional[int] = Query(None),
    limit: int = Query(10, le=50),
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Top selling items across org (optional shop filter)"""
    cutoff_date = datetime.now() - timedelta(days=days)
    query = (
        db.query(
            models.BillItem.item_name,
            func.sum(models.BillItem.quantity).label('total_quantity'),
            func.sum(models.BillItem.total_price).label('total_revenue'),
            func.count(models.BillItem.id).label('transaction_count')
        )
        .join(models.Bill, models.BillItem.bill_id == models.Bill.id)
        .join(Shop, models.Bill.shop_id == Shop.id)
        .filter(Shop.organization_id == admin.organization_id, models.Bill.created_at >= cutoff_date)
    )
    if shop_id:
        query = query.filter(models.Bill.shop_id == shop_id)

    results = (
        query.group_by(models.BillItem.item_name)
        .order_by(func.sum(models.BillItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "item_name": r.item_name,
            "total_quantity": r.total_quantity,
            "total_revenue": float(r.total_revenue),
            "transaction_count": r.transaction_count
        }
        for r in results
    ]

@router.get("/admin/daily-sales")
def get_admin_daily_sales(
    shop_id: Optional[int] = Query(None),
    days: int = Query(7, le=90),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Daily sales across org (optional shop filter)"""
    cutoff_date = datetime.now() - timedelta(days=days)
    query = (
        db.query(
            func.date(models.Bill.created_at).label('date'),
            func.count(models.Bill.id).label('bill_count'),
            func.sum(models.Bill.total_amount).label('total_sales')
        )
        .join(Shop, models.Bill.shop_id == Shop.id)
        .filter(Shop.organization_id == admin.organization_id, models.Bill.created_at >= cutoff_date)
    )
    if shop_id:
        query = query.filter(models.Bill.shop_id == shop_id)

    results = (
        query.group_by(func.date(models.Bill.created_at))
        .order_by(func.date(models.Bill.created_at).desc())
        .all()
    )
    return [
        {"date": str(r.date), "bill_count": r.bill_count, "total_sales": float(r.total_sales)}
        for r in results
    ]

@router.get("/admin/export/bills")
def export_admin_bills_excel(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Export bills to Excel (org-scoped, optional shop filter)"""
    query = (
        db.query(models.Bill)
        .join(Shop, models.Bill.shop_id == Shop.id)
        .filter(Shop.organization_id == admin.organization_id)
    )
    if shop_id:
        query = query.filter(models.Bill.shop_id == shop_id)
    if start_date:
        query = query.filter(models.Bill.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(models.Bill.created_at <= datetime.combine(end_date, datetime.max.time()))

    bills = query.order_by(models.Bill.created_at.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Bills"

    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    headers = ["Bill Number", "Date", "Shop", "Customer Name", "Customer Phone",
               "Doctor Name", "Payment Method", "Subtotal", "Discount", "Tax",
               "Total Amount", "Amount Paid", "Change", "Staff Name"]

    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Build shop_id → shop_name map for display
    shop_ids = list({b.shop_id for b in bills})
    shops = db.query(Shop).filter(Shop.id.in_(shop_ids)).all()
    shop_name_map = {s.id: s.shop_name for s in shops}

    for row, bill in enumerate(bills, 2):
        ws.cell(row=row, column=1, value=bill.bill_number)
        ws.cell(row=row, column=2, value=bill.created_at.strftime("%Y-%m-%d %H:%M"))
        ws.cell(row=row, column=3, value=shop_name_map.get(bill.shop_id, str(bill.shop_id)))
        ws.cell(row=row, column=4, value=bill.customer_name or "")
        ws.cell(row=row, column=5, value=bill.customer_phone or "")
        ws.cell(row=row, column=6, value=bill.doctor_name or "")
        ws.cell(row=row, column=7, value=bill.payment_method)
        ws.cell(row=row, column=8, value=bill.subtotal)
        ws.cell(row=row, column=9, value=bill.discount_amount)
        ws.cell(row=row, column=10, value=bill.tax_amount)
        ws.cell(row=row, column=11, value=bill.total_amount)
        ws.cell(row=row, column=12, value=bill.amount_paid)
        ws.cell(row=row, column=13, value=bill.change_returned)
        ws.cell(row=row, column=14, value=bill.staff_name)

    for col in ws.columns:
        max_length = max((len(str(cell.value)) for cell in col if cell.value), default=0)
        ws.column_dimensions[col[0].column_letter].width = min(max_length + 2, 50)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"admin_bills_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
