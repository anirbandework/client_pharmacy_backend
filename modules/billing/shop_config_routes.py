from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.billing.dependencies import get_current_user_with_geofence as get_current_user
from modules.auth.models import Shop
import json

router = APIRouter()

@router.get("/shop/bill-config")
def get_shop_bill_config(
    current_user: tuple = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bill configuration for current shop"""
    staff, shop_id = current_user
    
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Parse JSON config or return default
    if shop.bill_config:
        try:
            config = json.loads(shop.bill_config)
            return {"config": config}
        except:
            pass
    
    return {"config": get_default_config()}

def get_default_config():
    """Default bill configuration"""
    return {
        "storeName": "GENERICART MEDICINE STORE",
        "logo": "",
        "dlNumbers": {
            "dl20": "20-RLF20TR2025000266",
            "dl21": "21-RLF21TR2025000259"
        },
        "flNumber": "",
        "address": {
            "line1": "JOYNAGAR BUS STOP, ROLANDSAY ROAD, AGARTALA",
            "state": "Tripura",
            "pincode": "799001"
        },
        "phone": "6909319003",
        "gstIn": "16GDYPP9241P2Z6"
    }
