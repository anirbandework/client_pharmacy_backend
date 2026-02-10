from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime

from app.database.database import get_db
from .models import PurchaseInvoice, PurchaseInvoiceItem, ExpiryAlert, MonthlyInvoiceSummary
from .schemas import (
    PurchaseInvoiceCreate, PurchaseInvoiceResponse, ItemSaleCreate, ItemSaleResponse,
    ExpiryAlertResponse, MonthlyInvoiceSummaryResponse, InvoiceAnalytics,
    MovementAnalytics, AIInsights, DashboardSummary
)
from .service import PurchaseInvoiceService
from .ai_analytics import PurchaseInvoiceAIAnalytics
from .wings_integration import WINGSIntegrationService

router = APIRouter()
ai_analytics = PurchaseInvoiceAIAnalytics()

# Purchase Invoice Management
@router.post("/", response_model=PurchaseInvoiceResponse)
async def create_purchase_invoice(
    invoice_data: PurchaseInvoiceCreate,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Create a new purchase invoice with automatic calculations and expiry tracking"""
    try:
        invoice = PurchaseInvoiceService.create_invoice(db, invoice_data, shop_id)
        return invoice
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/monthly/{year}/{month}", response_model=List[PurchaseInvoiceResponse])
async def get_monthly_invoices(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get all purchase invoices for a specific month with color coding"""
    invoices = PurchaseInvoiceService.get_monthly_invoices(db, year, month, shop_id)
    return invoices

# Dashboard - Must come before /{invoice_id} to avoid path conflict
@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get dashboard summary with current month data, alerts, and AI insights"""
    
    current_date = date.today()
    
    # Get current month summary
    current_summary = db.query(MonthlyInvoiceSummary).filter(
        MonthlyInvoiceSummary.year == current_date.year,
        MonthlyInvoiceSummary.month == current_date.month,
        MonthlyInvoiceSummary.shop_id == shop_id
    ).first()
    
    if not current_summary:
        # Create empty summary if none exists
        current_summary = MonthlyInvoiceSummary(
            year=current_date.year,
            month=current_date.month,
            shop_id=shop_id,
            total_invoices=0,
            total_amount=0.0,
            total_items=0,
            green_invoices=0,
            yellow_invoices=0,
            red_invoices=0,
            month_color="red",
            overall_sold_percentage=0.0,
            expiring_items_count=0,
            expired_items_count=0
        )
    
    # Get pending alerts (limit to 10)
    alerts = PurchaseInvoiceService.get_expiry_alerts(db, 45, shop_id)[:10]
    formatted_alerts = []
    for alert in alerts:
        item = db.query(PurchaseInvoiceItem).filter(PurchaseInvoiceItem.id == alert.item_id).first()
        if item:
            formatted_alerts.append(ExpiryAlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                alert_date=alert.alert_date,
                message=alert.message,
                priority=alert.priority,
                is_acknowledged=alert.is_acknowledged,
                item_code=item.item_code,
                item_name=item.item_name,
                days_to_expiry=item.days_to_expiry
            ))
    
    # Get recent invoices (last 5)
    recent_invoices = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.shop_id == shop_id if shop_id else True
    ).order_by(PurchaseInvoice.created_at.desc()).limit(5).all()
    
    # Get movement analytics (top 10 items)
    movement_analytics = []
    top_items = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoice.shop_id == shop_id if shop_id else True
    ).order_by(PurchaseInvoiceItem.movement_rate.desc()).limit(10).all()
    
    for item in top_items:
        days_in_stock = (date.today() - item.invoice.received_date).days or 1
        predicted_sellout = None
        if item.movement_rate > 0 and item.remaining_quantity > 0:
            predicted_sellout = int(item.remaining_quantity / item.movement_rate)
        
        movement_analytics.append(MovementAnalytics(
            item_code=item.item_code,
            item_name=item.item_name,
            total_purchased=item.purchased_quantity,
            total_sold=item.sold_quantity,
            movement_rate=item.movement_rate,
            days_in_stock=days_in_stock,
            predicted_sellout_days=predicted_sellout,
            demand_category=item.demand_category,
            seasonal_factor=item.seasonal_factor
        ))
    
    # Get AI insights
    ai_insights = ai_analytics.get_comprehensive_analysis(db, shop_id)
    
    return DashboardSummary(
        current_month_summary=current_summary,
        pending_alerts=formatted_alerts,
        recent_invoices=recent_invoices,
        movement_analytics=movement_analytics,
        ai_insights=ai_insights
    )

@router.get("/{invoice_id}", response_model=PurchaseInvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get specific invoice details"""
    invoice = db.query(PurchaseInvoice).filter(PurchaseInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

# Sales Recording
@router.post("/sales", response_model=ItemSaleResponse)
async def record_item_sale(
    sale_data: ItemSaleCreate,
    db: Session = Depends(get_db)
):
    """Record a sale and update item quantities and invoice status"""
    try:
        sale = PurchaseInvoiceService.record_sale(db, sale_data)
        return sale
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Expiry Management
@router.get("/expiry/alerts", response_model=List[ExpiryAlertResponse])
async def get_expiry_alerts(
    days_ahead: int = Query(45, description="Days ahead to check for expiry"),
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get pending expiry alerts"""
    alerts = PurchaseInvoiceService.get_expiry_alerts(db, days_ahead, shop_id)
    
    # Format response
    formatted_alerts = []
    for alert in alerts:
        item = db.query(PurchaseInvoiceItem).filter(PurchaseInvoiceItem.id == alert.item_id).first()
        if item:
            formatted_alerts.append(ExpiryAlertResponse(
                id=alert.id,
                alert_type=alert.alert_type,
                alert_date=alert.alert_date,
                message=alert.message,
                priority=alert.priority,
                is_acknowledged=alert.is_acknowledged,
                item_code=item.item_code,
                item_name=item.item_name,
                days_to_expiry=item.days_to_expiry
            ))
    
    return formatted_alerts

@router.put("/expiry/alerts/{alert_id}/acknowledge")
async def acknowledge_expiry_alert(
    alert_id: int,
    acknowledged_by: str,
    db: Session = Depends(get_db)
):
    """Acknowledge an expiry alert"""
    alert = db.query(ExpiryAlert).filter(ExpiryAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_acknowledged = True
    alert.acknowledged_by = acknowledged_by
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    return {"message": "Alert acknowledged successfully"}

# Analytics
@router.get("/analytics/{year}/{month}", response_model=InvoiceAnalytics)
async def get_monthly_analytics(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get comprehensive analytics for a specific month"""
    analytics = PurchaseInvoiceService.get_analytics(db, year, month, shop_id)
    return analytics

@router.get("/analytics/monthly-summary/{year}/{month}", response_model=MonthlyInvoiceSummaryResponse)
async def get_monthly_summary(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get monthly summary with color coding"""
    summary = db.query(MonthlyInvoiceSummary).filter(
        MonthlyInvoiceSummary.year == year,
        MonthlyInvoiceSummary.month == month,
        MonthlyInvoiceSummary.shop_id == shop_id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Monthly summary not found")
    
    return summary

# AI Analytics
@router.get("/ai-analytics/comprehensive", response_model=AIInsights)
async def get_comprehensive_ai_analysis(
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get comprehensive AI analysis of purchase invoices and movement patterns"""
    insights = ai_analytics.get_comprehensive_analysis(db, shop_id)
    return insights

@router.get("/ai-analytics/item-movement/{item_code}")
async def analyze_item_movement(
    item_code: str,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Analyze specific item movement using 5 parameters for AI learning"""
    analysis = ai_analytics.analyze_item_movement_5_parameters(db, item_code, shop_id)
    return analysis

@router.get("/ai-analytics/stock-predictions")
async def get_stock_predictions(
    months_ahead: int = Query(3, description="Number of months to predict ahead"),
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get AI-powered stock requirement predictions"""
    predictions = ai_analytics.predict_stock_requirements(db, months_ahead, shop_id)
    return predictions



# WINGS Integration
@router.post("/wings/import-purchase")
async def import_purchase_from_wings(
    wings_data: dict,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Import purchase invoice from WINGS POS system"""
    
    # Validate WINGS data
    validation = WINGSIntegrationService.validate_wings_purchase_data(wings_data)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={
            "message": "Invalid WINGS data format",
            "errors": validation["errors"]
        })
    
    try:
        invoice = WINGSIntegrationService.import_purchase_invoice_from_wings(db, wings_data, shop_id)
        return {
            "message": "Purchase invoice imported successfully from WINGS",
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/wings/import-sales")
async def import_sales_from_wings(
    wings_sales_data: List[dict],
    db: Session = Depends(get_db)
):
    """Import sales data from WINGS POS system"""
    
    # Validate WINGS sales data
    validation = WINGSIntegrationService.validate_wings_sales_data(wings_sales_data)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail={
            "message": "Invalid WINGS sales data format",
            "errors": validation["errors"]
        })
    
    try:
        sales = WINGSIntegrationService.import_sales_from_wings(db, wings_sales_data)
        return {
            "message": "Sales data imported successfully from WINGS",
            "sales_imported": len(sales)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/wings/sync-live")
async def sync_with_wings_live(
    wings_api_endpoint: str,
    shop_code: str,
    db: Session = Depends(get_db)
):
    """Sync live data from WINGS POS system"""
    
    try:
        result = WINGSIntegrationService.sync_with_wings_live(db, wings_api_endpoint, shop_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-analytics/smart-alerts/{item_code}")
async def get_smart_expiry_analysis(
    item_code: str,
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get AI-powered expiry alert analysis for an item"""
    
    # Get item
    item = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoiceItem.item_code == item_code,
        PurchaseInvoice.shop_id == shop_id if shop_id else True
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get AI analysis
    analysis = ai_analytics.analyze_item_movement_5_parameters(db, item_code, shop_id)
    
    # Check if alerts should be suppressed
    should_suppress = ai_analytics.should_suppress_expiry_alert(db, item)
    
    return {
        "item_code": item_code,
        "item_name": item.item_name,
        "days_to_expiry": item.days_to_expiry,
        "should_suppress_alert": should_suppress,
        "ai_analysis": analysis,
        "recommendation": "Suppress expiry alerts - item will sell before expiry" if should_suppress else "Monitor expiry closely"
    }
@router.get("/items/slow-moving")
async def get_slow_moving_items(
    threshold: float = Query(1.0, description="Movement rate threshold"),
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get slow-moving items that need attention"""
    
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoiceItem.movement_rate < threshold,
        PurchaseInvoiceItem.remaining_quantity > 0
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.order_by(PurchaseInvoiceItem.movement_rate.asc()).all()
    
    return [
        {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "movement_rate": item.movement_rate,
            "remaining_quantity": item.remaining_quantity,
            "days_to_expiry": item.days_to_expiry,
            "invoice_number": item.invoice.invoice_number,
            "received_date": item.invoice.received_date
        }
        for item in items
    ]

@router.get("/items/expiring-soon")
async def get_expiring_items(
    days: int = Query(45, description="Days until expiry"),
    db: Session = Depends(get_db),
    shop_id: Optional[int] = Query(None)
):
    """Get items expiring within specified days"""
    
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoiceItem.days_to_expiry <= days,
        PurchaseInvoiceItem.days_to_expiry > 0,
        PurchaseInvoiceItem.remaining_quantity > 0
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.order_by(PurchaseInvoiceItem.days_to_expiry.asc()).all()
    
    return [
        {
            "item_code": item.item_code,
            "item_name": item.item_name,
            "remaining_quantity": item.remaining_quantity,
            "days_to_expiry": item.days_to_expiry,
            "expiry_date": item.expiry_date,
            "movement_rate": item.movement_rate,
            "invoice_number": item.invoice.invoice_number
        }
        for item in items
    ]