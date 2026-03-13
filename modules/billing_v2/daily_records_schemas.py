from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

class DailyExpenseBase(BaseModel):
    expense_category: str
    amount: float
    description: Optional[str] = None

class DailyExpenseCreate(DailyExpenseBase):
    pass

class DailyExpense(DailyExpenseBase):
    id: int
    daily_record_id: int
    staff_id: Optional[int]
    staff_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class DailyRecordBase(BaseModel):
    record_date: date
    unbilled_amount: float = 0.0
    unbilled_notes: Optional[str] = None
    actual_cash_deposited: float = 0.0
    cash_reserve: float = 0.0

class DailyRecordCreate(DailyRecordBase):
    expenses: List[DailyExpenseCreate] = []

class DailyRecordUpdate(BaseModel):
    unbilled_amount: Optional[float] = None
    unbilled_notes: Optional[str] = None
    actual_cash_deposited: Optional[float] = None
    cash_reserve: Optional[float] = None

class DailyRecordResponse(DailyRecordBase):
    id: int
    shop_id: int
    
    # Auto-calculated from bills
    no_of_bills: int
    software_sales: float
    cash_sales: float
    online_sales: float
    
    # Calculated fields
    average_bill: float
    total_cash: float  # cash_sales - should equal actual_cash + cash_reserve
    recorded_sales: float  # software_sales + unbilled_amount
    total_sales: float  # cash_sales + online_sales
    difference: float  # recorded_sales - total_sales
    reserve_balance: float  # cash_reserve
    depositable_amount: float  # Amount in 2000/500/200/100 notes
    small_denomination: float  # Amount in smaller notes/coins
    total_expenses: float
    
    # Staff
    staff_id: Optional[int]
    staff_name: Optional[str]
    
    # Expenses
    expenses: List[DailyExpense]
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
