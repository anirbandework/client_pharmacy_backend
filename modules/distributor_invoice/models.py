from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class DistributorInvoice(Base):
    __tablename__ = "distributor_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    distributor_id = Column(Integer, ForeignKey("distributors.id"), nullable=False, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)  # Nullable for external shops
    
    # External shop details (for non-registered shops)
    external_shop_name = Column(String, nullable=True)
    external_shop_phone = Column(String, nullable=True)
    external_shop_address = Column(Text, nullable=True)
    external_shop_license = Column(String, nullable=True)
    external_shop_gst = Column(String, nullable=True)
    external_shop_food_license = Column(String, nullable=True)
    
    invoice_number = Column(String, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    
    gross_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    taxable_amount = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_gst = Column(Float, default=0.0)
    round_off = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    
    # Custom fields for distributor-specific data
    custom_fields = Column(JSON, nullable=True, default={})
    
    is_staff_verified = Column(Boolean, default=False)
    staff_verified_by = Column(Integer, ForeignKey("staff.id"), nullable=True)
    staff_verified_at = Column(DateTime, nullable=True)
    
    is_admin_verified = Column(Boolean, default=False)
    admin_verified_by = Column(Integer, ForeignKey("admins.id"), nullable=True)
    admin_verified_at = Column(DateTime, nullable=True)
    
    is_rejected = Column(Boolean, default=False)
    rejected_by = Column(Integer, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    items = relationship("DistributorInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class DistributorInvoiceItem(Base):
    __tablename__ = "distributor_invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("distributor_invoices.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    
    # Product identification
    composition = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    hsn_code = Column(String, nullable=True)
    
    # Quantities
    quantity = Column(Float, nullable=False)
    free_quantity = Column(Float, default=0.0)
    unit = Column(String, nullable=False)
    
    # Packaging
    package = Column(String, nullable=True)
    
    # Dates
    manufacturing_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    
    # Pricing
    mrp = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    profit_margin = Column(Float, default=0.0)
    
    # Discounts
    discount_on_purchase = Column(Float, default=0.0)
    discount_on_sales = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    before_discount = Column(Float, default=0.0)
    
    # Tax
    taxable_amount = Column(Float, nullable=False)
    cgst_percent = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_percent = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_percent = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Custom fields for distributor-specific item data
    custom_fields = Column(JSON, nullable=True, default={})
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    invoice = relationship("DistributorInvoice", back_populates="items")
