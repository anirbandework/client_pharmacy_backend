from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Admin

def get_admin_user(user_dict: dict = Depends(get_user_dict), db: Session = Depends(get_db)) -> Admin:
    """Verify user is admin and return admin object"""
    if user_dict["token_data"].user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_dict["user"]
