from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime

class PurchaseInvoiceItemUpdate(BaseModel):
    id: Optional[int] = None
    composition: Optional[str] = None
    manufacturer: Optional[str] = None
    hsn_code: Optional[str] = None
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    quantity: float
    free_quantity: float = 0.0
    package: Optional[str] = None
    unit: Optional[str] = None
    manufacturing_date: Union[date, str, None] = None
    expiry_date: Union[date, str, None] = None
    mrp: Optional[str] = None
    unit_price: float
    selling_price: float = 0.0
    profit_margin: float = 0.0
    discount_on_purchase: float = 0.0
    discount_on_sales: float = 0.0
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    before_discount: float = 0.0
    taxable_amount: float
    cgst_percent: float = 0.0
    cgst_amount: float = 0.0
    sgst_percent: float = 0.0
    sgst_amount: float = 0.0
    igst_percent: float = 0.0
    igst_amount: float = 0.0
    total_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}
    
    @field_validator('manufacturing_date', 'expiry_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        if v == '' or v is None:
            return None
        return v

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
    
    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        if v == '' or v is None:
            return None
        return v

class PurchaseInvoiceItemResponse(BaseModel):
    id: int
    composition: Optional[str]
    manufacturer: Optional[str]
    hsn_code: Optional[str]
    product_name: Optional[str]
    batch_number: Optional[str]
    quantity: float
    free_quantity: float
    package: Optional[str]
    unit: Optional[str]
    manufacturing_date: Optional[date]
    expiry_date: Optional[date]
    mrp: Optional[str]
    unit_price: float
    selling_price: float
    profit_margin: float
    discount_on_purchase: float
    discount_on_sales: float
    discount_percent: float
    discount_amount: float
    before_discount: float
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
    is_staff_verified: bool = False
    staff_verified_by_name: Optional[str] = None
    staff_verified_at: Optional[datetime] = None
    is_admin_verified: bool = False
    admin_verified_by_name: Optional[str] = None
    admin_verified_at: Optional[datetime] = None
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
    is_staff_verified: bool = False
    staff_verified_by_name: Optional[str] = None
    is_admin_verified: bool = False
    admin_verified_by_name: Optional[str] = None
    staff_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
