from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import datetime, date, timedelta
from typing import Optional, List
from . import schemas, models, services
from .ai_service import StockAuditAIService
from modules.auth.dependencies import get_current_user as get_user_dict, get_current_admin
from modules.auth.models import Staff, Admin

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
    
    return query.offset(skip).limit(limit).all()

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
    return item

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