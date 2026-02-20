from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import date
from typing import List, Optional
from . import schemas, models, services
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Staff, Shop

def get_current_user(user_dict: dict = Depends(get_user_dict), db: Session = Depends(get_db)) -> tuple[Staff, int]:
    """Extract staff user and resolve shop_id"""
    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    staff = user_dict["user"]
    shop_code = user_dict["token_data"].shop_code
    
    shop = db.query(Shop).filter(
        Shop.shop_code == shop_code,
        Shop.organization_id == staff.shop.organization_id
    ).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    return staff, shop.id

router = APIRouter()

# CONTACT RECORDS

@router.post("/contacts/upload", response_model=schemas.ContactUploadResponse)
async def upload_contacts(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Upload contact records from Excel/CSV file"""
    staff, shop_id = current_user
    
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Only Excel and CSV files supported")
    
    content = await file.read()
    
    try:
        stats = services.CustomerTrackingService.process_contact_file(
            db, shop_id, content, file.filename, staff.id
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/contacts", response_model=List[schemas.ContactRecordResponse])
def get_contacts(
    contact_status: Optional[str] = None,
    whatsapp_status: Optional[str] = None,
    assigned_staff_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get contact records with filters"""
    staff, shop_id = current_user
    
    query = db.query(models.ContactRecord).filter(models.ContactRecord.shop_id == shop_id)
    
    if contact_status:
        query = query.filter(models.ContactRecord.contact_status == contact_status)
    if whatsapp_status:
        query = query.filter(models.ContactRecord.whatsapp_status == whatsapp_status)
    if assigned_staff_id:
        query = query.filter(models.ContactRecord.assigned_staff_id == assigned_staff_id)
    
    return query.order_by(models.ContactRecord.created_at.desc()).offset(skip).limit(limit).all()

@router.post("/contacts/assign")
def assign_contacts(
    staff_ids: List[int],
    contact_status: str = "pending",
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Assign pending contacts to staff members"""
    staff, shop_id = current_user
    
    if not staff.can_manage_staff:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    services.CustomerTrackingService.assign_contacts_to_staff(db, shop_id, staff_ids, contact_status)
    return {"message": "Contacts assigned successfully"}

@router.put("/contacts/{contact_id}", response_model=schemas.ContactRecordResponse)
def update_contact(
    contact_id: int,
    data: schemas.ContactRecordUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Update contact record"""
    staff, shop_id = current_user
    
    contact = db.query(models.ContactRecord).filter(
        models.ContactRecord.id == contact_id,
        models.ContactRecord.shop_id == shop_id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    
    db.commit()
    db.refresh(contact)
    return contact

@router.post("/contacts/{contact_id}/interactions")
def add_interaction(
    contact_id: int,
    data: schemas.ContactInteractionCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Add interaction to contact"""
    staff, shop_id = current_user
    
    contact = db.query(models.ContactRecord).filter(
        models.ContactRecord.id == contact_id,
        models.ContactRecord.shop_id == shop_id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    interaction = services.CustomerTrackingService.add_interaction(
        db, shop_id, contact_id, staff.id, data.model_dump()
    )
    return interaction

@router.post("/contacts/{contact_id}/reminders")
def add_reminder(
    contact_id: int,
    data: schemas.ContactReminderCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Add reminder for contact"""
    staff, shop_id = current_user
    
    reminder = models.ContactReminder(
        shop_id=shop_id,
        contact_id=contact_id,
        staff_id=staff.id,
        **data.model_dump()
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

@router.post("/contacts/{contact_id}/mark-yellow")
def mark_contact_yellow(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Mark contact as yellow (visited but didn't buy)"""
    staff, shop_id = current_user
    
    contact = db.query(models.ContactRecord).filter(
        models.ContactRecord.id == contact_id,
        models.ContactRecord.shop_id == shop_id
    ).first()
    
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    services.CustomerTrackingService.mark_contact_yellow(db, contact.phone, shop_id)
    return {"message": "Contact marked as yellow"}

# CUSTOMERS

@router.post("/customers", response_model=schemas.CustomerResponse)
def create_customer(
    data: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Create or get customer"""
    staff, shop_id = current_user
    
    customer = services.CustomerTrackingService.get_or_create_customer(
        db, shop_id, data.phone, data.name, data.category, data.contact_record_id
    )
    return customer

@router.get("/customers", response_model=List[schemas.CustomerResponse])
def get_customers(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get customers with filters"""
    staff, shop_id = current_user
    
    query = db.query(models.Customer).filter(models.Customer.shop_id == shop_id)
    
    if category:
        query = query.filter(models.Customer.category == category)
    
    return query.order_by(models.Customer.last_visit_date.desc()).offset(skip).limit(limit).all()

@router.get("/customers/phone/{phone}", response_model=schemas.CustomerResponse)
def get_customer_by_phone(
    phone: str,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get customer by phone number"""
    staff, shop_id = current_user
    
    customer = db.query(models.Customer).filter(
        models.Customer.shop_id == shop_id,
        models.Customer.phone == phone
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer

@router.put("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    data: schemas.CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Update customer details"""
    staff, shop_id = current_user
    
    customer = db.query(models.Customer).filter(
        models.Customer.id == customer_id,
        models.Customer.shop_id == shop_id
    ).first()
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    
    db.commit()
    db.refresh(customer)
    return customer

# REFILL REMINDERS

@router.get("/refill-reminders", response_model=List[schemas.RefillReminderResponse])
def get_refill_reminders(
    days_ahead: int = 0,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get due refill reminders"""
    staff, shop_id = current_user
    
    reminders = services.CustomerTrackingService.get_due_refill_reminders(db, shop_id, days_ahead)
    
    result = []
    for r in reminders:
        result.append({
            "id": r.id,
            "customer_id": r.customer_id,
            "customer_name": r.customer.name,
            "customer_phone": r.customer.phone,
            "medicine_name": r.medicine_name,
            "reminder_date": r.reminder_date,
            "whatsapp_sent": r.whatsapp_sent,
            "call_reminder_sent": r.call_reminder_sent,
            "customer_responded": r.customer_responded,
            "customer_purchased": r.customer_purchased
        })
    
    return result

@router.post("/refill-reminders/{reminder_id}/mark-sent")
def mark_reminder_sent(
    reminder_id: int,
    method: str = Query(..., regex="^(whatsapp|call)$"),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Mark reminder as sent"""
    staff, shop_id = current_user
    
    reminder = db.query(models.RefillReminder).filter(
        models.RefillReminder.id == reminder_id,
        models.RefillReminder.shop_id == shop_id
    ).first()
    
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    from datetime import datetime
    if method == "whatsapp":
        reminder.whatsapp_sent = True
        reminder.whatsapp_sent_date = datetime.utcnow()
    elif method == "call":
        reminder.call_reminder_sent = True
        reminder.call_reminder_date = datetime.utcnow()
    
    db.commit()
    return {"message": f"Reminder marked as sent via {method}"}

# REPORTS

@router.get("/reports/conversion")
def get_conversion_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get contact conversion report"""
    staff, shop_id = current_user
    
    return services.CustomerTrackingService.get_contact_conversion_report(
        db, shop_id, start_date, end_date
    )
