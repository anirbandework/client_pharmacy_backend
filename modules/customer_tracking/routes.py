from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from app.database.database import get_db
from datetime import datetime, timedelta, date
from typing import Optional, List
from . import schemas, models, services
from .ai_analytics import CustomerTrackingAI
import os
import tempfile

router = APIRouter()

# CONTACT RECORD MANAGEMENT

@router.post("/upload-contacts", response_model=schemas.ContactProcessingResult)
async def upload_contact_file(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Upload and process contact records from PDF or Excel file"""
    
    if not file.filename.endswith(('.pdf', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only PDF and Excel files are supported")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name
    
    try:
        result = services.ContactProcessingService.process_contact_file(
            db, tmp_file_path, file.filename, uploaded_by
        )
        return result
    finally:
        os.unlink(tmp_file_path)

@router.get("/contacts", response_model=List[schemas.ContactRecord])
def get_contacts(
    status: Optional[schemas.ContactStatusEnum] = None,
    whatsapp_status: Optional[schemas.WhatsAppStatusEnum] = None,
    staff_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get contact records with filters"""
    
    query = db.query(models.ContactRecord)
    
    if status:
        query = query.filter(models.ContactRecord.contact_status == status)
    if whatsapp_status:
        query = query.filter(models.ContactRecord.whatsapp_status == whatsapp_status)
    if staff_code:
        query = query.filter(models.ContactRecord.assigned_staff_code == staff_code)
    
    return query.offset(skip).limit(limit).all()

@router.post("/contacts/{contact_id}/interact", response_model=schemas.ContactInteraction)
def add_contact_interaction(
    contact_id: int,
    interaction: schemas.ContactInteractionCreate,
    db: Session = Depends(get_db)
):
    """Add interaction record for a contact"""
    
    contact = db.query(models.ContactRecord).filter(models.ContactRecord.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    # Create interaction
    db_interaction = models.ContactInteraction(**interaction.model_dump())
    db.add(db_interaction)
    
    # Update contact status and counters
    contact.contact_attempts += 1
    contact.last_contact_date = datetime.utcnow()
    if contact.contact_status == models.ContactStatus.PENDING.value:
        contact.contact_status = models.ContactStatus.CONTACTED.value
        contact.first_contact_date = datetime.utcnow()
    
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.post("/contacts/{contact_id}/reminder", response_model=schemas.ContactReminder)
def add_contact_reminder(
    contact_id: int,
    reminder: schemas.ContactReminderCreate,
    db: Session = Depends(get_db)
):
    """Add reminder for a contact"""
    
    contact = db.query(models.ContactRecord).filter(models.ContactRecord.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db_reminder = models.ContactReminder(**reminder.model_dump())
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

@router.put("/contacts/{contact_id}/status")
def update_contact_status(
    contact_id: int,
    status: schemas.ContactStatusEnum,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update contact status (e.g., mark as yellow, converted)"""
    
    contact = db.query(models.ContactRecord).filter(models.ContactRecord.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    contact.contact_status = status.value
    
    if status == models.ContactStatus.CONVERTED:
        contact.converted_date = datetime.utcnow()
    
    # Add interaction record for status change
    if notes:
        interaction = models.ContactInteraction(
            contact_id=contact_id,
            staff_code="system",
            interaction_type="status_update",
            notes=notes
        )
        db.add(interaction)
    
    db.commit()
    return {"message": f"Contact status updated to {status}"}

# WHATSAPP MESSAGING

@router.post("/send-whatsapp-bulk")
def send_whatsapp_to_contacts(
    whatsapp_only: bool = True,
    message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Send WhatsApp messages to contacts"""
    
    query = db.query(models.ContactRecord).filter(
        models.ContactRecord.whatsapp_sent == False
    )
    
    if whatsapp_only:
        query = query.filter(models.ContactRecord.whatsapp_status == models.WhatsAppStatus.ACTIVE.value)
    
    contacts = query.all()
    sent_count = 0
    failed_count = 0
    
    for contact in contacts:
        success = services.WhatsAppService.send_store_materials(contact.phone, message)
        if success:
            contact.whatsapp_sent = True
            contact.whatsapp_sent_date = datetime.utcnow()
            sent_count += 1
        else:
            failed_count += 1
    
    db.commit()
    
    return {
        "sent_count": sent_count,
        "failed_count": failed_count,
        "total_contacts": len(contacts)
    }

# STAFF MANAGEMENT

@router.post("/staff", response_model=schemas.StaffMember)
def create_staff_member(
    staff: schemas.StaffMemberCreate,
    db: Session = Depends(get_db)
):
    """Create new staff member"""
    
    existing = db.query(models.StaffMember).filter(
        models.StaffMember.staff_code == staff.staff_code
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Staff code already exists")
    
    db_staff = models.StaffMember(**staff.model_dump())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

@router.get("/staff", response_model=List[schemas.StaffMember])
def get_staff_members(db: Session = Depends(get_db)):
    """Get all staff members"""
    return db.query(models.StaffMember).all()

@router.post("/assign-contacts")
def assign_contacts_to_staff(db: Session = Depends(get_db)):
    """Automatically assign pending contacts to staff members"""
    
    assignments = services.TaskAssignmentService.assign_contacts_to_staff(db)
    return {
        "message": "Contacts assigned successfully",
        "assignments": assignments
    }

@router.get("/staff/{staff_code}/tasks", response_model=schemas.DailyTaskList)
def get_staff_daily_tasks(
    staff_code: str,
    db: Session = Depends(get_db)
):
    """Get daily task list for staff member"""
    
    tasks = services.TaskAssignmentService.get_daily_tasks(db, staff_code)
    return tasks

# CUSTOMER MANAGEMENT

@router.post("/customers", response_model=schemas.CustomerProfile)
def create_customer_profile(
    customer: schemas.CustomerProfileCreate,
    db: Session = Depends(get_db)
):
    """Create customer profile"""
    
    existing = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.phone == customer.phone
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Customer already exists")
    
    db_customer = models.CustomerProfile(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # If customer came from contact sheet, mark as converted
    if customer.contact_record_id:
        services.ConversionTrackingService.mark_conversion(db, customer.phone)
    
    return db_customer

@router.get("/customers/{customer_id}", response_model=schemas.CustomerProfile)
def get_customer_profile(
    customer_id: int,
    db: Session = Depends(get_db)
):
    """Get customer profile by ID"""
    
    customer = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.id == customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.get("/customers/phone/{phone}", response_model=schemas.CustomerProfile)
def get_customer_by_phone(
    phone: str,
    db: Session = Depends(get_db)
):
    """Get customer profile by phone number"""
    
    customer = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.phone == phone
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.post("/customers/{customer_id}/visit", response_model=schemas.CustomerVisit)
def add_customer_visit(
    customer_id: int,
    visit: schemas.CustomerVisitCreate,
    db: Session = Depends(get_db)
):
    """Record customer visit"""
    
    customer = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.id == customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db_visit = models.CustomerVisit(**visit.model_dump())
    db.add(db_visit)
    
    # Update customer stats
    customer.total_visits += 1
    customer.last_visit_date = datetime.utcnow()
    if visit.purchase_made and visit.purchase_amount:
        customer.total_purchases += visit.purchase_amount
    
    db.commit()
    db.refresh(db_visit)
    return db_visit

@router.post("/customers/{customer_id}/purchase", response_model=schemas.CustomerPurchase)
def add_customer_purchase(
    customer_id: int,
    purchase: schemas.CustomerPurchaseCreate,
    db: Session = Depends(get_db)
):
    """Record customer purchase"""
    
    customer = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.id == customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db_purchase = models.CustomerPurchase(**purchase.model_dump())
    db.add(db_purchase)
    
    # Update customer total purchases
    customer.total_purchases += purchase.total_amount
    customer.last_visit_date = datetime.utcnow()
    
    # Track generic medicine preference
    if purchase.is_generic:
        customer.prefers_generic = True
    
    db.commit()
    db.refresh(db_purchase)
    
    # Schedule refill reminder if duration provided
    if purchase.duration_days:
        services.ReminderService.schedule_refill_reminder(db, db_purchase.id, purchase.duration_days)
    
    # Mark conversion if customer came from contact sheet
    if customer.contact_record_id:
        services.ConversionTrackingService.mark_conversion(db, customer.phone, purchase.total_amount)
    
    return db_purchase

@router.post("/quick-purchase", response_model=schemas.QuickPurchaseResponse)
def quick_customer_purchase(
    purchase_data: schemas.QuickPurchaseCreate,
    db: Session = Depends(get_db)
):
    """Quick customer registration and purchase entry for walk-in customers"""
    
    # Check if customer exists by phone
    customer = db.query(models.CustomerProfile).filter(
        models.CustomerProfile.phone == purchase_data.phone
    ).first()
    
    is_new_customer = False
    
    if not customer:
        # Create new customer profile
        customer = models.CustomerProfile(
            phone=purchase_data.phone,
            name=purchase_data.name,
            category=purchase_data.category.value,
            age=purchase_data.age,
            gender=purchase_data.gender,
            address=purchase_data.address,
            chronic_conditions=purchase_data.chronic_conditions,
            allergies=purchase_data.allergies
        )
        db.add(customer)
        db.flush()
        is_new_customer = True
        
        # Check if customer came from contact sheet
        contact_record = db.query(models.ContactRecord).filter(
            models.ContactRecord.phone == purchase_data.phone
        ).first()
        if contact_record:
            customer.contact_record_id = contact_record.id
    else:
        # Update customer info if provided
        if purchase_data.name:
            customer.name = purchase_data.name
        if purchase_data.age:
            customer.age = purchase_data.age
        if purchase_data.address:
            customer.address = purchase_data.address
        customer.total_visits += 1
        customer.last_visit_date = datetime.utcnow()
    
    # Create purchase records
    purchases = []
    for item in purchase_data.items:
        db_purchase = models.CustomerPurchase(
            customer_id=customer.id,
            medicine_name=item.medicine_name,
            brand_name=item.brand_name,
            generic_name=item.generic_name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_amount=item.total_amount,
            is_generic=item.is_generic,
            is_prescription=item.is_prescription,
            duration_days=item.duration_days
        )
        db.add(db_purchase)
        purchases.append(db_purchase)
        
        customer.total_purchases += item.total_amount
        
        if item.is_generic:
            customer.prefers_generic = True
    
    db.commit()
    
    # Schedule refill reminders
    for purchase in purchases:
        if purchase.duration_days:
            services.ReminderService.schedule_refill_reminder(db, purchase.id, purchase.duration_days)
    
    # Mark conversion if from contact sheet
    if customer.contact_record_id:
        services.ConversionTrackingService.mark_conversion(db, customer.phone, customer.total_purchases)
    
    return {
        "customer_id": customer.id,
        "is_new_customer": is_new_customer,
        "is_repeat_customer": customer.total_visits > 1,
        "total_amount": sum(item.total_amount for item in purchase_data.items),
        "refill_reminders_scheduled": sum(1 for item in purchase_data.items if item.duration_days),
        "message": "Purchase recorded successfully"
    }

# REFILL REMINDERS

@router.get("/reminders/pending", response_model=List[schemas.RefillReminder])
def get_pending_refill_reminders(
    days_ahead: int = 3,
    db: Session = Depends(get_db)
):
    """Get customers due for refill reminders"""
    
    reminders = services.ReminderService.get_pending_reminders(db, days_ahead)
    
    # Enrich with customer details
    result = []
    for reminder in reminders:
        customer = db.query(models.CustomerProfile).filter(
            models.CustomerProfile.id == reminder.customer_id
        ).first()
        
        reminder_dict = {
            "id": reminder.id,
            "customer_id": reminder.customer_id,
            "medicine_name": reminder.medicine_name,
            "reminder_date": reminder.reminder_date,
            "notification_sent": reminder.notification_sent,
            "customer_purchased": reminder.customer_purchased,
            "customer_name": customer.name if customer else None,
            "customer_phone": customer.phone if customer else None,
            "total_visits": customer.total_visits if customer else 0,
            "is_repeat_customer": customer.total_visits > 1 if customer else False
        }
        result.append(reminder_dict)
    
    return result

@router.post("/reminders/{reminder_id}/notify")
def send_refill_notification(
    reminder_id: int,
    db: Session = Depends(get_db)
):
    """Send refill reminder notification to customer"""
    
    reminder = db.query(models.RefillReminder).filter(
        models.RefillReminder.id == reminder_id
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    success = services.ReminderService.send_refill_notification(db, reminder_id)
    
    return {
        "success": success,
        "message": "Notification sent" if success else "Failed to send notification"
    }

# ANALYTICS AND REPORTS

@router.get("/analytics/daily-summary")
def get_daily_summary(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Get daily summary of activities"""
    
    if not target_date:
        target_date = date.today()
    
    start_dt = datetime.combine(target_date, datetime.min.time())
    end_dt = datetime.combine(target_date, datetime.max.time())
    
    # Contacts processed today
    contacts_today = db.query(models.ContactRecord).filter(
        models.ContactRecord.upload_date >= start_dt,
        models.ContactRecord.upload_date <= end_dt
    ).count()
    
    # Interactions today
    interactions_today = db.query(models.ContactInteraction).filter(
        models.ContactInteraction.interaction_date >= start_dt,
        models.ContactInteraction.interaction_date <= end_dt
    ).count()
    
    # Conversions today
    conversions_today = db.query(models.ContactRecord).filter(
        models.ContactRecord.converted_date >= start_dt,
        models.ContactRecord.converted_date <= end_dt
    ).count()
    
    # Customer visits today
    visits_today = db.query(models.CustomerVisit).filter(
        models.CustomerVisit.visit_date >= start_dt,
        models.CustomerVisit.visit_date <= end_dt
    ).count()
    
    # Revenue today
    revenue_today = db.query(func.sum(models.CustomerPurchase.total_amount)).filter(
        models.CustomerPurchase.purchase_date >= start_dt,
        models.CustomerPurchase.purchase_date <= end_dt
    ).scalar() or 0
    
    return {
        'date': target_date.isoformat(),
        'contacts_processed': contacts_today,
        'interactions': interactions_today,
        'conversions': conversions_today,
        'customer_visits': visits_today,
        'revenue': float(revenue_today)
    }

# AI ANALYTICS

@router.get("/ai-analytics/comprehensive")
def get_comprehensive_ai_analytics(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get comprehensive AI analytics with insights, trends, and recommendations"""
    return CustomerTrackingAI.comprehensive_analytics(db, days)