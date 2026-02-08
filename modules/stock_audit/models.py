from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class StockRack(Base):
    __tablename__ = "stock_racks"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    rack_number = Column(String, unique=True, index=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    
    sections = relationship("StockSection", back_populates="rack")

class StockSection(Base):
    __tablename__ = "stock_sections_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    rack_id = Column(Integer, ForeignKey("stock_racks.id"))
    section_name = Column(String, nullable=False)
    section_code = Column(String, unique=True, index=True)
    
    rack = relationship("StockRack", back_populates="sections")
    items = relationship("StockItem", back_populates="section")

class StockItem(Base):
    __tablename__ = "stock_items_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    section_id = Column(Integer, ForeignKey("stock_sections_audit.id"))
    
    item_name = Column(String, nullable=False, index=True)
    generic_name = Column(String, nullable=True)
    brand_name = Column(String, nullable=True)
    batch_number = Column(String, nullable=False, index=True)
    
    quantity_software = Column(Integer, default=0)
    quantity_physical = Column(Integer, nullable=True)
    
    unit_price = Column(Float, nullable=True)
    expiry_date = Column(Date, nullable=True)
    manufacturer = Column(String, nullable=True)
    
    last_audit_date = Column(DateTime, nullable=True)
    last_audit_by = Column(String, nullable=True)
    audit_discrepancy = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    section = relationship("StockSection", back_populates="items")
    purchase_items = relationship("PurchaseItem", back_populates="stock_item")
    sale_items = relationship("SaleItem", back_populates="stock_item")
    audit_records = relationship("StockAuditRecord", back_populates="stock_item")

class Purchase(Base):
    __tablename__ = "purchases_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    purchase_date = Column(Date, nullable=False)
    supplier_name = Column(String, nullable=False)
    invoice_number = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    recorded_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("PurchaseItem", back_populates="purchase")

class PurchaseItem(Base):
    __tablename__ = "purchase_items_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases_audit.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items_audit.id"))
    
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    
    purchase = relationship("Purchase", back_populates="items")
    stock_item = relationship("StockItem", back_populates="purchase_items")

class Sale(Base):
    __tablename__ = "sales_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    sale_date = Column(Date, nullable=False)
    customer_phone = Column(String, nullable=True)
    bill_number = Column(String, nullable=True)
    total_amount = Column(Float, nullable=False)
    sold_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    items = relationship("SaleItem", back_populates="sale")

class SaleItem(Base):
    __tablename__ = "sale_items_audit"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales_audit.id"))
    stock_item_id = Column(Integer, ForeignKey("stock_items_audit.id"))
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    sale = relationship("Sale", back_populates="items")
    stock_item = relationship("StockItem", back_populates="sale_items")

class StockAuditRecord(Base):
    __tablename__ = "stock_audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    stock_item_id = Column(Integer, ForeignKey("stock_items_audit.id"))
    
    audit_date = Column(DateTime, default=datetime.utcnow)
    audited_by = Column(String, nullable=False)
    
    software_quantity = Column(Integer, nullable=False)
    physical_quantity = Column(Integer, nullable=False)
    discrepancy = Column(Integer, nullable=False)
    
    notes = Column(Text, nullable=True)
    reason_for_discrepancy = Column(String, nullable=True)
    
    resolved = Column(Boolean, default=False)
    resolved_date = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    stock_item = relationship("StockItem", back_populates="audit_records")

class StockAuditSession(Base):
    __tablename__ = "stock_audit_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    session_date = Column(Date, default=datetime.utcnow().date)
    auditor = Column(String, nullable=False)
    
    sections_audited = Column(Integer, default=0)
    items_audited = Column(Integer, default=0)
    discrepancies_found = Column(Integer, default=0)
    
    status = Column(String, default="in_progress")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    session_notes = Column(Text, nullable=True)