from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.database.database import get_db
from modules.auth.distributor.dependencies import get_current_distributor
from modules.auth.dependencies import get_current_staff, get_current_admin
from .models import DistributorInvoice, DistributorInvoiceItem
from .schemas import DistributorInvoiceCreate, DistributorInvoiceResponse, DistributorInvoiceItemResponse, DistributorBasic, ShopBasic

router = APIRouter(prefix="/api/distributor-invoices", tags=["Distributor Invoices"])

def generate_invoice_number(db: Session, distributor_id: int) -> str:
    """Generate unique invoice number: DIST-{dist_id}-{YYYYMMDD}-{seq}"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    prefix = f"DIST-{distributor_id}-{date_str}"
    
    # Get count of invoices created today by this distributor
    count = db.query(DistributorInvoice).filter(
        DistributorInvoice.distributor_id == distributor_id,
        DistributorInvoice.invoice_number.like(f"{prefix}-%")
    ).count()
    
    return f"{prefix}-{count + 1:04d}"

@router.post("/", response_model=DistributorInvoiceResponse)
def create_invoice(invoice_data: DistributorInvoiceCreate, db: Session = Depends(get_db), current_distributor = Depends(get_current_distributor)):
    # Auto-generate unique invoice number
    invoice_number = generate_invoice_number(db, current_distributor.id)
    
    invoice = DistributorInvoice(
        distributor_id=current_distributor.id,
        shop_id=invoice_data.shop_id,
        external_shop_name=invoice_data.external_shop_name,
        external_shop_phone=invoice_data.external_shop_phone,
        external_shop_address=invoice_data.external_shop_address,
        external_shop_license=invoice_data.external_shop_license,
        external_shop_gst=invoice_data.external_shop_gst,
        invoice_number=invoice_number,
        invoice_date=invoice_data.invoice_date,
        gross_amount=invoice_data.gross_amount,
        discount_amount=invoice_data.discount_amount,
        taxable_amount=invoice_data.taxable_amount,
        cgst_amount=invoice_data.cgst_amount,
        sgst_amount=invoice_data.sgst_amount,
        igst_amount=invoice_data.igst_amount,
        total_gst=invoice_data.total_gst,
        round_off=invoice_data.round_off,
        net_amount=invoice_data.net_amount
    )
    db.add(invoice)
    db.flush()
    
    for item_data in invoice_data.items:
        item = DistributorInvoiceItem(
            invoice_id=invoice.id,
            shop_id=invoice.shop_id,
            **item_data.model_dump()
        )
        db.add(item)
    
    db.commit()
    db.refresh(invoice)
    return invoice

@router.get("/my-invoices", response_model=List[DistributorInvoiceResponse])
def get_my_invoices(db: Session = Depends(get_db), current_distributor = Depends(get_current_distributor)):
    from modules.auth.models import Shop
    from sqlalchemy.orm import joinedload
    
    invoices = db.query(DistributorInvoice).options(joinedload(DistributorInvoice.items)).filter(
        DistributorInvoice.distributor_id == current_distributor.id
    ).all()
    
    result = []
    for invoice in invoices:
        shop = db.query(Shop).filter(Shop.id == invoice.shop_id).first()
        result.append(DistributorInvoiceResponse(
            id=invoice.id,
            distributor_id=invoice.distributor_id,
            shop_id=invoice.shop_id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            gross_amount=invoice.gross_amount,
            discount_amount=invoice.discount_amount,
            taxable_amount=invoice.taxable_amount,
            cgst_amount=invoice.cgst_amount,
            sgst_amount=invoice.sgst_amount,
            igst_amount=invoice.igst_amount,
            total_gst=invoice.total_gst,
            round_off=invoice.round_off,
            net_amount=invoice.net_amount,
            is_staff_verified=invoice.is_staff_verified,
            staff_verified_at=invoice.staff_verified_at,
            is_admin_verified=invoice.is_admin_verified,
            admin_verified_at=invoice.admin_verified_at,
            is_rejected=invoice.is_rejected,
            rejection_reason=invoice.rejection_reason,
            created_at=invoice.created_at,
            items=[DistributorInvoiceItemResponse.model_validate(item) for item in invoice.items],
            distributor=DistributorBasic.model_validate(current_distributor),
            shop=ShopBasic.model_validate(shop) if shop else None,
            external_shop_name=invoice.external_shop_name,
            external_shop_phone=invoice.external_shop_phone,
            external_shop_address=invoice.external_shop_address,
            external_shop_license=invoice.external_shop_license,
            external_shop_gst=invoice.external_shop_gst,
            due_date=invoice.due_date,
            custom_fields=invoice.custom_fields or {}
        ))
    
    return result

@router.get("/staff/imported-invoices", response_model=List[DistributorInvoiceResponse])
def get_imported_invoices_for_staff(db: Session = Depends(get_db), current_staff = Depends(get_current_staff)):
    """Get all distributor invoices for this shop (to show in staff's purchase invoice list)"""
    from modules.auth.distributor.models import Distributor
    from sqlalchemy.orm import joinedload
    
    invoices = db.query(DistributorInvoice).options(
        joinedload(DistributorInvoice.items)
    ).filter(
        DistributorInvoice.shop_id == current_staff.shop_id
    ).order_by(DistributorInvoice.created_at.desc()).all()
    
    result = []
    for invoice in invoices:
        distributor = db.query(Distributor).filter(Distributor.id == invoice.distributor_id).first()
        result.append(DistributorInvoiceResponse(
            id=invoice.id,
            distributor_id=invoice.distributor_id,
            shop_id=invoice.shop_id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            gross_amount=invoice.gross_amount,
            discount_amount=invoice.discount_amount,
            taxable_amount=invoice.taxable_amount,
            cgst_amount=invoice.cgst_amount,
            sgst_amount=invoice.sgst_amount,
            igst_amount=invoice.igst_amount,
            total_gst=invoice.total_gst,
            round_off=invoice.round_off,
            net_amount=invoice.net_amount,
            is_staff_verified=invoice.is_staff_verified,
            staff_verified_at=invoice.staff_verified_at,
            is_admin_verified=invoice.is_admin_verified,
            admin_verified_at=invoice.admin_verified_at,
            is_rejected=invoice.is_rejected,
            rejection_reason=invoice.rejection_reason,
            created_at=invoice.created_at,
            items=[DistributorInvoiceItemResponse.model_validate(item) for item in invoice.items],
            distributor=DistributorBasic.model_validate(distributor) if distributor else None,
            shop=None,
            external_shop_name=invoice.external_shop_name,
            external_shop_phone=invoice.external_shop_phone,
            external_shop_address=invoice.external_shop_address,
            external_shop_license=invoice.external_shop_license,
            external_shop_gst=invoice.external_shop_gst,
            external_shop_food_license=invoice.external_shop_food_license,
            custom_fields=invoice.custom_fields or {}
        ))
    
    return result

@router.post("/staff/verify/{invoice_id}")
def staff_verify(invoice_id: int, db: Session = Depends(get_db), current_staff = Depends(get_current_staff)):
    """Staff verifies distributor invoice"""
    invoice = db.query(DistributorInvoice).filter(
        DistributorInvoice.id == invoice_id,
        DistributorInvoice.shop_id == current_staff.shop_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.is_staff_verified and not invoice.is_rejected:
        raise HTTPException(status_code=400, detail="Invoice already staff-verified")
    
    invoice.is_staff_verified = True
    invoice.staff_verified_by = current_staff.id
    invoice.staff_verified_at = datetime.now()
    invoice.is_rejected = False
    invoice.rejected_by = None
    invoice.rejected_at = None
    invoice.rejection_reason = None
    db.commit()
    
    return {"message": "Invoice verified by staff, awaiting admin approval"}

@router.get("/admin/pending", response_model=List[DistributorInvoiceResponse])
def get_pending_for_admin(db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    from modules.auth.models import Shop
    from modules.auth.distributor.models import Distributor
    from sqlalchemy.orm import joinedload
    
    invoices = db.query(DistributorInvoice).options(
        joinedload(DistributorInvoice.items)
    ).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        Shop.organization_id == current_admin.organization_id,
        DistributorInvoice.is_staff_verified == True,
        DistributorInvoice.is_admin_verified == False,
        DistributorInvoice.is_rejected == False
    ).all()
    
    result = []
    for invoice in invoices:
        distributor = db.query(Distributor).filter(Distributor.id == invoice.distributor_id).first()
        shop = db.query(Shop).filter(Shop.id == invoice.shop_id).first()
        result.append(DistributorInvoiceResponse(
            id=invoice.id,
            distributor_id=invoice.distributor_id,
            shop_id=invoice.shop_id,
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.invoice_date,
            due_date=invoice.due_date,
            gross_amount=invoice.gross_amount,
            discount_amount=invoice.discount_amount,
            taxable_amount=invoice.taxable_amount,
            cgst_amount=invoice.cgst_amount,
            sgst_amount=invoice.sgst_amount,
            igst_amount=invoice.igst_amount,
            total_gst=invoice.total_gst,
            round_off=invoice.round_off,
            net_amount=invoice.net_amount,
            is_staff_verified=invoice.is_staff_verified,
            staff_verified_at=invoice.staff_verified_at,
            is_admin_verified=invoice.is_admin_verified,
            admin_verified_at=invoice.admin_verified_at,
            is_rejected=invoice.is_rejected,
            rejection_reason=invoice.rejection_reason,
            created_at=invoice.created_at,
            items=[DistributorInvoiceItemResponse.model_validate(item) for item in invoice.items],
            distributor=DistributorBasic.model_validate(distributor) if distributor else None,
            shop=ShopBasic.model_validate(shop) if shop else None,
            external_shop_name=invoice.external_shop_name,
            external_shop_phone=invoice.external_shop_phone,
            external_shop_address=invoice.external_shop_address,
            external_shop_license=invoice.external_shop_license,
            external_shop_gst=invoice.external_shop_gst,
            external_shop_food_license=invoice.external_shop_food_license,
            custom_fields=invoice.custom_fields or {}
        ))
    
    return result

@router.get("/admin/approved")
def get_approved_for_admin(limit: int = 50, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    from modules.auth.models import Shop
    from modules.auth.distributor.models import Distributor
    
    invoices = db.query(DistributorInvoice).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        Shop.organization_id == current_admin.organization_id,
        DistributorInvoice.is_admin_verified == True
    ).order_by(DistributorInvoice.admin_verified_at.desc()).limit(limit).all()
    
    result = []
    for inv in invoices:
        distributor = db.query(Distributor).filter(Distributor.id == inv.distributor_id).first()
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "supplier_name": distributor.company_name if distributor else "Unknown",
            "net_amount": inv.net_amount,
            "total_items": len(inv.items),
            "is_admin_verified": inv.is_admin_verified,
            "staff_name": f"Imported from {distributor.company_name}" if distributor else "Distributor",
            "created_at": inv.created_at,
            "is_distributor_invoice": True
        })
    
    return result

@router.get("/admin/{invoice_id}", response_model=DistributorInvoiceResponse)
def get_invoice_admin(invoice_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Get specific distributor invoice details for admin"""
    from modules.auth.models import Shop
    from modules.auth.distributor.models import Distributor
    from sqlalchemy.orm import joinedload
    
    invoice = db.query(DistributorInvoice).options(
        joinedload(DistributorInvoice.items)
    ).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        DistributorInvoice.id == invoice_id,
        Shop.organization_id == current_admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    distributor = db.query(Distributor).filter(Distributor.id == invoice.distributor_id).first()
    shop = db.query(Shop).filter(Shop.id == invoice.shop_id).first()
    
    return DistributorInvoiceResponse(
        id=invoice.id,
        distributor_id=invoice.distributor_id,
        shop_id=invoice.shop_id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        gross_amount=invoice.gross_amount,
        discount_amount=invoice.discount_amount,
        taxable_amount=invoice.taxable_amount,
        cgst_amount=invoice.cgst_amount,
        sgst_amount=invoice.sgst_amount,
        igst_amount=invoice.igst_amount,
        total_gst=invoice.total_gst,
        round_off=invoice.round_off,
        net_amount=invoice.net_amount,
        is_staff_verified=invoice.is_staff_verified,
        staff_verified_at=invoice.staff_verified_at,
        is_admin_verified=invoice.is_admin_verified,
        admin_verified_at=invoice.admin_verified_at,
        is_rejected=invoice.is_rejected,
        rejection_reason=invoice.rejection_reason,
        created_at=invoice.created_at,
        items=[DistributorInvoiceItemResponse.model_validate(item) for item in invoice.items],
        distributor=DistributorBasic.model_validate(distributor) if distributor else None,
        shop=ShopBasic.model_validate(shop) if shop else None,
        external_shop_name=invoice.external_shop_name,
        external_shop_phone=invoice.external_shop_phone,
        external_shop_address=invoice.external_shop_address,
        external_shop_license=invoice.external_shop_license,
        external_shop_gst=invoice.external_shop_gst,
        external_shop_food_license=invoice.external_shop_food_license,
        custom_fields=invoice.custom_fields or {}
    )

@router.put("/admin/{invoice_id}")
def admin_update_distributor_invoice(invoice_id: int, invoice_data: DistributorInvoiceCreate, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Admin updates distributor invoice and re-syncs to stock"""
    from modules.auth.models import Shop
    from modules.stock_audit.models import StockItem
    import logging
    logger = logging.getLogger(__name__)
    
    invoice = db.query(DistributorInvoice).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        DistributorInvoice.id == invoice_id,
        Shop.organization_id == current_admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # If already synced to stock, we need to reverse the old quantities and apply new ones
    if invoice.is_admin_verified:
        # Reverse old stock quantities
        for old_item in invoice.items:
            stock_item = db.query(StockItem).filter(
                StockItem.shop_id == invoice.shop_id,
                StockItem.product_name == old_item.product_name,
                StockItem.batch_number == old_item.batch_number
            ).first()
            if stock_item:
                stock_item.quantity_software -= int(old_item.quantity)
                if stock_item.quantity_software <= 0:
                    db.delete(stock_item)
                logger.info(f"Reversed stock for {old_item.product_name}: -{old_item.quantity}")
    
    # Update invoice fields
    invoice.invoice_date = invoice_data.invoice_date
    invoice.due_date = invoice_data.due_date
    invoice.gross_amount = invoice_data.gross_amount
    invoice.discount_amount = invoice_data.discount_amount
    invoice.taxable_amount = invoice_data.taxable_amount
    invoice.cgst_amount = invoice_data.cgst_amount
    invoice.sgst_amount = invoice_data.sgst_amount
    invoice.igst_amount = invoice_data.igst_amount
    invoice.total_gst = invoice_data.total_gst
    invoice.round_off = invoice_data.round_off
    invoice.net_amount = invoice_data.net_amount
    invoice.custom_fields = invoice_data.custom_fields
    
    # Delete old items
    db.query(DistributorInvoiceItem).filter(DistributorInvoiceItem.invoice_id == invoice.id).delete()
    
    # Add new items
    for item_data in invoice_data.items:
        item = DistributorInvoiceItem(
            invoice_id=invoice.id,
            shop_id=invoice.shop_id,
            **item_data.model_dump()
        )
        db.add(item)
    
    db.commit()
    
    # Re-sync to stock if already verified
    if invoice.is_admin_verified:
        try:
            for item_data in invoice_data.items:
                stock_item = db.query(StockItem).filter(
                    StockItem.shop_id == invoice.shop_id,
                    StockItem.product_name == item_data.product_name,
                    StockItem.batch_number == item_data.batch_number
                ).first()
                
                if stock_item:
                    stock_item.quantity_software += int(item_data.quantity)
                    stock_item.unit_price = item_data.unit_price
                    stock_item.selling_price = item_data.selling_price
                    stock_item.profit_margin = min(item_data.profit_margin or 0, 999.99)
                    stock_item.updated_at = datetime.now()
                else:
                    stock_item = StockItem(
                        shop_id=invoice.shop_id,
                        composition=item_data.composition,
                        manufacturer=item_data.manufacturer,
                        hsn_code=item_data.hsn_code,
                        product_name=item_data.product_name,
                        batch_number=item_data.batch_number,
                        package=item_data.package,
                        unit=item_data.unit,
                        manufacturing_date=item_data.manufacturing_date,
                        expiry_date=item_data.expiry_date,
                        mrp=item_data.mrp,
                        quantity_software=int(item_data.quantity),
                        unit_price=item_data.unit_price,
                        selling_price=item_data.selling_price,
                        profit_margin=min(item_data.profit_margin or 0, 999.99),
                        source_invoice_id=None,
                        section_id=None
                    )
                    db.add(stock_item)
            
            db.commit()
            logger.info(f"✅ Updated distributor invoice {invoice_id} and re-synced to stock")
        except Exception as e:
            logger.error(f"❌ Failed to re-sync to stock: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to re-sync to stock: {str(e)}")
    
    return {"message": "Invoice updated successfully"}

@router.get("/{invoice_id}", response_model=DistributorInvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db), current_staff = Depends(get_current_staff)):
    """Get specific distributor invoice details for staff"""
    from modules.auth.distributor.models import Distributor
    from sqlalchemy.orm import joinedload
    
    invoice = db.query(DistributorInvoice).options(
        joinedload(DistributorInvoice.items)
    ).filter(
        DistributorInvoice.id == invoice_id,
        DistributorInvoice.shop_id == current_staff.shop_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    distributor = db.query(Distributor).filter(Distributor.id == invoice.distributor_id).first()
    
    return DistributorInvoiceResponse(
        id=invoice.id,
        distributor_id=invoice.distributor_id,
        shop_id=invoice.shop_id,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        gross_amount=invoice.gross_amount,
        discount_amount=invoice.discount_amount,
        taxable_amount=invoice.taxable_amount,
        cgst_amount=invoice.cgst_amount,
        sgst_amount=invoice.sgst_amount,
        igst_amount=invoice.igst_amount,
        total_gst=invoice.total_gst,
        round_off=invoice.round_off,
        net_amount=invoice.net_amount,
        is_staff_verified=invoice.is_staff_verified,
        staff_verified_at=invoice.staff_verified_at,
        is_admin_verified=invoice.is_admin_verified,
        admin_verified_at=invoice.admin_verified_at,
        is_rejected=invoice.is_rejected,
        rejection_reason=invoice.rejection_reason,
        created_at=invoice.created_at,
        items=[DistributorInvoiceItemResponse.model_validate(item) for item in invoice.items],
        distributor=DistributorBasic.model_validate(distributor) if distributor else None,
        shop=None,
        external_shop_name=invoice.external_shop_name,
        external_shop_phone=invoice.external_shop_phone,
        external_shop_address=invoice.external_shop_address,
        external_shop_license=invoice.external_shop_license,
        external_shop_gst=invoice.external_shop_gst,
        external_shop_food_license=invoice.external_shop_food_license,
        custom_fields=invoice.custom_fields or {}
    )

@router.post("/admin/verify/{invoice_id}")
def admin_verify(invoice_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Admin verifies distributor invoice and syncs to stock"""
    from modules.auth.models import Shop
    from modules.stock_audit.models import StockItem
    import logging
    logger = logging.getLogger(__name__)
    
    invoice = db.query(DistributorInvoice).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        DistributorInvoice.id == invoice_id,
        Shop.organization_id == current_admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not invoice.is_staff_verified:
        raise HTTPException(status_code=400, detail="Staff verification required first")
    
    if invoice.is_admin_verified:
        raise HTTPException(status_code=400, detail="Invoice already admin-verified")
    
    # Mark as admin verified
    invoice.is_admin_verified = True
    invoice.admin_verified_by = current_admin.id
    invoice.admin_verified_at = datetime.now()
    db.commit()
    
    # Sync to stock
    try:
        synced_items = []
        updated_items = []
        
        for item in invoice.items:
            # Check if stock item already exists
            stock_item = db.query(StockItem).filter(
                StockItem.shop_id == invoice.shop_id,
                StockItem.product_name == item.product_name,
                StockItem.batch_number == item.batch_number
            ).first()
            
            if stock_item:
                # Update existing stock
                stock_item.quantity_software += int(item.quantity)
                stock_item.updated_at = datetime.now()
                updated_items.append(stock_item.id)
                logger.info(f"Updated stock item {stock_item.id}: +{item.quantity}")
            else:
                # Create new stock item
                stock_item = StockItem(
                    shop_id=invoice.shop_id,
                    composition=item.composition,
                    manufacturer=item.manufacturer,
                    hsn_code=item.hsn_code,
                    product_name=item.product_name,
                    batch_number=item.batch_number,
                    package=item.package,
                    unit=item.unit,
                    manufacturing_date=item.manufacturing_date,
                    expiry_date=item.expiry_date,
                    mrp=item.mrp,
                    quantity_software=int(item.quantity),
                    unit_price=item.unit_price,
                    selling_price=item.selling_price,
                    profit_margin=min(item.profit_margin or 0, 999.99),
                    source_invoice_id=None,
                    section_id=None
                )
                db.add(stock_item)
                db.flush()
                synced_items.append(stock_item.id)
                logger.info(f"Created stock item {stock_item.id}: {item.product_name}")
        
        db.commit()
        logger.info(f"✅ Admin verified and synced distributor invoice {invoice_id} to stock")
        return {
            "message": "Invoice admin-verified and synced to stock",
            "sync_result": {
                "new_items": len(synced_items),
                "updated_items": len(updated_items)
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to sync distributor invoice to stock: {e}")
        # Rollback admin verification if sync fails
        invoice.is_admin_verified = False
        invoice.admin_verified_by = None
        invoice.admin_verified_at = None
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to sync to stock: {str(e)}")

@router.post("/admin/reject/{invoice_id}")
def admin_reject(invoice_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):
    """Admin rejects distributor invoice"""
    from modules.auth.models import Shop
    
    invoice = db.query(DistributorInvoice).join(Shop, DistributorInvoice.shop_id == Shop.id).filter(
        DistributorInvoice.id == invoice_id,
        Shop.organization_id == current_admin.organization_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.is_rejected = True
    invoice.rejected_by = current_admin.id
    invoice.rejected_at = datetime.now()
    invoice.rejection_reason = "Rejected by admin"
    db.commit()
    
    return {"message": "Invoice rejected"}

@router.post("/reject/{invoice_id}")
def reject_invoice(invoice_id: int, reason: str, db: Session = Depends(get_db), current_user = Depends(get_current_staff)):
    invoice = db.query(DistributorInvoice).filter(DistributorInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.is_rejected = True
    invoice.rejected_by = current_user.id
    invoice.rejected_at = datetime.now()
    invoice.rejection_reason = reason
    db.commit()
    return {"message": "Invoice rejected"}
