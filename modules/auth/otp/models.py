from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database.database import Base

class OTPVerification(Base):
    """OTP verification for admin login"""
    __tablename__ = "otp_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), index=True, nullable=False)
    otp_code = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
