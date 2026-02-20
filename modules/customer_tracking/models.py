from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class ContactRecord(Base):
    __tablename__ = "contact_records"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    
    # WhatsApp status: active, inactive, unknown
    whatsapp_status = Column(String, default="unknown")
    
    # Contact status: pending, contacted, converted, yellow, inactive
    contact_status = Column(String, default="pending", index=True)
    
    # File upload tracking
    source_file = Column(String, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    
    # Staff assignment
    assigned_staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
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
    conversion_value = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    interactions = relationship("ContactInteraction", back_populates="contact", cascade="all, delete-orphan")
    reminders = relationship("ContactReminder", back_populates="contact", cascade="all, delete-orphan")

class ContactInteraction(Base):
    __tablename__ = "contact_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contact_records.id", ondelete="CASCADE"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    
    interaction_date = Column(DateTime, default=datetime.utcnow, index=True)
    interaction_type = Column(String, nullable=False)  # call, whatsapp, visit
    
    notes = Column(Text, nullable=True)
    customer_response = Column(Text, nullable=True)
    next_action = Column(String, nullable=True)
    
    call_duration = Column(Integer, nullable=True)
    call_successful = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("ContactRecord", back_populates="interactions")

class ContactReminder(Base):
    __tablename__ = "contact_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contact_records.id", ondelete="CASCADE"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    
    reminder_date = Column(DateTime, nullable=False, index=True)
    reminder_type = Column(String, nullable=False)  # follow_up, callback, visit_expected
    message = Column(Text, nullable=True)
    
    completed = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    contact = relationship("ContactRecord", back_populates="reminders")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    
    # Category: contact_sheet, first_time_prescription, regular_branded, generic_informed
    category = Column(String, nullable=False, index=True)
    
    # Link to contact record if from contact sheet
    contact_record_id = Column(Integer, ForeignKey("contact_records.id"), nullable=True)
    
    # Personal details
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    email = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    # Medical information
    chronic_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    primary_doctor = Column(String, nullable=True)
    
    # Tracking
    first_visit_date = Column(DateTime, default=datetime.utcnow)
    last_visit_date = Column(DateTime, nullable=True)
    total_visits = Column(Integer, default=0)
    total_purchases = Column(Float, default=0.0)
    
    # Preferences
    prefers_generic = Column(Boolean, default=False)
    generic_education_given = Column(Boolean, default=False)
    
    special_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    purchases = relationship("CustomerPurchase", back_populates="customer", cascade="all, delete-orphan")
    refill_reminders = relationship("RefillReminder", back_populates="customer", cascade="all, delete-orphan")

class CustomerPurchase(Base):
    __tablename__ = "customer_purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=True)
    
    purchase_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    medicine_name = Column(String, nullable=False)
    generic_name = Column(String, nullable=True)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    
    is_generic = Column(Boolean, default=False)
    
    # Duration tracking for refill reminders
    duration_days = Column(Integer, nullable=True)
    refill_reminder_date = Column(Date, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="purchases")

class RefillReminder(Base):
    __tablename__ = "refill_reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("customer_purchases.id"), nullable=True)
    
    medicine_name = Column(String, nullable=False)
    reminder_date = Column(Date, nullable=False, index=True)
    
    # Notification tracking
    whatsapp_sent = Column(Boolean, default=False)
    whatsapp_sent_date = Column(DateTime, nullable=True)
    call_reminder_sent = Column(Boolean, default=False)
    call_reminder_date = Column(DateTime, nullable=True)
    
    # Response tracking
    customer_responded = Column(Boolean, default=False)
    customer_purchased = Column(Boolean, default=False)
    response_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="refill_reminders")
