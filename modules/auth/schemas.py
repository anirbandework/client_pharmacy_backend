from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date

# SuperAdmin Schemas
class SuperAdminCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class SuperAdminLogin(BaseModel):
    email: EmailStr
    password: str

class SuperAdmin(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Admin Schemas
class AdminCreate(BaseModel):
    organization_id: str  # Shared ID for multiple admins
    phone: str
    password: str
    full_name: str
    email: Optional[EmailStr] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        # Normalize phone number
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        
        # Add country code if not present
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        
        # Add + prefix and validate
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class Admin(BaseModel):
    id: int
    organization_id: str
    email: Optional[str]
    full_name: str
    phone: str
    is_active: bool
    created_by_super_admin: str
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
    created_by_admin: str
    updated_by_admin: Optional[str]
    updated_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Staff Schemas
class StaffCreate(BaseModel):
    name: str  # Changed from full_name
    staff_code: str  # Added staff_code
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "staff"
    monthly_salary: Optional[float] = None  # Added salary field
    joining_date: Optional[date] = None  # Added joining date
    salary_eligibility_days: int = 30  # Days after joining to be eligible for salary
    can_manage_staff: bool = False
    can_view_analytics: bool = True
    can_manage_inventory: bool = True
    can_manage_customers: bool = True

class StaffUpdate(BaseModel):
    name: Optional[str] = None  # Changed from full_name
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    monthly_salary: Optional[float] = None  # Added salary field
    joining_date: Optional[date] = None  # Added joining date
    salary_eligibility_days: Optional[int] = None  # Days after joining to be eligible for salary
    can_manage_staff: Optional[bool] = None
    can_view_analytics: Optional[bool] = None
    can_manage_inventory: Optional[bool] = None
    can_manage_customers: Optional[bool] = None
    is_active: Optional[bool] = None

class Staff(BaseModel):
    id: int
    shop_id: int
    uuid: str
    name: str  # Changed from full_name
    staff_code: str  # Added staff_code
    phone: Optional[str]
    email: Optional[str]
    role: str
    monthly_salary: Optional[float]  # Added salary field
    joining_date: Optional[date]  # Added joining date
    salary_eligibility_days: int  # Days after joining to be eligible for salary
    can_manage_staff: bool
    can_view_analytics: bool
    can_manage_inventory: bool
    can_manage_customers: bool
    created_by_admin: str
    updated_by_admin: Optional[str]
    updated_at: Optional[datetime]
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
    user_type: str  # super_admin, admin, staff
    organization_id: Optional[str] = None  # For admins
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None

class TokenData(BaseModel):
    user_id: int
    user_type: str  # super_admin, admin, staff
    organization_id: Optional[str] = None  # For admins
    shop_id: Optional[int] = None
    email: Optional[str] = None
    user_name: Optional[str] = None
