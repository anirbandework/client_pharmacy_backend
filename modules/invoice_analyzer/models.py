from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False, index=True)
    staff_name = Column(String, nullable=False)
    
    # Invoice details
    invoice_number = Column(String, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    
    # Supplier details
    supplier_name = Column(String, nullable=False)
    supplier_address = Column(Text, nullable=True)
    supplier_gstin = Column(String, nullable=True)
    supplier_dl_numbers = Column(Text, nullable=True)
    supplier_phone = Column(String, nullable=True)
    
    # Financial summary
    gross_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    taxable_amount = Column(Float, default=0.0)
    cgst_amount = Column(Float, default=0.0)
    sgst_amount = Column(Float, default=0.0)
    igst_amount = Column(Float, default=0.0)
    total_gst = Column(Float, default=0.0)
    round_off = Column(Float, default=0.0)
    net_amount = Column(Float, default=0.0)
    
    # PDF storage
    pdf_filename = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)
    
    # Extracted data (raw JSON from PDF)
    raw_extracted_data = Column(JSON, nullable=True)
    
    # Custom fields for shop-specific data
    custom_fields = Column(JSON, nullable=True, default={})
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("staff.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False, index=True)
    
    # Product identification
    composition = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    hsn_code = Column(String, nullable=True)
    product_name = Column(String, nullable=True)  # Changed to nullable
    batch_number = Column(String, nullable=True)
    
    # Quantities
    quantity = Column(Float, nullable=False)
    free_quantity = Column(Float, default=0.0)
    
    # Packaging
    package = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    
    # Dates
    manufacturing_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    
    # Pricing
    mrp = Column(String, nullable=True)
    unit_price = Column(Float, nullable=False)
    selling_price = Column(Float, default=0.0)
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
    
    # Custom fields for shop-specific item data
    custom_fields = Column(JSON, nullable=True, default={})
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    invoice = relationship("PurchaseInvoice", back_populates="items")
