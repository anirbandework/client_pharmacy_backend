from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin
from modules.invoice_analyzer_v2 import schemas
from typing import Optional
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
    from modules.invoice_analyzer_v2 import models
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
    
    # Mark as admin verified (not yet committed — verification + stock sync commit atomically)
    invoice.is_admin_verified = True
    invoice.admin_verified_by = admin.id
    invoice.admin_verified_at = datetime.now()
    invoice.is_verified = True  # Legacy field
    invoice.updated_at = datetime.now()

    # Sync to stock and commit both together in one transaction
    try:
        from modules.stock_audit_v2.sync_service import InvoiceStockSyncService
        sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, invoice.shop_id)
        db.commit()  # Single commit: verification + all stock changes are atomic
    except Exception as e:
        db.rollback()  # Rolls back verification fields AND any partial stock writes
        logger.error(f"❌ Failed to sync invoice {invoice_id} to stock, rolling back verification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to sync to stock: {str(e)}")

    logger.info(
        f"AUDIT | action=admin_verify | invoice_id={invoice_id} | "
        f"admin_id={admin.id} | org_id={admin.organization_id} | at={datetime.now()}"
    )

    # Invalidate dashboard cache so analytics reflect new verified invoice
    from app.utils.cache import dashboard_cache
    dashboard_cache.clear_prefix(f"dashboard:{admin.organization_id}")
    dashboard_cache.clear_prefix(f"ai_analytics:{admin.organization_id}")

    logger.info(f"✅ Admin verified and synced invoice {invoice_id} to stock: {sync_result}")
    return {"message": "Invoice admin-verified and synced to stock", "sync_result": sync_result}

@router.post("/{invoice_id}/admin-reject")
def admin_reject_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin rejects invoice and sends back to staff for corrections"""
    from modules.invoice_analyzer_v2 import models
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

    logger.info(
        f"AUDIT | action=admin_reject | invoice_id={invoice_id} | "
        f"admin_id={admin.id} | org_id={admin.organization_id} | at={datetime.now()}"
    )

    # Invalidate dashboard cache
    from app.utils.cache import dashboard_cache
    dashboard_cache.clear_prefix(f"dashboard:{admin.organization_id}")

    return {"message": "Invoice rejected and sent back to staff"}

@router.put("/{invoice_id}/admin-update")
def admin_update_invoice(
    invoice_id: int,
    invoice_data: schemas.PurchaseInvoiceUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin updates invoice. If already admin-verified, reverses old stock sync and re-syncs with new items."""
    from modules.invoice_analyzer_v2 import models
    from modules.auth.models import Shop

    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    was_admin_verified = invoice.is_admin_verified

    # If already admin-verified, reverse old stock BEFORE deleting old items
    items_in_use = []
    if was_admin_verified:
        try:
            from modules.invoice_analyzer_v2.stock_reversal_service import reverse_stock_for_invoice
            _, items_in_use = reverse_stock_for_invoice(db, invoice, invoice_id, invoice.shop_id, reason="update")
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to reverse stock for invoice {invoice_id} during update: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to reverse stock before update: {str(e)}")

    # Update invoice fields (Pydantic already validated and parsed dates)
    invoice.invoice_number = invoice_data.invoice_number
    invoice.invoice_date = invoice_data.invoice_date
    invoice.due_date = invoice_data.due_date
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
    invoice.updated_at = datetime.now()

    logger.info(
        f"AUDIT | action=admin_update | invoice_id={invoice_id} | "
        f"admin_id={admin.id} | org_id={admin.organization_id} | at={datetime.now()}"
    )

    # Delete existing items
    db.query(models.PurchaseInvoiceItem).filter(
        models.PurchaseInvoiceItem.invoice_id == invoice_id
    ).delete()

    # Truncate string fields to prevent database errors
    def truncate_str(value, max_length=255, field_name=None):
        if value is None:
            return None
        s = str(value)
        if len(s) > max_length:
            if field_name in ("product_name", "batch_number"):
                # These fields are used as stock-matching keys — truncation causes sync/reversal mismatches
                raise HTTPException(
                    status_code=422,
                    detail=f"'{field_name}' exceeds {max_length} characters and cannot be safely stored. Please shorten it."
                )
            logger.warning(f"Truncating field '{field_name}' from {len(s)} to {max_length} chars")
            return s[:max_length]
        return s

    # Add updated items
    for item_data in invoice_data.items:
        item = models.PurchaseInvoiceItem(
            invoice_id=invoice.id,
            shop_id=invoice.shop_id,
            composition=truncate_str(item_data.composition, field_name="composition"),
            manufacturer=truncate_str(item_data.manufacturer, field_name="manufacturer"),
            hsn_code=truncate_str(item_data.hsn_code, field_name="hsn_code"),
            product_name=truncate_str(item_data.product_name or "Unknown Product", field_name="product_name"),
            batch_number=truncate_str(item_data.batch_number, field_name="batch_number"),
            quantity=item_data.quantity,
            free_quantity=item_data.free_quantity,
            package=truncate_str(item_data.package, field_name="package"),
            unit=truncate_str(item_data.unit, field_name="unit"),
            manufacturing_date=item_data.manufacturing_date,
            expiry_date=item_data.expiry_date,
            mrp=truncate_str(item_data.mrp, field_name="mrp"),
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

    # If invoice was already admin-verified, re-sync the new items to stock
    if was_admin_verified:
        try:
            db.flush()  # Write new items to the transaction
            db.expire(invoice)  # Expire cached invoice so sync re-reads fresh items from DB
            from modules.stock_audit_v2.sync_service import InvoiceStockSyncService
            sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, invoice.shop_id)
            logger.info(f"✅ Re-synced stock for updated verified invoice {invoice_id}: {sync_result}")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to re-sync stock for invoice {invoice_id} after update: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to re-sync stock after update: {str(e)}")

    db.commit()
    db.refresh(invoice)

    # Invalidate dashboard cache for this organization
    from app.utils.cache import dashboard_cache
    dashboard_cache.clear_prefix(f"dashboard:{admin.organization_id}")
    dashboard_cache.clear_prefix(f"ai_analytics:{admin.organization_id}")

    response = {"message": "Invoice updated successfully"}
    if items_in_use:
        response["warning"] = (
            f"{len(items_in_use)} item(s) were already sold in bills and had their stock quantity adjusted: "
            + ", ".join(items_in_use)
        )
    return response

@router.delete("/{invoice_id}/admin-delete")
def admin_delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Admin deletes invoice and reverses stock"""
    from modules.invoice_analyzer_v2 import models
    from modules.auth.models import Shop
    from modules.invoice_analyzer_v2.stock_reversal_service import reverse_stock_for_invoice

    invoice = db.query(models.PurchaseInvoice).join(Shop).filter(
        models.PurchaseInvoice.id == invoice_id,
        Shop.organization_id == admin.organization_id
    ).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    logger.info(
        f"AUDIT | action=admin_delete | invoice_id={invoice_id} | "
        f"admin_id={admin.id} | org_id={admin.organization_id} | at={datetime.now()}"
    )

    stock_reversed, items_in_use = reverse_stock_for_invoice(db, invoice, invoice_id, invoice.shop_id)

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

    # Invalidate dashboard cache
    from app.utils.cache import dashboard_cache
    dashboard_cache.clear_prefix(f"dashboard:{admin.organization_id}")
    dashboard_cache.clear_prefix(f"ai_analytics:{admin.organization_id}")

    response = {"message": "Invoice deleted successfully", "stock_reversed": stock_reversed}
    if items_in_use:
        response["warning"] = f"{len(items_in_use)} items are used in bills and were not deleted from stock"

    return response

@router.get("/pending-admin-verification")
def get_pending_admin_verification(
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get invoices pending admin verification (staff-verified but not admin-verified)"""
    from modules.invoice_analyzer_v2 import models
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
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get invoices pending staff verification with details"""
    from modules.invoice_analyzer_v2 import models
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
    shop_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get all invoices for admin (across organization)"""
    from modules.invoice_analyzer_v2 import models
    from modules.auth.models import Shop, Staff

    query = db.query(models.PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id
    )

    if shop_id:
        query = query.filter(models.PurchaseInvoice.shop_id == shop_id)

    invoices = query.order_by(models.PurchaseInvoice.created_at.desc()).offset(offset).limit(limit).all()
    
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
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_admin
from modules.auth.models import Admin
from typing import Optional
from datetime import date, datetime
from modules.invoice_analyzer_v2.admin.admin_ai_analytics_service import InvoiceAIAnalytics
from modules.invoice_analyzer_v2.admin.dashboard_analytics import DashboardAnalytics


@router.get("/admin/ai-analytics")
def get_ai_analytics(
    shop_id: Optional[int] = Query(None, description="Filter by specific shop (optional)"),
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Get comprehensive AI-powered analytics for invoice data (Admin only)
    
    Provides:
    - Financial health analysis
    - Supplier insights and recommendations
    - Inventory management insights
    - Expiry risk analysis
    - Procurement trends
    - Strategic recommendations
    """
    from app.utils.cache import dashboard_cache
    
    cache_key = f"ai_analytics:{admin.organization_id}:{shop_id}:{start_date}:{end_date}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=3600)
    if cached:
        return cached
    
    analytics_service = InvoiceAIAnalytics()
    
    result = analytics_service.generate_comprehensive_analysis(
        db=db,
        organization_id=admin.organization_id,
        shop_id=shop_id,
        start_date=start_date,
        end_date=end_date
    )
    
    dashboard_cache.set(cache_key, result)
    return result

@router.get("/admin/expiry-alerts")
def get_expiry_alerts(
    shop_id: Optional[int] = Query(None, description="Filter by specific shop"),
    days_threshold: int = Query(90, description="Days threshold for expiry warning"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get detailed expiry alerts for all shops (VERIFIED INVOICES ONLY)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice, PurchaseInvoiceItem
    from modules.auth.models import Shop
    from datetime import date, timedelta
    
    # Query items - ONLY FROM ADMIN-VERIFIED INVOICES
    query = db.query(PurchaseInvoiceItem).join(
        PurchaseInvoice
    ).join(
        Shop
    ).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_admin_verified == True,
        PurchaseInvoiceItem.expiry_date.isnot(None)
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoiceItem.shop_id == shop_id)
    
    items = query.all()
    
    # Categorize by expiry status
    expired = []
    expiring_soon = []
    safe = []
    
    today = date.today()
    threshold_date = today + timedelta(days=days_threshold)
    
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
    
    # Calculate financial impact
    expired_value = sum(item["value"] for item in expired)
    expiring_value = sum(item["value"] for item in expiring_soon)
    
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
        "safe": safe[:50]  # Limit safe items
    }

@router.get("/admin/supplier-performance")
def get_supplier_performance(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get detailed supplier performance metrics (VERIFIED INVOICES ONLY)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice
    from modules.auth.models import Shop
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_admin_verified == True
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    if start_date:
        query = query.filter(PurchaseInvoice.invoice_date >= start_date)
    
    if end_date:
        query = query.filter(PurchaseInvoice.invoice_date <= end_date)
    
    invoices = query.all()
    
    # Analyze suppliers
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
    
    # Calculate averages
    for name, data in suppliers.items():
        data["avg_invoice_value"] = round(data["total_spend"] / data["invoice_count"], 2)
        data["first_purchase"] = data["first_purchase"].isoformat()
        data["last_purchase"] = data["last_purchase"].isoformat()
        data["total_spend"] = round(data["total_spend"], 2)
        data["total_gst"] = round(data["total_gst"], 2)
    
    # Sort by total spend
    sorted_suppliers = sorted(
        suppliers.items(),
        key=lambda x: x[1]["total_spend"],
        reverse=True
    )
    
    return {
        "total_suppliers": len(suppliers),
        "suppliers": [
            {"name": name, **data}
            for name, data in sorted_suppliers
        ]
    }

@router.get("/admin/procurement-trends")
def get_procurement_trends(
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get procurement trends and patterns (Admin only)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice
    from modules.auth.models import Shop
    from sqlalchemy import func, extract
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.all()
    
    # Monthly trends
    monthly = {}
    for inv in invoices:
        month_key = inv.invoice_date.strftime("%Y-%m")
        if month_key not in monthly:
            monthly[month_key] = {
                "total_spend": 0,
                "invoice_count": 0,
                "total_items": 0
            }
        monthly[month_key]["total_spend"] += inv.net_amount
        monthly[month_key]["invoice_count"] += 1
        monthly[month_key]["total_items"] += len(inv.items)
    
    # Day of week analysis
    day_of_week = {}
    for inv in invoices:
        day = inv.invoice_date.strftime("%A")
        if day not in day_of_week:
            day_of_week[day] = {"count": 0, "total_spend": 0}
        day_of_week[day]["count"] += 1
        day_of_week[day]["total_spend"] += inv.net_amount
    
    return {
        "monthly_trends": monthly,
        "day_of_week_analysis": day_of_week,
        "total_invoices": len(invoices),
        "date_range": {
            "first_invoice": min(inv.invoice_date for inv in invoices).isoformat() if invoices else None,
            "last_invoice": max(inv.invoice_date for inv in invoices).isoformat() if invoices else None
        }
    }

@router.get("/admin/dashboard-analytics")
def get_dashboard_analytics(
    shop_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get comprehensive dashboard analytics with chart-ready data (Admin only)"""
    from app.utils.cache import dashboard_cache
    
    cache_key = f"dashboard:{admin.organization_id}:{shop_id}:{start_date}:{end_date}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=60)
    if cached:
        return cached
    
    analytics = DashboardAnalytics.get_comprehensive_analytics(
        db=db,
        organization_id=admin.organization_id,
        shop_id=shop_id,
        start_date=start_date,
        end_date=end_date
    )
    
    dashboard_cache.set(cache_key, analytics)
    return analytics

@router.get("/admin/pending-verification")
def get_pending_verification(
    shop_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get list of unverified invoices pending verification (Admin only)"""
    from modules.invoice_analyzer_v2.models import PurchaseInvoice
    from modules.auth.models import Shop, Staff
    
    query = db.query(PurchaseInvoice).join(Shop).filter(
        Shop.organization_id == admin.organization_id,
        PurchaseInvoice.is_staff_verified == False
    )
    
    if shop_id:
        query = query.filter(PurchaseInvoice.shop_id == shop_id)
    
    invoices = query.order_by(PurchaseInvoice.created_at.desc()).all()
    
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


