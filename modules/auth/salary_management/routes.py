from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from app.database.database import get_db
from datetime import datetime, date
from typing import Optional, List
from . import schemas, models, service
from ..models import Staff
from ..dependencies import get_current_admin, get_current_staff

router = APIRouter()

# ADMIN ROUTES

@router.get("/dashboard", response_model=schemas.SalaryDashboard)
def get_salary_dashboard(
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get salary management dashboard for admin"""
    service.SalaryService.update_overdue_status(db)
    return service.SalaryService.get_salary_dashboard(db)

@router.post("/records", response_model=schemas.SalaryRecord)
def create_salary_record(
    salary_data: schemas.SalaryRecordCreate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create salary record for staff"""
    try:
        return service.SalaryService.create_salary_record(db, salary_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/records", response_model=List[schemas.SalaryRecord])
def get_salary_records(
    staff_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[schemas.PaymentStatusEnum] = None,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get salary records with filters"""
    
    query = db.query(models.SalaryRecord)
    
    if staff_id:
        query = query.filter(models.SalaryRecord.staff_id == staff_id)
    if month:
        query = query.filter(models.SalaryRecord.month == month)
    if year:
        query = query.filter(models.SalaryRecord.year == year)
    if status:
        query = query.filter(models.SalaryRecord.payment_status == status.value)
    
    return query.order_by(models.SalaryRecord.due_date.desc()).all()

@router.put("/records/{record_id}/pay", response_model=schemas.SalaryRecord)
def pay_salary(
    record_id: int,
    payment_data: schemas.SalaryPayment,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Mark salary as paid"""
    try:
        payment_data.paid_by_admin = admin.full_name
        return service.SalaryService.pay_salary(db, record_id, payment_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/staff/{staff_id}/profile", response_model=schemas.StaffSalaryProfile)
def get_staff_salary_profile(
    staff_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get complete salary profile for staff"""
    try:
        return service.SalaryService.get_staff_salary_profile(db, staff_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/staff/{staff_id}/history", response_model=schemas.StaffSalaryHistory)
def get_staff_salary_history(
    staff_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get salary history for staff"""
    
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")
    
    records = db.query(models.SalaryRecord).filter(
        models.SalaryRecord.staff_id == staff_id
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
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get staff payment information"""
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == staff_id
    ).first()
    
    if not payment_info:
        raise HTTPException(status_code=404, detail="Payment info not found")
    
    return payment_info

@router.get("/staff/{staff_id}/qr-code")
def get_staff_qr_code(
    staff_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Download staff QR code"""
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == staff_id
    ).first()
    
    if not payment_info or not payment_info.qr_code_path:
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return FileResponse(payment_info.qr_code_path)

@router.get("/alerts", response_model=List[schemas.SalaryAlert])
def get_salary_alerts(
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all active salary alerts"""
    return service.SalaryService.get_active_alerts(db)

@router.put("/alerts/{alert_id}/dismiss")
def dismiss_alert(
    alert_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Dismiss salary alert"""
    
    alert = db.query(models.SalaryAlert).filter(models.SalaryAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_dismissed = True
    db.commit()
    
    return {"message": "Alert dismissed"}

@router.post("/generate-monthly-records/{year}/{month}")
def generate_monthly_salary_records(
    year: int,
    month: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Auto-generate salary records for all eligible staff for a given month"""
    
    from datetime import date, timedelta
    from calendar import monthrange
    
    # Get all staff with salary set
    staff_list = db.query(Staff).filter(
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
        
        # Create salary record with due date based on joining date + eligibility days
        if staff.joining_date:
            due_date = staff.joining_date + timedelta(days=staff.salary_eligibility_days)
        else:
            # Fallback to end of month if no joining date
            due_date = date(year, month, last_day)
        
        salary_record = models.SalaryRecord(
            staff_id=staff.id,
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
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get monthly salary summary"""
    
    records = db.query(models.SalaryRecord).filter(
        and_(
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
    pending_amount = total_amount - paid_amount
    
    return schemas.MonthlySalarySummary(
        month=month,
        year=year,
        total_staff=total_staff,
        paid_count=paid_count,
        pending_count=pending_count,
        overdue_count=overdue_count,
        total_salary_amount=total_amount,
        paid_amount=paid_amount,
        pending_amount=pending_amount
    )

# STAFF ROUTES

@router.get("/my-profile", response_model=schemas.StaffSalaryProfile)
def get_my_salary_profile(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's salary profile"""
    try:
        return service.SalaryService.get_staff_salary_profile(db, staff.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/my-history", response_model=schemas.StaffSalaryHistory)
def get_my_salary_history(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's salary history"""
    
    staff_id = staff.id
    staff_obj = db.query(Staff).filter(Staff.id == staff_id).first()
    
    records = db.query(models.SalaryRecord).filter(
        models.SalaryRecord.staff_id == staff_id
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
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Update current staff's payment information"""
    return service.PaymentInfoService.update_payment_info(db, staff.id, payment_data)

@router.post("/my-qr-code")
def upload_my_qr_code(
    file: UploadFile = File(...),
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Upload QR code for current staff"""
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    file_content = file.file.read()
    file_path = service.PaymentInfoService.upload_qr_code(db, staff.id, file_content, file.filename)
    
    return {"message": "QR code uploaded successfully", "file_path": file_path}

@router.get("/my-payment-info", response_model=schemas.StaffPaymentInfo)
def get_my_payment_info(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's payment information"""
    
    payment_info = db.query(models.StaffPaymentInfo).filter(
        models.StaffPaymentInfo.staff_id == staff.id
    ).first()
    
    if not payment_info:
        # Create empty payment info
        payment_info = models.StaffPaymentInfo(staff_id=staff.id)
        db.add(payment_info)
        db.commit()
        db.refresh(payment_info)
    
    return payment_info