"""
Shared stock reversal service for invoice deletion.
Used by both staff and admin delete endpoints to avoid duplication.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def reverse_stock_for_invoice(db: Session, invoice, invoice_id: int, shop_id: int) -> tuple[bool, list[str]]:
    """
    Reverse stock quantities when an admin-verified invoice is deleted.

    Returns:
        (stock_reversed: bool, items_in_use: list[str])

    Raises:
        HTTPException 400 if reversal fails (rolls back DB).
    """
    if not invoice.is_admin_verified:
        return False, []

    stock_reversed = False
    items_in_use = []

    try:
        from modules.stock_audit_v2.models import StockItem
        from modules.billing_v2.models import BillItem

        for invoice_item in invoice.items:
            stock_item = db.query(StockItem).filter(
                StockItem.shop_id == shop_id,
                StockItem.product_name == invoice_item.product_name,
                StockItem.batch_number == invoice_item.batch_number
            ).first()

            if not stock_item:
                continue

            bill_item_count = db.query(BillItem).filter(
                BillItem.stock_item_id == stock_item.id
            ).count()

            if bill_item_count > 0:
                # Item used in bills — reduce quantity and nullify source, but keep the stock item
                stock_item.quantity_software -= int(invoice_item.quantity)
                stock_item.source_invoice_id = None
                stock_item.updated_at = datetime.now()
                items_in_use.append(invoice_item.product_name)
                logger.info(
                    f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity} (item in use, not deleted)"
                )
            else:
                stock_item.quantity_software -= int(invoice_item.quantity)

                if stock_item.quantity_software <= 0 and stock_item.source_invoice_id == invoice_id:
                    # Clear FK before deletion
                    stock_item.source_invoice_id = None
                    db.flush()
                    db.delete(stock_item)
                    logger.info(f"Deleted stock item {stock_item.id} (quantity became <= 0)")
                else:
                    stock_item.source_invoice_id = None
                    stock_item.updated_at = datetime.now()
                    logger.info(
                        f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity}"
                    )

        # Clear any remaining FK references to this invoice
        from modules.stock_audit_v2.models import StockItem as SI
        db.query(SI).filter(
            SI.source_invoice_id == invoice_id
        ).update({"source_invoice_id": None})

        db.flush()
        stock_reversed = True

    except Exception as e:
        logger.error(f"Failed to reverse stock quantities for invoice {invoice_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Cannot delete invoice: {str(e)}")

    return stock_reversed, items_in_use
