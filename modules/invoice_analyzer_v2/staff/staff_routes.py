from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from modules.invoice_analyzer_v2.staff.staff_dependencies import get_current_user_with_geofence as get_current_user
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Staff, Shop
from typing import List, Optional
from datetime import datetime, date
import os
import shutil
import logging
import io
import pandas as pd
from modules.invoice_analyzer_v2 import models, schemas
from modules.invoice_analyzer_v2.ai_extractor import AIInvoiceExtractor
from modules.invoice_analyzer_v2.excel_extractor import ExcelInvoiceExtractor

logger = logging.getLogger(__name__)

router = APIRouter()


def generate_invoice_number() -> str:
    """Generate a unique invoice reference: PI-YYYYMMDD-XXXXXXXX"""
    import uuid
    date_str = datetime.now().strftime("%Y%m%d")
    return f"PI-{date_str}-{uuid.uuid4().hex[:8].upper()}"


def parse_mrp(mrp_str):
    """Parse MRP from string — handles '10.5', '10.5/STRIP', '10.00/strip of 10' etc."""
    if not mrp_str:
        return None
    try:
        return float(str(mrp_str).strip().split('/')[0].strip())
    except Exception:
        return None


# Upload directory
UPLOAD_DIR = "uploads/invoices"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=schemas.PurchaseInvoiceResponse)
async def upload_invoice_pdf(
    file: UploadFile = File(...),
    force_extract: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Upload and process purchase invoice PDF or Excel"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"📤 Upload request received - File: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}, Force: {force_extract}")
    
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
            
            if not validation.get("is_valid", False) and not force_extract:
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
            
            # Log if proceeding with format issues
            if force_extract and not validation.get("is_valid", False):
                logger.warning(f"⚠️ Proceeding with extraction despite format issues (force_extract=True)")
            
            # Proceed with extraction
            parsed_data = extractor.extract_from_pdf(file_path)
            logger.info(f"✅ PDF extraction completed - Found {len(parsed_data.get('items', []))} items")

            # Patch header fields from validation detected_fields.
            # The validation model (gemini-2.5-flash) reliably identifies header fields
            # and should override fallback regex results when available.
            detected = validation.get("detected_fields") or {}
            header_patch_map = {
                "invoice_number": "invoice_number",
                "invoice_date": "invoice_date",
                "supplier_name": "supplier_name",
                "supplier_address": "supplier_address",
                "supplier_gstin": "supplier_gstin",
                "supplier_dl_numbers": "supplier_dl_numbers",
                "supplier_phone": "supplier_phone",
            }
            for det_key, data_key in header_patch_map.items():
                val = detected.get(det_key)
                if val and val not in ("null", "None"):
                    old = parsed_data.get(data_key)
                    if old != val:
                        logger.info(f"🔧 Patching {data_key}: '{old}' → '{val}'")
                    parsed_data[data_key] = val

        else:  # Excel
            logger.info(f"📊 Starting Excel extraction...")
            
            # Read Excel and convert to text for validation
            import pandas as pd
            df = pd.read_excel(file_path, sheet_name=0)
            excel_text = df.to_string()
            
            # Validate format using AI
            extractor = AIInvoiceExtractor()
            validation = extractor.validate_document_format(excel_text, "Excel")
            
            if not validation.get("is_valid", False) and not force_extract:
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
            
            # Log if proceeding with format issues
            if force_extract and not validation.get("is_valid", False):
                logger.warning(f"⚠️ Proceeding with extraction despite format issues (force_extract=True)")
            
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
    
    # Auto-generate invoice number if missing or unextractable
    raw_number = (parsed_data.get("invoice_number") or "").strip()
    if not raw_number or raw_number.upper() == "UNKNOWN":
        invoice_number = generate_invoice_number()
        parsed_data["invoice_number"] = invoice_number
        logger.info(f"📋 Auto-generated invoice number: {invoice_number}")
    else:
        invoice_number = raw_number

    # Check for duplicate invoice
    supplier_name = parsed_data.get("supplier_name", "Unknown Supplier")
    net_amount = parsed_data.get("net_amount", 0.0)
    invoice_date_str = parsed_data.get("invoice_date")
    
    # Parse invoice date for comparison
    invoice_date = None
    if invoice_date_str:
        try:
            invoice_date = datetime.strptime(invoice_date_str, "%d/%m/%Y").date()
        except Exception as e:
            logger.warning(f"⚠️ Could not parse invoice_date '{invoice_date_str}' for duplicate check: {e}")
    
    # Check 1: Exact invoice number match
    existing_by_number = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id,
        models.PurchaseInvoice.invoice_number == invoice_number
    ).first()

    if existing_by_number:
        os.remove(file_path)
        if existing_by_number.is_admin_verified:
            raise HTTPException(
                status_code=409,
                detail=f"Invoice number '{invoice_number}' already exists and has been admin-approved. Contact your admin to make changes (Invoice ID: {existing_by_number.id})."
            )
        else:
            raise HTTPException(
                status_code=409,
                detail=f"Invoice number '{invoice_number}' already exists (Invoice ID: {existing_by_number.id}). It has not been approved yet — go to Invoice List and edit it directly instead of re-uploading."
            )

    
    # Parse dates
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%d/%m/%Y")
        except Exception as e:
            logger.warning(f"⚠️ Could not parse date '{date_str}': {e}")
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
            except Exception as e:
                logger.warning(f"⚠️ Could not parse expiry_date '{item_data.get('expiry_date')}' for item '{item_data.get('product_name')}': {e}")

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
            except Exception as e:
                logger.warning(f"⚠️ Could not parse manufacturing_date '{item_data.get('manufacturing_date')}' for item '{item_data.get('product_name')}': {e}")
        
        # Truncate string fields to prevent database errors
        def truncate_str(value, max_length=255):
            if value is None:
                return None
            return str(value)[:max_length] if len(str(value)) > max_length else str(value)
        
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            composition=truncate_str(item_data.get("composition")),
            manufacturer=truncate_str(item_data.get("manufacturer")),
            hsn_code=truncate_str(item_data.get("hsn_code")),
            product_name=truncate_str(item_data.get("product_name") or "Unknown Product"),
            batch_number=truncate_str(item_data.get("batch_number")),
            quantity=item_data.get("quantity", 1),
            free_quantity=item_data.get("free_quantity", 0.0),
            package=truncate_str(item_data.get("package")),
            unit=truncate_str(item_data.get("unit")),
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            mrp=truncate_str(item_data.get("mrp")),
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
            except Exception as e:
                logger.warning(f"⚠️ Could not parse date '{date_obj}': {e}")
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
    
    # Truncate string fields to prevent database errors
    def truncate_str(value, max_length=255):
        if value is None:
            return None
        return str(value)[:max_length] if len(str(value)) > max_length else str(value)
    
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
            composition=truncate_str(item_data.composition),
            manufacturer=truncate_str(item_data.manufacturer),
            hsn_code=truncate_str(item_data.hsn_code),
            product_name=truncate_str(item_data.product_name or "Unknown Product"),
            batch_number=truncate_str(item_data.batch_number),
            quantity=item_data.quantity,
            free_quantity=item_data.free_quantity,
            package=truncate_str(item_data.package),
            unit=truncate_str(item_data.unit),
            manufacturing_date=manufacturing_date,
            expiry_date=expiry_date,
            mrp=truncate_str(item_data.mrp),
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

@router.delete("/{invoice_id}")
def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Delete invoice and reverse stock quantities"""
    from modules.invoice_analyzer_v2.stock_reversal_service import reverse_stock_for_invoice

    staff, shop_id = current_user

    invoice = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.id == invoice_id,
        models.PurchaseInvoice.shop_id == shop_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    stock_reversed, items_in_use = reverse_stock_for_invoice(db, invoice, invoice_id, shop_id)

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

@router.post("/create", response_model=schemas.PurchaseInvoiceResponse)
def create_invoice_manually(
    invoice_data: schemas.PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Create invoice manually without file upload"""
    staff, shop_id = current_user

    # Auto-generate invoice number if not provided
    inv_number = (invoice_data.invoice_number or "").strip()
    if not inv_number:
        inv_number = generate_invoice_number()

    # Enforce uniqueness within the shop
    existing = db.query(models.PurchaseInvoice).filter(
        models.PurchaseInvoice.shop_id == shop_id,
        models.PurchaseInvoice.invoice_number == inv_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Invoice number '{inv_number}' already exists. Please use a different number."
        )

    invoice = models.PurchaseInvoice(
        shop_id=shop_id,
        staff_id=staff.id,
        staff_name=staff.name,
        invoice_number=inv_number,
        invoice_date=invoice_data.invoice_date,
        due_date=invoice_data.due_date,
        supplier_name=invoice_data.supplier_name,
        supplier_address=invoice_data.supplier_address,
        supplier_gstin=invoice_data.supplier_gstin,
        supplier_dl_numbers=invoice_data.supplier_dl_numbers,
        supplier_phone=invoice_data.supplier_phone,
        gross_amount=invoice_data.gross_amount,
        discount_amount=invoice_data.discount_amount,
        taxable_amount=invoice_data.taxable_amount,
        total_gst=invoice_data.total_gst,
        round_off=invoice_data.round_off,
        net_amount=invoice_data.net_amount,
        custom_fields=invoice_data.custom_fields or {},
        is_staff_verified=True,
        staff_verified_by=staff.id,
        staff_verified_at=datetime.now()
    )
    
    db.add(invoice)
    db.flush()
    
    # Truncate string fields to prevent database errors
    def truncate_str(value, max_length=255):
        if value is None:
            return None
        return str(value)[:max_length] if len(str(value)) > max_length else str(value)
    
    for item_data in invoice_data.items:
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=shop_id,
            composition=truncate_str(item_data.composition),
            manufacturer=truncate_str(item_data.manufacturer),
            hsn_code=truncate_str(item_data.hsn_code),
            product_name=truncate_str(item_data.product_name or "Unknown Product"),
            batch_number=truncate_str(item_data.batch_number),
            quantity=item_data.quantity,
            free_quantity=item_data.free_quantity,
            package=truncate_str(item_data.package),
            unit=truncate_str(item_data.unit),
            manufacturing_date=item_data.manufacturing_date if isinstance(item_data.manufacturing_date, date) else None,
            expiry_date=item_data.expiry_date if isinstance(item_data.expiry_date, date) else None,
            mrp=truncate_str(item_data.mrp),
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
    
    return invoice

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


@router.get("/download-pdf-template")
def download_pdf_template(current_user: tuple = Depends(get_current_user)):
    """Download PDF template/sample for invoice upload (requires authentication)"""
    from fastapi.responses import FileResponse
    staff, shop_id = current_user
    
    # Path to sample PDF template
    template_path = os.path.join(os.path.dirname(__file__), "sample_invoice_template.pdf")
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="PDF template not found")
    
    return FileResponse(
        path=template_path,
        media_type="application/pdf",
        filename="purchase_invoice_sample.pdf"
    )

@router.get("/download-template")
def download_excel_template(current_user: tuple = Depends(get_current_user)):
    """Download Excel template for invoice upload (requires authentication)"""
    staff, shop_id = current_user  # Ensures only authenticated staff can download
    
    # Create comprehensive sample data with 2 rows
    template_data = {
        "Invoice_Number": ["INV-001", ""],
        "Invoice_Date": ["15/01/2024", ""],
        "Supplier_Name": ["ABC Pharmaceuticals", ""],
        "Supplier_Address": ["123 Medical Street, Mumbai", ""],
        "Supplier_GSTIN": ["29ABCDE1234F1Z5", ""],
        "Supplier_DL_Numbers": ["DL-123, DL-456", ""],
        "Supplier_Phone": ["9876543210", ""],
        "Composition": ["Paracetamol 500mg", "Amoxicillin 250mg"],
        "Product_Name": ["Dolo 650", "Amoxil"],
        "Manufacturer": ["CIPLA", "SUN"],
        "HSN_Code": ["30049099", "30042064"],
        "Batch_Number": ["BATCH001", "BATCH002"],
        "Package": ["10 X 10", "10 X 6"],
        "Unit": ["Box", "Strip"],
        "Quantity": [10, 5],
        "Manufacturing_Date": ["01/2024", "02/2024"],
        "Expiry_Date": ["12/2025", "06/2026"],
        "MRP": ["5.00/STRIP", "120.00/STRIP"],
        "Unit_Price": [4.0, 100.0],
        "Profit_Margin": [20, 25],
        "Discount_On_Purchase": [10, 15],
        "Discount_On_Sales": [5, 8],
        "Taxable_Amount": [2000, 1500],
        "CGST_Percent": [2.5, 6.0],
        "CGST_Amount": [50, 90],
        "SGST_Percent": [2.5, 6.0],
        "SGST_Amount": [50, 90],
        "Total_Amount": [2100, 1680],
    }
    
    # Create DataFrame
    df = pd.DataFrame(template_data)
    
    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Invoice', index=False)
        
        # Add instructions sheet
        instructions = pd.DataFrame({
            "Column Name": [
                "Invoice_Number", "Invoice_Date", "Supplier_Name", "Supplier_Address", "Supplier_GSTIN", "Supplier_DL_Numbers", "Supplier_Phone",
                "Composition", "Product_Name", "Manufacturer", "HSN_Code", "Batch_Number",
                "Package", "Unit", "Quantity", "Manufacturing_Date", "Expiry_Date",
                "MRP", "Unit_Price", "Profit_Margin", "Discount_On_Purchase",
                "Taxable_Amount", "CGST_Percent", "CGST_Amount", "SGST_Percent", "SGST_Amount"
            ],
            "Required": [
                "Yes", "Yes", "At least one", "At least one", "At least one", "At least one", "At least one",
                "No", "Yes", "No", "No", "Yes",
                "No", "No", "Yes", "No", "No",
                "No", "No", "No", "No",
                "No", "No", "No", "No", "No"
            ],
            "Description": [
                "Unique invoice number (fill only in first row)",
                "Date in DD/MM/YYYY format (fill only in first row)",
                "Supplier/Vendor name (fill only in first row, at least one supplier field required)",
                "Complete supplier address (fill only in first row, at least one supplier field required)",
                "15-digit GSTIN (fill only in first row, at least one supplier field required)",
                "Drug license numbers comma-separated (fill only in first row, at least one supplier field required)",
                "10-digit contact number (fill only in first row, at least one supplier field required)",
                "Generic/Salt name (e.g., Paracetamol 500mg)",
                "Brand/Product name (required for each item)",
                "Manufacturer code (e.g., CIPLA, SUN)",
                "8-digit HSN code",
                "Batch number (required for each item)",
                "Package info (e.g., 10 X 10)",
                "Unit type (Box, Strip, Bottle, etc.)",
                "Quantity purchased (required)",
                "Manufacturing date (MM/YYYY or DD/MM/YYYY)",
                "Expiry date (MM/YYYY or DD/MM/YYYY)",
                "MRP with unit (e.g., 5.00/STRIP)",
                "Unit price per item",
                "Profit margin percentage",
                "Purchase discount percentage",
                "Taxable amount (auto-calculated if empty)",
                "CGST percentage (auto-calculated if empty)",
                "CGST amount (auto-calculated if empty)",
                "SGST percentage (auto-calculated if empty)",
                "SGST amount (auto-calculated if empty)"
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Add field reference sheet
        field_reference = pd.DataFrame({
            "Category": [
                "Invoice Header", "Invoice Header", "Invoice Header", "Invoice Header",
                "Product Info", "Product Info", "Product Info", "Product Info", "Product Info",
                "Packaging", "Packaging", "Quantity", "Dates", "Dates",
                "Pricing", "Pricing", "Pricing", "Discounts",
                "Tax", "Tax", "Tax", "Tax", "Tax"
            ],
            "Field": [
                "Invoice_Number", "Invoice_Date", "Supplier_Name", "Supplier_GSTIN",
                "Composition", "Product_Name", "Manufacturer", "HSN_Code", "Batch_Number",
                "Package", "Unit", "Quantity", "Manufacturing_Date", "Expiry_Date",
                "MRP", "Unit_Price", "Profit_Margin", "Discount_On_Purchase",
                "Taxable_Amount", "CGST_Percent", "CGST_Amount", "SGST_Percent", "SGST_Amount"
            ],
            "Example": [
                "INV-001", "15/01/2024", "ABC Pharmaceuticals", "29ABCDE1234F1Z5",
                "Paracetamol 500mg", "Dolo 650", "CIPLA", "30049099", "BATCH001",
                "10 X 10", "Box", "10", "01/2024", "12/2025",
                "5.00/STRIP", "4.0", "20", "10",
                "2000", "2.5", "50", "2.5", "50"
            ]
        })
        field_reference.to_excel(writer, sheet_name='Field Reference', index=False)
    
        # Format the sheets
        workbook = writer.book
        
        # Format Invoice sheet
        invoice_sheet = workbook['Invoice']
        for cell in invoice_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="D3D3D3")
        
        # Format Instructions sheet
        instructions_sheet = workbook['Instructions']
        for cell in instructions_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="90EE90")
        
        # Format Field Reference sheet
        reference_sheet = workbook['Field Reference']
        for cell in reference_sheet[1]:
            cell.font = cell.font.copy(bold=True)
            cell.fill = cell.fill.copy(fgColor="87CEEB")
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=purchase_invoice_template.xlsx"}
    )
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.invoice_analyzer_v2 import models


@router.get("/compositions")
def get_compositions(
    search: str = Query(None, min_length=1),
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get unique compositions for autocomplete - accessible by both staff and admin"""
    from modules.auth.models import Shop
    
    user_type = user_dict["token_data"].user_type
    
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
        
        shop_id = shop.id
        query = db.query(distinct(models.PurchaseInvoiceItem.composition)).filter(
            models.PurchaseInvoiceItem.shop_id == shop_id,
            models.PurchaseInvoiceItem.composition.isnot(None),
            models.PurchaseInvoiceItem.composition != ''
        )
    
    elif user_type == "admin":
        admin = user_dict["user"]
        # Admin can see compositions from all shops in their organization
        query = db.query(distinct(models.PurchaseInvoiceItem.composition)).join(
            models.PurchaseInvoice
        ).join(Shop).filter(
            Shop.organization_id == admin.organization_id,
            models.PurchaseInvoiceItem.composition.isnot(None),
            models.PurchaseInvoiceItem.composition != ''
        )
    
    else:
        raise HTTPException(status_code=403, detail="Staff or Admin access required")
    
    if search:
        query = query.filter(
            models.PurchaseInvoiceItem.composition.ilike(f'{search}%')
        )
    
    compositions = query.order_by(models.PurchaseInvoiceItem.composition).limit(20).all()
    
    return [comp[0] for comp in compositions if comp[0]]

@router.get("/product-names")
def get_product_names(
    search: str = Query(None, min_length=1),
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get unique product names for autocomplete - accessible by both staff and admin"""
    from modules.auth.models import Shop
    
    user_type = user_dict["token_data"].user_type
    
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
        
        shop_id = shop.id
        query = db.query(distinct(models.PurchaseInvoiceItem.product_name)).filter(
            models.PurchaseInvoiceItem.shop_id == shop_id,
            models.PurchaseInvoiceItem.product_name.isnot(None),
            models.PurchaseInvoiceItem.product_name != '',
            models.PurchaseInvoiceItem.product_name != 'Unknown Product'
        )
    
    elif user_type == "admin":
        admin = user_dict["user"]
        query = db.query(distinct(models.PurchaseInvoiceItem.product_name)).join(
            models.PurchaseInvoice
        ).join(Shop).filter(
            Shop.organization_id == admin.organization_id,
            models.PurchaseInvoiceItem.product_name.isnot(None),
            models.PurchaseInvoiceItem.product_name != '',
            models.PurchaseInvoiceItem.product_name != 'Unknown Product'
        )
    
    else:
        raise HTTPException(status_code=403, detail="Staff or Admin access required")
    
    if search:
        query = query.filter(
            models.PurchaseInvoiceItem.product_name.ilike(f'{search}%')
        )
    
    product_names = query.order_by(models.PurchaseInvoiceItem.product_name).limit(20).all()
    
    return [name[0] for name in product_names if name[0]]
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.invoice_analyzer_v2.models import PurchaseInvoiceItem, PurchaseInvoice
from typing import Optional


@router.get("/pricing/by-composition")
def get_pricing_by_composition(
    composition: Optional[str] = Query(None, description="Composition to lookup"),
    product_name: Optional[str] = Query(None, description="Product name to lookup"),
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get latest selling price and profit margin by composition and/or product name"""
    from modules.auth.models import Shop
    from sqlalchemy import or_
    
    if not composition and not product_name:
        return {"selling_price": None, "profit_margin": None, "found": False}
    
    user_type = user_dict["token_data"].user_type
    
    if user_type == "staff":
        staff = user_dict["user"]
        shop_code = user_dict["token_data"].shop_code
        
        shop = db.query(Shop).filter(
            Shop.shop_code == shop_code,
            Shop.organization_id == staff.shop.organization_id
        ).first()
        
        if not shop:
            return {"selling_price": None, "profit_margin": None}
        
        shop_id = shop.id
    elif user_type == "admin":
        admin = user_dict["user"]
        shop_id = None
    else:
        return {"selling_price": None, "profit_margin": None}
    
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoiceItem.selling_price > 0,
        PurchaseInvoiceItem.profit_margin > 0,
        PurchaseInvoice.is_admin_verified == True
    )
    
    filters = []
    if composition:
        filters.append(PurchaseInvoiceItem.composition.ilike(composition))
    if product_name:
        filters.append(PurchaseInvoiceItem.product_name.ilike(product_name))
    
    query = query.filter(or_(*filters))
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    elif user_type == "admin":
        query = query.join(Shop).filter(Shop.organization_id == admin.organization_id)
    
    item = query.order_by(desc(PurchaseInvoice.invoice_date)).first()
    
    if item:
        return {
            "selling_price": round(item.selling_price, 2),
            "profit_margin": round(item.profit_margin, 2),
            "found": True
        }
    
    return {"selling_price": None, "profit_margin": None, "found": False}
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, case, and_, or_
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.invoice_analyzer_v2.models import PurchaseInvoice, PurchaseInvoiceItem
from datetime import date, datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel
import statistics


class MarginSimulationRequest(BaseModel):
    product_names: Optional[List[str]] = None
    compositions: Optional[List[str]] = None
    new_margin: float
    apply_discount: Optional[float] = None

@router.get("/analytics/margin-playground")
async def get_margin_playground(
    shop_id: Optional[int] = None,
    product_name: Optional[str] = None,
    composition: Optional[str] = None,
    manufacturer: Optional[str] = None,
    margin_min: Optional[float] = None,
    margin_max: Optional[float] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Purchase Margin Analysis for admin.

    These products are purchased from distributors and NOT yet sold to customers.
    Metrics are purchase-side:
      - purchase_value    : unit_price × quantity  (what was paid to distributor)
      - purchase_margin   : (MRP - unit_price) / MRP × 100  (potential margin if sold at MRP)
      - potential_profit  : (MRP - unit_price) × quantity   (profit if every unit sold at MRP)
    """

    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).join(
        Shop, PurchaseInvoice.shop_id == Shop.id
    ).filter(
        PurchaseInvoice.is_admin_verified == True,
        Shop.organization_id == current_admin.organization_id
    )

    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    if product_name:
        query = query.filter(PurchaseInvoiceItem.product_name.ilike(f"%{product_name}%"))
    if composition:
        query = query.filter(PurchaseInvoiceItem.composition.ilike(f"%{composition}%"))
    if manufacturer:
        query = query.filter(PurchaseInvoiceItem.manufacturer.ilike(f"%{manufacturer}%"))
    if date_from:
        query = query.filter(PurchaseInvoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(PurchaseInvoice.invoice_date <= date_to)

    items = query.all()

    empty_response = {
        "summary": {
            "total_items": 0, "total_purchase_value": 0, "total_potential_profit": 0,
            "avg_purchase_margin": 0, "min_purchase_margin": 0, "max_purchase_margin": 0,
            "items_with_mrp": 0, "items_without_mrp": 0, "products_with_multiple_suppliers": 0
        },
        "top_products": [], "supplier_breakdown": [],
        "margin_distribution": [], "distributor_comparison": []
    }
    if not items:
        return empty_response

    # ── Per-item metrics (purchase-side only) ─────────────────────────────────
    item_metrics = []
    for item in items:
        mrp_value = parse_mrp(item.mrp)
        purchase_price = item.unit_price
        qty = item.quantity
        purchase_value = purchase_price * qty

        if mrp_value and mrp_value > 0 and purchase_price > 0 and mrp_value >= purchase_price:
            purchase_margin = ((mrp_value - purchase_price) / mrp_value) * 100
            potential_profit = (mrp_value - purchase_price) * qty
            has_mrp = True
        else:
            purchase_margin = 0
            potential_profit = 0
            has_mrp = False

        supplier_name = item.invoice.supplier_name if item.invoice else "Unknown"

        item_metrics.append({
            "id": item.id,
            "product_name": item.product_name or "Unknown",
            "composition": item.composition,
            "manufacturer": item.manufacturer,
            "batch_number": item.batch_number,
            "supplier_name": supplier_name,
            "purchase_price": round(purchase_price, 2),
            "mrp": mrp_value,
            "mrp_str": item.mrp,
            "quantity": qty,
            "purchase_value": round(purchase_value, 2),
            "purchase_margin": round(purchase_margin, 2),
            "potential_profit": round(potential_profit, 2),
            "has_mrp": has_mrp,
            "invoice_date": item.invoice.invoice_date.isoformat() if item.invoice else None,
        })

    # Apply margin range filter (after MRP-based computation)
    if margin_min is not None:
        item_metrics = [m for m in item_metrics if m["purchase_margin"] >= margin_min]
    if margin_max is not None:
        item_metrics = [m for m in item_metrics if m["purchase_margin"] <= margin_max]

    if not item_metrics:
        return empty_response

    # ── Summary ───────────────────────────────────────────────────────────────
    all_margins = [m["purchase_margin"] for m in item_metrics if m["has_mrp"]]
    total_purchase_value = sum(m["purchase_value"] for m in item_metrics)
    total_potential_profit = sum(m["potential_profit"] for m in item_metrics)
    items_with_mrp = sum(1 for m in item_metrics if m["has_mrp"])

    # ── Top Products by purchase value ────────────────────────────────────────
    prod_data = {}
    for m in item_metrics:
        key = m["product_name"]
        if key not in prod_data:
            prod_data[key] = {
                "product_name": m["product_name"],
                "composition": m["composition"],
                "purchase_value": 0, "potential_profit": 0,
                "quantity": 0, "margins": [], "suppliers": set()
            }
        prod_data[key]["purchase_value"] += m["purchase_value"]
        prod_data[key]["potential_profit"] += m["potential_profit"]
        prod_data[key]["quantity"] += m["quantity"]
        if m["has_mrp"]:
            prod_data[key]["margins"].append(m["purchase_margin"])
        prod_data[key]["suppliers"].add(m["supplier_name"])

    top_products = sorted([{
        "product_name": v["product_name"],
        "composition": v["composition"],
        "purchase_value": round(v["purchase_value"], 2),
        "potential_profit": round(v["potential_profit"], 2),
        "quantity": round(v["quantity"], 2),
        "avg_purchase_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "supplier_count": len(v["suppliers"]),
        "suppliers": list(v["suppliers"])
    } for v in prod_data.values()], key=lambda x: x["purchase_value"], reverse=True)[:20]

    # ── Supplier breakdown — who gives the best margins ───────────────────────
    supplier_data = {}
    for m in item_metrics:
        s = m["supplier_name"]
        if s not in supplier_data:
            supplier_data[s] = {
                "supplier_name": s,
                "total_purchase_value": 0, "total_potential_profit": 0,
                "item_count": 0, "margins": [], "products": set()
            }
        supplier_data[s]["total_purchase_value"] += m["purchase_value"]
        supplier_data[s]["total_potential_profit"] += m["potential_profit"]
        supplier_data[s]["item_count"] += 1
        if m["has_mrp"]:
            supplier_data[s]["margins"].append(m["purchase_margin"])
        supplier_data[s]["products"].add(m["product_name"])

    supplier_breakdown = sorted([{
        "supplier_name": v["supplier_name"],
        "total_purchase_value": round(v["total_purchase_value"], 2),
        "total_potential_profit": round(v["total_potential_profit"], 2),
        "item_count": v["item_count"],
        "product_count": len(v["products"]),
        "avg_margin_offered": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0
    } for v in supplier_data.values()], key=lambda x: x["avg_margin_offered"], reverse=True)

    # ── Margin distribution ───────────────────────────────────────────────────
    distribution = [
        {"range": "0-10%",  "count": sum(1 for m in all_margins if 0  <= m < 10)},
        {"range": "10-20%", "count": sum(1 for m in all_margins if 10 <= m < 20)},
        {"range": "20-30%", "count": sum(1 for m in all_margins if 20 <= m < 30)},
        {"range": "30-40%", "count": sum(1 for m in all_margins if 30 <= m < 40)},
        {"range": "40-50%", "count": sum(1 for m in all_margins if 40 <= m < 50)},
        {"range": "50%+",   "count": sum(1 for m in all_margins if m  >= 50)}
    ]

    # ── Distributor comparison — same medicine, different suppliers ───────────
    # Group by product_name, collect all distributors who supplied it
    comp_group = {}
    for m in item_metrics:
        key = m["product_name"]
        if key not in comp_group:
            comp_group[key] = {
                "product_name": m["product_name"],
                "composition": m["composition"],
                "mrp": m["mrp"],
                "entries": {}
            }
        s = m["supplier_name"]
        if s not in comp_group[key]["entries"]:
            comp_group[key]["entries"][s] = {
                "supplier_name": s,
                "total_qty": 0, "total_purchase_value": 0,
                "prices": [], "mrp": m["mrp"], "has_mrp": m["has_mrp"]
            }
        comp_group[key]["entries"][s]["total_qty"] += m["quantity"]
        comp_group[key]["entries"][s]["total_purchase_value"] += m["purchase_value"]
        comp_group[key]["entries"][s]["prices"].append(m["purchase_price"])

    distributor_comparison = []
    for key, data in comp_group.items():
        entries = list(data["entries"].values())
        if len(entries) < 2:
            continue  # Only show products with 2+ distributors

        supplier_list = []
        for e in entries:
            avg_price = e["total_purchase_value"] / e["total_qty"] if e["total_qty"] > 0 else 0
            mrp_v = e["mrp"]
            if mrp_v and mrp_v > 0 and avg_price > 0 and mrp_v >= avg_price:
                margin = ((mrp_v - avg_price) / mrp_v) * 100
            else:
                margin = None
            supplier_list.append({
                "supplier_name": e["supplier_name"],
                "avg_purchase_price": round(avg_price, 2),
                "purchase_margin": round(margin, 2) if margin is not None else None,
                "total_qty": round(e["total_qty"], 2),
                "total_purchase_value": round(e["total_purchase_value"], 2),
            })

        # Sort: best margin (highest) first
        supplier_list.sort(key=lambda x: x["purchase_margin"] if x["purchase_margin"] is not None else -999, reverse=True)

        # Badge best and worst
        if supplier_list[0]["purchase_margin"] is not None:
            supplier_list[0]["badge"] = "best"
        if len(supplier_list) > 1 and supplier_list[-1]["purchase_margin"] is not None:
            supplier_list[-1]["badge"] = "worst"

        valid_margins = [s["purchase_margin"] for s in supplier_list if s["purchase_margin"] is not None]
        margin_gap = round(max(valid_margins) - min(valid_margins), 2) if len(valid_margins) >= 2 else 0

        distributor_comparison.append({
            "product_name": data["product_name"],
            "composition": data["composition"],
            "mrp": data["mrp"],
            "supplier_count": len(supplier_list),
            "best_margin": supplier_list[0]["purchase_margin"],
            "margin_gap": margin_gap,
            "suppliers": supplier_list
        })

    # Sort by margin gap (biggest savings opportunity first)
    distributor_comparison.sort(key=lambda x: x["margin_gap"] if x["margin_gap"] else 0, reverse=True)

    return {
        "summary": {
            "total_items": len(item_metrics),
            "total_purchase_value": round(total_purchase_value, 2),
            "total_potential_profit": round(total_potential_profit, 2),
            "avg_purchase_margin": round(sum(all_margins) / len(all_margins), 2) if all_margins else 0,
            "min_purchase_margin": round(min(all_margins), 2) if all_margins else 0,
            "max_purchase_margin": round(max(all_margins), 2) if all_margins else 0,
            "items_with_mrp": items_with_mrp,
            "items_without_mrp": len(item_metrics) - items_with_mrp,
            "products_with_multiple_suppliers": len(distributor_comparison)
        },
        "top_products": top_products,
        "supplier_breakdown": supplier_breakdown,
        "margin_distribution": distribution,
        "distributor_comparison": distributor_comparison[:30]
    }

@router.post("/analytics/simulate-margin-change")
async def simulate_margin_change(
    request: MarginSimulationRequest,
    shop_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Simulate margin changes for products/compositions"""
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).join(
        Shop, PurchaseInvoice.shop_id == Shop.id
    ).filter(
        PurchaseInvoice.is_admin_verified == True,
        Shop.organization_id == current_admin.organization_id
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    if request.product_names:
        query = query.filter(PurchaseInvoiceItem.product_name.in_(request.product_names))
    
    if request.compositions:
        query = query.filter(PurchaseInvoiceItem.composition.in_(request.compositions))
    
    items = query.all()
    
    results = []
    for item in items:
        # Calculate new selling price with new margin
        new_selling_price = item.unit_price * (1 + request.new_margin / 100)
        
        # Apply discount if provided
        if request.apply_discount:
            new_selling_price = new_selling_price * (1 - request.apply_discount / 100)
        
        # Check MRP cap
        mrp_value = parse_mrp(item.mrp)
        capped = False
        
        if mrp_value and new_selling_price > mrp_value:
            new_selling_price = mrp_value
            capped = True
        
        # Calculate actual margin after adjustments
        actual_margin = ((new_selling_price - item.unit_price) / item.unit_price) * 100 if item.unit_price > 0 else 0
        
        # Calculate impact
        old_revenue = item.selling_price * item.quantity
        new_revenue = new_selling_price * item.quantity
        revenue_change = new_revenue - old_revenue
        
        old_profit = (item.selling_price - item.unit_price) * item.quantity
        new_profit = (new_selling_price - item.unit_price) * item.quantity
        profit_change = new_profit - old_profit
        
        results.append({
            "product_name": item.product_name,
            "composition": item.composition,
            "current_selling_price": round(item.selling_price, 2),
            "current_margin": round(item.profit_margin, 2) if item.profit_margin else 0,
            "new_selling_price": round(new_selling_price, 2),
            "new_margin": round(actual_margin, 2),
            "mrp": item.mrp,
            "capped_by_mrp": capped,
            "quantity": item.quantity,
            "revenue_change": round(revenue_change, 2),
            "profit_change": round(profit_change, 2),
            "old_revenue": round(old_revenue, 2),
            "new_revenue": round(new_revenue, 2),
            "old_profit": round(old_profit, 2),
            "new_profit": round(new_profit, 2)
        })
    
    # Summary
    total_revenue_change = sum(r["revenue_change"] for r in results)
    total_profit_change = sum(r["profit_change"] for r in results)
    
    return {
        "items": results,
        "summary": {
            "total_items": len(results),
            "total_revenue_change": round(total_revenue_change, 2),
            "total_profit_change": round(total_profit_change, 2),
            "avg_new_margin": round(sum(r["new_margin"] for r in results) / len(results), 2) if results else 0,
            "items_capped_by_mrp": sum(1 for r in results if r["capped_by_mrp"])
        }
    }

@router.get("/analytics/pricing-optimization")
async def get_pricing_optimization(
    shop_id: Optional[int] = None,
    target_margin: float = 35.0,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get pricing optimization recommendations"""
    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).join(
        Shop, PurchaseInvoice.shop_id == Shop.id
    ).filter(
        PurchaseInvoice.is_admin_verified == True,
        Shop.organization_id == current_admin.organization_id
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.all()
    
    recommendations = []
    for item in items:
        if not item.profit_margin or item.profit_margin < target_margin:
            # Calculate optimal selling price for target margin
            optimal_price = item.unit_price * (1 + target_margin / 100)
            
            # Check MRP constraint
            mrp_value = parse_mrp(item.mrp)
            
            if mrp_value and optimal_price > mrp_value:
                # MRP-constrained - calculate max achievable margin
                max_margin = ((mrp_value - item.unit_price) / item.unit_price) * 100
                recommended_price = mrp_value
                achievable_margin = max_margin
                mrp_constrained = True
            else:
                recommended_price = optimal_price
                achievable_margin = target_margin
                mrp_constrained = False
            
            # Calculate potential revenue and profit increase
            current_revenue = item.selling_price * item.quantity
            potential_revenue = recommended_price * item.quantity
            revenue_increase = potential_revenue - current_revenue
            
            current_profit = (item.selling_price - item.unit_price) * item.quantity
            potential_profit = (recommended_price - item.unit_price) * item.quantity
            profit_increase = potential_profit - current_profit
            
            recommendations.append({
                "product_name": item.product_name,
                "composition": item.composition,
                "current_price": round(item.selling_price, 2),
                "current_margin": round(item.profit_margin, 2) if item.profit_margin else 0,
                "recommended_price": round(recommended_price, 2),
                "achievable_margin": round(achievable_margin, 2),
                "mrp": item.mrp,
                "mrp_constrained": mrp_constrained,
                "quantity": item.quantity,
                "revenue_increase": round(revenue_increase, 2),
                "profit_increase": round(profit_increase, 2),
                "priority": "high" if profit_increase > 1000 else "medium" if profit_increase > 500 else "low"
            })
    
    # Sort by profit increase potential
    recommendations.sort(key=lambda x: x["profit_increase"], reverse=True)
    
    total_potential_revenue = sum(r["revenue_increase"] for r in recommendations)
    total_potential_profit = sum(r["profit_increase"] for r in recommendations)
    
    return {
        "recommendations": recommendations[:50],  # Top 50 opportunities
        "summary": {
            "total_opportunities": len(recommendations),
            "total_potential_revenue_increase": round(total_potential_revenue, 2),
            "total_potential_profit_increase": round(total_potential_profit, 2),
            "high_priority_count": sum(1 for r in recommendations if r["priority"] == "high"),
            "mrp_constrained_count": sum(1 for r in recommendations if r["mrp_constrained"])
        }
    }

@router.get("/analytics/margin-trends")
async def get_margin_trends(
    shop_id: Optional[int] = None,
    months: int = 6,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """Get margin trends over time"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=months * 30)

    query = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).join(
        Shop, PurchaseInvoice.shop_id == Shop.id
    ).filter(
        PurchaseInvoice.is_admin_verified == True,
        PurchaseInvoice.invoice_date >= start_date,
        Shop.organization_id == current_admin.organization_id
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    items = query.all()
    
    # Group by month
    monthly_data = {}
    for item in items:
        invoice = item.invoice
        month_key = invoice.invoice_date.strftime("%Y-%m")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {"margins": [], "revenue": 0, "cost": 0, "items": 0}
        
        monthly_data[month_key]["margins"].append(item.profit_margin or 0)
        monthly_data[month_key]["revenue"] += item.selling_price * item.quantity
        monthly_data[month_key]["cost"] += item.unit_price * item.quantity
        monthly_data[month_key]["items"] += 1
    
    trends = [{
        "month": k,
        "avg_margin": round(sum(v["margins"]) / len(v["margins"]), 2) if v["margins"] else 0,
        "total_revenue": round(v["revenue"], 2),
        "total_cost": round(v["cost"], 2),
        "total_profit": round(v["revenue"] - v["cost"], 2),
        "items_count": v["items"]
    } for k, v in sorted(monthly_data.items())]
    
    return {
        "trends": trends,
        "summary": {
            "months_analyzed": len(trends),
            "trend_direction": "improving" if len(trends) >= 2 and trends[-1]["avg_margin"] > trends[0]["avg_margin"] else "declining" if len(trends) >= 2 else "stable"
        }
    }

@router.get("/staff/expiry-alerts")
def get_expiry_alerts_staff(
    days_threshold: int = Query(90, description="Days threshold for expiry warning"),
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get expiry alerts for staff's shop (ADMIN-VERIFIED INVOICES ONLY)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice, PurchaseInvoiceItem
    from modules.auth.models import Shop
    from datetime import date, timedelta

    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")

    staff = user_dict["user"]
    shop_code = user_dict["token_data"].shop_code
    shop = db.query(Shop).filter(
        Shop.shop_code == shop_code,
        Shop.organization_id == staff.shop.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop_id = shop.id

    items = db.query(PurchaseInvoiceItem).join(PurchaseInvoice).filter(
        PurchaseInvoiceItem.shop_id == shop_id,
        PurchaseInvoice.is_admin_verified == True,
        PurchaseInvoiceItem.expiry_date.isnot(None)
    ).all()

    expired = []
    expiring_soon = []
    safe = []
    today = date.today()

    for item in items:
        days_to_expiry = (item.expiry_date - today).days
        item_data = {
            "product_name": item.product_name,
            "batch_number": item.batch_number,
            "quantity": item.quantity,
            "expiry_date": item.expiry_date.isoformat(),
            "days_to_expiry": days_to_expiry,
            "value": item.total_amount,
            "shop_id": item.shop_id,
            "invoice_id": item.invoice_id
        }
        if days_to_expiry < 0:
            item_data["status"] = "expired"
            item_data["expired_days_ago"] = abs(days_to_expiry)
            expired.append(item_data)
        elif days_to_expiry <= days_threshold:
            item_data["status"] = "expiring_soon"
            expiring_soon.append(item_data)
        else:
            item_data["status"] = "safe"
            safe.append(item_data)

    expired_value = sum(i["value"] for i in expired)
    expiring_value = sum(i["value"] for i in expiring_soon)

    return {
        "summary": {
            "expired_count": len(expired),
            "expiring_soon_count": len(expiring_soon),
            "safe_count": len(safe),
            "expired_value": round(expired_value, 2),
            "expiring_value": round(expiring_value, 2),
            "total_at_risk": round(expired_value + expiring_value, 2)
        },
        "expired": sorted(expired, key=lambda x: x["expired_days_ago"], reverse=True),
        "expiring_soon": sorted(expiring_soon, key=lambda x: x["days_to_expiry"]),
        "safe": safe[:50]
    }


@router.get("/staff/supplier-performance")
def get_supplier_performance_staff(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get supplier performance for staff's shop (ADMIN-VERIFIED INVOICES ONLY)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice
    from modules.auth.models import Shop

    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")

    staff = user_dict["user"]
    shop_code = user_dict["token_data"].shop_code
    shop = db.query(Shop).filter(
        Shop.shop_code == shop_code,
        Shop.organization_id == staff.shop.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    shop_id = shop.id

    query = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.shop_id == shop_id,
        PurchaseInvoice.is_admin_verified == True
    )

    if start_date:
        query = query.filter(PurchaseInvoice.invoice_date >= start_date)
    if end_date:
        query = query.filter(PurchaseInvoice.invoice_date <= end_date)

    invoices = query.all()

    suppliers = {}
    for inv in invoices:
        if inv.supplier_name not in suppliers:
            suppliers[inv.supplier_name] = {
                "total_spend": 0,
                "invoice_count": 0,
                "total_items": 0,
                "avg_invoice_value": 0,
                "total_gst": 0,
                "first_purchase": inv.invoice_date,
                "last_purchase": inv.invoice_date
            }
        s = suppliers[inv.supplier_name]
        s["total_spend"] += inv.net_amount
        s["invoice_count"] += 1
        s["total_items"] += len(inv.items)
        s["total_gst"] += inv.total_gst
        if inv.invoice_date < s["first_purchase"]:
            s["first_purchase"] = inv.invoice_date
        if inv.invoice_date > s["last_purchase"]:
            s["last_purchase"] = inv.invoice_date

    for data in suppliers.values():
        data["avg_invoice_value"] = round(data["total_spend"] / data["invoice_count"], 2)
        data["first_purchase"] = data["first_purchase"].isoformat()
        data["last_purchase"] = data["last_purchase"].isoformat()
        data["total_spend"] = round(data["total_spend"], 2)
        data["total_gst"] = round(data["total_gst"], 2)

    sorted_suppliers = sorted(suppliers.items(), key=lambda x: x[1]["total_spend"], reverse=True)

    return {
        "total_suppliers": len(suppliers),
        "suppliers": [{"name": name, **data} for name, data in sorted_suppliers]
    }


# NOTE: This route MUST remain last — FastAPI matches routes in order, and /{invoice_id}
# would shadow any specific GET routes defined after it (e.g. /product-names, /compositions).
@router.get("/{invoice_id}", response_model=schemas.PurchaseInvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get specific invoice details - accessible by both staff and admin"""
    from modules.auth.models import Admin, Shop

    user_type = user_dict["token_data"].user_type

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

    staff_verified_by_name = None
    if invoice.staff_verified_by:
        verifier = db.query(Staff).filter(Staff.id == invoice.staff_verified_by).first()
        if verifier:
            staff_verified_by_name = verifier.name

    admin_verified_by_name = None
    if invoice.admin_verified_by:
        admin_verifier = db.query(Admin).filter(Admin.id == invoice.admin_verified_by).first()
        if admin_verifier:
            admin_verified_by_name = admin_verifier.full_name

    return {
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
        "items": invoice.items,
    }
