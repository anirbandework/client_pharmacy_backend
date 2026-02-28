from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin
from typing import Optional
from datetime import date, datetime
from .ai_analytics import InvoiceAIAnalytics
from .dashboard_analytics import DashboardAnalytics

router = APIRouter()

@router.get("/admin/ai-analytics")
def get_ai_analytics(
    shop_id: Optional[int] = Query(None, description="Filter by specific shop (optional)"),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get comprehensive AI-powered analytics for invoice data (Admin only)
    
    Provides:
    - Financial health analysis
    - Supplier insights and recommendations
    - Inventory management insights
    - Expiry risk analysis
    - Procurement trends
    - Strategic recommendations
    """
    
    analytics_service = InvoiceAIAnalytics()
    
    result = analytics_service.generate_comprehensive_analysis(
        db=db,
        organization_id=admin.organization_id,
        shop_id=shop_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return result

@router.get("/admin/expiry-alerts")
def get_expiry_alerts(
    shop_id: Optional[int] = Query(None, description="Filter by specific shop"),
    days_threshold: int = Query(90, description="Days threshold for expiry warning"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get detailed expiry alerts for all shops (VERIFIED INVOICES ONLY)"""
    from .models import PurchaseInvoice, PurchaseInvoiceItem
    from modules.auth.models import Shop
    from datetime import date, timedelta
    
    # Query items - ONLY FROM VERIFIED INVOICES
    query = db.query(PurchaseInvoiceItem).join(
        PurchaseInvoice
    ).join(
        Shop
    ).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_verified == True,
        PurchaseInvoiceItem.expiry_date.isnot(None)
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoiceItem.shop_id == shop_id)
    
    items = query.all()
    
    # Categorize by expiry status
    expired = []
    expiring_soon = []
    safe = []
    
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)
    
    for item in items:
        days_to_expiry = (item.expiry_date - today).days
        
        item_data = {
            "product_name": item.product_name,
            "batch_number": item.batch_number,
            "quantity": item.quantity,
            "expiry_date": item.expiry_date.isoformat(),
            "days_to_expiry": days_to_expiry,
            "value": item.total_amount,
            "shop_id": item.shop_id,
            "invoice_id": item.invoice_id
        }
        
        if days_to_expiry < 0:
            item_data["status"] = "expired"
            item_data["expired_days_ago"] = abs(days_to_expiry)
            expired.append(item_data)
        elif days_to_expiry <= days_threshold:
            item_data["status"] = "expiring_soon"
            expiring_soon.append(item_data)
        else:
            item_data["status"] = "safe"
            safe.append(item_data)
    
    # Calculate financial impact
    expired_value = sum(item["value"] for item in expired)
    expiring_value = sum(item["value"] for item in expiring_soon)
    
    return {
        "summary": {
            "expired_count": len(expired),
            "expiring_soon_count": len(expiring_soon),
            "safe_count": len(safe),
            "expired_value": round(expired_value, 2),
            "expiring_value": round(expiring_value, 2),
            "total_at_risk": round(expired_value + expiring_value, 2)
        },
        "expired": sorted(expired, key=lambda x: x["expired_days_ago"], reverse=True),
        "expiring_soon": sorted(expiring_soon, key=lambda x: x["days_to_expiry"]),
        "safe": safe[:50]  # Limit safe items
    }

@router.get("/admin/supplier-performance")
def get_supplier_performance(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get detailed supplier performance metrics (VERIFIED INVOICES ONLY)"""
    from .models import PurchaseInvoice
    from modules.auth.models import Shop
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_verified == True
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    if start_date:
        query = query.filter(PurchaseInvoice.invoice_date >= start_date)
    
    if end_date:
        query = query.filter(PurchaseInvoice.invoice_date <= end_date)
    
    invoices = query.all()
    
    # Analyze suppliers
    suppliers = {}
    for inv in invoices:
        if inv.supplier_name not in suppliers:
            suppliers[inv.supplier_name] = {
                "total_spend": 0,
                "invoice_count": 0,
                "total_items": 0,
                "avg_invoice_value": 0,
                "total_gst": 0,
                "first_purchase": inv.invoice_date,
                "last_purchase": inv.invoice_date
            }
        
        s = suppliers[inv.supplier_name]
        s["total_spend"] += inv.net_amount
        s["invoice_count"] += 1
        s["total_items"] += len(inv.items)
        s["total_gst"] += inv.total_gst
        
        if inv.invoice_date < s["first_purchase"]:
            s["first_purchase"] = inv.invoice_date
        if inv.invoice_date > s["last_purchase"]:
            s["last_purchase"] = inv.invoice_date
    
    # Calculate averages
    for name, data in suppliers.items():
        data["avg_invoice_value"] = round(data["total_spend"] / data["invoice_count"], 2)
        data["first_purchase"] = data["first_purchase"].isoformat()
        data["last_purchase"] = data["last_purchase"].isoformat()
        data["total_spend"] = round(data["total_spend"], 2)
        data["total_gst"] = round(data["total_gst"], 2)
    
    # Sort by total spend
    sorted_suppliers = sorted(
        suppliers.items(),
        key=lambda x: x[1]["total_spend"],
        reverse=True
    )
    
    return {
        "total_suppliers": len(suppliers),
        "suppliers": [
            {"name": name, **data}
            for name, data in sorted_suppliers
        ]
    }

@router.get("/admin/procurement-trends")
def get_procurement_trends(
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get procurement trends and patterns (Admin only)"""
    from .models import PurchaseInvoice
    from modules.auth.models import Shop
    from sqlalchemy import func, extract
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.all()
    
    # Monthly trends
    monthly = {}
    for inv in invoices:
        month_key = inv.invoice_date.strftime("%Y-%m")
        if month_key not in monthly:
            monthly[month_key] = {
                "total_spend": 0,
                "invoice_count": 0,
                "total_items": 0
            }
        monthly[month_key]["total_spend"] += inv.net_amount
        monthly[month_key]["invoice_count"] += 1
        monthly[month_key]["total_items"] += len(inv.items)
    
    # Day of week analysis
    day_of_week = {}
    for inv in invoices:
        day = inv.invoice_date.strftime("%A")
        if day not in day_of_week:
            day_of_week[day] = {"count": 0, "total_spend": 0}
        day_of_week[day]["count"] += 1
        day_of_week[day]["total_spend"] += inv.net_amount
    
    return {
        "monthly_trends": monthly,
        "day_of_week_analysis": day_of_week,
        "total_invoices": len(invoices),
        "date_range": {
            "first_invoice": min(inv.invoice_date for inv in invoices).isoformat() if invoices else None,
            "last_invoice": max(inv.invoice_date for inv in invoices).isoformat() if invoices else None
        }
    }

@router.get("/admin/dashboard-analytics")
def get_dashboard_analytics(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get comprehensive dashboard analytics with chart-ready data (Admin only)"""
    
    analytics = DashboardAnalytics.get_comprehensive_analytics(
        db=db,
        organization_id=admin.organization_id,
        shop_id=shop_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return analytics

@router.get("/admin/pending-verification")
def get_pending_verification(
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get list of unverified invoices pending verification (Admin only)"""
    from .models import PurchaseInvoice
    from modules.auth.models import Shop, Staff
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_verified == False
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.order_by(PurchaseInvoice.created_at.desc()).all()
    
    # Get shop names
    shop_map = {}
    shops = db.query(Shop).filter(Shop.organization_id == admin.organization_id).all()
    for shop in shops:
        shop_map[shop.id] = shop.shop_name
    
    result = []
    for inv in invoices:
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat(),
            "supplier_name": inv.supplier_name,
            "net_amount": round(inv.net_amount, 2),
            "total_items": len(inv.items),
            "shop_id": inv.shop_id,
            "shop_name": shop_map.get(inv.shop_id, "Unknown"),
            "staff_name": inv.staff_name,
            "created_at": inv.created_at.isoformat(),
            "days_pending": (datetime.now() - inv.created_at).days
        })
    
    return {
        "total_pending": len(result),
        "total_value": round(sum(inv.net_amount for inv in invoices), 2),
        "invoices": result
    }


