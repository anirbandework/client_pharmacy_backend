from pydantic import BaseModel, Field, computed_field
from datetime import datetime, date
from typing import Optional, List

class DailyRecordBase(BaseModel):
    date: date
    day: str
    cash_balance: float
    average_bill: Optional[float] = None
    no_of_bills: Optional[int] = None
    actual_cash: Optional[float] = None
    online_sales: Optional[float] = None
    unbilled_sales: Optional[float] = None
    software_figure: Optional[float] = None
    cash_reserve: Optional[float] = None
    reserve_comments: Optional[str] = None
    expense_amount: Optional[float] = None
    notes: Optional[str] = None

class DailyRecordCreate(DailyRecordBase):
    created_by: Optional[str] = None

class DailyRecordUpdate(BaseModel):
    day: Optional[str] = None
    cash_balance: Optional[float] = None
    average_bill: Optional[float] = None
    no_of_bills: Optional[int] = None
    actual_cash: Optional[float] = None
    online_sales: Optional[float] = None
    unbilled_sales: Optional[float] = None
    software_figure: Optional[float] = None
    cash_reserve: Optional[float] = None
    reserve_comments: Optional[str] = None
    expense_amount: Optional[float] = None
    notes: Optional[str] = None

class DailyRecord(DailyRecordBase):
    id: int
    total_cash: Optional[float] = None
    total_sales: Optional[float] = None
    recorded_sales: Optional[float] = None
    sales_difference: Optional[float] = None
    created_at: datetime
    created_by: Optional[str] = None
    modified_at: datetime
    modified_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class RecordModification(BaseModel):
    id: int
    daily_record_id: int
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    modified_at: datetime
    modified_by: Optional[str] = None
    action: str = "update"
    
    class Config:
        from_attributes = True

class AuditLog(BaseModel):
    """Audit log entry for record activity"""
    record_id: int
    date: date
    action: str  # created, updated, deleted
    user: Optional[str] = None
    timestamp: datetime
    changes: Optional[List[dict]] = None

class AuditLogResponse(BaseModel):
    """Response for audit log queries"""
    total_logs: int
    logs: List[AuditLog]

class ExcelImportResponse(BaseModel):
    success: bool
    records_imported: int
    errors: list = []
    message: str