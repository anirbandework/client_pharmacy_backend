from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class DailyRecord(Base):
    __tablename__ = "daily_records"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Basic info (Columns A-B)
    date = Column(Date, index=True)
    day = Column(String)
    
    # Cash management (Column C)
    cash_balance = Column(Float)
    
    # Sales metrics (Columns D-E)
    average_bill = Column(Float, nullable=True)
    no_of_bills = Column(Integer, nullable=True)
    
    # Cash transactions (Columns F-G)
    total_cash = Column(Float, nullable=True)  # Calculated field
    actual_cash = Column(Float, nullable=True)
    
    # Online sales (Column H)
    online_sales = Column(Float, nullable=True)
    
    # Total sales (Column I)
    total_sales = Column(Float, nullable=True)  # Calculated field
    
    # Sales breakdown (Columns J-L)
    unbilled_sales = Column(Float, nullable=True)
    software_figure = Column(Float, nullable=True)
    recorded_sales = Column(Float, nullable=True)  # Calculated field
    
    # Difference tracking (Column M)
    sales_difference = Column(Float, nullable=True)  # Calculated field
    
    # Cash reserve (Columns N-O)
    cash_reserve = Column(Float, nullable=True)
    reserve_comments = Column(Text, nullable=True)
    
    # Expenses (Column Q)
    expense_amount = Column(Float, nullable=True)
    
    # Additional tracking
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String, nullable=True)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    modified_by = Column(String, nullable=True)
    
    modifications = relationship("RecordModification", back_populates="daily_record", cascade="all, delete-orphan")
    
    # Unique constraint per shop per date
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

class RecordModification(Base):
    __tablename__ = "record_modifications"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    daily_record_id = Column(Integer, ForeignKey("daily_records.id", ondelete="CASCADE"), index=True)
    field_name = Column(String, nullable=False)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    modified_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    modified_by = Column(String, nullable=True)
    action = Column(String, default="update")  # update, create, delete
    
    daily_record = relationship("DailyRecord", back_populates="modifications")