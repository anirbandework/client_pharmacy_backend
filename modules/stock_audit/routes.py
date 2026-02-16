from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import datetime, date, timedelta
from typing import Optional, List
from . import schemas, models, services
from .ai_service import StockAuditAIService
from modules.auth.dependencies import get_current_user as get_user_dict, get_current_admin
from modules.auth.models import Staff, Admin
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from io import BytesIO

def get_current_user(user_dict: dict = Depends(get_user_dict)) -> Staff:
    """Extract staff user from auth dict"""
    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    return user_dict["user"]

router = APIRouter()

# RACK AND SECTION MANAGEMENT

@router.post("/racks", response_model=schemas.StoreRack)
def create_rack(
    rack: schemas.StoreRackCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Create a new store rack"""
    existing = db.query(models.StockRack).filter(
        models.StockRack.rack_number == rack.rack_number,
        models.StockRack.shop_id == current_user.shop_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rack number already exists")
    
    db_rack = models.StockRack(**rack.model_dump(), shop_id=current_user.shop_id)
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)
    return db_rack

@router.get("/racks", response_model=List[schemas.StoreRack])
def get_racks(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get all store racks"""
    return db.query(models.StockRack).filter(models.StockRack.shop_id == current_user.shop_id).all()

@router.put("/racks/{rack_id}", response_model=schemas.StoreRack)
def update_rack(
    rack_id: int,
    rack: schemas.StoreRackCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Update store rack"""
    db_rack = db.query(models.StockRack).filter(
        models.StockRack.id == rack_id,
        models.StockRack.shop_id == current_user.shop_id
    ).first()
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    
    for key, value in rack.model_dump().items():
        setattr(db_rack, key, value)
    
    db.commit()
    db.refresh(db_rack)
    return db_rack

@router.delete("/racks/{rack_id}")
def delete_rack(
    rack_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Delete store rack"""
    db_rack = db.query(models.StockRack).filter(
        models.StockRack.id == rack_id,
        models.StockRack.shop_id == current_user.shop_id
    ).first()
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    
    db.delete(db_rack)
    db.commit()
    return {"message": "Rack deleted successfully"}

@router.post("/sections", response_model=schemas.StoreSection)
def create_section(
    section: schemas.StoreSectionCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Create a new store section"""
    existing = db.query(models.StockSection).filter(
        models.StockSection.section_code == section.section_code,
        models.StockSection.shop_id == current_user.shop_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Section code already exists")
    
    db_section = models.StockSection(**section.model_dump(), shop_id=current_user.shop_id)
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

@router.get("/sections", response_model=List[schemas.StoreSection])
def get_sections(
    rack_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get all sections, optionally filtered by rack"""
    query = db.query(models.StockSection).filter(models.StockSection.shop_id == current_user.shop_id)
    if rack_id:
        query = query.filter(models.StockSection.rack_id == rack_id)
    return query.all()

@router.put("/sections/{section_id}", response_model=schemas.StoreSection)
def update_section(
    section_id: int,
    section: schemas.StoreSectionCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Update store section"""
    db_section = db.query(models.StockSection).filter(
        models.StockSection.id == section_id,
        models.StockSection.shop_id == current_user.shop_id
    ).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    for key, value in section.model_dump().items():
        setattr(db_section, key, value)
    
    db.commit()
    db.refresh(db_section)
    return db_section

@router.delete("/sections/{section_id}")
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Delete store section"""
    db_section = db.query(models.StockSection).filter(
        models.StockSection.id == section_id,
        models.StockSection.shop_id == current_user.shop_id
    ).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    db.delete(db_section)
    db.commit()
    return {"message": "Section deleted successfully"}

# STOCK ITEM MANAGEMENT

@router.post("/items", response_model=schemas.StockItem)
def add_stock_item(
    item: schemas.StockItemCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Add new stock item"""
    db_item = models.StockItem(**item.model_dump(), shop_id=current_user.shop_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items", response_model=List[schemas.StockItem])
def get_stock_items(
    section_id: Optional[int] = None,
    item_name: Optional[str] = None,
    batch_number: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get stock items with filters"""
    query = db.query(models.StockItem).filter(models.StockItem.shop_id == current_user.shop_id)
    
    if section_id:
        query = query.filter(models.StockItem.section_id == section_id)
    if item_name:
        query = query.filter(models.StockItem.item_name.ilike(f"%{item_name}%"))
    if batch_number:
        query = query.filter(models.StockItem.batch_number == batch_number)
    
    items = query.offset(skip).limit(limit).all()
    
    # Add section and rack names
    result = []
    for item in items:
        item_dict = {
            **item.__dict__,
            "section_name": item.section.section_name if item.section else None,
            "rack_name": item.section.rack.rack_number if item.section and item.section.rack else None,
            "total_value": (item.quantity_software * item.unit_price) if item.unit_price else None
        }
        result.append(item_dict)
    
    return result

@router.get("/items/{item_id}", response_model=schemas.StockItem)
def get_stock_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get specific stock item"""
    item = db.query(models.StockItem).filter(
        models.StockItem.id == item_id,
        models.StockItem.shop_id == current_user.shop_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    # Add section and rack names
    item_dict = {
        **item.__dict__,
        "section_name": item.section.section_name if item.section else None,
        "rack_name": item.section.rack.rack_number if item.section and item.section.rack else None,
        "total_value": (item.quantity_software * item.unit_price) if item.unit_price else None
    }
    return item_dict

@router.put("/items/{item_id}", response_model=schemas.StockItem)
def update_stock_item(
    item_id: int,
    item: schemas.StockItemCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Update stock item"""
    db_item = db.query(models.StockItem).filter(
        models.StockItem.id == item_id,
        models.StockItem.shop_id == current_user.shop_id
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}")
def delete_stock_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Delete stock item"""
    db_item = db.query(models.StockItem).filter(
        models.StockItem.id == item_id,
        models.StockItem.shop_id == current_user.shop_id
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Stock item deleted successfully"}

# PURCHASE MANAGEMENT

@router.post("/purchases", response_model=schemas.Purchase)
def add_purchase(
    purchase_data: dict,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Add purchase and update stock levels"""
    try:
        purchase = services.StockCalculationService.add_purchase(
            db, 
            purchase_data['purchase'], 
            purchase_data['items'],
            current_user.shop_id,
            current_user.id,
            current_user.name
        )
        return purchase
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/purchases", response_model=List[schemas.Purchase])
def get_purchases(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    supplier_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get purchases with filters"""
    query = db.query(models.Purchase).filter(models.Purchase.shop_id == current_user.shop_id)
    
    if start_date:
        query = query.filter(models.Purchase.purchase_date >= start_date)
    if end_date:
        query = query.filter(models.Purchase.purchase_date <= end_date)
    if supplier_name:
        query = query.filter(models.Purchase.supplier_name.ilike(f"%{supplier_name}%"))
    
    return query.order_by(models.Purchase.purchase_date.desc()).offset(skip).limit(limit).all()

@router.put("/purchases/{purchase_id}", response_model=schemas.Purchase)
def update_purchase(
    purchase_id: int,
    purchase_data: dict,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Update purchase record"""
    db_purchase = db.query(models.Purchase).filter(
        models.Purchase.id == purchase_id,
        models.Purchase.shop_id == current_user.shop_id
    ).first()
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    for key, value in purchase_data.get('purchase', {}).items():
        if hasattr(db_purchase, key):
            setattr(db_purchase, key, value)
    
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@router.delete("/purchases/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Delete purchase record"""
    db_purchase = db.query(models.Purchase).filter(
        models.Purchase.id == purchase_id,
        models.Purchase.shop_id == current_user.shop_id
    ).first()
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    db.delete(db_purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}

# SALES MANAGEMENT

@router.post("/sales", response_model=schemas.Sale)
def add_sale(
    sale_data: dict,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Add sale and update stock levels"""
    try:
        sale = services.StockCalculationService.add_sale(
            db, 
            sale_data['sale'], 
            sale_data['items'],
            current_user.shop_id,
            current_user.id,
            current_user.name
        )
        return sale
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/sales", response_model=List[schemas.Sale])
def get_sales(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    customer_phone: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get sales with filters"""
    query = db.query(models.Sale).filter(models.Sale.shop_id == current_user.shop_id)
    
    if start_date:
        query = query.filter(models.Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(models.Sale.sale_date <= end_date)
    if customer_phone:
        query = query.filter(models.Sale.customer_phone == customer_phone)
    
    return query.order_by(models.Sale.sale_date.desc()).offset(skip).limit(limit).all()

@router.put("/sales/{sale_id}", response_model=schemas.Sale)
def update_sale(
    sale_id: int,
    sale_data: dict,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Update sale record"""
    db_sale = db.query(models.Sale).filter(
        models.Sale.id == sale_id,
        models.Sale.shop_id == current_user.shop_id
    ).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    for key, value in sale_data.get('sale', {}).items():
        if hasattr(db_sale, key):
            setattr(db_sale, key, value)
    
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.delete("/sales/{sale_id}")
def delete_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Delete sale record"""
    db_sale = db.query(models.Sale).filter(
        models.Sale.id == sale_id,
        models.Sale.shop_id == current_user.shop_id
    ).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    db.delete(db_sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

# AUDIT FUNCTIONALITY

@router.get("/audit/random-section", response_model=schemas.RandomAuditSection)
def get_random_audit_section(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get random section for audit"""
    result = services.StockAuditService.get_random_section_for_audit(db, current_user.shop_id)
    if not result:
        raise HTTPException(status_code=404, detail="No sections available for audit")
    return result

@router.post("/audit/sessions", response_model=schemas.StockAuditSession)
def start_audit_session(
    session: schemas.StockAuditSessionCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Start new audit session"""
    return services.StockAuditService.start_audit_session(db, current_user.id, current_user.name, current_user.shop_id)

@router.put("/items/{item_id}/audit", response_model=schemas.StockAuditRecord)
def audit_stock_item(
    item_id: int,
    physical_quantity: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Record audit result for stock item"""
    try:
        audit_record = services.StockAuditService.record_audit(
            db, item_id, physical_quantity, current_user.id, current_user.name, notes, current_user.shop_id
        )
        return audit_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit/discrepancies")
def get_stock_discrepancies(
    threshold: int = Query(0, description="Minimum discrepancy threshold"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get all stock discrepancies above threshold"""
    discrepancies = services.StockAuditService.get_discrepancies(db, threshold, current_user.shop_id)
    return {
        "total_discrepancies": len(discrepancies),
        "threshold": threshold,
        "discrepancies": discrepancies
    }

@router.get("/audit/summary")
def get_audit_summary(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get overall audit summary"""
    return services.StockAuditService.get_audit_summary(db, current_user.shop_id)

# STOCK CALCULATIONS

@router.post("/calculate-stock")
def update_software_stock(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Recalculate software stock for all items based on purchases/sales"""
    result = services.StockCalculationService.update_all_software_stock(db, current_user.shop_id)
    return {
        "message": "Stock calculations updated",
        "details": result
    }

@router.get("/items/{item_id}/stock-calculation")
def get_item_stock_calculation(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get detailed stock calculation for specific item"""
    item = db.query(models.StockItem).filter(
        models.StockItem.id == item_id,
        models.StockItem.shop_id == current_user.shop_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    calculated_stock = services.StockCalculationService.calculate_software_stock(db, item_id)
    
    purchases = db.query(models.PurchaseItem).filter(
        models.PurchaseItem.stock_item_id == item_id
    ).all()
    
    sales = db.query(models.SaleItem).filter(
        models.SaleItem.stock_item_id == item_id
    ).all()
    
    total_purchased = sum(p.quantity for p in purchases)
    total_sold = sum(s.quantity for s in sales)
    
    return {
        "item": item,
        "calculated_stock": calculated_stock,
        "current_software_stock": item.quantity_software,
        "total_purchased": total_purchased,
        "total_sold": total_sold,
        "purchase_transactions": len(purchases),
        "sale_transactions": len(sales)
    }

# REPORTS

@router.get("/reports/low-stock")
def get_low_stock_report(
    threshold: int = Query(10, description="Low stock threshold"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get low stock items report"""
    items = services.StockReportService.get_low_stock_items(db, threshold, current_user.shop_id)
    return {
        "threshold": threshold,
        "total_low_stock_items": len(items),
        "items": items
    }

@router.get("/reports/expiring")
def get_expiring_items_report(
    days_ahead: int = Query(30, description="Days ahead to check for expiry"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get expiring items report"""
    items = services.StockReportService.get_expiring_items(db, days_ahead, current_user.shop_id)
    return {
        "days_ahead": days_ahead,
        "total_expiring_items": len(items),
        "items": items
    }

@router.get("/reports/stock-movement")
def get_stock_movement_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get stock movement report for date range"""
    return services.StockReportService.get_stock_movement_report(db, start_date, end_date, current_user.shop_id)

@router.post("/adjustments", response_model=schemas.StockAdjustment)
def create_stock_adjustment(
    adjustment: schemas.StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Create stock adjustment for corrections/damages/returns"""
    item = db.query(models.StockItem).filter(
        models.StockItem.id == adjustment.stock_item_id,
        models.StockItem.shop_id == current_user.shop_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    db_adjustment = models.StockAdjustment(
        **adjustment.model_dump(),
        shop_id=current_user.shop_id,
        staff_id=current_user.id,
        staff_name=current_user.name
    )
    db.add(db_adjustment)
    
    item.quantity_software += adjustment.quantity_change
    if item.quantity_software < 0:
        raise HTTPException(status_code=400, detail="Adjustment would result in negative stock")
    
    db.commit()
    db.refresh(db_adjustment)
    return db_adjustment

@router.get("/adjustments", response_model=List[schemas.StockAdjustment])
def get_stock_adjustments(
    stock_item_id: Optional[int] = None,
    adjustment_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get stock adjustments with filters"""
    query = db.query(models.StockAdjustment).filter(models.StockAdjustment.shop_id == current_user.shop_id)
    
    if stock_item_id:
        query = query.filter(models.StockAdjustment.stock_item_id == stock_item_id)
    if adjustment_type:
        query = query.filter(models.StockAdjustment.adjustment_type == adjustment_type)
    
    return query.order_by(models.StockAdjustment.adjustment_date.desc()).offset(skip).limit(limit).all()

# AI ANALYTICS

@router.get("/ai-analytics/comprehensive")
def get_comprehensive_ai_analysis(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get comprehensive AI analysis with charts and insights"""
    try:
        return StockAuditAIService.get_comprehensive_analysis(db, current_user.shop_id, days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ai-analytics/charts")
def get_ai_chart_data(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get chart data for frontend visualization"""
    return StockAuditAIService.get_chart_data(db, current_user.shop_id, days)

@router.get("/ai-analytics/insights")
def get_ai_insights(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Get AI-generated insights and recommendations"""
    try:
        return StockAuditAIService.get_ai_insights(db, current_user.shop_id, days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# EXCEL EXPORT

@router.get("/export/stock-items")
def export_stock_items_excel(
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Export all stock items to Excel"""
    items = db.query(models.StockItem).filter(models.StockItem.shop_id == current_user.shop_id).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Items"
    
    # Header styling
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    # Headers
    headers = ["ID", "Item Name", "Generic Name", "Brand Name", "Batch Number", "Rack", "Section", 
               "Software Qty", "Physical Qty", "Discrepancy", "Unit Price", "Total Value", "Expiry Date", 
               "Manufacturer", "Last Audit Date", "Created At"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    # Data rows
    for row, item in enumerate(items, 2):
        ws.cell(row=row, column=1, value=item.id)
        ws.cell(row=row, column=2, value=item.item_name)
        ws.cell(row=row, column=3, value=item.generic_name)
        ws.cell(row=row, column=4, value=item.brand_name)
        ws.cell(row=row, column=5, value=item.batch_number)
        ws.cell(row=row, column=6, value=item.section.rack.rack_number if item.section and item.section.rack else "")
        ws.cell(row=row, column=7, value=item.section.section_name if item.section else "")
        ws.cell(row=row, column=8, value=item.quantity_software)
        ws.cell(row=row, column=9, value=item.quantity_physical)
        ws.cell(row=row, column=10, value=item.audit_discrepancy)
        ws.cell(row=row, column=11, value=item.unit_price)
        ws.cell(row=row, column=12, value=(item.quantity_software * item.unit_price) if item.unit_price else None)
        ws.cell(row=row, column=13, value=item.expiry_date.strftime("%Y-%m-%d") if item.expiry_date else "")
        ws.cell(row=row, column=14, value=item.manufacturer)
        ws.cell(row=row, column=15, value=item.last_audit_date.strftime("%Y-%m-%d %H:%M") if item.last_audit_date else "")
        ws.cell(row=row, column=16, value=item.created_at.strftime("%Y-%m-%d %H:%M"))
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_length + 2, 50)
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"stock_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/audit-records")
def export_audit_records_excel(
    days: int = Query(30, description="Number of days to export"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Export audit records to Excel"""
    start_date = datetime.now() - timedelta(days=days)
    records = db.query(models.StockAuditRecord).filter(
        models.StockAuditRecord.shop_id == current_user.shop_id,
        models.StockAuditRecord.audit_date >= start_date
    ).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Records"
    
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    headers = ["ID", "Item Name", "Batch Number", "Rack", "Section", "Audit Date", "Staff Name",
               "Software Qty", "Physical Qty", "Discrepancy", "Notes", "Resolved", "Resolution Notes"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for row, record in enumerate(records, 2):
        ws.cell(row=row, column=1, value=record.id)
        ws.cell(row=row, column=2, value=record.stock_item.item_name if record.stock_item else "")
        ws.cell(row=row, column=3, value=record.stock_item.batch_number if record.stock_item else "")
        ws.cell(row=row, column=4, value=record.stock_item.section.rack.rack_number if record.stock_item and record.stock_item.section and record.stock_item.section.rack else "")
        ws.cell(row=row, column=5, value=record.stock_item.section.section_name if record.stock_item and record.stock_item.section else "")
        ws.cell(row=row, column=6, value=record.audit_date.strftime("%Y-%m-%d %H:%M"))
        ws.cell(row=row, column=7, value=record.staff_name)
        ws.cell(row=row, column=8, value=record.software_quantity)
        ws.cell(row=row, column=9, value=record.physical_quantity)
        ws.cell(row=row, column=10, value=record.discrepancy)
        ws.cell(row=row, column=11, value=record.notes)
        ws.cell(row=row, column=12, value="Yes" if record.resolved else "No")
        ws.cell(row=row, column=13, value=record.resolution_notes)
    
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_length + 2, 50)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"audit_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/adjustments")
def export_adjustments_excel(
    days: int = Query(30, description="Number of days to export"),
    db: Session = Depends(get_db),
    current_user: Staff = Depends(get_current_user)
):
    """Export stock adjustments to Excel"""
    start_date = datetime.now() - timedelta(days=days)
    adjustments = db.query(models.StockAdjustment).filter(
        models.StockAdjustment.shop_id == current_user.shop_id,
        models.StockAdjustment.adjustment_date >= start_date
    ).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Stock Adjustments"
    
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    
    headers = ["ID", "Item Name", "Batch Number", "Rack", "Section", "Adjustment Type", 
               "Quantity Change", "Reason", "Notes", "Staff Name", "Adjustment Date"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    for row, adj in enumerate(adjustments, 2):
        ws.cell(row=row, column=1, value=adj.id)
        ws.cell(row=row, column=2, value=adj.stock_item.item_name if adj.stock_item else "")
        ws.cell(row=row, column=3, value=adj.stock_item.batch_number if adj.stock_item else "")
        ws.cell(row=row, column=4, value=adj.stock_item.section.rack.rack_number if adj.stock_item and adj.stock_item.section and adj.stock_item.section.rack else "")
        ws.cell(row=row, column=5, value=adj.stock_item.section.section_name if adj.stock_item and adj.stock_item.section else "")
        ws.cell(row=row, column=6, value=adj.adjustment_type)
        ws.cell(row=row, column=7, value=adj.quantity_change)
        ws.cell(row=row, column=8, value=adj.reason)
        ws.cell(row=row, column=9, value=adj.notes)
        ws.cell(row=row, column=10, value=adj.staff_name)
        ws.cell(row=row, column=11, value=adj.adjustment_date.strftime("%Y-%m-%d %H:%M"))
    
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = min(max_length + 2, 50)
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"stock_adjustments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
