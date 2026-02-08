from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

# Store Rack Schemas
class StoreRackBase(BaseModel):
    rack_number: str
    location: Optional[str] = None
    description: Optional[str] = None

class StoreRackCreate(StoreRackBase):
    pass

class StoreRack(StoreRackBase):
    id: int
    
    class Config:
        from_attributes = True

# Store Section Schemas
class StoreSectionBase(BaseModel):
    section_name: str
    section_code: str

class StoreSectionCreate(StoreSectionBase):
    rack_id: int

class StoreSection(StoreSectionBase):
    id: int
    rack_id: int
    
    class Config:
        from_attributes = True

# Stock Item Schemas
class StockItemBase(BaseModel):
    item_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    batch_number: str
    unit_price: Optional[float] = None
    expiry_date: Optional[date] = None
    manufacturer: Optional[str] = None

class StockItemCreate(StockItemBase):
    section_id: int
    quantity_software: int = 0

class StockItem(StockItemBase):
    id: int
    section_id: int
    quantity_software: int
    quantity_physical: Optional[int] = None
    last_audit_date: Optional[datetime] = None
    audit_discrepancy: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

# Purchase Schemas
class PurchaseBase(BaseModel):
    purchase_date: date
    supplier_name: str
    invoice_number: Optional[str] = None
    total_amount: float

class PurchaseCreate(PurchaseBase):
    recorded_by: Optional[str] = None

class Purchase(PurchaseBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PurchaseItemBase(BaseModel):
    quantity: int
    unit_cost: float
    total_cost: float

class PurchaseItemCreate(PurchaseItemBase):
    stock_item_id: int

class PurchaseItem(PurchaseItemBase):
    id: int
    purchase_id: int
    stock_item_id: int
    
    class Config:
        from_attributes = True

# Sale Schemas
class SaleBase(BaseModel):
    sale_date: date
    customer_phone: Optional[str] = None
    bill_number: Optional[str] = None
    total_amount: float

class SaleCreate(SaleBase):
    sold_by: Optional[str] = None

class Sale(SaleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class SaleItemBase(BaseModel):
    quantity: int
    unit_price: float
    total_price: float

class SaleItemCreate(SaleItemBase):
    stock_item_id: int

class SaleItem(SaleItemBase):
    id: int
    sale_id: int
    stock_item_id: int
    
    class Config:
        from_attributes = True

# Audit Schemas
class StockAuditRecordBase(BaseModel):
    audited_by: str
    physical_quantity: int
    notes: Optional[str] = None
    reason_for_discrepancy: Optional[str] = None

class StockAuditRecordCreate(StockAuditRecordBase):
    stock_item_id: int

class StockAuditRecord(StockAuditRecordBase):
    id: int
    stock_item_id: int
    audit_date: datetime
    software_quantity: int
    discrepancy: int
    resolved: bool = False
    
    class Config:
        from_attributes = True

class StockAuditSessionBase(BaseModel):
    auditor: str
    session_notes: Optional[str] = None

class StockAuditSessionCreate(StockAuditSessionBase):
    pass

class StockAuditSession(StockAuditSessionBase):
    id: int
    session_date: date
    sections_audited: int = 0
    items_audited: int = 0
    discrepancies_found: int = 0
    status: str
    started_at: datetime
    
    class Config:
        from_attributes = True

# Response Schemas
class RandomAuditSection(BaseModel):
    section: StoreSection
    items_to_audit: List[StockItem]
    total_items: int
    message: str

class StockDiscrepancy(BaseModel):
    item: StockItem
    software_qty: int
    physical_qty: int
    difference: int
    section_name: str
    rack_number: str

class StockSummary(BaseModel):
    total_items: int
    total_sections: int
    items_with_discrepancies: int
    last_audit_date: Optional[datetime]
    pending_audits: int

class PurchaseWithItems(BaseModel):
    purchase: Purchase
    items: List[PurchaseItem]

class SaleWithItems(BaseModel):
    sale: Sale
    items: List[SaleItem]