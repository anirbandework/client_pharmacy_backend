from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import Bill, BillItem
from modules.stock_audit_v2.models import StockItem, StockSection, StockRack
from modules.customer_tracking.services import CustomerTrackingService
from modules.customer_tracking.models import Customer
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import random
import string
import re
import math


def _parse_tablets_per_strip(package: str) -> int | None:
    """Parse '10 X 10' or '40X6' → tablets_per_strip (the second number)."""
    if not package:
        return None
    m = re.match(r"^\s*(\d+)\s*[xX*]\s*(\d+)\s*$", str(package).strip())
    return int(m.group(2)) if m else None


def _strips_to_deduct(tablet_qty: int, tablets_per_strip: int) -> int:
    """Strips consumed when selling tablet_qty loose tablets.
    Physically, opening a strip consumes the whole strip from inventory."""
    return math.ceil(tablet_qty / tablets_per_strip)

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
        ).outerjoin(
            StockSection, StockItem.section_id == StockSection.id
        ).outerjoin(
            StockRack, StockSection.rack_id == StockRack.id
        ).filter(
            StockItem.shop_id == shop_id,
            StockItem.quantity_software > 0,  # Only available items
            or_(
                StockItem.product_name.ilike(f"%{search_term}%"),
                StockItem.batch_number.ilike(f"%{search_term}%"),
                StockItem.manufacturer.ilike(f"%{search_term}%")
            )
        ).order_by(
            StockItem.expiry_date.asc().nulls_last()
        ).limit(limit)

        results = []
        for item, section_name, rack_number in query.all():
            results.append({
                "id": item.id,
                "product_name": item.product_name,
                "batch_number": item.batch_number,
                "quantity_available": item.quantity_software,
                "mrp": item.mrp,
                "unit_price": item.unit_price,
                "selling_price": item.selling_price,
                "rack_number": rack_number or "Unassigned",
                "section_name": section_name or "Unassigned",
                "expiry_date": item.expiry_date.isoformat() if item.expiry_date else None,
                "manufacturer": item.manufacturer,
                "hsn_code": item.hsn_code,
                "package": item.package
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

            sale_unit = item_data.get('sale_unit', 'strip')
            if sale_unit == 'tablet':
                tps = _parse_tablets_per_strip(stock_item.package)
                if not tps:
                    raise ValueError(
                        f"Cannot sell by tablet: package info missing for {stock_item.product_name}"
                    )
                required_strips = _strips_to_deduct(item_data['quantity'], tps)
            else:
                required_strips = item_data['quantity']

            if stock_item.quantity_software < required_strips:
                available = stock_item.quantity_software
                unit_label = "strips"
                raise ValueError(
                    f"Insufficient stock for {stock_item.product_name}. "
                    f"Available: {available} {unit_label}, Required: {required_strips} {unit_label}"
                )

            # Calculate item totals (quantity × unit_price works for both strip and tablet modes)
            item_subtotal = item_data['quantity'] * item_data['unit_price']
            item_discount = item_subtotal * (item_data.get('discount_percent', 0) / 100)
            item_after_discount = item_subtotal - item_discount
            item_tax = item_after_discount * (item_data.get('tax_percent', 5.0) / 100)  # Default 5%

            subtotal += item_subtotal
            tax_amount += item_tax
        
        # Apply bill-level discount before tax (discount reduces the taxable base)
        discount_amount = bill_data.get('discount_amount', 0.0)
        tax_amount = tax_amount * ((subtotal - discount_amount) / subtotal) if subtotal > 0 else 0.0
        total_amount = (subtotal - discount_amount) + tax_amount
        
        # Calculate total paid and change
        cash_amount = bill_data.get('cash_amount', 0.0)
        card_amount = bill_data.get('card_amount', 0.0)
        online_amount = bill_data.get('online_amount', 0.0)
        amount_paid = cash_amount + card_amount + online_amount
        is_pay_later = bill_data.get('is_pay_later', False)

        if is_pay_later:
            if not bill_data.get('customer_phone'):
                raise ValueError("Customer phone number is required for Pay Later bills.")
            amount_due = round(max(0.0, total_amount - amount_paid), 2)
            payment_status = 'pay_later' if amount_paid == 0 else 'partial'
            change_returned = 0.0
        else:
            if amount_paid < total_amount - 0.01:  # 1 paisa tolerance for floating point
                raise ValueError(f"Insufficient payment. Total: {total_amount}, Paid: {amount_paid}")
            amount_due = 0.0
            payment_status = 'paid'
            change_returned = max(0.0, amount_paid - total_amount)
        
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
            customer_category=bill_data.get('customer_category'),
            was_contacted_before=bill_data.get('was_contacted_before', False),
            cash_amount=cash_amount,
            card_amount=card_amount,
            online_amount=online_amount,
            payment_reference=bill_data.get('payment_reference'),
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=amount_paid,
            change_returned=change_returned,
            payment_status=payment_status,
            amount_due=amount_due,
            notes=bill_data.get('notes'),
            prescription_required=bill_data.get('prescription_required')
        )
        db.add(bill)
        db.flush()
        
        # Handle customer tracking
        if bill_data.get('customer_phone'):
            phone = bill_data['customer_phone']
            category = bill_data.get('customer_category', 'first_time_prescription')
            
            # Get or create customer
            customer = CustomerTrackingService.get_or_create_customer(
                db, shop_id, phone, bill_data.get('customer_name'), category
            )
            
            # Mark contact as converted if from contact sheet
            if bill_data.get('was_contacted_before'):
                CustomerTrackingService.mark_contact_converted(db, phone, shop_id, total_amount)
        
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
                item_name=stock_item.product_name,
                batch_number=stock_item.batch_number,
                generic_name=None,
                brand_name=None,
                rack_number=rack_number,
                section_name=section_name,
                quantity=item_data['quantity'],
                mrp=stock_item.mrp,
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
            
            # Update stock quantity (always deduct in strips)
            sale_unit = item_data.get('sale_unit', 'strip')
            if sale_unit == 'tablet':
                tps = _parse_tablets_per_strip(stock_item.package)
                strips_deducted = _strips_to_deduct(item_data['quantity'], tps)
            else:
                strips_deducted = item_data['quantity']

            bill_item.strips_deducted = strips_deducted
            stock_item.quantity_software -= strips_deducted
            if stock_item.quantity_physical is not None:
                stock_item.audit_discrepancy = stock_item.quantity_software - stock_item.quantity_physical
            stock_item.updated_at = datetime.now()
        
        db.commit()
        db.refresh(bill)
        return bill
    
    @staticmethod
    def get_pay_later_customers(
        db: Session,
        shop_id: int,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Get all customers with outstanding Pay Later balances, sorted by total due desc."""
        q = db.query(Bill).filter(
            Bill.shop_id == shop_id,
            Bill.payment_status.in_(['pay_later', 'partial']),
            Bill.amount_due > 0
        )
        if from_date:
            q = q.filter(func.date(Bill.created_at) >= from_date)
        if to_date:
            q = q.filter(func.date(Bill.created_at) <= to_date)
        outstanding_bills = q.order_by(Bill.created_at.asc()).all()

        customer_map: Dict[str, Dict] = {}
        for bill in outstanding_bills:
            phone = bill.customer_phone
            if phone not in customer_map:
                customer_map[phone] = {
                    'customer_name': bill.customer_name,
                    'customer_phone': phone,
                    'total_due': 0.0,
                    'bill_count': 0,
                    'oldest_bill_date': bill.created_at,
                    'bills': []
                }
            customer_map[phone]['total_due'] += bill.amount_due
            customer_map[phone]['bill_count'] += 1
            customer_map[phone]['bills'].append({
                'id': bill.id,
                'bill_number': bill.bill_number,
                'total_amount': bill.total_amount,
                'amount_paid': bill.amount_paid,
                'amount_due': bill.amount_due,
                'payment_status': bill.payment_status,
                'created_at': bill.created_at,
                'items_count': len(bill.items),
                'notes': bill.notes,
            })

        result = sorted(customer_map.values(), key=lambda x: x['total_due'], reverse=True)
        for c in result:
            c['total_due'] = round(c['total_due'], 2)
        return result

    @staticmethod
    def record_payment(db: Session, shop_id: int, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment for a customer's outstanding bills (oldest first / FIFO)."""
        customer_phone = payment_data['customer_phone']
        cash_amount = payment_data.get('cash_amount', 0.0)
        card_amount = payment_data.get('card_amount', 0.0)
        online_amount = payment_data.get('online_amount', 0.0)
        total_payment = cash_amount + card_amount + online_amount

        if total_payment <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        outstanding_bills = db.query(Bill).filter(
            Bill.shop_id == shop_id,
            Bill.customer_phone == customer_phone,
            Bill.payment_status.in_(['pay_later', 'partial']),
            Bill.amount_due > 0
        ).order_by(Bill.created_at.asc()).all()

        if not outstanding_bills:
            raise ValueError(f"No outstanding bills found for {customer_phone}.")

        total_due = sum(b.amount_due for b in outstanding_bills)
        if total_payment > total_due + 0.01:
            raise ValueError(f"Payment ₹{total_payment:.2f} exceeds outstanding balance ₹{total_due:.2f}.")

        remaining = total_payment
        bills_cleared = 0
        applied_to = []
        # Distribute cash/card/online proportionally across bills
        pay_ratio = total_payment / total_due if total_due > 0 else 1

        for bill in outstanding_bills:
            if remaining <= 0.001:
                break
            apply = min(remaining, bill.amount_due)
            # Distribute payment methods proportionally to this bill's share
            bill_ratio = apply / total_payment if total_payment > 0 else 0
            bill.cash_amount += round(cash_amount * bill_ratio, 2)
            bill.card_amount += round(card_amount * bill_ratio, 2)
            bill.online_amount += round(online_amount * bill_ratio, 2)
            bill.amount_paid = round(bill.amount_paid + apply, 2)
            bill.amount_due = round(max(0.0, bill.amount_due - apply), 2)
            if bill.amount_due < 0.01:
                bill.amount_due = 0.0
                bill.payment_status = 'paid'
                bills_cleared += 1
            else:
                bill.payment_status = 'partial'
            if payment_data.get('payment_reference'):
                bill.payment_reference = payment_data['payment_reference']
            applied_to.append({
                'bill_number': bill.bill_number,
                'applied': round(apply, 2),
                'remaining_due': bill.amount_due,
                'cleared': bill.payment_status == 'paid'
            })
            remaining = round(remaining - apply, 2)

        db.commit()
        remaining_due = sum(b.amount_due for b in outstanding_bills)
        return {
            'message': f'Payment of ₹{total_payment:.2f} recorded successfully.',
            'total_paid': round(total_payment, 2),
            'bills_cleared': bills_cleared,
            'remaining_due': round(remaining_due, 2),
            'applied_to': applied_to
        }

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
        cash_sales = sum(b.cash_amount for b in bills)
        card_sales = sum(b.card_amount for b in bills)
        online_sales = sum(b.online_amount for b in bills)
        
        return {
            "total_bills": total_bills,
            "total_revenue": float(total_revenue),
            "cash_sales": float(cash_sales),
            "card_sales": float(card_sales),
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
        cutoff_date = datetime.now() - timedelta(days=days)
        
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
                "product_name": r.item_name,
                "total_quantity": r.total_quantity,
                "total_revenue": float(r.total_revenue),
                "transaction_count": r.transaction_count
            }
            for r in results
        ]
