"""Service to sync verified invoices to stock audit system"""
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InvoiceStockSyncService:

    @staticmethod
    def sync_invoice_to_stock(db: Session, invoice_id: int, shop_id: int) -> dict:
        """Sync verified invoice items to stock audit system.

        Does NOT commit — caller is responsible for the final commit or rollback.
        This allows the caller to wrap verification + sync in a single atomic transaction.
        """
        from modules.invoice_analyzer_v2.models import PurchaseInvoice, PurchaseInvoiceItem
        from modules.stock_audit_v2.models import StockItem

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
        skipped_items = []

        for invoice_item in invoice.items:
            # Skip items with no product name — can't match or create a meaningful stock entry
            if not invoice_item.product_name:
                logger.warning(
                    f"Skipping invoice item id={invoice_item.id} on invoice {invoice_id}: product_name is null"
                )
                skipped_items.append(invoice_item.id)
                continue

            # Include free/bonus units in stock quantity
            billed_qty = invoice_item.quantity or 0
            free_qty = invoice_item.free_quantity or 0
            total_quantity = round(billed_qty + free_qty)

            # Check if item already exists (by product_name + batch_number)
            existing_item = db.query(StockItem).filter(
                StockItem.shop_id == shop_id,
                StockItem.product_name == invoice_item.product_name,
                StockItem.batch_number == invoice_item.batch_number
            ).first()

            if existing_item:
                # Update quantity
                existing_item.quantity_software += total_quantity
                existing_item.updated_at = datetime.now()
                updated_items.append(existing_item.id)
                logger.info(f"Updated stock item {existing_item.id}: +{total_quantity} (billed={billed_qty}, free={free_qty})")
            else:
                # Create new stock item
                stock_item = StockItem(
                    shop_id=shop_id,
                    composition=invoice_item.composition,
                    manufacturer=invoice_item.manufacturer,
                    hsn_code=invoice_item.hsn_code,
                    product_name=invoice_item.product_name,
                    batch_number=invoice_item.batch_number,
                    package=invoice_item.package,
                    unit=invoice_item.unit,
                    manufacturing_date=invoice_item.manufacturing_date,
                    expiry_date=invoice_item.expiry_date,
                    mrp=invoice_item.mrp,
                    quantity_software=total_quantity,
                    unit_price=invoice_item.unit_price,
                    selling_price=invoice_item.selling_price,
                    profit_margin=invoice_item.profit_margin,
                    source_invoice_id=invoice_id,
                    section_id=None  # Staff will assign later
                )
                db.add(stock_item)
                db.flush()
                synced_items.append(stock_item.id)
                logger.info(f"Created stock item {stock_item.id}: {invoice_item.product_name} qty={total_quantity} (billed={billed_qty}, free={free_qty})")

        # Caller commits — do not call db.commit() here
        return {
            "invoice_id": invoice_id,
            "new_items": len(synced_items),
            "updated_items": len(updated_items),
            "skipped_items": len(skipped_items),
            "synced_item_ids": synced_items,
            "updated_item_ids": updated_items,
        }
