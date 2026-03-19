from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime

class DistributorCreate(BaseModel):
    company_name: str
    distributor_code: str
    contact_person: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    dl_number: Optional[str] = None
    credit_limit: float = 0.0
    credit_days: int = 30
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class DistributorUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    dl_number: Optional[str] = None
    food_license: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    credit_limit: Optional[float] = None
    credit_days: Optional[int] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            import re
            phone = re.sub(r'[^\d+]', '', v)
            phone = phone.replace('+', '')
            if not phone.startswith('91') and len(phone) == 10:
                phone = '91' + phone
            phone = '+' + phone
            if not re.match(r'^\+91\d{10}$', phone):
                raise ValueError('Invalid Indian phone number')
            return phone
        return v

class DistributorOTPRequest(BaseModel):
    phone: str
    password: Optional[str] = None
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class DistributorOTPVerify(BaseModel):
    phone: str
    otp: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class DistributorLogin(BaseModel):
    email: EmailStr
    password: str

class DistributorSignupRequest(BaseModel):
    phone: str
    password: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class ShopBasic(BaseModel):
    id: int
    shop_name: str
    shop_code: str
    organization_id: str
    
    class Config:
        from_attributes = True

class DistributorPasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

# Password Reset Schemas for Distributor
class DistributorPasswordResetRequest(BaseModel):
    phone: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class DistributorPasswordResetVerifyOTP(BaseModel):
    phone: str
    otp: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        import re
        phone = re.sub(r'[^\d+]', '', v)
        phone = phone.replace('+', '')
        if not phone.startswith('91') and len(phone) == 10:
            phone = '91' + phone
        phone = '+' + phone
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class DistributorPasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v

class Distributor(BaseModel):
    id: int
    company_name: str
    distributor_code: str
    contact_person: str
    email: Optional[str]
    phone: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    gstin: Optional[str]
    dl_number: Optional[str]
    food_license: Optional[str]
    bank_name: Optional[str]
    bank_account: Optional[str]
    bank_ifsc: Optional[str]
    bank_branch: Optional[str]
    credit_limit: float
    credit_days: int
    is_active: bool
    is_verified: bool
    is_password_set: bool
    created_by_super_admin: str
    updated_by_super_admin: Optional[str]
    updated_at: Optional[datetime]
    created_at: datetime
    last_login: Optional[datetime]
    shops: List[ShopBasic] = []  # Assigned shops
    
    class Config:
        from_attributes = True