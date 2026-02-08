from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import datetime, date, timedelta
from typing import Optional, List
from . import schemas, models, services

router = APIRouter()

# RACK AND SECTION MANAGEMENT

@router.post("/racks", response_model=schemas.StoreRack)
def create_rack(
    rack: schemas.StoreRackCreate,
    db: Session = Depends(get_db)
):
    """Create a new store rack"""
    existing = db.query(models.StockRack).filter(
        models.StockRack.rack_number == rack.rack_number
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Rack number already exists")
    
    db_rack = models.StockRack(**rack.model_dump())
    db.add(db_rack)
    db.commit()
    db.refresh(db_rack)
    return db_rack

@router.get("/racks", response_model=List[schemas.StoreRack])
def get_racks(db: Session = Depends(get_db)):
    """Get all store racks"""
    return db.query(models.StockRack).all()

@router.put("/racks/{rack_id}", response_model=schemas.StoreRack)
def update_rack(
    rack_id: int,
    rack: schemas.StoreRackCreate,
    db: Session = Depends(get_db)
):
    """Update store rack"""
    db_rack = db.query(models.StockRack).filter(models.StockRack.id == rack_id).first()
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    
    for key, value in rack.model_dump().items():
        setattr(db_rack, key, value)
    
    db.commit()
    db.refresh(db_rack)
    return db_rack

@router.delete("/racks/{rack_id}")
def delete_rack(rack_id: int, db: Session = Depends(get_db)):
    """Delete store rack"""
    db_rack = db.query(models.StockRack).filter(models.StockRack.id == rack_id).first()
    if not db_rack:
        raise HTTPException(status_code=404, detail="Rack not found")
    
    # Check if rack has sections
    sections = db.query(models.StockSection).filter(models.StockSection.rack_id == rack_id).first()
    if sections:
        raise HTTPException(status_code=400, detail="Cannot delete rack with existing sections")
    
    db.delete(db_rack)
    db.commit()
    return {"message": "Rack deleted successfully"}

@router.post("/sections", response_model=schemas.StoreSection)
def create_section(
    section: schemas.StoreSectionCreate,
    db: Session = Depends(get_db)
):
    """Create a new store section"""
    existing = db.query(models.StockSection).filter(
        models.StockSection.section_code == section.section_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Section code already exists")
    
    db_section = models.StockSection(**section.model_dump())
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section

@router.get("/sections", response_model=List[schemas.StoreSection])
def get_sections(rack_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all sections, optionally filtered by rack"""
    query = db.query(models.StockSection)
    if rack_id:
        query = query.filter(models.StockSection.rack_id == rack_id)
    return query.all()

@router.put("/sections/{section_id}", response_model=schemas.StoreSection)
def update_section(
    section_id: int,
    section: schemas.StoreSectionCreate,
    db: Session = Depends(get_db)
):
    """Update store section"""
    db_section = db.query(models.StockSection).filter(models.StockSection.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    for key, value in section.model_dump().items():
        setattr(db_section, key, value)
    
    db.commit()
    db.refresh(db_section)
    return db_section

@router.delete("/sections/{section_id}")
def delete_section(section_id: int, db: Session = Depends(get_db)):
    """Delete store section"""
    db_section = db.query(models.StockSection).filter(models.StockSection.id == section_id).first()
    if not db_section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Check if section has items
    items = db.query(models.StockItem).filter(models.StockItem.section_id == section_id).first()
    if items:
        raise HTTPException(status_code=400, detail="Cannot delete section with existing items")
    
    db.delete(db_section)
    db.commit()
    return {"message": "Section deleted successfully"}

# STOCK ITEM MANAGEMENT

@router.post("/items", response_model=schemas.StockItem)
def add_stock_item(
    item: schemas.StockItemCreate,
    db: Session = Depends(get_db)
):
    """Add new stock item"""
    db_item = models.StockItem(**item.model_dump())
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
    db: Session = Depends(get_db)
):
    """Get stock items with filters"""
    query = db.query(models.StockItem)
    
    if section_id:
        query = query.filter(models.StockItem.section_id == section_id)
    if item_name:
        query = query.filter(models.StockItem.item_name.ilike(f"%{item_name}%"))
    if batch_number:
        query = query.filter(models.StockItem.batch_number == batch_number)
    
    return query.offset(skip).limit(limit).all()

@router.get("/items/{item_id}", response_model=schemas.StockItem)
def get_stock_item(item_id: int, db: Session = Depends(get_db)):
    """Get specific stock item"""
    item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    return item

@router.put("/items/{item_id}", response_model=schemas.StockItem)
def update_stock_item(
    item_id: int,
    item: schemas.StockItemCreate,
    db: Session = Depends(get_db)
):
    """Update stock item"""
    db_item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/items/{item_id}")
def delete_stock_item(item_id: int, db: Session = Depends(get_db)):
    """Delete stock item"""
    db_item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    # Check if item has purchase/sale records
    purchases = db.query(models.PurchaseItem).filter(models.PurchaseItem.stock_item_id == item_id).first()
    sales = db.query(models.SaleItem).filter(models.SaleItem.stock_item_id == item_id).first()
    
    if purchases or sales:
        raise HTTPException(status_code=400, detail="Cannot delete item with existing transactions")
    
    db.delete(db_item)
    db.commit()
    return {"message": "Stock item deleted successfully"}

# PURCHASE MANAGEMENT

@router.post("/purchases", response_model=schemas.Purchase)
def add_purchase(
    purchase_data: dict,
    db: Session = Depends(get_db)
):
    """Add purchase and update stock levels"""
    try:
        purchase = services.StockCalculationService.add_purchase(
            db, 
            purchase_data['purchase'], 
            purchase_data['items']
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
    db: Session = Depends(get_db)
):
    """Get purchases with filters"""
    query = db.query(models.Purchase)
    
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
    db: Session = Depends(get_db)
):
    """Update purchase record"""
    db_purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Update purchase fields
    for key, value in purchase_data.get('purchase', {}).items():
        if hasattr(db_purchase, key):
            setattr(db_purchase, key, value)
    
    db.commit()
    db.refresh(db_purchase)
    return db_purchase

@router.delete("/purchases/{purchase_id}")
def delete_purchase(purchase_id: int, db: Session = Depends(get_db)):
    """Delete purchase record"""
    db_purchase = db.query(models.Purchase).filter(models.Purchase.id == purchase_id).first()
    if not db_purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Delete related purchase items
    db.query(models.PurchaseItem).filter(models.PurchaseItem.purchase_id == purchase_id).delete()
    db.delete(db_purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}

# SALES MANAGEMENT

@router.post("/sales", response_model=schemas.Sale)
def add_sale(
    sale_data: dict,
    db: Session = Depends(get_db)
):
    """Add sale and update stock levels"""
    try:
        sale = services.StockCalculationService.add_sale(
            db, 
            sale_data['sale'], 
            sale_data['items']
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
    db: Session = Depends(get_db)
):
    """Get sales with filters"""
    query = db.query(models.Sale)
    
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
    db: Session = Depends(get_db)
):
    """Update sale record"""
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Update sale fields
    for key, value in sale_data.get('sale', {}).items():
        if hasattr(db_sale, key):
            setattr(db_sale, key, value)
    
    db.commit()
    db.refresh(db_sale)
    return db_sale

@router.delete("/sales/{sale_id}")
def delete_sale(sale_id: int, db: Session = Depends(get_db)):
    """Delete sale record"""
    db_sale = db.query(models.Sale).filter(models.Sale.id == sale_id).first()
    if not db_sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    
    # Delete related sale items
    db.query(models.SaleItem).filter(models.SaleItem.sale_id == sale_id).delete()
    db.delete(db_sale)
    db.commit()
    return {"message": "Sale deleted successfully"}

# AUDIT FUNCTIONALITY

@router.get("/audit/random-section", response_model=schemas.RandomAuditSection)
def get_random_audit_section(db: Session = Depends(get_db)):
    """Get random section for audit"""
    result = services.StockAuditService.get_random_section_for_audit(db)
    if not result:
        raise HTTPException(status_code=404, detail="No sections available for audit")
    return result

@router.post("/audit/sessions", response_model=schemas.StockAuditSession)
def start_audit_session(
    session: schemas.StockAuditSessionCreate,
    db: Session = Depends(get_db)
):
    """Start new audit session"""
    return services.StockAuditService.start_audit_session(db, session.auditor)

@router.put("/items/{item_id}/audit", response_model=schemas.StockAuditRecord)
def audit_stock_item(
    item_id: int,
    physical_quantity: int,
    audited_by: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Record audit result for stock item"""
    try:
        audit_record = services.StockAuditService.record_audit(
            db, item_id, physical_quantity, audited_by, notes
        )
        return audit_record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/audit/discrepancies")
def get_stock_discrepancies(
    threshold: int = Query(0, description="Minimum discrepancy threshold"),
    db: Session = Depends(get_db)
):
    """Get all stock discrepancies above threshold"""
    discrepancies = services.StockAuditService.get_discrepancies(db, threshold)
    return {
        "total_discrepancies": len(discrepancies),
        "threshold": threshold,
        "discrepancies": discrepancies
    }

@router.get("/audit/summary")
def get_audit_summary(db: Session = Depends(get_db)):
    """Get overall audit summary"""
    return services.StockAuditService.get_audit_summary(db)

# STOCK CALCULATIONS

@router.post("/calculate-stock")
def update_software_stock(db: Session = Depends(get_db)):
    """Recalculate software stock for all items based on purchases/sales"""
    result = services.StockCalculationService.update_all_software_stock(db)
    return {
        "message": "Stock calculations updated",
        "details": result
    }

@router.get("/items/{item_id}/stock-calculation")
def get_item_stock_calculation(item_id: int, db: Session = Depends(get_db)):
    """Get detailed stock calculation for specific item"""
    item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Stock item not found")
    
    calculated_stock = services.StockCalculationService.calculate_software_stock(db, item_id)
    
    # Get purchase and sale details
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
    db: Session = Depends(get_db)
):
    """Get low stock items report"""
    items = services.StockReportService.get_low_stock_items(db, threshold)
    return {
        "threshold": threshold,
        "total_low_stock_items": len(items),
        "items": items
    }

@router.get("/reports/expiring")
def get_expiring_items_report(
    days_ahead: int = Query(30, description="Days ahead to check for expiry"),
    db: Session = Depends(get_db)
):
    """Get expiring items report"""
    items = services.StockReportService.get_expiring_items(db, days_ahead)
    return {
        "days_ahead": days_ahead,
        "total_expiring_items": len(items),
        "items": items
    }

@router.get("/reports/stock-movement")
def get_stock_movement_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db)
):
    """Get stock movement report for date range"""
    return services.StockReportService.get_stock_movement_report(db, start_date, end_date)