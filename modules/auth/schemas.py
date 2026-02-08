from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Admin Schemas
class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class Admin(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Shop Schemas
class ShopCreate(BaseModel):
    shop_name: str
    shop_code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    gst_number: Optional[str] = None

class ShopUpdate(BaseModel):
    shop_name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    license_number: Optional[str] = None
    gst_number: Optional[str] = None
    is_active: Optional[bool] = None

class Shop(BaseModel):
    id: int
    admin_id: int
    shop_name: str
    shop_code: str
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    license_number: Optional[str]
    gst_number: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Staff Schemas
class StaffCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "staff"
    can_manage_staff: bool = False
    can_view_analytics: bool = True
    can_manage_inventory: bool = True
    can_manage_customers: bool = True

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    can_manage_staff: Optional[bool] = None
    can_view_analytics: Optional[bool] = None
    can_manage_inventory: Optional[bool] = None
    can_manage_customers: Optional[bool] = None
    is_active: Optional[bool] = None

class Staff(BaseModel):
    id: int
    shop_id: int
    uuid: str
    full_name: str
    phone: Optional[str]
    email: Optional[str]
    role: str
    can_manage_staff: bool
    can_view_analytics: bool
    can_manage_inventory: bool
    can_manage_customers: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class StaffLogin(BaseModel):
    uuid: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user_type: str  # admin, staff
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None

class TokenData(BaseModel):
    user_id: int
    user_type: str  # admin, staff
    shop_id: Optional[int] = None
    email: Optional[str] = None
