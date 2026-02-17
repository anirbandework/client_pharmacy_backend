from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from typing import List
from datetime import datetime
from . import schemas, models
from .service import AuthService
from .dependencies import get_current_admin, get_current_staff, get_current_super_admin, require_permission
from .otp import OTPService, SendOTPRequest, VerifyOTPRequest, OTPResponse

router = APIRouter()

# SUPER ADMIN AUTHENTICATION WITH OTP

@router.post("/super-admin/send-otp", response_model=OTPResponse)
async def send_super_admin_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to super admin phone for login"""
    try:
        otp = OTPService.create_super_admin_otp(db, request.phone, request.password)
        return OTPResponse(
            message="OTP sent successfully",
            expires_in=300,
            can_resend_in=30
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/super-admin/verify-otp", response_model=schemas.Token)
def verify_super_admin_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login super admin"""
    try:
        super_admin = OTPService.verify_super_admin_otp(db, request.phone, request.otp_code)
        
        token = AuthService.create_access_token({
            "user_id": super_admin.id,
            "user_type": "super_admin",
            "email": super_admin.email,
            "user_name": super_admin.full_name
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "super_admin",
            "user_name": super_admin.full_name,
            "organization_id": None,
            "shop_id": None,
            "shop_name": None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# SUPER ADMIN AUTHENTICATION (OLD)

@router.post("/super-admin/register", response_model=schemas.SuperAdmin)
def register_super_admin(super_admin_data: schemas.SuperAdminCreate, db: Session = Depends(get_db)):
    """Register new super admin"""
    existing = db.query(models.SuperAdmin).filter(models.SuperAdmin.email == super_admin_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    super_admin = AuthService.create_super_admin(db, super_admin_data)
    return super_admin

@router.post("/super-admin/login", response_model=schemas.Token)
def super_admin_login(login_data: schemas.SuperAdminLogin, db: Session = Depends(get_db)):
    """SuperAdmin login (legacy - use OTP instead)"""
    super_admin = AuthService.authenticate_super_admin(db, login_data.email, login_data.password)
    if not super_admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = AuthService.create_access_token({
        "user_id": super_admin.id,
        "user_type": "super_admin",
        "email": super_admin.email,
        "user_name": super_admin.full_name
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "super_admin",
        "user_name": super_admin.full_name,
        "organization_id": None,
        "shop_id": None,
        "shop_name": None
    }

@router.get("/super-admin/me", response_model=schemas.SuperAdmin)
def get_super_admin_profile(super_admin: models.SuperAdmin = Depends(get_current_super_admin)):
    """Get current super admin profile"""
    return super_admin

# SUPER ADMIN - ADMIN MANAGEMENT

@router.post("/super-admin/admins", response_model=schemas.Admin)
def create_admin(
    admin_data: schemas.AdminCreate,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin creates admin with organization_id"""
    existing = db.query(models.Admin).filter(models.Admin.phone == admin_data.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    admin = AuthService.create_admin(db, admin_data, super_admin.full_name)
    return admin

@router.get("/super-admin/admins", response_model=List[schemas.Admin])
def get_all_admins(
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get all admins"""
    return db.query(models.Admin).all()

@router.get("/super-admin/admins/organization/{organization_id}", response_model=List[schemas.Admin])
def get_organization_admins(
    organization_id: str,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get all admins with same organization_id"""
    return db.query(models.Admin).filter(models.Admin.organization_id == organization_id).all()

@router.put("/super-admin/admins/{admin_id}", response_model=schemas.Admin)
def update_admin(
    admin_id: int,
    admin_data: schemas.AdminUpdate,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin updates admin details"""
    admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    for key, value in admin_data.model_dump(exclude_unset=True).items():
        setattr(admin, key, value)
    
    db.commit()
    db.refresh(admin)
    return admin

@router.delete("/super-admin/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin deletes admin (shops/staff remain for other admins in same org)"""
    admin = db.query(models.Admin).filter(models.Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    org_id = admin.organization_id
    
    # Get all admins in organization
    org_admins = db.query(models.Admin).filter(
        models.Admin.organization_id == org_id
    ).all()
    
    if len(org_admins) == 1:
        # Last admin - delete all shops and staff in organization
        admin_ids = [a.id for a in org_admins]
        shops = db.query(models.Shop).filter(models.Shop.admin_id.in_(admin_ids)).all()
        shop_count = len(shops)
        staff_count = 0
        
        # Delete staff first
        for shop in shops:
            staff_list = db.query(models.Staff).filter(models.Staff.shop_id == shop.id).all()
            staff_count += len(staff_list)
            for staff in staff_list:
                db.delete(staff)
        
        # Delete shops
        for shop in shops:
            db.delete(shop)
        
        # Expunge admin to prevent relationship updates
        db.expunge(admin)
        
        # Delete admin using raw delete
        db.query(models.Admin).filter(models.Admin.id == admin_id).delete()
        db.commit()
        
        return {
            "message": "Last admin in organization deleted. All shops and staff removed.",
            "admins_remaining": 0,
            "shops_deleted": shop_count,
            "staff_deleted": staff_count
        }
    else:
        # Other admins exist - expunge and delete
        db.expunge(admin)
        db.query(models.Admin).filter(models.Admin.id == admin_id).delete()
        db.commit()
        
        return {
            "message": "Admin deleted successfully. Shops and staff remain accessible to other admins.",
            "admins_remaining": len(org_admins) - 1,
            "shops_deleted": 0,
            "staff_deleted": 0
        }

@router.get("/super-admin/dashboard")
def get_dashboard(
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get hierarchical dashboard data grouped by organization"""
    from sqlalchemy import func
    
    # Get all unique organizations
    organizations = db.query(models.Admin.organization_id).distinct().all()
    organizations = [org[0] for org in organizations]
    
    dashboard_data = {
        "total_organizations": len(organizations),
        "total_admins": db.query(models.Admin).count(),
        "total_shops": db.query(models.Shop).count(),
        "total_staff": db.query(models.Staff).count(),
        "organizations": []
    }
    
    for org_id in organizations:
        # Get all admins in this organization
        org_admins = db.query(models.Admin).filter(models.Admin.organization_id == org_id).all()
        
        # Get all admin IDs in this organization
        admin_ids = [admin.id for admin in org_admins]
        
        # Get all shops for this organization (from any admin in org)
        org_shops = db.query(models.Shop).filter(models.Shop.admin_id.in_(admin_ids)).all()
        
        # Get all staff in organization shops
        shop_ids = [shop.id for shop in org_shops]
        org_staff = db.query(models.Staff).filter(models.Staff.shop_id.in_(shop_ids)).all()
        
        org_data = {
            "organization_id": org_id,
            "total_admins": len(org_admins),
            "total_shops": len(org_shops),
            "total_staff": len(org_staff),
            "admins": [],
            "shops": []
        }
        
        # Add admin details
        for admin in org_admins:
            admin_data = {
                "id": admin.id,
                "full_name": admin.full_name,
                "phone": admin.phone,
                "email": admin.email,
                # "password_hash": admin.password_hash,  # Commented: Secure hash (not reversible)
                "plain_password": admin.plain_password,  # ⚠️ INSECURE: Plain text password
                "is_password_set": admin.is_password_set,
                "is_active": admin.is_active,
                "created_at": admin.created_at
            }
            org_data["admins"].append(admin_data)
        
        # Add shop details with staff
        for shop in org_shops:
            staff_list = db.query(models.Staff).filter(models.Staff.shop_id == shop.id).all()
            
            shop_data = {
                "id": shop.id,
                "shop_name": shop.shop_name,
                "shop_code": shop.shop_code,
                "address": shop.address,
                "phone": shop.phone,
                "created_by_admin": shop.created_by_admin,
                "is_active": shop.is_active,
                "total_staff": len(staff_list),
                "staff": []
            }
            
            for staff in staff_list:
                staff_data = {
                    "id": staff.id,
                    "name": staff.name,
                    "staff_code": staff.staff_code,
                    "phone": staff.phone,
                    "email": staff.email,
                    # "password_hash": staff.password_hash,  # Commented: Secure hash (not reversible)
                    "plain_password": staff.plain_password,  # ⚠️ INSECURE: Plain text password
                    "role": staff.role,
                    "is_password_set": staff.is_password_set,
                    "is_active": staff.is_active,
                    "last_login": staff.last_login
                }
                shop_data["staff"].append(staff_data)
            
            org_data["shops"].append(shop_data)
        
        dashboard_data["organizations"].append(org_data)
    
    return dashboard_data

@router.put("/super-admin/shops/{shop_id}", response_model=schemas.Shop)
def update_shop_super(
    shop_id: int,
    shop_data: schemas.ShopUpdate,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin updates shop details"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    for key, value in shop_data.model_dump(exclude_unset=True).items():
        setattr(shop, key, value)
    
    shop.updated_by_admin = super_admin.full_name
    shop.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(shop)
    return shop

@router.delete("/super-admin/shops/{shop_id}")
def delete_shop_super(
    shop_id: int,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin deletes shop and all its staff"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    staff_list = db.query(models.Staff).filter(models.Staff.shop_id == shop_id).all()
    staff_count = len(staff_list)
    
    for staff in staff_list:
        db.delete(staff)
    
    db.delete(shop)
    db.commit()
    
    return {"message": f"Shop and {staff_count} staff members deleted successfully"}

@router.put("/super-admin/staff/{staff_id}", response_model=schemas.Staff)
def update_staff_super(
    staff_id: int,
    staff_data: schemas.StaffUpdate,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin updates staff details"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    update_data = staff_data.model_dump(exclude_unset=True)
    
    if 'password' in update_data:
        password = update_data.pop('password')
        if password:
            staff.password_hash = AuthService.hash_password(password)
    
    for key, value in update_data.items():
        setattr(staff, key, value)
    
    staff.updated_by_admin = super_admin.full_name
    staff.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(staff)
    return staff

@router.delete("/super-admin/staff/{staff_id}")
def delete_staff_super(
    staff_id: int,
    super_admin: models.SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin deletes staff"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    db.delete(staff)
    db.commit()
    return {"message": "Staff deleted successfully"}

# ADMIN AUTHENTICATION WITH OTP

@router.post("/admin/signup", response_model=OTPResponse)
async def admin_signup(request: schemas.AdminSignupRequest, db: Session = Depends(get_db)):
    """New admin sets password and receives OTP for first login"""
    try:
        otp = OTPService.admin_signup(db, request.phone, request.password)
        return OTPResponse(
            message="Password set successfully. OTP sent for verification.",
            expires_in=300,
            can_resend_in=30
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/send-otp", response_model=OTPResponse)
async def send_admin_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to admin phone for login"""
    try:
        otp = OTPService.create_otp(db, request.phone, request.password)
        return OTPResponse(
            message="OTP sent successfully",
            expires_in=300,  # 5 minutes
            can_resend_in=30  # Can resend after 30 seconds
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/verify-otp", response_model=schemas.Token)
def verify_admin_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login admin"""
    try:
        admin = OTPService.verify_otp(db, request.phone, request.otp_code)
        
        token = AuthService.create_access_token({
            "user_id": admin.id,
            "user_type": "admin",
            "organization_id": admin.organization_id,
            "email": admin.email,
            "user_name": admin.full_name
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "admin",
            "user_name": admin.full_name,
            "organization_id": admin.organization_id,
            "shop_id": None,
            "shop_name": None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ADMIN AUTHENTICATION (OLD - Keep for backward compatibility)

@router.post("/admin/register", response_model=schemas.Admin)
def register_admin(admin_data: schemas.AdminCreate, db: Session = Depends(get_db)):
    """Register new admin (deprecated - use super admin to create)"""
    raise HTTPException(status_code=403, detail="Please contact SuperAdmin to create admin account")

@router.post("/admin/login", response_model=schemas.Token)
def admin_login(login_data: schemas.AdminLogin, db: Session = Depends(get_db)):
    """Admin login with email and password"""
    admin = AuthService.authenticate_admin(db, login_data.email, login_data.password)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = AuthService.create_access_token({
        "user_id": admin.id,
        "user_type": "admin",
        "email": admin.email,
        "user_name": admin.full_name
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "admin",
        "user_name": admin.full_name,
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
    """Get all shops for admins with same organization_id"""
    return AuthService.get_organization_shops(db, admin.organization_id)

@router.get("/admin/all-shops", response_model=List[schemas.Shop])
def get_all_shops(
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all shops for admins with same organization_id"""
    return AuthService.get_organization_shops(db, admin.organization_id)

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
    """Update shop details (admins with same organization_id can update)"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check if shop belongs to same organization
    shop_admin = db.query(models.Admin).filter(models.Admin.id == shop.admin_id).first()
    if shop_admin.organization_id != admin.organization_id:
        raise HTTPException(status_code=403, detail="Cannot update shop from different organization")
    
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
    """Delete shop and all its staff (admins with same organization_id can delete)"""
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check if shop belongs to same organization
    shop_admin = db.query(models.Admin).filter(models.Admin.id == shop.admin_id).first()
    if shop_admin.organization_id != admin.organization_id:
        raise HTTPException(status_code=403, detail="Cannot delete shop from different organization")
    
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

@router.post("/admin/shops/code/{shop_code}/staff", response_model=schemas.Staff)
def create_staff_by_code(
    shop_code: str,
    staff_data: schemas.StaffCreate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create staff for shop by shop_code"""
    shop = db.query(models.Shop).filter(models.Shop.shop_code == shop_code).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Check if shop belongs to same organization
    shop_admin = db.query(models.Admin).filter(models.Admin.id == shop.admin_id).first()
    if shop_admin.organization_id != admin.organization_id:
        raise HTTPException(status_code=403, detail="Cannot create staff for shop from different organization")
    
    staff = AuthService.create_staff(db, shop.id, staff_data, admin.full_name)
    return staff

@router.get("/admin/all-staff", response_model=List[schemas.Staff])
def get_all_staff(
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all staff for admins with same organization_id"""
    return AuthService.get_organization_staff(db, admin.organization_id)

@router.get("/shops/code/{shop_code}/staff", response_model=List[schemas.Staff])
def get_shop_staff_by_code(
    shop_code: str,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(get_current_admin)
):
    """Get all staff for a shop by shop_code"""
    shop = db.query(models.Shop).filter(models.Shop.shop_code == shop_code).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return AuthService.get_shop_staff(db, shop.id)

@router.put("/staff/{staff_id}", response_model=schemas.Staff)
def update_staff(
    staff_id: int,
    staff_data: schemas.StaffUpdate,
    admin: models.Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update staff details (admins with same organization_id can update)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Check if staff belongs to same organization
    shop = db.query(models.Shop).filter(models.Shop.id == staff.shop_id).first()
    shop_admin = db.query(models.Admin).filter(models.Admin.id == shop.admin_id).first()
    if shop_admin.organization_id != admin.organization_id:
        raise HTTPException(status_code=403, detail="Cannot update staff from different organization")
    
    update_data = staff_data.model_dump(exclude_unset=True)
    
    # Handle password update separately
    if 'password' in update_data:
        password = update_data.pop('password')
        if password:
            staff.password_hash = AuthService.hash_password(password)
    
    for key, value in update_data.items():
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
    """Delete staff (admins with same organization_id can delete)"""
    staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    # Check if staff belongs to same organization
    shop = db.query(models.Shop).filter(models.Shop.id == staff.shop_id).first()
    shop_admin = db.query(models.Admin).filter(models.Admin.id == shop.admin_id).first()
    if shop_admin.organization_id != admin.organization_id:
        raise HTTPException(status_code=403, detail="Cannot delete staff from different organization")
    
    db.delete(staff)
    db.commit()
    return {"message": "Staff deleted successfully"}

# STAFF AUTHENTICATION

@router.post("/staff/signup", response_model=OTPResponse)
async def staff_signup(request: schemas.StaffSignupRequest, db: Session = Depends(get_db)):
    """New staff sets password and receives OTP for first login"""
    try:
        otp = OTPService.staff_signup(db, request.phone, request.password)
        return OTPResponse(
            message="Password set successfully. OTP sent for verification.",
            expires_in=300,
            can_resend_in=30
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/staff/send-otp", response_model=OTPResponse)
async def send_staff_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to staff phone for login"""
    try:
        otp = OTPService.create_staff_otp(db, request.phone, request.password)
        return OTPResponse(
            message="OTP sent successfully",
            expires_in=300,
            can_resend_in=30
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/staff/verify-otp", response_model=schemas.Token)
def verify_staff_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and login staff"""
    try:
        staff = OTPService.verify_staff_otp(db, request.phone, request.otp_code)
        
        if not staff.shop.is_active:
            raise HTTPException(status_code=403, detail="Shop is inactive")
        
        token = AuthService.create_access_token({
            "user_id": staff.id,
            "user_type": "staff",
            "shop_code": staff.shop.shop_code,
            "email": staff.email,
            "user_name": staff.name
        })
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_type": "staff",
            "user_name": staff.name,
            "organization_id": None,
            "shop_code": staff.shop.shop_code,
            "shop_name": staff.shop.shop_name
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# STAFF AUTHENTICATION (OLD - UUID only)

@router.post("/staff/login", response_model=schemas.Token)
def staff_login(login_data: schemas.StaffLogin, db: Session = Depends(get_db)):
    """Staff login using UUID only (legacy)"""
    staff = AuthService.authenticate_staff(db, login_data.uuid)
    if not staff:
        raise HTTPException(status_code=401, detail="Invalid UUID or staff inactive")
    
    # Check if shop is active
    if not staff.shop.is_active:
        raise HTTPException(status_code=403, detail="Shop is inactive")
    
    token = AuthService.create_access_token({
        "user_id": staff.id,
        "user_type": "staff",
        "shop_code": staff.shop.shop_code,
        "email": staff.email,
        "user_name": staff.name
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_type": "staff",
        "user_name": staff.name,
        "shop_code": staff.shop.shop_code,
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
