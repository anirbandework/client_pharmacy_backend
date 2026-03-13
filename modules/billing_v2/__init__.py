"""
Billing V2 Module

Organized structure:
- staff/: Staff routes and dependencies
- admin/: Admin routes and analytics
- models.py: Database models
- schemas.py: Pydantic schemas
- services.py: Business logic
- daily_records_models.py: Daily records models
- daily_records_schemas.py: Daily records schemas
- daily_records_service.py: Daily records service
"""

from .models import Bill, BillItem, PaymentMethod
from .schemas import (
    BillCreate,
    BillResponse,
    BillItemCreate,
    BillItemResponse,
    BillSummary,
    MedicineSearchResult
)
from .daily_records_models import DailyRecord, DailyExpense
from .daily_records_schemas import (
    DailyRecordCreate,
    DailyRecordUpdate,
    DailyRecordResponse,
    DailyExpenseCreate,
    DailyExpense as DailyExpenseSchema
)

__all__ = [
    "Bill",
    "BillItem", 
    "PaymentMethod",
    "BillCreate",
    "BillResponse",
    "BillItemCreate",
    "BillItemResponse",
    "BillSummary",
    "MedicineSearchResult",
    "DailyRecord",
    "DailyExpense",
    "DailyRecordCreate",
    "DailyRecordUpdate", 
    "DailyRecordResponse",
    "DailyExpenseCreate",
    "DailyExpenseSchema",
]
