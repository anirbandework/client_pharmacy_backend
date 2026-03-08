from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from . import models

router = APIRouter()

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
