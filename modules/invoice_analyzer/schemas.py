from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class PurchaseInvoiceItemUpdate(BaseModel):
    id: Optional[int] = None
    manufacturer: Optional[str] = None
    hsn_code: Optional[str] = None
    product_name: str
    batch_number: Optional[str] = None
    quantity: float
    package: Optional[str] = None
    expiry_date: Optional[date] = None
    mrp: Optional[str] = None
    quantity: float
    free_quantity: float = 0.0
    unit_price: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    taxable_amount: float
    cgst_percent: float = 0.0
    cgst_amount: float = 0.0
    sgst_percent: float = 0.0
    sgst_amount: float = 0.0
    igst_percent: float = 0.0
    igst_amount: float = 0.0
    total_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}

class PurchaseInvoiceUpdate(BaseModel):
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    supplier_name: str
    supplier_address: Optional[str] = None
    supplier_gstin: Optional[str] = None
    supplier_dl_numbers: Optional[str] = None
    supplier_phone: Optional[str] = None
    gross_amount: float
    discount_amount: float = 0.0
    taxable_amount: float
    total_gst: float
    round_off: float = 0.0
    net_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}
    items: List[PurchaseInvoiceItemUpdate]

class PurchaseInvoiceItemResponse(BaseModel):
    id: int
    manufacturer: Optional[str]
    hsn_code: Optional[str]
    product_name: str
    batch_number: Optional[str]
    quantity: float
    package: Optional[str]
    expiry_date: Optional[date]
    mrp: Optional[str]
    free_quantity: float
    unit_price: float
    discount_percent: float
    discount_amount: float
    taxable_amount: float
    cgst_percent: float
    cgst_amount: float
    sgst_percent: float
    sgst_amount: float
    igst_percent: float
    igst_amount: float
    total_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}
    
    class Config:
        from_attributes = True

class PurchaseInvoiceResponse(BaseModel):
    id: int
    shop_id: int
    staff_id: int
    staff_name: str
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    supplier_name: str
    supplier_address: Optional[str]
    supplier_gstin: Optional[str]
    supplier_dl_numbers: Optional[str]
    supplier_phone: Optional[str]
    gross_amount: float
    discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_gst: float
    round_off: float
    net_amount: float
    pdf_filename: Optional[str]
    custom_fields: Optional[Dict[str, Any]] = {}
    is_verified: bool = False
    verified_by_name: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    items: List[PurchaseInvoiceItemResponse]
    
    class Config:
        from_attributes = True

class PurchaseInvoiceListResponse(BaseModel):
    id: int
    invoice_number: str
    invoice_date: date
    supplier_name: str
    net_amount: float
    total_items: int
    is_verified: bool = False
    verified_by_name: Optional[str] = None
    staff_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
