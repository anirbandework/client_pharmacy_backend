from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from .dependencies import get_current_user_with_geofence as get_current_user
from modules.auth.models import Staff
from typing import List, Optional
from datetime import datetime, date
import os
import shutil
import logging
from . import models, schemas
from .ai_extractor import AIInvoiceExtractor

logger = logging.getLogger(__name__)

router = APIRouter()

# Upload directory
UPLOAD_DIR = "uploads/invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.PurchaseInvoiceResponse)
async def upload_invoice_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Upload and process purchase invoice PDF"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📤 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    staff, shop_id = current_user
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        logger.error(f"❌ Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Save PDF file temporarily
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{shop_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        logger.info(f"💾 Saving file to: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"✅ File saved successfully")
    except Exception as e:
        logger.error(f"❌ Failed to save file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Extract text from PDF
    try:
        logger.info(f"🔍 Starting PDF extraction...")
        extractor = AIInvoiceExtractor()
        parsed_data = extractor.extract_from_pdf(file_path)
        logger.info(f"✅ PDF extraction completed - Found {len(parsed_data.get('items', []))} items")
    except Exception as e:
        logger.error(f"❌ PDF extraction failed: {str(e)}")
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")
    
    # Check for duplicate invoice (by invoice number OR by supplier+date+amount)
    invoice_number = parsed_data.get("invoice_number", "UNKNOWN")
    supplier_name = parsed_data.get("supplier_name", "Unknown Supplier")
    net_amount = parsed_data.get("net_amount", 0.0)
    
    existing_invoice = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id,
        models.PurchaseInvoice.invoice_number == invoice_number
    ).first()
    
    if existing_invoice:
        os.remove(file_path)
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate invoice detected! Invoice number '{invoice_number}' already exists."
        )
    
    # Parse dates
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except:
            return None
    
    # Create invoice record
    invoice = models.PurchaseInvoice(
        shop_id=shop_id,
        staff_id=staff.id,
        staff_name=staff.name,
        invoice_number=invoice_number,
        invoice_date=parse_date(parsed_data.get("invoice_date")) or datetime.now(),
        due_date=parse_date(parsed_data.get("due_date")),
        supplier_name=supplier_name,
        supplier_address=parsed_data.get("supplier_address"),
        supplier_gstin=parsed_data.get("supplier_gstin"),
        supplier_dl_numbers=parsed_data.get("supplier_dl_numbers"),
        supplier_phone=parsed_data.get("supplier_phone"),
        gross_amount=parsed_data.get("gross_amount", 0.0),
        discount_amount=parsed_data.get("discount_amount", 0.0),
        taxable_amount=parsed_data.get("taxable_amount", 0.0),
        total_gst=parsed_data.get("total_gst", 0.0),
        round_off=parsed_data.get("round_off", 0.0),
        net_amount=net_amount,
        pdf_filename=filename,
        pdf_path=file_path,
        raw_extracted_data=parsed_data
    )
    
    db.add(invoice)
    db.flush()
    
    # Create invoice items
    for item_data in parsed_data.get("items", []):
        # Parse expiry date - handle both MM/YYYY and DD/MM/YYYY formats
        expiry_date = None
        if item_data.get("expiry_date"):
            try:
                expiry_str = item_data['expiry_date']
                # If it's already a datetime, convert to date
                if isinstance(expiry_str, datetime):
                    expiry_date = expiry_str.date()
                elif '/' in expiry_str:
                    parts = expiry_str.split('/')
                    # If only 2 parts (MM/YYYY), prepend day as 01
                    if len(parts) == 2:
                        expiry_date = datetime.strptime(f"01/{expiry_str}", "%d/%m/%Y").date()
                    # If 3 parts (DD/MM/YYYY), parse as-is
                    elif len(parts) == 3:
                        expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y").date()
            except:
                pass
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            manufacturer=item_data.get("manufacturer"),
            hsn_code=item_data.get("hsn_code"),
            product_name=item_data.get("product_name", "Unknown Product"),
            batch_number=item_data.get("batch_number"),
            quantity=item_data.get("quantity", 1),
            package=item_data.get("package"),
            expiry_date=expiry_date,
            mrp=item_data.get("mrp"),
            free_quantity=item_data.get("free_quantity", 0.0),
            unit_price=item_data.get("unit_price", 0.0),
            discount_percent=item_data.get("discount_percent", 0.0),
            discount_amount=item_data.get("discount_amount", 0.0),
            taxable_amount=item_data.get("taxable_amount", 0.0),
            cgst_percent=item_data.get("cgst_percent", 0.0),
            cgst_amount=item_data.get("cgst_amount", 0.0),
            sgst_percent=item_data.get("sgst_percent", 0.0),
            sgst_amount=item_data.get("sgst_amount", 0.0),
            igst_percent=item_data.get("igst_percent", 0.0),
            igst_amount=item_data.get("igst_amount", 0.0),
            total_amount=item_data.get("total_amount", 0.0)
        )
        db.add(item)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice

@router.get("/", response_model=List[schemas.PurchaseInvoiceListResponse])
def get_invoices(
    skip: int = 0,
    limit: int = 100,
    supplier_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get all purchase invoices for the shop"""
    staff, shop_id = current_user
    
    query = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id
    )
    
    if supplier_name:
        query = query.filter(models.PurchaseInvoice.supplier_name.ilike(f"%{supplier_name}%"))
    
    if start_date:
        query = query.filter(models.PurchaseInvoice.invoice_date >= start_date)
    
    if end_date:
        query = query.filter(models.PurchaseInvoice.invoice_date <= end_date)
    
    invoices = query.order_by(models.PurchaseInvoice.invoice_date.desc()).offset(skip).limit(limit).all()
    
    # Add item count and verified_by_name
    result = []
    for inv in invoices:
        verified_by_name = None
        if inv.verified_by:
            verifier = db.query(Staff).filter(Staff.id == inv.verified_by).first()
            if verifier:
                verified_by_name = verifier.name
        
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": inv.invoice_date,
            "supplier_name": inv.supplier_name,
            "net_amount": inv.net_amount,
            "total_items": len(inv.items),
            "is_verified": inv.is_verified,
            "verified_by_name": verified_by_name,
            "staff_name": inv.staff_name,
            "created_at": inv.created_at
        })
    
    return result

@router.put("/{invoice_id}", response_model=schemas.PurchaseInvoiceResponse)
def update_invoice(
    invoice_id: int,
    invoice_data: schemas.PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Update invoice details after manual verification"""
    staff, shop_id = current_user
    
    invoice = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.id == invoice_id,
        models.PurchaseInvoice.shop_id == shop_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Parse dates
    def parse_date(date_obj):
        if isinstance(date_obj, str):
            try:
                return datetime.strptime(date_obj, "%Y-%m-%d").date()
            except:
                return None
        return date_obj
    
    # Update invoice fields
    invoice.invoice_number = invoice_data.invoice_number
    invoice.invoice_date = parse_date(invoice_data.invoice_date)
    invoice.due_date = parse_date(invoice_data.due_date) if invoice_data.due_date else None
    invoice.supplier_name = invoice_data.supplier_name
    invoice.supplier_address = invoice_data.supplier_address
    invoice.supplier_gstin = invoice_data.supplier_gstin
    invoice.supplier_dl_numbers = invoice_data.supplier_dl_numbers
    invoice.supplier_phone = invoice_data.supplier_phone
    invoice.gross_amount = invoice_data.gross_amount
    invoice.discount_amount = invoice_data.discount_amount
    invoice.taxable_amount = invoice_data.taxable_amount
    invoice.total_gst = invoice_data.total_gst
    invoice.round_off = invoice_data.round_off
    invoice.net_amount = invoice_data.net_amount
    invoice.custom_fields = invoice_data.custom_fields or {}
    invoice.is_verified = True
    invoice.verified_by = staff.id
    invoice.verified_at = datetime.now()
    invoice.updated_at = datetime.now()
    
    # Delete existing items
    db.query(models.PurchaseInvoiceItem).filter(
        models.PurchaseInvoiceItem.invoice_id == invoice_id
    ).delete()
    
    # Add updated items
    for item_data in invoice_data.items:
        expiry_date = None
        if item_data.expiry_date:
            expiry_date = parse_date(item_data.expiry_date)
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            manufacturer=item_data.manufacturer,
            hsn_code=item_data.hsn_code,
            product_name=item_data.product_name,
            batch_number=item_data.batch_number,
            quantity=item_data.quantity,
            package=item_data.package,
            expiry_date=expiry_date,
            mrp=item_data.mrp,
            free_quantity=item_data.free_quantity,
            unit_price=item_data.unit_price,
            discount_percent=item_data.discount_percent,
            discount_amount=item_data.discount_amount,
            taxable_amount=item_data.taxable_amount,
            cgst_percent=item_data.cgst_percent,
            cgst_amount=item_data.cgst_amount,
            sgst_percent=item_data.sgst_percent,
            sgst_amount=item_data.sgst_amount,
            igst_percent=item_data.igst_percent,
            igst_amount=item_data.igst_amount,
            total_amount=item_data.total_amount,
            custom_fields=item_data.custom_fields or {}
        )
        db.add(item)
    
    db.commit()
    db.refresh(invoice)
    
    # Sync to stock audit system
    try:
        from modules.stock_audit.sync_service import InvoiceStockSyncService
        sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)
        logger.info(f"✅ Synced invoice {invoice_id} to stock: {sync_result}")
    except Exception as e:
        logger.error(f"❌ Failed to sync invoice to stock: {e}")
        # Don't fail the request if sync fails
    
    return invoice

@router.get("/{invoice_id}", response_model=schemas.PurchaseInvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get specific invoice details"""
    staff, shop_id = current_user
    
    invoice = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.id == invoice_id,
        models.PurchaseInvoice.shop_id == shop_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get verified_by_name
    verified_by_name = None
    if invoice.verified_by:
        verifier = db.query(Staff).filter(Staff.id == invoice.verified_by).first()
        if verifier:
            verified_by_name = verifier.name
    
    # Convert to dict and add verified_by_name
    invoice_dict = {
        "id": invoice.id,
        "shop_id": invoice.shop_id,
        "staff_id": invoice.staff_id,
        "staff_name": invoice.staff_name,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "supplier_name": invoice.supplier_name,
        "supplier_address": invoice.supplier_address,
        "supplier_gstin": invoice.supplier_gstin,
        "supplier_dl_numbers": invoice.supplier_dl_numbers,
        "supplier_phone": invoice.supplier_phone,
        "gross_amount": invoice.gross_amount,
        "discount_amount": invoice.discount_amount,
        "taxable_amount": invoice.taxable_amount,
        "cgst_amount": invoice.cgst_amount,
        "sgst_amount": invoice.sgst_amount,
        "igst_amount": invoice.igst_amount,
        "total_gst": invoice.total_gst,
        "round_off": invoice.round_off,
        "net_amount": invoice.net_amount,
        "pdf_filename": invoice.pdf_filename,
        "custom_fields": invoice.custom_fields or {},
        "is_verified": invoice.is_verified,
        "verified_by_name": verified_by_name,
        "verified_at": invoice.verified_at,
        "created_at": invoice.created_at,
        "items": invoice.items
    }
    
    return invoice_dict

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Delete invoice and reverse stock quantities"""
    staff, shop_id = current_user
    
    invoice = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.id == invoice_id,
        models.PurchaseInvoice.shop_id == shop_id
    ).first()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Reverse stock quantities if invoice was verified and synced
    if invoice.is_verified:
        try:
            from modules.stock_audit.models import StockItem
            
            for invoice_item in invoice.items:
                # Find corresponding stock item
                stock_item = db.query(StockItem).filter(
                    StockItem.shop_id == shop_id,
                    StockItem.product_name == invoice_item.product_name,
                    StockItem.batch_number == invoice_item.batch_number
                ).first()
                
                if stock_item:
                    # Reverse the quantity
                    stock_item.quantity_software -= int(invoice_item.quantity)
                    
                    # If quantity becomes 0 or negative and item was only from this invoice, delete it
                    if stock_item.quantity_software <= 0 and stock_item.source_invoice_id == invoice_id:
                        db.delete(stock_item)
                        logger.info(f"Deleted stock item {stock_item.id} (quantity became {stock_item.quantity_software})")
                    else:
                        stock_item.updated_at = datetime.now()
                        logger.info(f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity}")
            
            db.flush()
        except Exception as e:
            logger.error(f"Failed to reverse stock quantities: {e}")
            # Continue with invoice deletion even if stock reversal fails
    
    # Delete PDF file
    if invoice.pdf_path and os.path.exists(invoice.pdf_path):
        try:
            os.remove(invoice.pdf_path)
        except Exception as e:
            pass  # Continue even if file deletion fails
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully", "stock_reversed": invoice.is_verified}

@router.get("/stats/summary")
def get_invoice_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get invoice statistics summary"""
    staff, shop_id = current_user
    
    query = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id
    )
    
    if start_date:
        query = query.filter(models.PurchaseInvoice.invoice_date >= start_date)
    
    if end_date:
        query = query.filter(models.PurchaseInvoice.invoice_date <= end_date)
    
    invoices = query.all()
    
    total_invoices = len(invoices)
    total_amount = sum(inv.net_amount for inv in invoices)
    total_items = sum(len(inv.items) for inv in invoices)
    
    # Top suppliers
    supplier_totals = {}
    for inv in invoices:
        if inv.supplier_name not in supplier_totals:
            supplier_totals[inv.supplier_name] = 0
        supplier_totals[inv.supplier_name] += inv.net_amount
    
    top_suppliers = sorted(supplier_totals.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "total_items": total_items,
        "average_invoice_amount": total_amount / total_invoices if total_invoices > 0 else 0,
        "top_suppliers": [{"name": name, "total": total} for name, total in top_suppliers]
    }

@router.get("/items/search")
def search_items(
    product_name: Optional[str] = None,
    batch_number: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Search invoice items"""
    staff, shop_id = current_user
    
    query = db.query(models.PurchaseInvoiceItem).filter(
        models.PurchaseInvoiceItem.shop_id == shop_id
    )
    
    if product_name:
        query = query.filter(models.PurchaseInvoiceItem.product_name.ilike(f"%{product_name}%"))
    
    if batch_number:
        query = query.filter(models.PurchaseInvoiceItem.batch_number == batch_number)
    
    items = query.offset(skip).limit(limit).all()
    
    return items
