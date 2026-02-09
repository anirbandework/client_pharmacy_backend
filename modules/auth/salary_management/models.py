from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime, date
from enum import Enum

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"

class SalaryRecord(Base):
    __tablename__ = "salary_records"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    salary_amount = Column(Float, nullable=False)
    payment_status = Column(String(20), default=PaymentStatus.PENDING.value)
    payment_date = Column(DateTime, nullable=True)
    paid_by_admin = Column(String(100), nullable=True)
    due_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = relationship("Staff", back_populates="salary_records")

class StaffPaymentInfo(Base):
    __tablename__ = "staff_payment_info"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), unique=True, nullable=False)
    upi_id = Column(String(100), nullable=True)
    qr_code_path = Column(String(255), nullable=True)
    bank_account = Column(String(50), nullable=True)
    ifsc_code = Column(String(20), nullable=True)
    account_holder_name = Column(String(100), nullable=True)
    preferred_payment_method = Column(String(20), default="upi")  # upi, bank
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    staff = relationship("Staff", back_populates="payment_info")

class SalaryAlert(Base):
    __tablename__ = "salary_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    salary_record_id = Column(Integer, ForeignKey("salary_records.id"), nullable=False)
    alert_type = Column(String(20), nullable=False)  # upcoming, overdue
    alert_date = Column(Date, nullable=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    staff = relationship("Staff")
    salary_record = relationship("SalaryRecord")