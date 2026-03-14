from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from app.database.database import get_db
from datetime import datetime, date
from typing import Optional, List
from . import schemas, models, service
from .dependencies import get_current_salary_user
from ..models import Staff

router = APIRouter()

# ADMIN ROUTES

@router.get("/dashboard", response_model=schemas.SalaryDashboard)
def get_salary_dashboard(
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get salary management dashboard for admin"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service.SalaryService.update_overdue_status(db, shop_id)
    return service.SalaryService.get_salary_dashboard(db, shop_id)

@router.post("/records", response_model=schemas.SalaryRecord)
def create_salary_record(
    salary_data: schemas.SalaryRecordCreate,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Create salary record for staff"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        return service.SalaryService.create_salary_record(db, salary_data, shop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/records", response_model=List[schemas.SalaryRecord])
def get_salary_records(
    staff_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[schemas.PaymentStatusEnum] = None,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get salary records with filters"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(models.SalaryRecord, Staff.name).join(
        Staff, models.SalaryRecord.staff_id == Staff.id
    ).filter(models.SalaryRecord.shop_id == shop_id)
    
    if staff_id:
        query = query.filter(models.SalaryRecord.staff_id == staff_id)
    if month:
        query = query.filter(models.SalaryRecord.month == month)
    if year:
        query = query.filter(models.SalaryRecord.year == year)
    if status:
        query = query.filter(models.SalaryRecord.payment_status == status.value)
    
    results = query.order_by(models.SalaryRecord.due_date.desc()).all()
    
    return [
        schemas.SalaryRecord(
            id=record.id,
            staff_id=record.staff_id,
            staff_name=staff_name,
            month=record.month,
            year=record.year,
            salary_amount=record.salary_amount,
            payment_status=record.payment_status,
            payment_date=record.payment_date,
            paid_by_admin=record.paid_by_admin,
            due_date=record.due_date,
            notes=record.notes,
            created_at=record.created_at,
            updated_at=record.updated_at
        )
        for record, staff_name in results
    ]

@router.put("/records/{record_id}/pay", response_model=schemas.SalaryRecord)
def pay_salary(
    record_id: int,
    payment_data: schemas.SalaryPayment,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Mark salary as paid"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        payment_data.paid_by_admin = user.full_name
        return service.SalaryService.pay_salary(db, record_id, payment_data, shop_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/staff/{staff_id}/profile", response_model=schemas.StaffSalaryProfile)
def get_staff_salary_profile(
    staff_id: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get complete salary profile for staff"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        return service.SalaryService.get_staff_salary_profile(db, staff_id, shop_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/staff/{staff_id}/history", response_model=schemas.StaffSalaryHistory)
def get_staff_salary_history(
    staff_id: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get salary history for staff"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.shop_id == shop_id
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    records = db.query(models.SalaryRecord).filter(
        models.SalaryRecord.staff_id == staff_id,
        models.SalaryRecord.shop_id == shop_id
    ).order_by(models.SalaryRecord.year.desc(), models.SalaryRecord.month.desc()).all()
    
    paid_records = [r for r in records if r.payment_status == models.PaymentStatus.PAID.value]
    pending_records = [r for r in records if r.payment_status != models.PaymentStatus.PAID.value]
    
    total_paid = sum(r.salary_amount for r in paid_records)
    total_pending = sum(r.salary_amount for r in pending_records)
    
    return schemas.StaffSalaryHistory(
        staff_id=staff_id,
        staff_name=staff.name,
        records=records,
        total_paid=total_paid,
        total_pending=total_pending,
        months_paid=len(paid_records),
        months_pending=len(pending_records)
    )

@router.get("/staff/{staff_id}/payment-info", response_model=schemas.StaffPaymentInfo)
def get_staff_payment_info(
    staff_id: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get staff payment information"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == staff_id,
        models.StaffPaymentInfo.shop_id == shop_id
    ).first()
    
    if not payment_info:
        raise HTTPException(status_code=404, detail="Payment info not found")
    
    return payment_info

@router.get("/staff/{staff_id}/qr-code")
def get_staff_qr_code(
    staff_id: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Download staff QR code"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == staff_id,
        models.StaffPaymentInfo.shop_id == shop_id
    ).first()
    
    if not payment_info or not payment_info.qr_code_path:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return FileResponse(payment_info.qr_code_path)

@router.get("/alerts", response_model=List[schemas.SalaryAlert])
def get_salary_alerts(
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get all active salary alerts"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return service.SalaryService.get_active_alerts(db, shop_id)

@router.put("/alerts/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Dismiss salary alert"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    alert = db.query(models.SalaryAlert).filter(
        models.SalaryAlert.id == alert_id,
        models.SalaryAlert.shop_id == shop_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_dismissed = True
    db.commit()
    
    return {"message": "Alert dismissed"}

@router.post("/generate-monthly-records/{year}/{month}")
def generate_monthly_salary_records(
    year: int,
    month: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Auto-generate salary records for all eligible staff for a given month"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from datetime import date, timedelta
    from calendar import monthrange
    
    # Get all staff with salary set
    staff_list = db.query(Staff).filter(
        Staff.shop_id == shop_id,
        Staff.monthly_salary.isnot(None),
        Staff.is_active == True
    ).all()
    
    created_count = 0
    skipped_count = 0
    
    # Last day of the month as due date
    last_day = monthrange(year, month)[1]
    due_date = date(year, month, last_day)
    
    for staff in staff_list:
        # Check if record already exists
        existing = db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.staff_id == staff.id,
                models.SalaryRecord.shop_id == shop_id,
                models.SalaryRecord.month == month,
                models.SalaryRecord.year == year
            )
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # Check eligibility
        if not service.SalaryService._is_staff_eligible_for_salary(staff):
            skipped_count += 1
            continue
        
        # Due date is 5th of next month (e.g., Jan salary due on Feb 5)
        if month == 12:
            due_date = date(year + 1, 1, 5)
        else:
            due_date = date(year, month + 1, 5)
        
        salary_record = models.SalaryRecord(
            staff_id=staff.id,
            shop_id=shop_id,
            month=month,
            year=year,
            salary_amount=staff.monthly_salary,
            due_date=due_date
        )
        
        db.add(salary_record)
        created_count += 1
    
    db.commit()
    
    return {
        "message": f"Generated salary records for {month}/{year}",
        "created": created_count,
        "skipped": skipped_count
    }

@router.get("/monthly-summary/{year}/{month}", response_model=schemas.MonthlySalarySummary)
def get_monthly_salary_summary(
    year: int,
    month: int,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get monthly salary summary"""
    user, shop_id, user_type = current_user
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    records = db.query(models.SalaryRecord).filter(
        and_(
            models.SalaryRecord.shop_id == shop_id,
            models.SalaryRecord.year == year,
            models.SalaryRecord.month == month
        )
    ).all()
    
    total_staff = len(records)
    paid_count = len([r for r in records if r.payment_status == models.PaymentStatus.PAID.value])
    pending_count = len([r for r in records if r.payment_status == models.PaymentStatus.PENDING.value])
    overdue_count = len([r for r in records if r.payment_status == models.PaymentStatus.OVERDUE.value])
    
    total_amount = sum(r.salary_amount for r in records)
    paid_amount = sum(r.salary_amount for r in records if r.payment_status == models.PaymentStatus.PAID.value)
    pending_amount = sum(r.salary_amount for r in records if r.payment_status == models.PaymentStatus.PENDING.value)
    overdue_amount = sum(r.salary_amount for r in records if r.payment_status == models.PaymentStatus.OVERDUE.value)

    return schemas.MonthlySalarySummary(
        month=month,
        year=year,
        total_staff=total_staff,
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        total_salary_amount=total_amount,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount
    )

# STAFF ROUTES

@router.get("/my-profile", response_model=schemas.StaffSalaryProfile)
def get_my_salary_profile(
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get current staff's salary profile"""
    user, shop_id, user_type = current_user
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    try:
        return service.SalaryService.get_staff_salary_profile(db, user.id, shop_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/my-history", response_model=schemas.StaffSalaryHistory)
def get_my_salary_history(
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get current staff's salary history"""
    user, shop_id, user_type = current_user
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    staff_id = user.id
    staff_obj = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.shop_id == shop_id
    ).first()
    
    records = db.query(models.SalaryRecord).filter(
        models.SalaryRecord.staff_id == staff_id,
        models.SalaryRecord.shop_id == shop_id
    ).order_by(models.SalaryRecord.year.desc(), models.SalaryRecord.month.desc()).all()
    
    paid_records = [r for r in records if r.payment_status == models.PaymentStatus.PAID.value]
    pending_records = [r for r in records if r.payment_status != models.PaymentStatus.PAID.value]
    
    total_paid = sum(r.salary_amount for r in paid_records)
    total_pending = sum(r.salary_amount for r in pending_records)
    
    return schemas.StaffSalaryHistory(
        staff_id=staff_id,
        staff_name=staff_obj.name,
        records=records,
        total_paid=total_paid,
        total_pending=total_pending,
        months_paid=len(paid_records),
        months_pending=len(pending_records)
    )

@router.put("/my-payment-info", response_model=schemas.StaffPaymentInfo)
def update_my_payment_info(
    payment_data: schemas.StaffPaymentInfoUpdate,
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Update current staff's payment information"""
    user, shop_id, user_type = current_user
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    return service.PaymentInfoService.update_payment_info(db, user.id, payment_data, shop_id)

@router.post("/my-qr-code")
def upload_my_qr_code(
    file: UploadFile = File(...),
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Upload QR code for current staff"""
    user, shop_id, user_type = current_user
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    file_content = file.file.read()
    file_path = service.PaymentInfoService.upload_qr_code(db, user.id, file_content, file.filename, shop_id)
    
    return {"message": "QR code uploaded successfully", "file_path": file_path}

@router.get("/my-payment-info", response_model=schemas.StaffPaymentInfo)
def get_my_payment_info(
    current_user: tuple = Depends(get_current_salary_user),
    db: Session = Depends(get_db)
):
    """Get current staff's payment information"""
    user, shop_id, user_type = current_user
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == user.id,
        models.StaffPaymentInfo.shop_id == shop_id
    ).first()
    
    if not payment_info:
        # Create empty payment info
        payment_info = models.StaffPaymentInfo(staff_id=user.id, shop_id=shop_id)
        db.add(payment_info)
        db.commit()
        db.refresh(payment_info)
    
    return payment_info