"""Service to sync verified invoices to stock audit system"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)

class InvoiceStockSyncService:
    
    @staticmethod
    def sync_invoice_to_stock(db: Session, invoice_id: int, shop_id: int) -> dict:
        """Sync verified invoice items to stock audit system"""
        from modules.invoice_analyzer.models import PurchaseInvoice, PurchaseInvoiceItem
        from modules.stock_audit.models import StockItem
        
        # Get invoice
        invoice = db.query(PurchaseInvoice).filter(
            PurchaseInvoice.id == invoice_id,
            PurchaseInvoice.shop_id == shop_id,
            PurchaseInvoice.is_verified == True
        ).first()
        
        if not invoice:
            raise ValueError("Invoice not found or not verified")
        
        synced_items = []
        updated_items = []
        
        for invoice_item in invoice.items:
            # Check if item already exists (by product_name + batch_number)
            existing_item = db.query(StockItem).filter(
                StockItem.shop_id == shop_id,
                StockItem.product_name == invoice_item.product_name,
                StockItem.batch_number == invoice_item.batch_number
            ).first()
            
            if existing_item:
                # Update quantity
                existing_item.quantity_software += int(invoice_item.quantity)
                existing_item.updated_at = datetime.now()
                updated_items.append(existing_item.id)
                logger.info(f"Updated stock item {existing_item.id}: +{invoice_item.quantity}")
            else:
                # Create new stock item
                stock_item = StockItem(
                    shop_id=shop_id,
                    manufacturer=invoice_item.manufacturer,
                    hsn_code=invoice_item.hsn_code,
                    product_name=invoice_item.product_name,
                    batch_number=invoice_item.batch_number,
                    package=invoice_item.package,
                    expiry_date=invoice_item.expiry_date,
                    mrp=invoice_item.mrp,
                    quantity_software=int(invoice_item.quantity),
                    unit_price=invoice_item.unit_price,
                    source_invoice_id=invoice_id,
                    section_id=None  # Staff will assign later
                )
                db.add(stock_item)
                db.flush()
                synced_items.append(stock_item.id)
                logger.info(f"Created stock item {stock_item.id}: {invoice_item.product_name}")
        
        db.commit()
        
        return {
            "invoice_id": invoice_id,
            "new_items": len(synced_items),
            "updated_items": len(updated_items),
            "synced_item_ids": synced_items,
            "updated_item_ids": updated_items
        }
