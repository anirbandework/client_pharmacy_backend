from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from .models import PaymentMethod
from typing import Dict, Any

class BillItemCreate(BaseModel):
    stock_item_id: int
    quantity: int                      # in strips OR tablets depending on sale_unit
    mrp: Optional[str] = None         # Maximum Retail Price (e.g., "69.00/STRIP")
    unit_price: float                  # selling price per strip or per tablet
    discount_percent: float = 0.0
    tax_percent: float = 5.0          # Default 5% GST for medicines
    sale_unit: str = 'strip'          # 'strip' or 'tablet'

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
    mrp: Optional[str]
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
    customer_category: Optional[str] = None
    was_contacted_before: bool = False
    
    # Split payment amounts
    cash_amount: float = 0.0
    card_amount: float = 0.0
    online_amount: float = 0.0
    payment_reference: Optional[str] = None
    
    discount_amount: float = 0.0
    is_pay_later: bool = False
    notes: Optional[str] = None
    prescription_required: Optional[str] = None
    items: List[BillItemCreate]
    
    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one item is required')
        return v
    
    @field_validator('cash_amount', 'card_amount', 'online_amount')
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
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
    
    # Split payment
    cash_amount: float
    card_amount: float
    online_amount: float
    payment_reference: Optional[str]
    
    subtotal: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    change_returned: float
    payment_status: str
    amount_due: float
    notes: Optional[str]
    prescription_required: Optional[str]
    created_at: datetime
    items: List[BillItemResponse]

    class Config:
        from_attributes = True

class MedicineSearchResult(BaseModel):
    id: int
    product_name: str
    batch_number: str
    quantity_available: int
    mrp: Optional[str]
    unit_price: Optional[float]
    selling_price: Optional[float]
    rack_number: Optional[str]
    section_name: Optional[str]
    expiry_date: Optional[str]
    manufacturer: Optional[str]
    hsn_code: Optional[str]
    package: Optional[str]

class BillSummary(BaseModel):
    total_bills: int
    total_revenue: float
    cash_sales: float
    card_sales: float
    online_sales: float
    average_bill_value: float


class PayLaterBillSummary(BaseModel):
    id: int
    bill_number: str
    total_amount: float
    amount_paid: float
    amount_due: float
    payment_status: str
    created_at: datetime
    items_count: int
    notes: Optional[str]

    class Config:
        from_attributes = True

class PayLaterCustomer(BaseModel):
    customer_name: Optional[str]
    customer_phone: str
    total_due: float
    bill_count: int
    oldest_bill_date: datetime
    bills: List[PayLaterBillSummary]

class RecordPaymentRequest(BaseModel):
    customer_phone: str
    cash_amount: float = 0.0
    card_amount: float = 0.0
    online_amount: float = 0.0
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

    @field_validator('cash_amount', 'card_amount', 'online_amount')
    @classmethod
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return v

class RecordPaymentResponse(BaseModel):
    message: str
    total_paid: float
    bills_cleared: int
    remaining_due: float
    applied_to: List[dict]
