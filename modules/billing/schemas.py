from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from .models import PaymentMethod

class BillItemCreate(BaseModel):
    stock_item_id: int
    quantity: int
    mrp: Optional[float] = None  # Maximum Retail Price
    unit_price: float  # Actual selling price
    discount_percent: float = 0.0
    tax_percent: float = 5.0  # Default 5% GST for medicines

class BillItemResponse(BaseModel):
    id: int
    stock_item_id: int
    item_name: str
    batch_number: str
    generic_name: Optional[str]
    brand_name: Optional[str]
    rack_number: Optional[str]
    section_name: Optional[str]
    quantity: int
    mrp: Optional[float]
    unit_price: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    sgst_percent: float
    cgst_percent: float
    sgst_amount: float
    cgst_amount: float
    tax_amount: float
    total_price: float
    
    class Config:
        from_attributes = True

class BillCreate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    doctor_name: Optional[str] = None
    customer_category: Optional[str] = None  # contact_sheet, first_time_prescription, regular_branded, generic_informed
    was_contacted_before: bool = False
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    discount_amount: float = 0.0
    amount_paid: float
    notes: Optional[str] = None
    prescription_required: Optional[str] = None
    items: List[BillItemCreate]
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item is required')
        return v

class BillResponse(BaseModel):
    id: int
    shop_id: int
    staff_id: int
    staff_name: str
    bill_number: str
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_email: Optional[str]
    doctor_name: Optional[str]
    payment_method: PaymentMethod
    payment_reference: Optional[str]
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    change_returned: float
    notes: Optional[str]
    prescription_required: Optional[str]
    created_at: datetime
    items: List[BillItemResponse]
    
    class Config:
        from_attributes = True

class MedicineSearchResult(BaseModel):
    id: int
    item_name: str
    generic_name: Optional[str]
    brand_name: Optional[str]
    batch_number: str
    quantity_available: int
    unit_price: Optional[float]
    rack_number: Optional[str]
    section_name: Optional[str]
    expiry_date: Optional[str]
    manufacturer: Optional[str]

class BillSummary(BaseModel):
    total_bills: int
    total_revenue: float
    cash_sales: float
    online_sales: float
    average_bill_value: float
