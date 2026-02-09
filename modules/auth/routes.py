from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from typing import List
from datetime import datetime
from . import schemas, models
from .service import AuthService
from .dependencies import get_current_admin, get_current_staff, require_permission

router = APIRouter()

# ADMIN AUTHENTICATION

@router.post("/admin/register", response_model=schemas.Admin)
def register_admin(admin_data: schemas.AdminCreate, db: Session = Depends(get_db)):
    """Register new admin (business owner)"""
    existing = db.query(models.Admin).filter(models.Admin.email == admin_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    admin = AuthService.create_admin(db, admin_data)
    return admin

@router.post("/admin/login", response_model=schemas.Token)
def admin_login(login_data: schemas.AdminLogin, db: Session = Depends(get_db)):
    """Admin login with email and password"""
    admin = AuthService.authenticate_admin(db, login_data.email, login_data.password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = AuthService.create_access_token({
        "user_id": admin.id,
        "user_type": "admin",
        "email": admin.email
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "admin",
        "shop_id": None,
        "shop_name": None
    }

@router.get("/admin/me", response_model=schemas.Admin)
def get_admin_profile(admin: models.Admin = Depends(get_current_admin)):
    """Get current admin profile"""
    return admin

# SHOP MANAGEMENT (Admin only)

@router.post("/admin/shops", response_model=schemas.Shop)
def create_shop(
    shop_data: schemas.ShopCreate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new shop"""
    existing = db.query(models.Shop).filter(models.Shop.shop_code == shop_data.shop_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Shop code already exists")
    
    shop = AuthService.create_shop(db, admin.id, shop_data, admin.full_name)
    return shop

@router.get("/admin/shops", response_model=List[schemas.Shop])
def get_admin_shops(
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all shops (shared visibility)"""
    return AuthService.get_all_shops(db)

@router.get("/admin/all-shops", response_model=List[schemas.Shop])
def get_all_shops(
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all shops from all admins"""
    return AuthService.get_all_shops(db)

@router.get("/admin/shops/{shop_id}", response_model=schemas.Shop)
def get_shop(
    shop_id: int,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specific shop details"""
    shop = db.query(models.Shop).filter(
        models.Shop.id == shop_id,
        models.Shop.admin_id == admin.id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

@router.put("/admin/shops/{shop_id}", response_model=schemas.Shop)
def update_shop(
    shop_id: int,
    shop_data: schemas.ShopUpdate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update shop details (any admin can update any shop)"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    for key, value in shop_data.model_dump(exclude_unset=True).items():
        setattr(shop, key, value)
    
    shop.updated_by_admin = admin.full_name
    shop.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(shop)
    return shop

@router.delete("/admin/shops/{shop_id}")
def delete_shop(
    shop_id: int,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete shop and all its staff"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Delete all staff in the shop first
    staff_list = db.query(models.Staff).filter(models.Staff.shop_id == shop_id).all()
    staff_count = len(staff_list)
    
    for staff in staff_list:
        db.delete(staff)
    
    # Delete the shop
    db.delete(shop)
    db.commit()
    
    return {"message": f"Shop and {staff_count} staff members deleted successfully"}

# STAFF MANAGEMENT

@router.post("/admin/shops/{shop_id}/staff", response_model=schemas.Staff)
def create_staff(
    shop_id: int,
    staff_data: schemas.StaffCreate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create staff for any shop (any admin can create staff)"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    staff = AuthService.create_staff(db, shop_id, staff_data, admin.full_name)
    return staff

@router.get("/admin/all-staff", response_model=List[schemas.Staff])
def get_all_staff(
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all staff from all shops"""
    return AuthService.get_all_staff(db)

@router.get("/shops/{shop_id}/staff", response_model=List[schemas.Staff])
def get_shop_staff(
    shop_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin)
):
    """Get all staff for a shop"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return AuthService.get_shop_staff(db, shop_id)

@router.put("/staff/{staff_id}", response_model=schemas.Staff)
def update_staff(
    staff_id: int,
    staff_data: schemas.StaffUpdate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update staff details (any admin can update any staff)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    for key, value in staff_data.model_dump(exclude_unset=True).items():
        setattr(staff, key, value)
    
    staff.updated_by_admin = admin.full_name
    staff.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/staff/{staff_id}")
def delete_staff(
    staff_id: int,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete staff (any admin can delete any staff)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db.delete(staff)
    db.commit()
    return {"message": "Staff deleted successfully"}

# STAFF AUTHENTICATION

@router.post("/staff/login", response_model=schemas.Token)
def staff_login(login_data: schemas.StaffLogin, db: Session = Depends(get_db)):
    """Staff login using UUID"""
    staff = AuthService.authenticate_staff(db, login_data.uuid)
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid UUID or staff inactive")
    
    # Check if shop is active
    if not staff.shop.is_active:
        raise HTTPException(status_code=403, detail="Shop is inactive")
    
    token = AuthService.create_access_token({
        "user_id": staff.id,
        "user_type": "staff",
        "shop_id": staff.shop_id,
        "email": staff.email
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "staff",
        "shop_id": staff.shop_id,
        "shop_name": staff.shop.shop_name
    }

@router.get("/staff/me", response_model=schemas.Staff)
def get_staff_profile(staff: models.Staff = Depends(get_current_staff)):
    """Get current staff profile"""
    return staff

@router.get("/staff/shop", response_model=schemas.Shop)
def get_staff_shop(
    staff: models.Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get shop details for current staff"""
    return staff.shop
