from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/{invoice_id}/admin-verify")
def admin_verify_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin verifies invoice and syncs to stock"""
    from . import models
    from modules.auth.models import Shop
    
    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.is_staff_verified:
        raise HTTPException(status_code=400, detail="Invoice must be staff-verified first")
    
    if invoice.is_admin_verified:
        raise HTTPException(status_code=400, detail="Invoice already admin-verified")
    
    # Mark as admin verified
    invoice.is_admin_verified = True
    invoice.admin_verified_by = admin.id
    invoice.admin_verified_at = datetime.now()
    invoice.is_verified = True  # Legacy field
    invoice.updated_at = datetime.now()
    
    db.commit()
    
    # Now sync to stock
    try:
        from modules.stock_audit.sync_service import InvoiceStockSyncService
        sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, invoice.shop_id)
        logger.info(f"✅ Admin verified and synced invoice {invoice_id} to stock: {sync_result}")
        return {"message": "Invoice admin-verified and synced to stock", "sync_result": sync_result}
    except Exception as e:
        logger.error(f"❌ Failed to sync invoice to stock: {e}")
        # Rollback admin verification if sync fails
        invoice.is_admin_verified = False
        invoice.admin_verified_by = None
        invoice.admin_verified_at = None
        invoice.is_verified = False
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to sync to stock: {str(e)}")

@router.post("/{invoice_id}/admin-reject")
def admin_reject_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin rejects invoice and sends back to staff for corrections"""
    from . import models
    from modules.auth.models import Shop
    
    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.is_admin_verified:
        raise HTTPException(status_code=400, detail="Cannot reject already verified invoice")
    
    # Reset staff verification and track rejection
    invoice.is_staff_verified = False
    invoice.staff_verified_by = None
    invoice.staff_verified_at = None
    invoice.admin_rejected_by = admin.id
    invoice.admin_rejected_at = datetime.now()
    invoice.updated_at = datetime.now()
    
    db.commit()
    
    return {"message": "Invoice rejected and sent back to staff"}

@router.put("/{invoice_id}/admin-update")
def admin_update_invoice(
    invoice_id: int,
    invoice_data: dict,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin updates invoice before verification"""
    from . import models
    from modules.auth.models import Shop
    
    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Allow editing even if verified
    
    # Parse dates
    def parse_date(date_obj):
        if isinstance(date_obj, str):
            try:
                from datetime import datetime as dt
                return dt.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return None
        return date_obj
    
    # Update invoice fields
    invoice.invoice_number = invoice_data['invoice_number']
    invoice.invoice_date = parse_date(invoice_data['invoice_date'])
    invoice.due_date = parse_date(invoice_data.get('due_date')) if invoice_data.get('due_date') else None
    invoice.supplier_name = invoice_data['supplier_name']
    invoice.supplier_address = invoice_data.get('supplier_address')
    invoice.supplier_gstin = invoice_data.get('supplier_gstin')
    invoice.supplier_dl_numbers = invoice_data.get('supplier_dl_numbers')
    invoice.supplier_phone = invoice_data.get('supplier_phone')
    invoice.gross_amount = invoice_data['gross_amount']
    invoice.discount_amount = invoice_data.get('discount_amount', 0)
    invoice.taxable_amount = invoice_data['taxable_amount']
    invoice.total_gst = invoice_data['total_gst']
    invoice.round_off = invoice_data.get('round_off', 0)
    invoice.net_amount = invoice_data['net_amount']
    invoice.custom_fields = invoice_data.get('custom_fields', {})
    invoice.updated_at = datetime.now()
    
    # Delete existing items
    db.query(models.PurchaseInvoiceItem).filter(
        models.PurchaseInvoiceItem.invoice_id == invoice_id
    ).delete()
    
    # Add updated items
    for item_data in invoice_data['items']:
        expiry_date = parse_date(item_data.get('expiry_date')) if item_data.get('expiry_date') else None
        manufacturing_date = parse_date(item_data.get('manufacturing_date')) if item_data.get('manufacturing_date') else None
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=invoice.shop_id,
            composition=item_data.get('composition'),
            manufacturer=item_data.get('manufacturer'),
            hsn_code=item_data.get('hsn_code'),
            product_name=item_data.get('product_name') or "Unknown Product",
            batch_number=item_data.get('batch_number'),
            quantity=item_data['quantity'],
            free_quantity=item_data.get('free_quantity', 0),
            package=item_data.get('package'),
            unit=item_data.get('unit'),
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            mrp=item_data.get('mrp'),
            unit_price=item_data['unit_price'],
            selling_price=item_data.get('selling_price', 0),
            profit_margin=item_data.get('profit_margin', 0),
            discount_on_purchase=item_data.get('discount_on_purchase', 0),
            discount_on_sales=item_data.get('discount_on_sales', 0),
            discount_percent=item_data.get('discount_percent', 0),
            discount_amount=item_data.get('discount_amount', 0),
            before_discount=item_data.get('before_discount', 0),
            taxable_amount=item_data['taxable_amount'],
            cgst_percent=item_data.get('cgst_percent', 0),
            cgst_amount=item_data.get('cgst_amount', 0),
            sgst_percent=item_data.get('sgst_percent', 0),
            sgst_amount=item_data.get('sgst_amount', 0),
            igst_percent=item_data.get('igst_percent', 0),
            igst_amount=item_data.get('igst_amount', 0),
            total_amount=item_data['total_amount'],
            custom_fields=item_data.get('custom_fields', {})
        )
        db.add(item)
    
    db.commit()
    db.refresh(invoice)
    
    return {"message": "Invoice updated successfully"}

@router.delete("/{invoice_id}/admin-delete")
def admin_delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin deletes invoice and reverses stock"""
    from . import models
    from modules.auth.models import Shop
    import logging
    logger = logging.getLogger(__name__)
    
    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if stock items are used in bills
    stock_reversed = False
    items_in_use = []
    
    if invoice.is_admin_verified:
        try:
            from modules.stock_audit.models import StockItem
            from modules.billing.models import BillItem
            
            for invoice_item in invoice.items:
                stock_item = db.query(StockItem).filter(
                    StockItem.shop_id == invoice.shop_id,
                    StockItem.product_name == invoice_item.product_name,
                    StockItem.batch_number == invoice_item.batch_number
                ).first()
                
                if stock_item:
                    bill_item_count = db.query(BillItem).filter(
                        BillItem.stock_item_id == stock_item.id
                    ).count()
                    
                    if bill_item_count > 0:
                        stock_item.quantity_software -= int(invoice_item.quantity)
                        stock_item.source_invoice_id = None
                        stock_item.updated_at = datetime.now()
                        items_in_use.append(invoice_item.product_name)
                        logger.info(f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity}")
                    else:
                        stock_item.quantity_software -= int(invoice_item.quantity)
                        
                        if stock_item.quantity_software <= 0 and stock_item.source_invoice_id == invoice_id:
                            db.delete(stock_item)
                            logger.info(f"Deleted stock item {stock_item.id}")
                        else:
                            stock_item.source_invoice_id = None
                            stock_item.updated_at = datetime.now()
                            logger.info(f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity}")
            
            db.flush()
            stock_reversed = True
        except Exception as e:
            logger.error(f"Failed to reverse stock quantities: {e}")
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Cannot delete invoice: {str(e)}")
    
    pdf_path = invoice.pdf_path
    db.delete(invoice)
    db.commit()
    
    if pdf_path:
        import os
        if os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except Exception as e:
                logger.warning(f"Failed to delete PDF file: {e}")
    
    response = {"message": "Invoice deleted successfully", "stock_reversed": stock_reversed}
    if items_in_use:
        response["warning"] = f"{len(items_in_use)} items are used in bills and were not deleted from stock"
    
    return response

@router.get("/pending-admin-verification")
def get_pending_admin_verification(
    shop_id: int = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get invoices pending admin verification (staff-verified but not admin-verified)"""
    from . import models
    from modules.auth.models import Shop, Staff
    
    query = db.query(models.PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        models.PurchaseInvoice.is_staff_verified == True,
        models.PurchaseInvoice.is_admin_verified == False
    )
    
    if shop_id:
        query = query.filter(models.PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.order_by(models.PurchaseInvoice.staff_verified_at.desc()).all()
    
    # Get shop names
    shop_map = {}
    shops = db.query(Shop).filter(Shop.organization_id == admin.organization_id).all()
    for shop in shops:
        shop_map[shop.id] = shop.shop_name
    
    result = []
    for inv in invoices:
        staff_verified_by_name = None
        if inv.staff_verified_by:
            verifier = db.query(Staff).filter(Staff.id == inv.staff_verified_by).first()
            if verifier:
                staff_verified_by_name = verifier.name
        
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat(),
            "supplier_name": inv.supplier_name,
            "net_amount": round(inv.net_amount, 2),
            "total_items": len(inv.items),
            "shop_id": inv.shop_id,
            "shop_name": shop_map.get(inv.shop_id, "Unknown"),
            "staff_name": inv.staff_name,
            "staff_verified_by_name": staff_verified_by_name,
            "staff_verified_at": inv.staff_verified_at.isoformat() if inv.staff_verified_at else None,
            "created_at": inv.created_at.isoformat(),
            "days_pending": (datetime.now() - inv.staff_verified_at).days if inv.staff_verified_at else 0
        })
    
    return {
        "total_pending": len(result),
        "total_value": round(sum(inv.net_amount for inv in invoices), 2),
        "invoices": result
    }

@router.get("/pending-staff-verification")
def get_pending_staff_verification(
    shop_id: int = None,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get invoices pending staff verification with details"""
    from . import models
    from modules.auth.models import Shop
    
    query = db.query(models.PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        models.PurchaseInvoice.is_staff_verified == False
    )
    
    if shop_id:
        query = query.filter(models.PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.order_by(models.PurchaseInvoice.created_at.desc()).all()
    
    # Get shop names
    shop_map = {}
    shops = db.query(Shop).filter(Shop.organization_id == admin.organization_id).all()
    for shop in shops:
        shop_map[shop.id] = shop.shop_name
    
    result = []
    for inv in invoices:
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date.isoformat(),
            "supplier_name": inv.supplier_name,
            "net_amount": round(inv.net_amount, 2),
            "total_items": len(inv.items),
            "shop_id": inv.shop_id,
            "shop_name": shop_map.get(inv.shop_id, "Unknown"),
            "staff_name": inv.staff_name,
            "created_at": inv.created_at.isoformat(),
            "days_pending": (datetime.now() - inv.created_at).days
        })
    
    return {
        "total_pending": len(result),
        "total_value": round(sum(inv.net_amount for inv in invoices), 2),
        "invoices": result
    }

@router.get("/admin-invoices")
def get_admin_invoices(
    shop_id: int = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get all invoices for admin (across organization)"""
    from . import models
    from modules.auth.models import Shop, Staff
    
    query = db.query(models.PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id
    )
    
    if shop_id:
        query = query.filter(models.PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.order_by(models.PurchaseInvoice.invoice_date.desc()).limit(limit).all()
    
    result = []
    for inv in invoices:
        staff_verified_by_name = None
        if inv.staff_verified_by:
            verifier = db.query(Staff).filter(Staff.id == inv.staff_verified_by).first()
            if verifier:
                staff_verified_by_name = verifier.name
        
        admin_verified_by_name = None
        if inv.admin_verified_by:
            admin_verifier = db.query(Admin).filter(Admin.id == inv.admin_verified_by).first()
            if admin_verifier:
                admin_verified_by_name = admin_verifier.full_name
        
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "supplier_name": inv.supplier_name,
            "net_amount": inv.net_amount,
            "total_items": len(inv.items),
            "is_staff_verified": inv.is_staff_verified,
            "staff_verified_by_name": staff_verified_by_name,
            "is_admin_verified": inv.is_admin_verified,
            "admin_verified_by_name": admin_verified_by_name,
            "staff_name": inv.staff_name,
            "created_at": inv.created_at
        })
    
    return result
