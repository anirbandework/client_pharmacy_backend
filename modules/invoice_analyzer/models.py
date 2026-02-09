from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.database.database import Base

class PurchaseInvoice(Base):
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, nullable=True, index=True)
    
    # Invoice details
    invoice_number = Column(String, unique=True, index=True, nullable=False)
    supplier_name = Column(String, nullable=False)
    invoice_date = Column(Date, nullable=False, index=True)
    received_date = Column(Date, nullable=False, index=True)
    
    # Financial details
    total_amount = Column(Float, nullable=False)
    total_items = Column(Integer, nullable=False)
    total_quantity = Column(Float, nullable=False)
    
    # Status tracking
    sold_percentage = Column(Float, default=0.0)  # 0-100
    status = Column(String, default="received")  # received, partial, sold_out, expired
    color_code = Column(String, default="red")  # red, yellow, green
    
    # Expiry tracking
    has_expiring_items = Column(Boolean, default=False)
    nearest_expiry_days = Column(Integer, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("PurchaseInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    sales = relationship("ItemSale", back_populates="purchase_invoice")

class PurchaseInvoiceItem(Base):
    __tablename__ = "purchase_invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id", ondelete="CASCADE"))
    
    # Item details
    item_code = Column(String, nullable=False, index=True)
    item_name = Column(String, nullable=False)
    batch_number = Column(String, nullable=True)
    
    # Quantities
    purchased_quantity = Column(Float, nullable=False)
    sold_quantity = Column(Float, default=0.0)
    remaining_quantity = Column(Float, nullable=False)
    
    # Pricing
    unit_cost = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    # Expiry tracking
    expiry_date = Column(Date, nullable=True)
    days_to_expiry = Column(Integer, nullable=True)
    is_expiring_soon = Column(Boolean, default=False)  # Within 45 days
    is_expiring_critical = Column(Boolean, default=False)  # Within 1 year on receipt
    
    # Movement tracking (for AI)
    movement_rate = Column(Float, default=0.0)  # Items sold per day
    seasonal_factor = Column(Float, default=1.0)
    demand_category = Column(String, default="unknown")  # fast, medium, slow, dead
    
    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="items")
    sales = relationship("ItemSale", back_populates="item")

class ItemSale(Base):
    __tablename__ = "item_sales"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"))
    item_id = Column(Integer, ForeignKey("purchase_invoice_items.id"))
    
    # Sale details
    sale_date = Column(Date, nullable=False, index=True)
    quantity_sold = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    profit_margin = Column(Float, nullable=False)
    
    # Customer info (optional)
    customer_type = Column(String, nullable=True)  # regular, walk-in, insurance
    
    # Relationships
    purchase_invoice = relationship("PurchaseInvoice", back_populates="sales")
    item = relationship("PurchaseInvoiceItem", back_populates="sales")

class ExpiryAlert(Base):
    __tablename__ = "expiry_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("purchase_invoice_items.id"))
    
    # Alert details
    alert_type = Column(String, nullable=False)  # "45_days", "1_year", "expired"
    alert_date = Column(Date, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String, nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    
    # Message
    message = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # low, medium, high, critical

class MonthlyInvoiceSummary(Base):
    __tablename__ = "monthly_invoice_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, nullable=True, index=True)
    
    # Period
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    # Summary stats
    total_invoices = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    total_items = Column(Integer, default=0)
    
    # Status breakdown
    green_invoices = Column(Integer, default=0)  # Fully sold
    yellow_invoices = Column(Integer, default=0)  # Partially sold
    red_invoices = Column(Integer, default=0)  # Not sold/slow moving
    
    # Overall status
    month_color = Column(String, default="red")
    overall_sold_percentage = Column(Float, default=0.0)
    
    # Expiry tracking
    expiring_items_count = Column(Integer, default=0)
    expired_items_count = Column(Integer, default=0)
    
    # AI insights
    ai_insights = Column(Text, nullable=True)
    movement_prediction = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)