from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from .dependencies import get_current_user_with_geofence as get_current_user
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Staff
from typing import List, Optional
from datetime import datetime, date
import os
import shutil
import logging
from . import models, schemas
from .ai_extractor import AIInvoiceExtractor
from .excel_extractor import ExcelInvoiceExtractor

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
    """Upload and process purchase invoice PDF or Excel"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📤 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
    
    staff, shop_id = current_user
    
    # Validate file type
    is_pdf = file.filename.lower().endswith('.pdf')
    is_excel = file.filename.lower().endswith(('.xlsx', '.xls'))
    
    if not (is_pdf or is_excel):
        logger.error(f"❌ Invalid file type: {file.filename}")
        raise HTTPException(status_code=400, detail="Only PDF or Excel files are allowed")
    
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
    
    # Extract data from file
    try:
        if is_pdf:
            logger.info(f"🔍 Starting PDF extraction...")
            extractor = AIInvoiceExtractor()
            
            # First, extract text for validation
            with open(file_path, "rb") as f:
                import pdfplumber
                text = ""
                with pdfplumber.open(f) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            
            # Validate format
            validation = extractor.validate_document_format(text, "PDF")
            
            if not validation.get("is_valid", False):
                if os.path.exists(file_path):
                    os.remove(file_path)
                error_details = {
                    "error": "Invalid document format",
                    "validation": validation
                }
                raise HTTPException(
                    status_code=400,
                    detail=error_details
                )
            
            # Proceed with extraction
            parsed_data = extractor.extract_from_pdf(file_path)
            logger.info(f"✅ PDF extraction completed - Found {len(parsed_data.get('items', []))} items")
        else:  # Excel
            logger.info(f"📊 Starting Excel extraction...")
            
            # Read Excel and convert to text for validation
            import pandas as pd
            df = pd.read_excel(file_path, sheet_name=0)
            excel_text = df.to_string()
            
            # Validate format using AI
            extractor = AIInvoiceExtractor()
            validation = extractor.validate_document_format(excel_text, "Excel")
            
            if not validation.get("is_valid", False):
                if os.path.exists(file_path):
                    os.remove(file_path)
                error_details = {
                    "error": "Invalid document format",
                    "validation": validation
                }
                raise HTTPException(
                    status_code=400,
                    detail=error_details
                )
            
            # Proceed with extraction
            parsed_data = ExcelInvoiceExtractor.extract_from_excel(file_path)
            logger.info(f"✅ Excel extraction completed - Found {len(parsed_data.get('items', []))} items")
    except HTTPException:
        # Re-raise HTTPException as-is (validation errors, etc.)
        raise
    except Exception as e:
        logger.error(f"❌ Extraction failed: {str(e)}")
        logger.exception(e)  # Log full traceback
        if os.path.exists(file_path):
            os.remove(file_path)
        error_msg = str(e) if str(e) else "Unknown error during file processing"
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {error_msg}")
    
    # Check for duplicate invoice
    invoice_number = parsed_data.get("invoice_number", "UNKNOWN")
    supplier_name = parsed_data.get("supplier_name", "Unknown Supplier")
    net_amount = parsed_data.get("net_amount", 0.0)
    invoice_date_str = parsed_data.get("invoice_date")
    
    # Parse invoice date for comparison
    invoice_date = None
    if invoice_date_str:
        try:
            invoice_date = datetime.strptime(invoice_date_str, "%d/%m/%Y").date()
        except:
            pass
    
    # Check 1: Exact invoice number match
    existing_by_number = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id,
        models.PurchaseInvoice.invoice_number == invoice_number
    ).first()
    
    if existing_by_number:
        os.remove(file_path)
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate invoice detected! Invoice number '{invoice_number}' already exists (Invoice ID: {existing_by_number.id})."
        )
    
    # Check 2: Similar invoice (same supplier + date + amount)
    if invoice_date and supplier_name and net_amount > 0:
        existing_similar = db.query(models.PurchaseInvoice).filter(
            models.PurchaseInvoice.shop_id == shop_id,
            models.PurchaseInvoice.supplier_name == supplier_name,
            func.date(models.PurchaseInvoice.invoice_date) == invoice_date,
            models.PurchaseInvoice.net_amount == net_amount
        ).first()
        
        if existing_similar:
            os.remove(file_path)
            raise HTTPException(
                status_code=409,
                detail=f"Possible duplicate invoice detected! A similar invoice from '{supplier_name}' with same date ({invoice_date_str}) and amount (₹{net_amount:.2f}) already exists (Invoice: {existing_similar.invoice_number})."
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
        
        # Parse manufacturing date
        manufacturing_date = None
        if item_data.get("manufacturing_date"):
            try:
                mfg_str = item_data['manufacturing_date']
                if isinstance(mfg_str, datetime):
                    manufacturing_date = mfg_str.date()
                elif '/' in mfg_str:
                    parts = mfg_str.split('/')
                    if len(parts) == 2:
                        manufacturing_date = datetime.strptime(f"01/{mfg_str}", "%d/%m/%Y").date()
                    elif len(parts) == 3:
                        manufacturing_date = datetime.strptime(mfg_str, "%d/%m/%Y").date()
            except:
                pass
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            composition=item_data.get("composition"),
            manufacturer=item_data.get("manufacturer"),
            hsn_code=item_data.get("hsn_code"),
            product_name=item_data.get("product_name") or "Unknown Product",
            batch_number=item_data.get("batch_number"),
            quantity=item_data.get("quantity", 1),
            free_quantity=item_data.get("free_quantity", 0.0),
            package=item_data.get("package"),
            unit=item_data.get("unit"),
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            mrp=item_data.get("mrp"),
            unit_price=item_data.get("unit_price", 0.0),
            selling_price=item_data.get("selling_price", 0.0),
            profit_margin=item_data.get("profit_margin", 0.0),
            discount_on_purchase=item_data.get("discount_on_purchase", 0.0),
            discount_on_sales=item_data.get("discount_on_sales", 0.0),
            discount_percent=item_data.get("discount_percent", 0.0),
            discount_amount=item_data.get("discount_amount", 0.0),
            before_discount=item_data.get("before_discount", 0.0),
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

@router.get("/")
def get_invoices(
    skip: int = 0,
    limit: int = 20,
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
        staff_verified_by_name = None
        if inv.staff_verified_by:
            verifier = db.query(Staff).filter(Staff.id == inv.staff_verified_by).first()
            if verifier:
                staff_verified_by_name = verifier.name
        
        from modules.auth.models import Admin
        admin_verified_by_name = None
        if inv.admin_verified_by:
            admin_verifier = db.query(Admin).filter(Admin.id == inv.admin_verified_by).first()
            if admin_verifier:
                admin_verified_by_name = admin_verifier.full_name
        
        admin_rejected_by_name = None
        if inv.admin_rejected_by:
            admin_rejector = db.query(Admin).filter(Admin.id == inv.admin_rejected_by).first()
            if admin_rejector:
                admin_rejected_by_name = admin_rejector.full_name
        
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
            "admin_rejected_by_name": admin_rejected_by_name,
            "admin_rejected_at": inv.admin_rejected_at,
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
    invoice.is_staff_verified = True
    invoice.staff_verified_by = staff.id
    invoice.staff_verified_at = datetime.now()
    invoice.admin_rejected_by = None  # Clear rejection when re-verified
    invoice.admin_rejected_at = None
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
        
        manufacturing_date = None
        if item_data.manufacturing_date:
            manufacturing_date = parse_date(item_data.manufacturing_date)
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            composition=item_data.composition,
            manufacturer=item_data.manufacturer,
            hsn_code=item_data.hsn_code,
            product_name=item_data.product_name or "Unknown Product",
            batch_number=item_data.batch_number,
            quantity=item_data.quantity,
            free_quantity=item_data.free_quantity,
            package=item_data.package,
            unit=item_data.unit,
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            mrp=item_data.mrp,
            unit_price=item_data.unit_price,
            selling_price=item_data.selling_price,
            profit_margin=item_data.profit_margin,
            discount_on_purchase=item_data.discount_on_purchase,
            discount_on_sales=item_data.discount_on_sales,
            discount_percent=item_data.discount_percent,
            discount_amount=item_data.discount_amount,
            before_discount=item_data.before_discount,
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
    
    # DO NOT sync to stock yet - wait for admin verification
    
    return invoice

@router.get("/{invoice_id}", response_model=schemas.PurchaseInvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get specific invoice details - accessible by both staff and admin"""
    from modules.auth.models import Admin, Shop
    
    user_type = user_dict["token_data"].user_type
    
    # Query invoice based on user type
    if user_type == "staff":
        staff = user_dict["user"]
        shop_code = user_dict["token_data"].shop_code
        
        if not shop_code:
            raise HTTPException(status_code=400, detail="Shop code not found in token")
        
        shop = db.query(Shop).filter(
            Shop.shop_code == shop_code,
            Shop.organization_id == staff.shop.organization_id
        ).first()
        if not shop:
            raise HTTPException(status_code=404, detail=f"Shop not found with code: {shop_code}")
        
        invoice = db.query(models.PurchaseInvoice).filter(
            models.PurchaseInvoice.id == invoice_id,
            models.PurchaseInvoice.shop_id == shop.id
        ).first()
    
    elif user_type == "admin":
        admin = user_dict["user"]
        invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
            models.PurchaseInvoice.id == invoice_id,
            Shop.organization_id == admin.organization_id
        ).first()
    
    else:
        raise HTTPException(status_code=403, detail="Staff or Admin access required")
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get verified_by_name (staff who verified)
    staff_verified_by_name = None
    if invoice.staff_verified_by:
        verifier = db.query(Staff).filter(Staff.id == invoice.staff_verified_by).first()
        if verifier:
            staff_verified_by_name = verifier.name
    
    # Get admin_verified_by_name
    admin_verified_by_name = None
    if invoice.admin_verified_by:
        admin_verifier = db.query(Admin).filter(Admin.id == invoice.admin_verified_by).first()
        if admin_verifier:
            admin_verified_by_name = admin_verifier.full_name
    
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
        "is_staff_verified": invoice.is_staff_verified,
        "staff_verified_by_name": staff_verified_by_name,
        "staff_verified_at": invoice.staff_verified_at,
        "is_admin_verified": invoice.is_admin_verified,
        "admin_verified_by_name": admin_verified_by_name,
        "admin_verified_at": invoice.admin_verified_at,
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
    
    # Check if stock items are used in bills
    stock_reversed = False
    items_in_use = []
    
    if invoice.is_admin_verified:
        try:
            from modules.stock_audit.models import StockItem
            from modules.billing.models import BillItem
            
            for invoice_item in invoice.items:
                # Find corresponding stock item
                stock_item = db.query(StockItem).filter(
                    StockItem.shop_id == shop_id,
                    StockItem.product_name == invoice_item.product_name,
                    StockItem.batch_number == invoice_item.batch_number
                ).first()
                
                if stock_item:
                    # Check if stock item is used in any bills
                    bill_item_count = db.query(BillItem).filter(
                        BillItem.stock_item_id == stock_item.id
                    ).count()
                    
                    if bill_item_count > 0:
                        # Stock item is used in bills, only reverse quantity and nullify source
                        stock_item.quantity_software -= int(invoice_item.quantity)
                        stock_item.source_invoice_id = None  # Nullify reference
                        stock_item.updated_at = datetime.now()
                        items_in_use.append(invoice_item.product_name)
                        logger.info(f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity} (item in use, not deleted)")
                    else:
                        # Stock item not used in bills, safe to delete if quantity <= 0
                        stock_item.quantity_software -= int(invoice_item.quantity)
                        
                        if stock_item.quantity_software <= 0 and stock_item.source_invoice_id == invoice_id:
                            db.delete(stock_item)
                            logger.info(f"Deleted stock item {stock_item.id} (quantity became {stock_item.quantity_software})")
                        else:
                            stock_item.source_invoice_id = None  # Nullify reference
                            stock_item.updated_at = datetime.now()
                            logger.info(f"Reversed stock for {stock_item.product_name}: -{invoice_item.quantity}")
            
            db.flush()
            stock_reversed = True
        except Exception as e:
            logger.error(f"Failed to reverse stock quantities: {e}")
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete invoice: {str(e)}"
            )
    
    # Store pdf_path before deleting invoice
    pdf_path = invoice.pdf_path
    
    # Delete invoice (cascade will delete items)
    db.delete(invoice)
    db.commit()
    
    # Delete PDF file after successful commit
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            logger.warning(f"Failed to delete PDF file: {e}")
    
    response = {"message": "Invoice deleted successfully", "stock_reversed": stock_reversed}
    if items_in_use:
        response["warning"] = f"{len(items_in_use)} items are used in bills and were not deleted from stock"
    
    return response

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
    limit: int = 50,
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

@router.get("/fields-guide")
def get_fields_guide():
    """Get invoice fields documentation"""
    import os
    guide_path = os.path.join(os.path.dirname(__file__), "INVOICE_FIELDS_GUIDE.md")
    
    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "format": "markdown"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Fields guide not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading guide: {str(e)}")
