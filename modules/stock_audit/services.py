from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import *
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import random

class StockCalculationService:
    
    @staticmethod
    def calculate_software_stock(db: Session, stock_item_id: int) -> int:
        """Calculate software stock based on purchases and sales"""
        
        # Get total purchases
        total_purchased = db.query(func.sum(PurchaseItem.quantity)).filter(
            PurchaseItem.stock_item_id == stock_item_id
        ).scalar() or 0
        
        # Get total sales
        total_sold = db.query(func.sum(SaleItem.quantity)).filter(
            SaleItem.stock_item_id == stock_item_id
        ).scalar() or 0
        
        return total_purchased - total_sold
    
    @staticmethod
    def update_all_software_stock(db: Session) -> Dict[str, int]:
        """Update software stock for all items based on purchases/sales"""
        
        updated_count = 0
        items = db.query(StockItem).all()
        
        for item in items:
            calculated_stock = StockCalculationService.calculate_software_stock(db, item.id)
            if item.quantity_software != calculated_stock:
                item.quantity_software = calculated_stock
                item.updated_at = datetime.utcnow()
                updated_count += 1
        
        db.commit()
        
        return {
            "total_items": len(items),
            "updated_items": updated_count
        }
    
    @staticmethod
    def add_purchase(db: Session, purchase_data: dict, items_data: List[dict]) -> Purchase:
        """Add purchase and update stock levels"""
        
        # Create purchase record
        purchase = Purchase(**purchase_data)
        db.add(purchase)
        db.flush()  # Get the ID
        
        for item_data in items_data:
            # Create purchase item
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                **item_data
            )
            db.add(purchase_item)
            
            # Update stock item software quantity
            stock_item = db.query(StockItem).filter(
                StockItem.id == item_data['stock_item_id']
            ).first()
            if stock_item:
                stock_item.quantity_software += item_data['quantity']
                stock_item.updated_at = datetime.utcnow()
        
        db.commit()
        return purchase
    
    @staticmethod
    def add_sale(db: Session, sale_data: dict, items_data: List[dict]) -> Sale:
        """Add sale and update stock levels"""
        
        # Create sale record
        sale = Sale(**sale_data)
        db.add(sale)
        db.flush()  # Get the ID
        
        for item_data in items_data:
            # Check if enough stock available
            stock_item = db.query(StockItem).filter(
                StockItem.id == item_data['stock_item_id']
            ).first()
            
            if not stock_item:
                raise ValueError(f"Stock item {item_data['stock_item_id']} not found")
            
            if stock_item.quantity_software < item_data['quantity']:
                raise ValueError(f"Insufficient stock for {stock_item.item_name}. Available: {stock_item.quantity_software}, Required: {item_data['quantity']}")
            
            # Create sale item
            sale_item = SaleItem(
                sale_id=sale.id,
                **item_data
            )
            db.add(sale_item)
            
            # Update stock item software quantity
            stock_item.quantity_software -= item_data['quantity']
            stock_item.updated_at = datetime.utcnow()
        
        db.commit()
        return sale

class StockAuditService:
    
    @staticmethod
    def get_random_section_for_audit(db: Session, exclude_recent_days: int = 7) -> Optional[Dict[str, Any]]:
        """Get a random section that hasn't been audited recently"""
        
        # Get sections that haven't been audited recently
        cutoff_date = datetime.utcnow() - timedelta(days=exclude_recent_days)
        
        # Find sections with items that need auditing
        sections_query = db.query(StockSection).join(StockItem).filter(
            or_(
                StockItem.last_audit_date.is_(None),
                StockItem.last_audit_date < cutoff_date
            )
        ).distinct()
        
        sections = sections_query.all()
        
        if not sections:
            # If all sections audited recently, get any section
            sections = db.query(StockSection).all()
        
        if not sections:
            return None
        
        # Select random section
        random_section = random.choice(sections)
        
        # Get items in this section that need auditing
        items = db.query(StockItem).filter(
            StockItem.section_id == random_section.id
        ).all()
        
        return {
            "section": random_section,
            "items_to_audit": items,
            "total_items": len(items),
            "message": f"Audit section {random_section.section_name} in rack {random_section.rack.rack_number}"
        }
    
    @staticmethod
    def start_audit_session(db: Session, auditor: str) -> StockAuditSession:
        """Start a new audit session"""
        
        session = StockAuditSession(
            auditor=auditor,
            status="in_progress"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def record_audit(db: Session, stock_item_id: int, physical_quantity: int, audited_by: str, notes: str = None) -> StockAuditRecord:
        """Record audit result for a stock item"""
        
        stock_item = db.query(StockItem).filter(StockItem.id == stock_item_id).first()
        if not stock_item:
            raise ValueError("Stock item not found")
        
        # Calculate discrepancy
        software_quantity = stock_item.quantity_software
        discrepancy = software_quantity - physical_quantity
        
        # Create audit record
        audit_record = StockAuditRecord(
            stock_item_id=stock_item_id,
            audited_by=audited_by,
            software_quantity=software_quantity,
            physical_quantity=physical_quantity,
            discrepancy=discrepancy,
            notes=notes
        )
        db.add(audit_record)
        
        # Update stock item
        stock_item.quantity_physical = physical_quantity
        stock_item.last_audit_date = datetime.utcnow()
        stock_item.last_audit_by = audited_by
        stock_item.audit_discrepancy = discrepancy
        
        db.commit()
        db.refresh(audit_record)
        return audit_record
    
    @staticmethod
    def get_discrepancies(db: Session, threshold: int = 0) -> List[Dict[str, Any]]:
        """Get all stock discrepancies above threshold"""
        
        items = db.query(StockItem).join(StockSection).join(StockRack).filter(
            StockItem.quantity_physical.isnot(None),
            func.abs(StockItem.audit_discrepancy) > threshold
        ).all()
        
        discrepancies = []
        for item in items:
            discrepancies.append({
                "item": item,
                "software_qty": item.quantity_software,
                "physical_qty": item.quantity_physical,
                "difference": item.audit_discrepancy,
                "section_name": item.section.section_name,
                "rack_number": item.section.rack.rack_number,
                "last_audit_date": item.last_audit_date,
                "audited_by": item.last_audit_by
            })
        
        return discrepancies
    
    @staticmethod
    def complete_audit_session(db: Session, session_id: int, notes: str = None) -> StockAuditSession:
        """Complete an audit session"""
        
        session = db.query(StockAuditSession).filter(StockAuditSession.id == session_id).first()
        if not session:
            raise ValueError("Audit session not found")
        
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        if notes:
            session.session_notes = notes
        
        db.commit()
        return session
    
    @staticmethod
    def get_audit_summary(db: Session) -> Dict[str, Any]:
        """Get overall audit summary"""
        
        total_items = db.query(StockItem).count()
        total_sections = db.query(StockSection).count()
        
        items_with_discrepancies = db.query(StockItem).filter(
            StockItem.quantity_physical.isnot(None),
            StockItem.audit_discrepancy != 0
        ).count()
        
        last_audit = db.query(func.max(StockItem.last_audit_date)).scalar()
        
        pending_audits = db.query(StockItem).filter(
            StockItem.last_audit_date.is_(None)
        ).count()
        
        return {
            "total_items": total_items,
            "total_sections": total_sections,
            "items_with_discrepancies": items_with_discrepancies,
            "last_audit_date": last_audit,
            "pending_audits": pending_audits,
            "audit_completion_rate": ((total_items - pending_audits) / total_items * 100) if total_items > 0 else 0
        }

class StockReportService:
    
    @staticmethod
    def get_low_stock_items(db: Session, threshold: int = 10) -> List[StockItem]:
        """Get items with low stock"""
        
        return db.query(StockItem).filter(
            StockItem.quantity_software <= threshold
        ).all()
    
    @staticmethod
    def get_expiring_items(db: Session, days_ahead: int = 30) -> List[StockItem]:
        """Get items expiring within specified days"""
        
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        return db.query(StockItem).filter(
            StockItem.expiry_date.isnot(None),
            StockItem.expiry_date <= cutoff_date,
            StockItem.quantity_software > 0
        ).all()
    
    @staticmethod
    def get_stock_movement_report(db: Session, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get stock movement report for date range"""
        
        # Purchases in date range
        purchases = db.query(Purchase).filter(
            Purchase.purchase_date >= start_date,
            Purchase.purchase_date <= end_date
        ).all()
        
        # Sales in date range
        sales = db.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        ).all()
        
        total_purchased = sum(p.total_amount for p in purchases)
        total_sold = sum(s.total_amount for s in sales)
        
        return {
            "period": f"{start_date} to {end_date}",
            "total_purchases": len(purchases),
            "total_purchase_value": float(total_purchased),
            "total_sales": len(sales),
            "total_sales_value": float(total_sold),
            "net_movement": float(total_sold - total_purchased)
        }