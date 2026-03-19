from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

# Association table for distributor-shop relationships
distributor_shops = Table(
    'distributor_shops',
    Base.metadata,
    Column('distributor_id', Integer, ForeignKey('distributors.id'), primary_key=True),
    Column('shop_id', Integer, ForeignKey('shops.id'), primary_key=True),
    Column('is_active', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.now)
)

class Distributor(Base):
    __tablename__ = "distributors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    company_name = Column(String, nullable=False)
    distributor_code = Column(String, unique=True, index=True, nullable=False)
    contact_person = Column(String, nullable=False)
    
    # Authentication
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_password_set = Column(Boolean, default=False)
    
    # Business details
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    gstin = Column(String, nullable=True)
    dl_number = Column(String, nullable=True)
    food_license = Column(String, nullable=True)
    
    # Bank details
    bank_name = Column(String, nullable=True)
    bank_account = Column(String, nullable=True)
    bank_ifsc = Column(String, nullable=True)
    bank_branch = Column(String, nullable=True)
    
    # Financial
    credit_limit = Column(Float, default=0.0)
    credit_days = Column(Integer, default=30)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Password reset fields
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # Audit fields
    created_by_super_admin = Column(String, nullable=False)  # SuperAdmin who created
    updated_by_super_admin = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships - can serve multiple shops across organizations
    shops = relationship("Shop", secondary=distributor_shops, back_populates="distributors")