from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
import enum

class ContactStatus(enum.Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CONVERTED = "converted"
    YELLOW = "yellow"  # Visited but didn't buy
    INACTIVE = "inactive"

class CustomerCategory(enum.Enum):
    CONTACT_SHEET = "contact_sheet"  # From uploaded contact records
    FIRST_TIME_PRESCRIPTION = "first_time_prescription"  # Walk-in with prescription
    REGULAR_BRANDED = "regular_branded"  # Regular customer using branded medicines
    GENERIC_INFORMED = "generic_informed"  # Informed about generic medicines

class WhatsAppStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"

class ContactRecord(Base):
    __tablename__ = "contact_records"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    whatsapp_status = Column(String, default="unknown")
    contact_status = Column(String, default="pending")
    
    # File upload tracking
    source_file = Column(String, nullable=True)  # Original filename
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String, nullable=True)
    
    # Staff assignment
    assigned_staff_code = Column(String, nullable=True)
    assigned_date = Column(DateTime, nullable=True)
    
    # Contact tracking
    first_contact_date = Column(DateTime, nullable=True)
    last_contact_date = Column(DateTime, nullable=True)
    contact_attempts = Column(Integer, default=0)
    
    # WhatsApp messaging
    whatsapp_sent = Column(Boolean, default=False)
    whatsapp_sent_date = Column(DateTime, nullable=True)
    
    # Conversion tracking
    converted_date = Column(DateTime, nullable=True)
    conversion_value = Column(Float, nullable=True)  # First purchase amount
    
    # Relationships
    interactions = relationship("ContactInteraction", back_populates="contact")
    reminders = relationship("ContactReminder", back_populates="contact")
    customer = relationship("CustomerProfile", back_populates="contact_record", uselist=False)

class ContactInteraction(Base):
    __tablename__ = "contact_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("contact_records.id"))
    staff_code = Column(String, nullable=False)
    interaction_date = Column(DateTime, default=datetime.utcnow)
    interaction_type = Column(String)  # call, whatsapp, visit, etc.
    
    # Interaction details
    notes = Column(Text, nullable=True)
    customer_response = Column(Text, nullable=True)
    next_action = Column(String, nullable=True)
    
    # Call specific
    call_duration = Column(Integer, nullable=True)  # in seconds
    call_successful = Column(Boolean, default=False)
    
    contact = relationship("ContactRecord", back_populates="interactions")

class ContactReminder(Base):
    __tablename__ = "contact_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    contact_id = Column(Integer, ForeignKey("contact_records.id"))
    staff_code = Column(String, nullable=False)
    
    reminder_date = Column(DateTime, nullable=False)
    reminder_type = Column(String)  # follow_up, callback, visit_expected
    message = Column(Text, nullable=True)
    
    completed = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("ContactRecord", back_populates="reminders")

class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    phone = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    
    # Customer categorization
    category = Column(String, nullable=False)
    
    # Contact record link (if from contact sheet)
    contact_record_id = Column(Integer, ForeignKey("contact_records.id"), nullable=True)
    
    # Personal details
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Medical information
    chronic_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    preferred_brands = Column(Text, nullable=True)
    
    # Behavioral tracking
    first_visit_date = Column(DateTime, default=datetime.utcnow)
    last_visit_date = Column(DateTime, nullable=True)
    total_visits = Column(Integer, default=1)
    total_purchases = Column(Float, default=0.0)
    
    # Preferences
    prefers_generic = Column(Boolean, default=False)
    generic_education_given = Column(Boolean, default=False)
    
    # Staff notes
    special_notes = Column(Text, nullable=True)
    
    # Relationships
    contact_record = relationship("ContactRecord", back_populates="customer")
    visits = relationship("CustomerVisit", back_populates="customer")
    purchases = relationship("CustomerPurchase", back_populates="customer")

class CustomerVisit(Base):
    __tablename__ = "customer_visits"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    
    visit_date = Column(DateTime, default=datetime.utcnow)
    staff_code = Column(String, nullable=False)
    
    # Visit details
    visit_purpose = Column(String, nullable=True)  # prescription, consultation, purchase
    prescription_brought = Column(Boolean, default=False)
    
    # Outcome
    purchase_made = Column(Boolean, default=False)
    purchase_amount = Column(Float, nullable=True)
    
    # Notes
    staff_notes = Column(Text, nullable=True)
    customer_feedback = Column(Text, nullable=True)
    
    customer = relationship("CustomerProfile", back_populates="visits")

class CustomerPurchase(Base):
    __tablename__ = "customer_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    visit_id = Column(Integer, ForeignKey("customer_visits.id"), nullable=True)
    
    purchase_date = Column(DateTime, default=datetime.utcnow)
    
    # Purchase details
    medicine_name = Column(String, nullable=False)
    brand_name = Column(String, nullable=True)
    generic_name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    # Medicine type
    is_generic = Column(Boolean, default=False)
    is_prescription = Column(Boolean, default=False)
    
    # Duration tracking
    duration_days = Column(Integer, nullable=True)
    refill_reminder_sent = Column(Boolean, default=False)
    
    customer = relationship("CustomerProfile", back_populates="purchases")
    refill_reminders = relationship("RefillReminder", back_populates="purchase")

class RefillReminder(Base):
    __tablename__ = "refill_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    purchase_id = Column(Integer, ForeignKey("customer_purchases.id"))
    customer_id = Column(Integer, ForeignKey("customer_profiles.id"))
    
    medicine_name = Column(String, nullable=False)
    reminder_date = Column(Date, nullable=False)
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    notification_sent_date = Column(DateTime, nullable=True)
    notification_method = Column(String, nullable=True)  # whatsapp, sms, call
    
    # Customer response
    customer_responded = Column(Boolean, default=False)
    customer_purchased = Column(Boolean, default=False)
    response_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    purchase = relationship("CustomerPurchase", back_populates="refill_reminders")
    customer = relationship("CustomerProfile")

class StaffMember(Base):
    __tablename__ = "staff_members"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    staff_code = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    
    # Work assignment
    active = Column(Boolean, default=True)
    max_contacts_per_day = Column(Integer, default=20)
    
    # Performance tracking
    total_contacts_assigned = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ContactUpload(Base):
    __tablename__ = "contact_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, excel
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String, nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_date = Column(DateTime, nullable=True)
    
    # Results
    total_contacts = Column(Integer, default=0)
    whatsapp_contacts = Column(Integer, default=0)
    non_whatsapp_contacts = Column(Integer, default=0)
    duplicate_contacts = Column(Integer, default=0)
    
    # Error tracking
    processing_errors = Column(Text, nullable=True)