from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
import enum

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    ONLINE = "online"

class Bill(Base):
    __tablename__ = "bills"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    staff_name = Column(String, nullable=False)
    
    bill_number = Column(String, unique=True, index=True, nullable=False)
    
    # Customer details
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True, index=True)
    customer_email = Column(String, nullable=True)
    doctor_name = Column(String, nullable=True)
    
    # Customer tracking
    customer_category = Column(String, nullable=True)  # contact_sheet, first_time_prescription, regular_branded, generic_informed
    was_contacted_before = Column(Boolean, default=False)  # Did staff contact them before?
    visited_but_no_purchase = Column(Boolean, default=False)  # Mark as yellow
    
    # Payment details
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_reference = Column(String, nullable=True)  # Transaction ID for online/UPI
    
    # Amounts
    subtotal = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False)
    change_returned = Column(Float, default=0.0)
    
    # Additional info
    notes = Column(Text, nullable=True)
    prescription_required = Column(String, nullable=True)  # Yes/No/Partial
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    items = relationship("BillItem", back_populates="bill", cascade="all, delete-orphan")

class BillItem(Base):
    __tablename__ = "bill_items"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    stock_item_id = Column(Integer, ForeignKey("stock_items_audit.id"), nullable=False)
    
    # Item details (snapshot at time of sale)
    item_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=False)
    generic_name = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    
    # Location info
    rack_number = Column(String, nullable=True)
    section_name = Column(String, nullable=True)
    
    # Pricing
    quantity = Column(Integer, nullable=False)
    mrp = Column(Float, nullable=True)  # Maximum Retail Price
    unit_price = Column(Float, nullable=False)  # Actual selling price
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_percent = Column(Float, default=0.0)
    sgst_percent = Column(Float, default=0.0)  # State GST %
    cgst_percent = Column(Float, default=0.0)  # Central GST %
    sgst_amount = Column(Float, default=0.0)   # State GST amount
    cgst_amount = Column(Float, default=0.0)   # Central GST amount
    tax_amount = Column(Float, default=0.0)    # Total tax (SGST + CGST)
    total_price = Column(Float, nullable=False)
    
    bill = relationship("Bill", back_populates="items")
