"""Service to sync verified invoices to stock audit system"""
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


def parse_strips_per_box(package: str) -> int | None:
    """
    Parse a tablet package notation like "10X10", "40 x 6", "10 X 10" into
    strips_per_box (the first number).

    Returns the strips_per_box integer, or None if the package string does not
    match the NxM tablet format (e.g. "Bottle", "100ml", None).

    Convention: the format is  strips_per_box  X  tablets_per_strip.
    The order in practice can vary (tablets_per_strip X strips_per_box) and the
    user has acknowledged this ambiguity — the first number is always treated as
    strips_per_box.
    """
    if not package:
        return None
    match = re.match(r"^\s*(\d+)\s*[xX*]\s*(\d+)\s*$", str(package).strip())
    if not match:
        return None
    return int(match.group(1))


def boxes_to_strips(boxes: float, package: str) -> int:
    """Convert a box quantity to strip quantity using the package notation.

    If the package is a tablet NxM format, returns boxes * strips_per_box.
    Otherwise returns boxes unchanged (non-tablet products already counted in
    their native unit).
    """
    strips_per_box = parse_strips_per_box(package)
    if strips_per_box and strips_per_box > 0:
        return round(boxes * strips_per_box)
    return round(boxes)

class InvoiceStockSyncService:

    @staticmethod
    def sync_invoice_to_stock(db: Session, invoice_id: int, shop_id: int) -> dict:
        """Sync verified invoice items to stock audit system.

        Does NOT commit — caller is responsible for the final commit or rollback.
        This allows the caller to wrap verification + sync in a single atomic transaction.
        """
        from modules.invoice_analyzer_v2.models import PurchaseInvoice, PurchaseInvoiceItem
        from modules.stock_audit_v2.models import StockItem

        # Get invoice — caller (admin_routes) already validates staff verification
        # before calling this, so we don't re-check is_verified here (the flag is
        # set in-memory by the caller but not yet flushed when this query runs).
        invoice = db.query(PurchaseInvoice).filter(
            PurchaseInvoice.id == invoice_id,
            PurchaseInvoice.shop_id == shop_id,
        ).first()

        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found for shop {shop_id}")

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

            # Include free/bonus units, then convert boxes → strips for tablet products.
            # For products with a package like "10X10" (strips_per_box X tablets_per_strip),
            # the invoice records quantity in boxes but stock is counted in strips.
            billed_qty = invoice_item.quantity or 0
            free_qty = invoice_item.free_quantity or 0
            total_boxes = billed_qty + free_qty
            strips_per_box = parse_strips_per_box(invoice_item.package)
            total_quantity = round(total_boxes * strips_per_box) if strips_per_box else round(total_boxes)

            # unit_price on the invoice is per box; convert to per strip so that
            # quantity_software × unit_price still equals the correct purchase value.
            # e.g. ₹193.60/box ÷ 10 strips/box = ₹19.36/strip
            raw_unit_price = invoice_item.unit_price or 0.0
            unit_price = round(raw_unit_price / strips_per_box, 4) if strips_per_box else raw_unit_price

            # Check if item already exists (by product_name + batch_number)
            existing_item = db.query(StockItem).filter(
                StockItem.shop_id == shop_id,
                StockItem.product_name == invoice_item.product_name,
                StockItem.batch_number == invoice_item.batch_number
            ).first()

            if existing_item:
                # Update quantity; also update unit_price to the latest per-strip cost
                existing_item.quantity_software += total_quantity
                existing_item.unit_price = unit_price
                existing_item.updated_at = datetime.now()
                updated_items.append(existing_item.id)
                logger.info(
                    f"Updated stock item {existing_item.id}: +{total_quantity} strips "
                    f"unit_price={unit_price} (boxes_billed={billed_qty}, boxes_free={free_qty}, package={invoice_item.package})"
                )
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
                    unit_price=unit_price,
                    selling_price=invoice_item.selling_price,
                    profit_margin=invoice_item.profit_margin,
                    source_invoice_id=invoice_id,
                    section_id=None  # Staff will assign later
                )
                db.add(stock_item)
                db.flush()
                synced_items.append(stock_item.id)
                logger.info(
                    f"Created stock item {stock_item.id}: {invoice_item.product_name} "
                    f"qty={total_quantity} strips (boxes_billed={billed_qty}, boxes_free={free_qty}, package={invoice_item.package})"
                )

        # Caller commits — do not call db.commit() here
        return {
            "invoice_id": invoice_id,
            "new_items": len(synced_items),
            "updated_items": len(updated_items),
            "skipped_items": len(skipped_items),
            "synced_item_ids": synced_items,
            "updated_item_ids": updated_items,
        }
