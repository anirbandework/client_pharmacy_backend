from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import Bill, BillItem
from modules.stock_audit.models import StockItem, StockSection, StockRack
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import random
import string

class BillingService:
    
    @staticmethod
    def generate_bill_number(db: Session, shop_id: int) -> str:
        """Generate unique bill number for shop"""
        today = datetime.now()
        prefix = f"BILL-{today.strftime('%Y%m%d')}"
        
        # Get count of bills today for this shop
        count = db.query(Bill).filter(
            Bill.shop_id == shop_id,
            func.date(Bill.created_at) == today.date()
        ).count()
        
        return f"{prefix}-{shop_id}-{count + 1:04d}"
    
    @staticmethod
    def search_medicines(
        db: Session, 
        shop_id: int, 
        search_term: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search medicines by name, generic name, brand, or batch number"""
        query = db.query(
            StockItem,
            StockSection.section_name,
            StockRack.rack_number
        ).join(
            StockSection, StockItem.section_id == StockSection.id
        ).join(
            StockRack, StockSection.rack_id == StockRack.id
        ).filter(
            StockItem.shop_id == shop_id,
            StockItem.quantity_software > 0,  # Only available items
            or_(
                StockItem.item_name.ilike(f"%{search_term}%"),
                StockItem.generic_name.ilike(f"%{search_term}%"),
                StockItem.brand_name.ilike(f"%{search_term}%"),
                StockItem.batch_number.ilike(f"%{search_term}%")
            )
        ).limit(limit)
        
        results = []
        for item, section_name, rack_number in query.all():
            results.append({
                "id": item.id,
                "item_name": item.item_name,
                "generic_name": item.generic_name,
                "brand_name": item.brand_name,
                "batch_number": item.batch_number,
                "quantity_available": item.quantity_software,
                "mrp": item.mrp,
                "unit_price": item.unit_price,
                "rack_number": rack_number,
                "section_name": section_name,
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "manufacturer": item.manufacturer
            })
        
        return results
    
    @staticmethod
    def create_bill(
        db: Session,
        shop_id: int,
        staff_id: int,
        staff_name: str,
        bill_data: dict,
        items_data: List[dict]
    ) -> Bill:
        """Create bill and update stock"""
        
        # Calculate totals
        subtotal = 0.0
        tax_amount = 0.0
        
        # Validate stock availability
        for item_data in items_data:
            stock_item = db.query(StockItem).filter(
                StockItem.id == item_data['stock_item_id'],
                StockItem.shop_id == shop_id
            ).first()
            
            if not stock_item:
                raise ValueError(f"Stock item {item_data['stock_item_id']} not found")
            
            if stock_item.quantity_software < item_data['quantity']:
                raise ValueError(
                    f"Insufficient stock for {stock_item.item_name}. "
                    f"Available: {stock_item.quantity_software}, Required: {item_data['quantity']}"
                )
            
            # Calculate item totals
            item_subtotal = item_data['quantity'] * item_data['unit_price']
            item_discount = item_subtotal * (item_data.get('discount_percent', 0) / 100)
            item_after_discount = item_subtotal - item_discount
            item_tax = item_after_discount * (item_data.get('tax_percent', 5.0) / 100)  # Default 5%
            
            subtotal += item_subtotal
            tax_amount += item_tax
        
        # Apply bill-level discount
        discount_amount = bill_data.get('discount_amount', 0.0)
        total_amount = subtotal - discount_amount + tax_amount
        
        # Calculate change
        amount_paid = bill_data['amount_paid']
        change_returned = max(0, amount_paid - total_amount)
        
        # Generate bill number
        bill_number = BillingService.generate_bill_number(db, shop_id)
        
        # Create bill
        bill = Bill(
            shop_id=shop_id,
            staff_id=staff_id,
            staff_name=staff_name,
            bill_number=bill_number,
            customer_name=bill_data.get('customer_name'),
            customer_phone=bill_data.get('customer_phone'),
            customer_email=bill_data.get('customer_email'),
            doctor_name=bill_data.get('doctor_name'),
            payment_method=bill_data['payment_method'],
            payment_reference=bill_data.get('payment_reference'),
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=amount_paid,
            change_returned=change_returned,
            notes=bill_data.get('notes'),
            prescription_required=bill_data.get('prescription_required')
        )
        db.add(bill)
        db.flush()
        
        # Create bill items and update stock
        for item_data in items_data:
            stock_item = db.query(StockItem).filter(
                StockItem.id == item_data['stock_item_id'],
                StockItem.shop_id == shop_id
            ).first()
            
            # Calculate item pricing
            item_subtotal = item_data['quantity'] * item_data['unit_price']
            discount_percent = item_data.get('discount_percent', 0)
            item_discount = item_subtotal * (discount_percent / 100)
            item_after_discount = item_subtotal - item_discount
            tax_percent = item_data.get('tax_percent', 5.0)  # Default 5% GST
            
            # Split tax into SGST and CGST (equal split)
            sgst_percent = tax_percent / 2
            cgst_percent = tax_percent / 2
            sgst_amount = item_after_discount * (sgst_percent / 100)
            cgst_amount = item_after_discount * (cgst_percent / 100)
            item_tax = sgst_amount + cgst_amount
            
            item_total = item_after_discount + item_tax
            
            # Get location info
            section_name = stock_item.section.section_name if stock_item.section else None
            rack_number = stock_item.section.rack.rack_number if stock_item.section and stock_item.section.rack else None
            
            # Create bill item
            bill_item = BillItem(
                shop_id=shop_id,
                bill_id=bill.id,
                stock_item_id=stock_item.id,
                item_name=stock_item.item_name,
                batch_number=stock_item.batch_number,
                generic_name=stock_item.generic_name,
                brand_name=stock_item.brand_name,
                rack_number=rack_number,
                section_name=section_name,
                quantity=item_data['quantity'],
                mrp=item_data.get('mrp'),
                unit_price=item_data['unit_price'],
                discount_percent=discount_percent,
                discount_amount=item_discount,
                tax_percent=tax_percent,
                sgst_percent=sgst_percent,
                cgst_percent=cgst_percent,
                sgst_amount=sgst_amount,
                cgst_amount=cgst_amount,
                tax_amount=item_tax,
                total_price=item_total
            )
            db.add(bill_item)
            
            # Update stock quantity and recalculate discrepancy
            stock_item.quantity_software -= item_data['quantity']
            if stock_item.quantity_physical is not None:
                stock_item.audit_discrepancy = stock_item.quantity_software - stock_item.quantity_physical
            stock_item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(bill)
        return bill
    
    @staticmethod
    def get_bill_summary(
        db: Session,
        shop_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get billing summary for date range"""
        query = db.query(Bill).filter(Bill.shop_id == shop_id)
        
        if start_date:
            query = query.filter(func.date(Bill.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(Bill.created_at) <= end_date)
        
        bills = query.all()
        
        total_bills = len(bills)
        total_revenue = sum(b.total_amount for b in bills)
        
        # Payment method breakdown
        from .models import PaymentMethod
        cash_sales = sum(b.total_amount for b in bills if b.payment_method == PaymentMethod.CASH)
        online_sales = sum(b.total_amount for b in bills if b.payment_method == PaymentMethod.ONLINE)
        
        return {
            "total_bills": total_bills,
            "total_revenue": float(total_revenue),
            "cash_sales": float(cash_sales),
            "online_sales": float(online_sales),
            "average_bill_value": float(total_revenue / total_bills) if total_bills > 0 else 0.0
        }
    
    @staticmethod
    def get_top_selling_items(
        db: Session,
        shop_id: int,
        limit: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get top selling items"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            BillItem.item_name,
            func.sum(BillItem.quantity).label('total_quantity'),
            func.sum(BillItem.total_price).label('total_revenue'),
            func.count(BillItem.id).label('transaction_count')
        ).join(
            Bill, BillItem.bill_id == Bill.id
        ).filter(
            BillItem.shop_id == shop_id,
            Bill.created_at >= cutoff_date
        ).group_by(
            BillItem.item_name
        ).order_by(
            func.sum(BillItem.quantity).desc()
        ).limit(limit).all()
        
        return [
            {
                "item_name": r.item_name,
                "total_quantity": r.total_quantity,
                "total_revenue": float(r.total_revenue),
                "transaction_count": r.transaction_count
            }
            for r in results
        ]
