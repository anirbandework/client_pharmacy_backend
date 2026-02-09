from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

# Enums
class ContactStatusEnum(str, Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CONVERTED = "converted"
    YELLOW = "yellow"
    INACTIVE = "inactive"

class CustomerCategoryEnum(str, Enum):
    CONTACT_SHEET = "contact_sheet"
    FIRST_TIME_PRESCRIPTION = "first_time_prescription"
    REGULAR_BRANDED = "regular_branded"
    GENERIC_INFORMED = "generic_informed"

class WhatsAppStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"

# Contact Record Schemas
class ContactRecordBase(BaseModel):
    phone: str
    name: Optional[str] = None
    whatsapp_status: WhatsAppStatusEnum = WhatsAppStatusEnum.UNKNOWN

class ContactRecordCreate(ContactRecordBase):
    source_file: Optional[str] = None
    uploaded_by: Optional[str] = None

class ContactRecord(ContactRecordBase):
    id: int
    contact_status: ContactStatusEnum
    upload_date: datetime
    assigned_staff_code: Optional[str] = None
    contact_attempts: int = 0
    whatsapp_sent: bool = False
    
    class Config:
        from_attributes = True

# Contact Interaction Schemas
class ContactInteractionBase(BaseModel):
    staff_code: str
    interaction_type: str
    notes: Optional[str] = None
    customer_response: Optional[str] = None
    next_action: Optional[str] = None

class ContactInteractionCreate(ContactInteractionBase):
    contact_id: int
    call_duration: Optional[int] = None
    call_successful: bool = False

class ContactInteraction(ContactInteractionBase):
    id: int
    contact_id: int
    interaction_date: datetime
    
    class Config:
        from_attributes = True

# Contact Reminder Schemas
class ContactReminderBase(BaseModel):
    staff_code: str
    reminder_date: datetime
    reminder_type: str
    message: Optional[str] = None

class ContactReminderCreate(ContactReminderBase):
    contact_id: int

class ContactReminder(ContactReminderBase):
    id: int
    contact_id: int
    completed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

# Customer Profile Schemas
class CustomerProfileBase(BaseModel):
    phone: str
    name: Optional[str] = None
    category: CustomerCategoryEnum
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    primary_doctor: Optional[str] = None
    doctor_phone: Optional[str] = None

class CustomerProfileCreate(CustomerProfileBase):
    contact_record_id: Optional[int] = None
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None

class CustomerProfile(CustomerProfileBase):
    id: int
    first_visit_date: datetime
    total_visits: int = 1
    total_purchases: float = 0.0
    prefers_generic: bool = False
    
    class Config:
        from_attributes = True

# Customer Visit Schemas
class CustomerVisitBase(BaseModel):
    staff_code: str
    visit_purpose: Optional[str] = None
    prescription_brought: bool = False
    purchase_made: bool = False
    purchase_amount: Optional[float] = None

class CustomerVisitCreate(CustomerVisitBase):
    customer_id: int
    staff_notes: Optional[str] = None

class CustomerVisit(CustomerVisitBase):
    id: int
    customer_id: int
    visit_date: datetime
    
    class Config:
        from_attributes = True

# Customer Purchase Schemas
class CustomerPurchaseBase(BaseModel):
    medicine_name: str
    quantity: int
    unit_price: float
    total_amount: float
    is_generic: bool = False
    is_prescription: bool = False

class CustomerPurchaseCreate(CustomerPurchaseBase):
    customer_id: int
    visit_id: Optional[int] = None
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    duration_days: Optional[int] = None

class CustomerPurchase(CustomerPurchaseBase):
    id: int
    customer_id: int
    purchase_date: datetime
    
    class Config:
        from_attributes = True

# Quick Purchase Schemas
class PurchaseItem(BaseModel):
    medicine_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    quantity: int
    unit_price: float
    total_amount: float
    is_generic: bool = False
    is_prescription: bool = False
    duration_days: Optional[int] = None

class QuickPurchaseCreate(BaseModel):
    # Customer info
    phone: str
    name: Optional[str] = None
    category: CustomerCategoryEnum
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    chronic_conditions: Optional[str] = None
    allergies: Optional[str] = None
    
    # Purchase items
    items: List[PurchaseItem]

class QuickPurchaseResponse(BaseModel):
    customer_id: int
    is_new_customer: bool
    is_repeat_customer: bool
    total_amount: float
    refill_reminders_scheduled: int
    message: str

# Refill Reminder Schemas
class RefillReminderBase(BaseModel):
    medicine_name: str
    reminder_date: date

class RefillReminder(RefillReminderBase):
    id: int
    customer_id: int
    notification_sent: bool
    customer_purchased: bool
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    total_visits: Optional[int] = None
    is_repeat_customer: Optional[bool] = None
    
    class Config:
        from_attributes = True

# Staff Member Schemas
class StaffMemberBase(BaseModel):
    staff_code: str
    name: str
    phone: Optional[str] = None
    max_contacts_per_day: int = 20

class StaffMemberCreate(StaffMemberBase):
    pass

class StaffMember(StaffMemberBase):
    id: int
    active: bool = True
    total_contacts_assigned: int = 0
    total_conversions: int = 0
    conversion_rate: float = 0.0
    
    class Config:
        from_attributes = True

# File Upload Schemas
class ContactUploadBase(BaseModel):
    filename: str
    file_type: str

class ContactUploadCreate(ContactUploadBase):
    uploaded_by: Optional[str] = None

class ContactUpload(ContactUploadBase):
    id: int
    upload_date: datetime
    processed: bool = False
    total_contacts: int = 0
    whatsapp_contacts: int = 0
    non_whatsapp_contacts: int = 0
    
    class Config:
        from_attributes = True

# Response Schemas
class ContactProcessingResult(BaseModel):
    total_processed: int
    whatsapp_contacts: int
    non_whatsapp_contacts: int
    duplicates_found: int
    errors: List[str] = []

class ConversionReport(BaseModel):
    total_contacts: int
    contacted: int
    converted: int
    yellow_status: int
    conversion_rate: float
    staff_performance: List[dict]

class DailyTaskList(BaseModel):
    staff_code: str
    pending_contacts: List[ContactRecord]
    pending_reminders: List[ContactReminder]
    total_tasks: int

# Prescription Schemas
class PrescriptionMedicineBase(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    dosage: str
    frequency: str
    duration_days: int
    total_quantity_prescribed: int
    refill_allowed: bool = True
    refills_remaining: int = 0
    start_date: date
    end_date: date

class PrescriptionMedicineCreate(PrescriptionMedicineBase):
    prescription_id: int

class PrescriptionMedicine(PrescriptionMedicineBase):
    id: int
    purchased: bool = False
    purchase_date: Optional[date] = None
    
    class Config:
        from_attributes = True

class CustomerPrescriptionBase(BaseModel):
    prescription_date: date
    doctor_name: str
    doctor_phone: Optional[str] = None
    clinic_name: Optional[str] = None
    condition_name: str
    condition_severity: Optional[str] = None
    is_chronic: bool = False
    next_followup_date: Optional[date] = None
    followup_type: Optional[str] = None
    prescription_notes: Optional[str] = None

class CustomerPrescriptionCreate(CustomerPrescriptionBase):
    customer_id: int
    medicines: List[PrescriptionMedicineBase]

class CustomerPrescription(CustomerPrescriptionBase):
    id: int
    customer_id: int
    followup_completed: bool = False
    is_active: bool = True
    completion_date: Optional[date] = None
    created_at: datetime
    medicines: List[PrescriptionMedicine] = []
    
    class Config:
        from_attributes = True

# Medical Condition Schemas
class CustomerMedicalConditionBase(BaseModel):
    condition_name: str
    condition_type: str  # chronic, acute, preventive
    severity: Optional[str] = None
    diagnosed_date: Optional[date] = None
    primary_medicine: Optional[str] = None
    treatment_duration: Optional[str] = None
    requires_monitoring: bool = False
    monitoring_frequency: Optional[str] = None
    last_checkup_date: Optional[date] = None
    next_checkup_date: Optional[date] = None
    condition_notes: Optional[str] = None

class CustomerMedicalConditionCreate(CustomerMedicalConditionBase):
    customer_id: int

class CustomerMedicalCondition(CustomerMedicalConditionBase):
    id: int
    customer_id: int
    is_active: bool = True
    created_at: datetime
    
    class Config:
        from_attributes = True

# Call Script Schemas
class CallScriptBase(BaseModel):
    call_type: str  # refill_reminder, follow_up, new_prescription
    priority: str = "medium"  # high, medium, low
    customer_summary: str
    medical_summary: Optional[str] = None
    purchase_history_summary: Optional[str] = None
    key_talking_points: Optional[str] = None
    medicines_to_discuss: Optional[str] = None
    follow_up_reminders: Optional[str] = None

class CallScriptCreate(CallScriptBase):
    customer_id: int

class CallScript(CallScriptBase):
    id: int
    customer_id: int
    script_used: bool = False
    call_successful: bool = False
    customer_response: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Enhanced Customer Details for Calls
class CustomerCallDetails(BaseModel):
    # Basic info
    customer_id: int
    name: Optional[str]
    phone: str
    age: Optional[int]
    
    # Medical summary
    active_conditions: List[CustomerMedicalCondition]
    current_prescriptions: List[CustomerPrescription]
    allergies: Optional[str]
    
    # Purchase behavior
    total_visits: int
    last_visit_date: Optional[datetime]
    total_purchases: float
    prefers_generic: bool
    
    # Upcoming needs
    pending_refills: List[RefillReminder]
    upcoming_followups: List[dict]
    
    # Call script
    suggested_script: Optional[CallScript]
    
    class Config:
        from_attributes = True

class CustomerAnalytics(BaseModel):
    total_customers: int
    by_category: dict
    conversion_metrics: dict
    top_medicines: List[dict]
    generic_adoption_rate: float
    prescription_compliance_rate: float
    chronic_condition_distribution: dict