from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from .models import PurchaseInvoiceItem, PurchaseInvoice
from typing import Optional

router = APIRouter()

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
