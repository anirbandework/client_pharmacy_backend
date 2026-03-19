from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from modules.auth.dependencies import get_current_super_admin
from modules.auth.service import AuthService
from modules.auth.models import SuperAdmin, Shop
from modules.auth.otp.service import OTPService
from datetime import datetime
from typing import List, Optional
from . import models, schemas
from .dependencies import get_current_distributor

router = APIRouter()

# SuperAdmin routes for managing distributors
@router.post("/", response_model=schemas.Distributor)
def create_distributor(
    distributor: schemas.DistributorCreate,
    db: Session = Depends(get_db),
    super_admin: SuperAdmin = Depends(get_current_super_admin)
):
    """SuperAdmin creates a new distributor"""
    # Check if distributor code already exists
    existing = db.query(models.Distributor).filter(
        models.Distributor.distributor_code == distributor.distributor_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Distributor code already exists")
    
    # Check if phone already exists
    existing_phone = db.query(models.Distributor).filter(
        models.Distributor.phone == distributor.phone
    ).first()
    if existing_phone:
        raise HTTPException(status_code=409, detail="Phone number already registered")
    
    # Check if email already exists (if provided)
    if distributor.email:
        existing_email = db.query(models.Distributor).filter(
            models.Distributor.email == distributor.email
        ).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Email already registered")
    
    # Create distributor
    db_distributor = models.Distributor(
        **distributor.model_dump(),
        created_by_super_admin=super_admin.full_name
    )
    db.add(db_distributor)
    db.commit()
    db.refresh(db_distributor)
    
    return db_distributor

@router.get("/", response_model=List[schemas.Distributor])
def get_distributors(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    super_admin: SuperAdmin = Depends(get_current_super_admin)
):
    """SuperAdmin gets all distributors"""
    return db.query(models.Distributor).offset(skip).limit(limit).all()

@router.get("/{distributor_id}", response_model=schemas.Distributor)
def get_distributor(
    distributor_id: int,
    db: Session = Depends(get_db),
    super_admin: SuperAdmin = Depends(get_current_super_admin)
):
    """SuperAdmin gets specific distributor"""
    distributor = db.query(models.Distributor).filter(
        models.Distributor.id == distributor_id
    ).first()
    
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    return distributor

@router.put("/{distributor_id}", response_model=schemas.Distributor)
def update_distributor(
    distributor_id: int,
    distributor_update: schemas.DistributorUpdate,
    db: Session = Depends(get_db),
    super_admin: SuperAdmin = Depends(get_current_super_admin)
):
    """SuperAdmin updates distributor"""
    distributor = db.query(models.Distributor).filter(
        models.Distributor.id == distributor_id
    ).first()
    
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    # Check for duplicate phone/email if being updated
    if distributor_update.phone and distributor_update.phone != distributor.phone:
        existing = db.query(models.Distributor).filter(
            models.Distributor.phone == distributor_update.phone,
            models.Distributor.id != distributor_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Phone number already exists")
    
    if distributor_update.email and distributor_update.email != distributor.email:
        existing = db.query(models.Distributor).filter(
            models.Distributor.email == distributor_update.email,
            models.Distributor.id != distributor_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")
    
    # Update fields
    for key, value in distributor_update.model_dump(exclude_unset=True).items():
        setattr(distributor, key, value)
    
    distributor.updated_by_super_admin = super_admin.full_name
    distributor.updated_at = datetime.now()
    
    db.commit()
    db.refresh(distributor)
    
    return distributor

@router.delete("/{distributor_id}")
def delete_distributor(
    distributor_id: int,
    db: Session = Depends(get_db),
    super_admin: SuperAdmin = Depends(get_current_super_admin)
):
    """SuperAdmin deletes distributor"""
    distributor = db.query(models.Distributor).filter(
        models.Distributor.id == distributor_id
    ).first()
    
    if not distributor:
        raise HTTPException(status_code=404, detail="Distributor not found")
    
    db.delete(distributor)
    db.commit()
    
    return {"message": "Distributor deleted successfully"}

# Distributor authentication routes
@router.post("/login")
def distributor_login(
    login_data: schemas.DistributorLogin,
    db: Session = Depends(get_db)
):
    """Distributor login with email and password"""
    distributor = db.query(models.Distributor).filter(
        models.Distributor.email == login_data.email
    ).first()
    
    if not distributor or not distributor.is_active:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not distributor.is_password_set or not distributor.password_hash:
        raise HTTPException(status_code=400, detail="Password not set. Please complete signup first.")
    
    if not AuthService.verify_password(login_data.password, distributor.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    distributor.last_login = datetime.now()
    db.commit()
    
    # Generate token
    token = AuthService.create_access_token({
        "user_id": distributor.id,
        "user_type": "distributor",
        "email": distributor.email,
        "user_name": distributor.contact_person
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "distributor",
        "distributor_id": distributor.id,
        "company_name": distributor.company_name
    }

@router.post("/signup")
def distributor_signup(
    signup_data: schemas.DistributorSignupRequest,
    db: Session = Depends(get_db)
):
    """Distributor completes signup by setting password"""
    try:
        otp = OTPService.distributor_signup(db, signup_data.phone, signup_data.password)
        return {"message": "Password set successfully. OTP sent for verification."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/request-otp")
def request_distributor_otp(
    request: schemas.DistributorOTPRequest,
    db: Session = Depends(get_db)
):
    """Request OTP for distributor phone login"""
    try:
        otp = OTPService.create_distributor_otp(db, request.phone, request.password)
        return {"message": "OTP sent successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-otp")
def verify_distributor_otp(
    request: schemas.DistributorOTPVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP and login distributor"""
    try:
        distributor = OTPService.verify_distributor_otp(db, request.phone, request.otp)
        
        # Generate token
        token = AuthService.create_access_token({
            "user_id": distributor.id,
            "user_type": "distributor",
            "email": distributor.email,
            "user_name": distributor.contact_person
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "distributor",
            "distributor_id": distributor.id,
            "company_name": distributor.company_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Distributor shop search route
@router.get("/shops/search")
def search_shops(
    q: str,
    distributor: models.Distributor = Depends(get_current_distributor),
    db: Session = Depends(get_db)
):
    """Search shops by name, phone, license number, or GST number"""
    if not q or len(q) < 2:
        return []
    
    search_term = f"%{q}%"
    shops = db.query(Shop).filter(
        (Shop.shop_name.ilike(search_term)) |
        (Shop.phone.ilike(search_term)) |
        (Shop.license_number.ilike(search_term)) |
        (Shop.gst_number.ilike(search_term)) |
        (Shop.shop_code.ilike(search_term))
    ).limit(20).all()
    
    return [{
        "id": shop.id,
        "shop_name": shop.shop_name,
        "shop_code": shop.shop_code,
        "phone": shop.phone,
        "email": shop.email,
        "address": shop.address,
        "license_number": shop.license_number,
        "gst_number": shop.gst_number,
        "organization_id": shop.organization_id,
        "is_registered": True
    } for shop in shops]
@router.get("/profile/me", response_model=schemas.Distributor)
def get_my_profile(
    distributor: models.Distributor = Depends(get_current_distributor)
):
    """Get current distributor profile"""
    return distributor

@router.put("/profile/me", response_model=schemas.Distributor)
def update_my_profile(
    profile_update: schemas.DistributorUpdate,
    db: Session = Depends(get_db),
    distributor: models.Distributor = Depends(get_current_distributor)
):
    """Update current distributor profile"""
    # Check for duplicate phone/email if being updated
    if profile_update.phone and profile_update.phone != distributor.phone:
        existing = db.query(models.Distributor).filter(
            models.Distributor.phone == profile_update.phone,
            models.Distributor.id != distributor.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Phone number already exists")
    
    if profile_update.email and profile_update.email != distributor.email:
        existing = db.query(models.Distributor).filter(
            models.Distributor.email == profile_update.email,
            models.Distributor.id != distributor.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")
    
    # Update allowed fields only
    allowed_fields = ['company_name', 'contact_person', 'email', 'phone', 'address', 'city', 'state', 'pincode', 'gstin', 'dl_number', 'food_license', 'bank_name', 'bank_account', 'bank_ifsc', 'bank_branch']
    for key, value in profile_update.model_dump(exclude_unset=True).items():
        if key in allowed_fields:
            setattr(distributor, key, value)
    
    distributor.updated_at = datetime.now()
    db.commit()
    db.refresh(distributor)
    
    return distributor

@router.put("/profile/change-password")
def change_password(
    password_data: schemas.DistributorPasswordChange,
    db: Session = Depends(get_db),
    distributor: models.Distributor = Depends(get_current_distributor)
):
    """Change distributor password"""
    if not distributor.is_password_set or not distributor.password_hash:
        raise HTTPException(status_code=400, detail="No password set. Please complete signup first.")
    
    if not AuthService.verify_password(password_data.current_password, distributor.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    distributor.password_hash = AuthService.hash_password(password_data.new_password)
    distributor.updated_at = datetime.now()
    db.commit()
    
    return {"message": "Password changed successfully"}

# PASSWORD RESET ROUTES FOR DISTRIBUTOR

@router.post("/forgot-password")
def forgot_password(
    request: schemas.DistributorPasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset - sends OTP to phone"""
    try:
        result = OTPService.request_password_reset(db, request.phone, "distributor")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify-reset-otp")
def verify_reset_otp(
    request: schemas.DistributorPasswordResetVerifyOTP,
    db: Session = Depends(get_db)
):
    """Verify OTP and get reset token"""
    try:
        result = OTPService.verify_reset_otp(db, request.phone, request.otp, "distributor")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reset-password")
def reset_password(
    request: schemas.DistributorPasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    try:
        result = OTPService.reset_password_with_token(db, request.reset_token, request.new_password, "distributor")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))