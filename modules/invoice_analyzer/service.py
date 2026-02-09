from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from .models import (
    PurchaseInvoice, PurchaseInvoiceItem, ItemSale, 
    ExpiryAlert, MonthlyInvoiceSummary
)
from .schemas import (
    PurchaseInvoiceCreate, ItemSaleCreate, InvoiceAnalytics,
    MovementAnalytics, AIInsights
)

logger = logging.getLogger(__name__)

class PurchaseInvoiceService:
    
    @staticmethod
    def create_invoice(db: Session, invoice_data: PurchaseInvoiceCreate, shop_id: Optional[int] = None) -> PurchaseInvoice:
        """Create a new purchase invoice with items and automatic calculations"""
        
        # Calculate totals
        total_amount = sum(item.purchased_quantity * item.unit_cost for item in invoice_data.items)
        total_items = len(invoice_data.items)
        total_quantity = sum(item.purchased_quantity for item in invoice_data.items)
        
        # Create invoice
        invoice = PurchaseInvoice(
            shop_id=shop_id,
            invoice_number=invoice_data.invoice_number,
            supplier_name=invoice_data.supplier_name,
            invoice_date=invoice_data.invoice_date,
            received_date=invoice_data.received_date,
            total_amount=total_amount,
            total_items=total_items,
            total_quantity=total_quantity
        )
        
        db.add(invoice)
        db.flush()  # Get invoice ID
        
        # Create items
        for item_data in invoice_data.items:
            item = PurchaseInvoiceItem(
                invoice_id=invoice.id,
                item_code=item_data.item_code,
                item_name=item_data.item_name,
                batch_number=item_data.batch_number,
                purchased_quantity=item_data.purchased_quantity,
                remaining_quantity=item_data.purchased_quantity,
                unit_cost=item_data.unit_cost,
                selling_price=item_data.selling_price,
                total_cost=item_data.purchased_quantity * item_data.unit_cost,
                expiry_date=item_data.expiry_date
            )
            
            # Calculate expiry info
            if item.expiry_date:
                days_to_expiry = (item.expiry_date - date.today()).days
                item.days_to_expiry = days_to_expiry
                item.is_expiring_soon = days_to_expiry <= 45
                item.is_expiring_critical = days_to_expiry <= 365
                
                # Create expiry alerts
                PurchaseInvoiceService._create_expiry_alerts(db, item)
            
            db.add(item)
        
        # Update invoice status and color
        PurchaseInvoiceService._update_invoice_status(db, invoice)
        
        # Update monthly summary
        PurchaseInvoiceService._update_monthly_summary(db, invoice)
        
        db.commit()
        db.refresh(invoice)
        return invoice
    
    @staticmethod
    def record_sale(db: Session, sale_data: ItemSaleCreate) -> ItemSale:
        """Record a sale and update item quantities and invoice status"""
        
        # Get item
        item = db.query(PurchaseInvoiceItem).filter(
            PurchaseInvoiceItem.id == sale_data.item_id
        ).first()
        
        if not item:
            raise ValueError("Item not found")
        
        if item.remaining_quantity < sale_data.quantity_sold:
            raise ValueError("Insufficient stock")
        
        # Calculate profit
        profit_margin = ((sale_data.sale_price - item.unit_cost) / item.unit_cost) * 100
        
        # Create sale record
        sale = ItemSale(
            purchase_invoice_id=item.invoice_id,
            item_id=item.id,
            sale_date=date.today(),
            quantity_sold=sale_data.quantity_sold,
            sale_price=sale_data.sale_price,
            profit_margin=profit_margin,
            customer_type=sale_data.customer_type
        )
        
        # Update item quantities
        item.sold_quantity += sale_data.quantity_sold
        item.remaining_quantity -= sale_data.quantity_sold
        
        # Update movement rate (items sold per day)
        days_since_receipt = (date.today() - item.invoice.received_date).days or 1
        item.movement_rate = item.sold_quantity / days_since_receipt
        
        # Update demand category
        item.demand_category = PurchaseInvoiceService._calculate_demand_category(item.movement_rate)
        
        db.add(sale)
        db.commit()
        
        # Update invoice status
        invoice = db.query(PurchaseInvoice).filter(PurchaseInvoice.id == item.invoice_id).first()
        PurchaseInvoiceService._update_invoice_status(db, invoice)
        
        return sale
    
    @staticmethod
    def get_monthly_invoices(db: Session, year: int, month: int, shop_id: Optional[int] = None) -> List[PurchaseInvoice]:
        """Get all invoices for a specific month"""
        query = db.query(PurchaseInvoice).filter(
            extract('year', PurchaseInvoice.invoice_date) == year,
            extract('month', PurchaseInvoice.invoice_date) == month
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        return query.order_by(PurchaseInvoice.invoice_date.desc()).all()
    
    @staticmethod
    def get_expiry_alerts(db: Session, days_ahead: int = 45, shop_id: Optional[int] = None) -> List[ExpiryAlert]:
        """Get pending expiry alerts"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = db.query(ExpiryAlert).join(
            PurchaseInvoiceItem, ExpiryAlert.item_id == PurchaseInvoiceItem.id
        ).join(
            PurchaseInvoice, PurchaseInvoiceItem.invoice_id == PurchaseInvoice.id
        ).filter(
            ExpiryAlert.is_acknowledged == False,
            ExpiryAlert.alert_date <= cutoff_date
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        return query.order_by(ExpiryAlert.alert_date).all()
    
    @staticmethod
    def get_analytics(db: Session, year: int, month: int, shop_id: Optional[int] = None) -> InvoiceAnalytics:
        """Get comprehensive analytics for a month"""
        
        # Base query
        base_query = db.query(PurchaseInvoice).filter(
            extract('year', PurchaseInvoice.invoice_date) == year,
            extract('month', PurchaseInvoice.invoice_date) == month
        )
        
        if shop_id:
            base_query = base_query.filter(PurchaseInvoice.shop_id == shop_id)
        
        invoices = base_query.all()
        
        # Calculate metrics
        total_invoices = len(invoices)
        total_value = sum(inv.total_amount for inv in invoices)
        sold_out_invoices = len([inv for inv in invoices if inv.color_code == "green"])
        partial_invoices = len([inv for inv in invoices if inv.color_code == "yellow"])
        unsold_invoices = len([inv for inv in invoices if inv.color_code == "red"])
        
        avg_sold_percentage = sum(inv.sold_percentage for inv in invoices) / total_invoices if total_invoices > 0 else 0
        
        # Get expiring alerts count
        expiring_alerts = len(PurchaseInvoiceService.get_expiry_alerts(db, 45, shop_id))
        
        # Get top and slow moving items
        top_moving_items = PurchaseInvoiceService._get_top_moving_items(db, year, month, shop_id)
        slow_moving_items = PurchaseInvoiceService._get_slow_moving_items(db, year, month, shop_id)
        
        return InvoiceAnalytics(
            total_invoices=total_invoices,
            total_value=total_value,
            sold_out_invoices=sold_out_invoices,
            partial_invoices=partial_invoices,
            unsold_invoices=unsold_invoices,
            average_sold_percentage=avg_sold_percentage,
            expiring_alerts=expiring_alerts,
            top_moving_items=top_moving_items,
            slow_moving_items=slow_moving_items
        )
    
    @staticmethod
    def _update_invoice_status(db: Session, invoice: PurchaseInvoice):
        """Update invoice status and color based on sold percentage"""
        
        # Calculate sold percentage
        total_purchased = sum(item.purchased_quantity for item in invoice.items)
        total_sold = sum(item.sold_quantity for item in invoice.items)
        
        if total_purchased > 0:
            sold_percentage = (total_sold / total_purchased) * 100
        else:
            sold_percentage = 0
        
        invoice.sold_percentage = sold_percentage
        
        # Update status and color
        if sold_percentage >= 95:
            invoice.status = "sold_out"
            invoice.color_code = "green"
        elif sold_percentage >= 30:
            invoice.status = "partial"
            invoice.color_code = "yellow"
        else:
            invoice.status = "received"
            invoice.color_code = "red"
        
        # Check for expiring items
        invoice.has_expiring_items = any(item.is_expiring_soon for item in invoice.items)
        
        # Find nearest expiry
        expiry_days = [item.days_to_expiry for item in invoice.items if item.days_to_expiry is not None]
        invoice.nearest_expiry_days = min(expiry_days) if expiry_days else None
        
        db.commit()
    
    @staticmethod
    def _create_expiry_alerts(db: Session, item: PurchaseInvoiceItem):
        """Create expiry alerts for an item with AI-powered suppression"""
        
        if not item.expiry_date:
            return
        
        days_to_expiry = item.days_to_expiry
        
        # Initialize AI analytics for smart alert suppression
        from .ai_analytics import PurchaseInvoiceAIAnalytics
        ai_analytics = PurchaseInvoiceAIAnalytics()
        
        # Check if alert should be suppressed for fast-moving items
        suppress_alert = ai_analytics.should_suppress_expiry_alert(db, item)
        
        # 45-day alert
        if days_to_expiry <= 45 and days_to_expiry > 0:
            if not suppress_alert:  # Only create if not suppressed
                alert = ExpiryAlert(
                    item_id=item.id,
                    alert_type="45_days",
                    alert_date=date.today(),
                    message=f"Item {item.item_name} (Code: {item.item_code}) expires in {days_to_expiry} days",
                    priority="high" if days_to_expiry <= 15 else "medium"
                )
                db.add(alert)
            else:
                # Log suppression for tracking
                logger.info(f"Expiry alert suppressed for fast-moving item {item.item_code} - predicted sellout before expiry")
        
        # 1-year alert (on receipt) - always create for tracking
        if days_to_expiry <= 365:
            alert = ExpiryAlert(
                item_id=item.id,
                alert_type="1_year",
                alert_date=date.today(),
                message=f"Item {item.item_name} (Code: {item.item_code}) expires within 1 year ({days_to_expiry} days)",
                priority="low"
            )
            db.add(alert)
        
        # Expired alert - always create
        if days_to_expiry <= 0:
            alert = ExpiryAlert(
                item_id=item.id,
                alert_type="expired",
                alert_date=date.today(),
                message=f"Item {item.item_name} (Code: {item.item_code}) has EXPIRED",
                priority="critical"
            )
            db.add(alert)
    
    @staticmethod
    def _calculate_demand_category(movement_rate: float) -> str:
        """Calculate demand category based on movement rate"""
        if movement_rate >= 5:
            return "fast"
        elif movement_rate >= 2:
            return "medium"
        elif movement_rate >= 0.5:
            return "slow"
        else:
            return "dead"
    
    @staticmethod
    def _update_monthly_summary(db: Session, invoice: PurchaseInvoice):
        """Update or create monthly summary"""
        
        year = invoice.invoice_date.year
        month = invoice.invoice_date.month
        
        summary = db.query(MonthlyInvoiceSummary).filter(
            MonthlyInvoiceSummary.year == year,
            MonthlyInvoiceSummary.month == month,
            MonthlyInvoiceSummary.shop_id == invoice.shop_id
        ).first()
        
        if not summary:
            summary = MonthlyInvoiceSummary(
                shop_id=invoice.shop_id,
                year=year,
                month=month
            )
            db.add(summary)
        
        # Recalculate summary stats
        monthly_invoices = PurchaseInvoiceService.get_monthly_invoices(db, year, month, invoice.shop_id)
        
        summary.total_invoices = len(monthly_invoices)
        summary.total_amount = sum(inv.total_amount for inv in monthly_invoices)
        summary.total_items = sum(inv.total_items for inv in monthly_invoices)
        
        summary.green_invoices = len([inv for inv in monthly_invoices if inv.color_code == "green"])
        summary.yellow_invoices = len([inv for inv in monthly_invoices if inv.color_code == "yellow"])
        summary.red_invoices = len([inv for inv in monthly_invoices if inv.color_code == "red"])
        
        # Overall month color
        if summary.green_invoices == summary.total_invoices and summary.total_invoices > 0:
            summary.month_color = "green"
        elif summary.green_invoices + summary.yellow_invoices >= summary.total_invoices * 0.7:
            summary.month_color = "yellow"
        else:
            summary.month_color = "red"
        
        # Overall sold percentage
        if summary.total_invoices > 0:
            summary.overall_sold_percentage = sum(inv.sold_percentage for inv in monthly_invoices) / summary.total_invoices
        
        db.commit()
    
    @staticmethod
    def _get_top_moving_items(db: Session, year: int, month: int, shop_id: Optional[int] = None, limit: int = 10) -> List[dict]:
        """Get top moving items for the month"""
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            extract('year', PurchaseInvoice.invoice_date) == year,
            extract('month', PurchaseInvoice.invoice_date) == month
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.order_by(PurchaseInvoiceItem.movement_rate.desc()).limit(limit).all()
        
        return [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "movement_rate": item.movement_rate,
                "sold_percentage": (item.sold_quantity / item.purchased_quantity) * 100 if item.purchased_quantity > 0 else 0
            }
            for item in items
        ]
    
    @staticmethod
    def _get_slow_moving_items(db: Session, year: int, month: int, shop_id: Optional[int] = None, limit: int = 10) -> List[dict]:
        """Get slow moving items for the month"""
        
        query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
            extract('year', PurchaseInvoice.invoice_date) == year,
            extract('month', PurchaseInvoice.invoice_date) == month,
            PurchaseInvoiceItem.movement_rate < 1.0  # Slow moving threshold
        )
        
        if shop_id:
            query = query.filter(PurchaseInvoice.shop_id == shop_id)
        
        items = query.order_by(PurchaseInvoiceItem.movement_rate.asc()).limit(limit).all()
        
        return [
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "movement_rate": item.movement_rate,
                "remaining_quantity": item.remaining_quantity,
                "days_to_expiry": item.days_to_expiry
            }
            for item in items
        ]