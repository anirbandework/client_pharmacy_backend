from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime, date

# Admin Schemas
class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

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
    user_type: str  # admin, staff
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None

class TokenData(BaseModel):
    user_id: int
    user_type: str  # admin, staff
    shop_id: Optional[int] = None
    email: Optional[str] = None
