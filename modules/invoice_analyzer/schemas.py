from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

class InvoiceStatus(str, Enum):
    RECEIVED = "received"
    PARTIAL = "partial"
    SOLD_OUT = "sold_out"
    EXPIRED = "expired"

class ColorCode(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

class DemandCategory(str, Enum):
    FAST = "fast"
    MEDIUM = "medium"
    SLOW = "slow"
    DEAD = "dead"

class AlertType(str, Enum):
    DAYS_45 = "45_days"
    YEAR_1 = "1_year"
    EXPIRED = "expired"

# Purchase Invoice Item Schemas
class PurchaseInvoiceItemCreate(BaseModel):
    item_code: str
    item_name: str
    batch_number: Optional[str] = None
    purchased_quantity: float
    unit_cost: float
    selling_price: float
    expiry_date: Optional[date] = None

class PurchaseInvoiceItemResponse(BaseModel):
    id: int
    item_code: str
    item_name: str
    batch_number: Optional[str]
    purchased_quantity: float
    sold_quantity: float
    remaining_quantity: float
    unit_cost: float
    selling_price: float
    total_cost: float
    expiry_date: Optional[date]
    days_to_expiry: Optional[int]
    is_expiring_soon: bool
    is_expiring_critical: bool
    movement_rate: float
    demand_category: str
    
    class Config:
        from_attributes = True

# Purchase Invoice Schemas
class PurchaseInvoiceCreate(BaseModel):
    invoice_number: str
    supplier_name: str
    invoice_date: date
    received_date: date
    items: List[PurchaseInvoiceItemCreate]

class PurchaseInvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    supplier_name: str
    invoice_date: date
    received_date: date
    total_amount: float
    total_items: int
    total_quantity: float
    sold_percentage: float
    status: str
    color_code: str
    has_expiring_items: bool
    nearest_expiry_days: Optional[int]
    created_at: datetime
    items: List[PurchaseInvoiceItemResponse]
    
    class Config:
        from_attributes = True

# Item Sale Schemas
class ItemSaleCreate(BaseModel):
    item_id: int
    quantity_sold: float
    sale_price: float
    customer_type: Optional[str] = None

class ItemSaleResponse(BaseModel):
    id: int
    sale_date: date
    quantity_sold: float
    sale_price: float
    profit_margin: float
    customer_type: Optional[str]
    
    class Config:
        from_attributes = True

# Expiry Alert Schemas
class ExpiryAlertResponse(BaseModel):
    id: int
    alert_type: str
    alert_date: date
    message: str
    priority: str
    is_acknowledged: bool
    item_code: str
    item_name: str
    days_to_expiry: Optional[int]
    
    class Config:
        from_attributes = True

# Monthly Summary Schemas
class MonthlyInvoiceSummaryResponse(BaseModel):
    id: int
    year: int
    month: int
    total_invoices: int
    total_amount: float
    total_items: int
    green_invoices: int
    yellow_invoices: int
    red_invoices: int
    month_color: str
    overall_sold_percentage: float
    expiring_items_count: int
    expired_items_count: int
    ai_insights: Optional[str]
    movement_prediction: Optional[str]
    
    class Config:
        from_attributes = True

# Analytics Schemas
class InvoiceAnalytics(BaseModel):
    total_invoices: int
    total_value: float
    sold_out_invoices: int
    partial_invoices: int
    unsold_invoices: int
    average_sold_percentage: float
    expiring_alerts: int
    top_moving_items: List[dict]
    slow_moving_items: List[dict]

class MovementAnalytics(BaseModel):
    item_code: str
    item_name: str
    total_purchased: float
    total_sold: float
    movement_rate: float
    days_in_stock: int
    predicted_sellout_days: Optional[int]
    demand_category: str
    seasonal_factor: float

class AIInsights(BaseModel):
    movement_patterns: List[dict]
    seasonal_trends: List[dict]
    expiry_predictions: List[dict]
    stock_recommendations: List[dict]
    profit_optimization: List[dict]

# Dashboard Schemas
class DashboardSummary(BaseModel):
    current_month_summary: MonthlyInvoiceSummaryResponse
    pending_alerts: List[ExpiryAlertResponse]
    recent_invoices: List[PurchaseInvoiceResponse]
    movement_analytics: List[MovementAnalytics]
    ai_insights: AIInsights