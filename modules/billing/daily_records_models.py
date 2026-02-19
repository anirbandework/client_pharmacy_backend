from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class DailyRecord(Base):
    __tablename__ = "daily_records"
    __table_args__ = (UniqueConstraint('shop_id', 'record_date', name='uq_daily_records_shop_date'),)
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, index=True)
    
    # Sales figures (auto-calculated from bills)
    no_of_bills = Column(Integer, default=0)
    software_sales = Column(Float, default=0.0)  # Total from bills
    cash_sales = Column(Float, default=0.0)  # From cash bills
    online_sales = Column(Float, default=0.0)  # From online bills
    
    # Manual entries
    unbilled_amount = Column(Float, default=0.0)  # Items sold without billing
    unbilled_notes = Column(Text, nullable=True)
    
    # Cash management
    actual_cash_deposited = Column(Float, default=0.0)  # 500, 200, 100 notes deposited
    cash_reserve = Column(Float, default=0.0)  # 10, 20, 50 notes and coins
    
    # Expenses
    total_expenses = Column(Float, default=0.0)
    
    # Staff info
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    staff_name = Column(String, nullable=True)
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    expenses = relationship("DailyExpense", back_populates="daily_record", cascade="all, delete-orphan")

class DailyExpense(Base):
    __tablename__ = "daily_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id"), nullable=False)
    
    expense_category = Column(String, nullable=False)  # rent, utilities, salary, supplies, etc.
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    # Staff who added the expense
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    staff_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    daily_record = relationship("DailyRecord", back_populates="expenses")
