from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date

# Contact Record Schemas
class ContactRecordCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    whatsapp_status: str = "unknown"

class ContactRecordUpdate(BaseModel):
    name: Optional[str] = None
    whatsapp_status: Optional[str] = None
    contact_status: Optional[str] = None
    assigned_staff_id: Optional[int] = None

class ContactInteractionCreate(BaseModel):
    interaction_type: str  # call, whatsapp, visit
    notes: Optional[str] = None
    customer_response: Optional[str] = None
    next_action: Optional[str] = None
    call_duration: Optional[int] = None
    call_successful: bool = False

class ContactReminderCreate(BaseModel):
    reminder_date: datetime
    reminder_type: str  # follow_up, callback, visit_expected
    message: Optional[str] = None

class ContactRecordResponse(BaseModel):
    id: int
    shop_id: int
    phone: str
    name: Optional[str]
    whatsapp_status: str
    contact_status: str
    assigned_staff_id: Optional[int]
    contact_attempts: int
    whatsapp_sent: bool
    converted_date: Optional[datetime]
    conversion_value: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Customer Schemas
class CustomerCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    category: str  # contact_sheet, first_time_prescription, regular_branded, generic_informed
    contact_record_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    primary_doctor: Optional[str] = None
    prefers_generic: Optional[bool] = None
    generic_education_given: Optional[bool] = None
    special_notes: Optional[str] = None

class CustomerPurchaseCreate(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    quantity: int
    total_amount: float
    is_generic: bool = False
    duration_days: Optional[int] = None

class CustomerResponse(BaseModel):
    id: int
    shop_id: int
    phone: str
    name: Optional[str]
    category: str
    total_visits: int
    total_purchases: float
    prefers_generic: bool
    generic_education_given: bool
    last_visit_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Refill Reminder Schemas
class RefillReminderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str]
    customer_phone: str
    medicine_name: str
    reminder_date: date
    whatsapp_sent: bool
    call_reminder_sent: bool
    customer_responded: bool
    customer_purchased: bool
    
    class Config:
        from_attributes = True

# Upload Response
class ContactUploadResponse(BaseModel):
    total_contacts: int
    whatsapp_active: int
    whatsapp_inactive: int
    duplicates_skipped: int
    contacts_added: int
