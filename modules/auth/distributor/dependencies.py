from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.service import AuthService
from .models import Distributor

security = HTTPBearer()

def get_current_distributor(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated distributor"""
    token = credentials.credentials
    token_data = AuthService.decode_token(token)
    
    if not token_data or token_data.user_type != "distributor":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid distributor authentication"
        )
    
    distributor = db.query(Distributor).filter(
        Distributor.id == token_data.user_id
    ).first()
    
    if not distributor or not distributor.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Distributor not found or inactive"
        )
    
    return distributor