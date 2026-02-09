from pydantic import BaseModel, validator
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"

class PaymentMethodEnum(str, Enum):
    UPI = "upi"
    BANK = "bank"

class AlertTypeEnum(str, Enum):
    UPCOMING = "upcoming"
    OVERDUE = "overdue"

# Staff Payment Info Schemas
class StaffPaymentInfoCreate(BaseModel):
    upi_id: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    preferred_payment_method: PaymentMethodEnum = PaymentMethodEnum.UPI

class StaffPaymentInfoUpdate(BaseModel):
    upi_id: Optional[str] = None
    bank_account: Optional[str] = None
    ifsc_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethodEnum] = None

class StaffPaymentInfo(BaseModel):
    id: int
    staff_id: int
    upi_id: Optional[str]
    qr_code_path: Optional[str]
    bank_account: Optional[str]
    ifsc_code: Optional[str]
    account_holder_name: Optional[str]
    preferred_payment_method: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Salary Record Schemas
class SalaryRecordCreate(BaseModel):
    staff_id: int
    month: int
    year: int
    salary_amount: float
    due_date: date
    notes: Optional[str] = None
    
    @validator('month')
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v

class SalaryRecordUpdate(BaseModel):
    salary_amount: Optional[float] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None

class SalaryPayment(BaseModel):
    paid_by_admin: str
    notes: Optional[str] = None

class SalaryRecord(BaseModel):
    id: int
    staff_id: int
    month: int
    year: int
    salary_amount: float
    payment_status: str
    payment_date: Optional[datetime]
    paid_by_admin: Optional[str]
    due_date: date
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Staff Profile with Salary Info
class StaffSalaryProfile(BaseModel):
    id: int
    name: str
    staff_code: str
    phone: Optional[str]
    email: Optional[str]
    monthly_salary: Optional[float]
    payment_info: Optional[StaffPaymentInfo]
    pending_months: int
    paid_months: int
    overdue_months: int
    last_payment_date: Optional[datetime]
    joining_date: Optional[date]
    salary_eligibility_days: int
    is_eligible_for_salary: bool  # Computed field
    
    class Config:
        from_attributes = True

# Salary Alert Schemas
class SalaryAlert(BaseModel):
    id: int
    staff_id: int
    salary_record_id: int
    alert_type: str
    alert_date: date
    is_dismissed: bool
    created_at: datetime
    staff_name: str
    month: int
    year: int
    salary_amount: float
    
    class Config:
        from_attributes = True

# Dashboard Schemas
class SalaryDashboard(BaseModel):
    total_staff: int
    pending_payments: int
    overdue_payments: int
    upcoming_payments: int  # Due in next 5 days
    total_pending_amount: float
    total_overdue_amount: float
    alerts: List[SalaryAlert]

class MonthlySalarySummary(BaseModel):
    month: int
    year: int
    total_staff: int
    paid_count: int
    pending_count: int
    overdue_count: int
    total_salary_amount: float
    paid_amount: float
    pending_amount: float

class StaffSalaryHistory(BaseModel):
    staff_id: int
    staff_name: str
    records: List[SalaryRecord]
    total_paid: float
    total_pending: float
    months_paid: int
    months_pending: int