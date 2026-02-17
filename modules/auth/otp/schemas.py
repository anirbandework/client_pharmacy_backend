from pydantic import BaseModel, field_validator
import re

def normalize_phone(phone: str) -> str:
    """Normalize phone number to +91XXXXXXXXXX format"""
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # Remove + if present
    phone = phone.replace('+', '')
    
    # Add country code if not present
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    # Add + prefix
    return '+' + phone

class SendOTPRequest(BaseModel):
    phone: str
    password: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        phone = normalize_phone(v)
        if not re.match(r'^\+91\d{10}$', phone):
            raise ValueError('Invalid Indian phone number')
        return phone

class VerifyOTPRequest(BaseModel):
    phone: str
    otp_code: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        return normalize_phone(v)
    
    @field_validator('otp_code')
    @classmethod
    def validate_otp(cls, v):
        if not v.isdigit() or len(v) != 6:
            raise ValueError('OTP must be 6 digits')
        return v

class OTPResponse(BaseModel):
    message: str
    expires_in: int  # seconds
    can_resend_in: int = 30  # seconds until can resend
