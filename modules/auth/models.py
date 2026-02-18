from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
import uuid

class SuperAdmin(Base):
    __tablename__ = "super_admins"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String(15), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, index=True, nullable=False)  # Shared ID for multiple admins
    email = Column(String, unique=True, index=True, nullable=True)  # Optional now
    password_hash = Column(String, nullable=True)  # Nullable - set during signup
    plain_password = Column(String, nullable=True)  # ⚠️ SECURITY RISK: Plain text password for SuperAdmin visibility
    full_name = Column(String, nullable=False)
    phone = Column(String(15), unique=True, index=True, nullable=False)  # Required for OTP
    is_active = Column(Boolean, default=True)
    is_password_set = Column(Boolean, default=False)  # Track if user completed signup
    created_by_super_admin = Column(String, nullable=False)  # SuperAdmin name who created
    created_at = Column(DateTime, default=datetime.utcnow)
    
    shops = relationship("Shop", back_populates="admin")

class Shop(Base):
    __tablename__ = "shops"
    __table_args__ = (
        UniqueConstraint('shop_code', 'admin_id', name='unique_shop_code_per_admin'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    
    shop_name = Column(String, nullable=False)
    shop_code = Column(String, index=True, nullable=False)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    
    # Business details
    license_number = Column(String, nullable=True)
    gst_number = Column(String, nullable=True)
    
    # Audit fields
    created_by_admin = Column(String, nullable=False)  # Admin name who created
    updated_by_admin = Column(String, nullable=True)   # Admin name who last updated
    updated_at = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    admin = relationship("Admin", back_populates="shops")
    staff = relationship("Staff", back_populates="shop", cascade="all, delete-orphan")
    stock_racks = relationship("StockRack", cascade="all, delete-orphan")
    stock_sections = relationship("StockSection", cascade="all, delete-orphan")
    stock_items = relationship("StockItem", cascade="all, delete-orphan")
    purchases = relationship("Purchase", cascade="all, delete-orphan")
    purchase_items = relationship("PurchaseItem", cascade="all, delete-orphan")
    sales = relationship("Sale", cascade="all, delete-orphan")
    sale_items = relationship("SaleItem", cascade="all, delete-orphan")
    audit_records = relationship("StockAuditRecord", cascade="all, delete-orphan")
    audit_sessions = relationship("StockAuditSession", cascade="all, delete-orphan")
    stock_adjustments = relationship("StockAdjustment", cascade="all, delete-orphan")

class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    uuid = Column(String, unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)  # Changed from full_name to name
    staff_code = Column(String, unique=True, index=True, nullable=False)  # Added staff_code
    phone = Column(String, unique=True, index=True, nullable=False)  # Required for OTP login
    password_hash = Column(String, nullable=True)  # Nullable - set during signup
    plain_password = Column(String, nullable=True)  # ⚠️ SECURITY RISK: Plain text password for SuperAdmin visibility
    email = Column(String, nullable=True)
    
    role = Column(String, default="staff")  # staff, shop_manager
    
    # Salary information
    monthly_salary = Column(Float, nullable=True)
    joining_date = Column(Date, nullable=True)
    salary_eligibility_days = Column(Integer, default=30)  # Days after joining to be eligible for salary
    
    # Permissions
    can_manage_staff = Column(Boolean, default=False)
    can_view_analytics = Column(Boolean, default=True)
    can_manage_inventory = Column(Boolean, default=True)
    can_manage_customers = Column(Boolean, default=True)
    
    is_password_set = Column(Boolean, default=False)  # Track if user completed signup
    
    # Audit fields
    created_by_admin = Column(String, nullable=False)  # Admin name who created
    updated_by_admin = Column(String, nullable=True)   # Admin name who last updated
    updated_at = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    shop = relationship("Shop", back_populates="staff")
    salary_records = relationship("SalaryRecord", back_populates="staff", cascade="all, delete-orphan")
    payment_info = relationship("StaffPaymentInfo", back_populates="staff", uselist=False, cascade="all, delete-orphan")
    devices = relationship("StaffDevice", foreign_keys="[StaffDevice.staff_id]", back_populates="staff", cascade="all, delete-orphan")
    attendance_records = relationship("AttendanceRecord", foreign_keys="[AttendanceRecord.staff_id]", back_populates="staff", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", foreign_keys="[LeaveRequest.staff_id]", back_populates="staff", cascade="all, delete-orphan")
