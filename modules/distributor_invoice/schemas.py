from pydantic import BaseModel, ConfigDict, field_validator
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime

class DistributorBasic(BaseModel):
    company_name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: Optional[str] = None
    dl_number: Optional[str] = None
    food_license: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    bank_branch: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ShopBasic(BaseModel):
    shop_name: str
    shop_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    dl_number_1: Optional[str] = None
    dl_number_2: Optional[str] = None
    food_license: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class DistributorInvoiceItemCreate(BaseModel):
    composition: Optional[str] = None
    product_name: str
    batch_number: str
    manufacturer: Optional[str] = None
    hsn_code: str
    quantity: float
    free_quantity: float = 0.0
    unit: str
    package: Optional[str] = None
    manufacturing_date: Union[date, str, None] = None
    expiry_date: Union[date, str]
    mrp: str
    unit_price: float
    selling_price: float
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
    def validate_dates(cls, v, info):
        if v == '' or v is None:
            if info.field_name == 'expiry_date':
                raise ValueError('Expiry date is required')
            return None
        return v

class DistributorInvoiceCreate(BaseModel):
    shop_id: Optional[int] = None
    external_shop_name: Optional[str] = None
    external_shop_phone: Optional[str] = None
    external_shop_address: Optional[str] = None
    external_shop_license: Optional[str] = None
    external_shop_gst: Optional[str] = None
    external_shop_food_license: Optional[str] = None
    invoice_date: date
    due_date: Optional[date] = None
    gross_amount: float
    discount_amount: float = 0.0
    taxable_amount: float
    cgst_amount: float = 0.0
    sgst_amount: float = 0.0
    igst_amount: float = 0.0
    total_gst: float
    round_off: float = 0.0
    net_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}
    items: List[DistributorInvoiceItemCreate]
    
    @field_validator('due_date', mode='before')
    @classmethod
    def validate_due_date(cls, v):
        if v == '' or v is None:
            return None
        return v

class DistributorInvoiceItemResponse(BaseModel):
    id: int
    composition: Optional[str]
    product_name: Optional[str]
    batch_number: Optional[str]
    manufacturer: Optional[str]
    hsn_code: Optional[str]
    quantity: float
    free_quantity: float
    unit: str
    package: Optional[str]
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
    
    model_config = ConfigDict(from_attributes=True)

class DistributorInvoiceResponse(BaseModel):
    id: int
    distributor_id: int
    shop_id: Optional[int]
    external_shop_name: Optional[str] = None
    external_shop_phone: Optional[str] = None
    external_shop_address: Optional[str] = None
    external_shop_license: Optional[str] = None
    external_shop_gst: Optional[str] = None
    external_shop_food_license: Optional[str] = None
    invoice_number: str
    invoice_date: date
    due_date: Optional[date]
    gross_amount: float
    discount_amount: float
    taxable_amount: float
    cgst_amount: float
    sgst_amount: float
    igst_amount: float
    total_gst: float
    round_off: float
    net_amount: float
    custom_fields: Optional[Dict[str, Any]] = {}
    is_staff_verified: bool
    staff_verified_at: Optional[datetime]
    is_admin_verified: bool
    admin_verified_at: Optional[datetime]
    is_rejected: bool
    rejection_reason: Optional[str]
    created_at: datetime
    items: List[DistributorInvoiceItemResponse]
    distributor: Optional[DistributorBasic] = None
    shop: Optional[ShopBasic] = None
    
    model_config = ConfigDict(from_attributes=True)
