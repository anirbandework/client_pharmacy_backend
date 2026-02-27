from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.billing.dependencies import get_current_user_with_geofence as get_current_user
from modules.auth.models import Shop
from pydantic import BaseModel
import json

router = APIRouter()

class BillConfigUpdate(BaseModel):
    storeName: str
    logo: str
    dlNumbers: dict
    flNumber: str
    address: dict
    phone: str
    gstIn: str

@router.put("/admin/bill-config")
def update_shop_bill_config(
    config: BillConfigUpdate,
    current_user: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Staff updates bill configuration for their shop"""
    staff, shop_id = current_user
    
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    shop.bill_config = json.dumps(config.dict())
    db.commit()
    
    return {"message": "Bill configuration updated successfully"}

@router.get("/admin/bill-config")
def get_shop_bill_config_admin(
    current_user: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Staff gets bill configuration for their shop"""
    staff, shop_id = current_user
    
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    if shop.bill_config:
        try:
            config = json.loads(shop.bill_config)
            return {"config": config}
        except:
            pass
    
    return {"config": None}
