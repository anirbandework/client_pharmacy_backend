from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from . import models, schemas
from ..models import Staff
import os
import uuid

class SalaryService:
    
    @staticmethod
    def create_salary_record(db: Session, salary_data: schemas.SalaryRecordCreate) -> models.SalaryRecord:
        """Create a new salary record"""
        
        # Check if record already exists for this month/year
        existing = db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.staff_id == salary_data.staff_id,
                models.SalaryRecord.month == salary_data.month,
                models.SalaryRecord.year == salary_data.year
            )
        ).first()
        
        if existing:
            raise ValueError(f"Salary record already exists for {salary_data.month}/{salary_data.year}")
        
        # Create record
        db_record = models.SalaryRecord(**salary_data.model_dump())
        
        # Set status based on due date
        if db_record.due_date < date.today():
            db_record.payment_status = models.PaymentStatus.OVERDUE.value
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # Create alert if due in next 5 days
        SalaryService._create_alerts_for_record(db, db_record)
        
        return db_record
    
    @staticmethod
    def pay_salary(db: Session, record_id: int, payment_data: schemas.SalaryPayment) -> models.SalaryRecord:
        """Mark salary as paid"""
        
        record = db.query(models.SalaryRecord).filter(models.SalaryRecord.id == record_id).first()
        if not record:
            raise ValueError("Salary record not found")
        
        if record.payment_status == models.PaymentStatus.PAID.value:
            raise ValueError("Salary already paid")
        
        record.payment_status = models.PaymentStatus.PAID.value
        record.payment_date = datetime.utcnow()
        record.paid_by_admin = payment_data.paid_by_admin
        if payment_data.notes:
            record.notes = payment_data.notes
        
        db.commit()
        db.refresh(record)
        
        # Dismiss related alerts
        db.query(models.SalaryAlert).filter(
            models.SalaryAlert.salary_record_id == record_id
        ).update({"is_dismissed": True})
        db.commit()
        
        return record
    
    @staticmethod
    def get_staff_salary_profile(db: Session, staff_id: int) -> schemas.StaffSalaryProfile:
        """Get complete salary profile for staff"""
        
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            raise ValueError("Staff not found")
        
        # Get payment info
        payment_info = db.query(models.StaffPaymentInfo).filter(
            models.StaffPaymentInfo.staff_id == staff_id
        ).first()
        
        # Get salary statistics
        records = db.query(models.SalaryRecord).filter(
            models.SalaryRecord.staff_id == staff_id
        ).all()
        
        pending_months = len([r for r in records if r.payment_status == models.PaymentStatus.PENDING.value])
        paid_months = len([r for r in records if r.payment_status == models.PaymentStatus.PAID.value])
        overdue_months = len([r for r in records if r.payment_status == models.PaymentStatus.OVERDUE.value])
        
        # Get last payment and next due date
        last_payment = db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.staff_id == staff_id,
                models.SalaryRecord.payment_status == models.PaymentStatus.PAID.value
            )
        ).order_by(models.SalaryRecord.payment_date.desc()).first()
        
        next_due = db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.staff_id == staff_id,
                models.SalaryRecord.payment_status.in_([
                    models.PaymentStatus.PENDING.value,
                    models.PaymentStatus.OVERDUE.value
                ])
            )
        ).order_by(models.SalaryRecord.due_date.asc()).first()
        
        # Check salary eligibility
        is_eligible = SalaryService._is_staff_eligible_for_salary(staff)
        
        return schemas.StaffSalaryProfile(
            id=staff.id,
            name=staff.name,
            staff_code=staff.staff_code,
            phone=staff.phone,
            email=staff.email,
            monthly_salary=staff.monthly_salary,
            payment_info=payment_info,
            pending_months=pending_months,
            paid_months=paid_months,
            overdue_months=overdue_months,
            last_payment_date=last_payment.payment_date if last_payment else None,
            joining_date=staff.joining_date,
            salary_eligibility_days=staff.salary_eligibility_days,
            is_eligible_for_salary=is_eligible
        )
    
    @staticmethod
    def get_salary_dashboard(db: Session) -> schemas.SalaryDashboard:
        """Get admin dashboard with salary overview"""
        
        total_staff = db.query(Staff).count()
        
        # Count pending and overdue payments
        pending_count = db.query(models.SalaryRecord).filter(
            models.SalaryRecord.payment_status == models.PaymentStatus.PENDING.value
        ).count()
        
        overdue_count = db.query(models.SalaryRecord).filter(
            models.SalaryRecord.payment_status == models.PaymentStatus.OVERDUE.value
        ).count()
        
        # Upcoming payments (due in next 5 days)
        upcoming_date = date.today() + timedelta(days=5)
        upcoming_count = db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.payment_status == models.PaymentStatus.PENDING.value,
                models.SalaryRecord.due_date <= upcoming_date,
                models.SalaryRecord.due_date >= date.today()
            )
        ).count()
        
        # Calculate amounts
        pending_amount = db.query(func.sum(models.SalaryRecord.salary_amount)).filter(
            models.SalaryRecord.payment_status == models.PaymentStatus.PENDING.value
        ).scalar() or 0
        
        overdue_amount = db.query(func.sum(models.SalaryRecord.salary_amount)).filter(
            models.SalaryRecord.payment_status == models.PaymentStatus.OVERDUE.value
        ).scalar() or 0
        
        # Get active alerts
        alerts = SalaryService.get_active_alerts(db)
        
        return schemas.SalaryDashboard(
            total_staff=total_staff,
            pending_payments=pending_count,
            overdue_payments=overdue_count,
            upcoming_payments=upcoming_count,
            total_pending_amount=pending_amount,
            total_overdue_amount=overdue_amount,
            alerts=alerts
        )
    
    @staticmethod
    def get_active_alerts(db: Session) -> List[schemas.SalaryAlert]:
        """Get all active salary alerts"""
        
        alerts = db.query(
            models.SalaryAlert,
            Staff.name,
            models.SalaryRecord.month,
            models.SalaryRecord.year,
            models.SalaryRecord.salary_amount
        ).join(
            Staff, models.SalaryAlert.staff_id == Staff.id
        ).join(
            models.SalaryRecord, models.SalaryAlert.salary_record_id == models.SalaryRecord.id
        ).filter(
            models.SalaryAlert.is_dismissed == False
        ).order_by(models.SalaryAlert.alert_date.asc()).all()
        
        return [
            schemas.SalaryAlert(
                id=alert.id,
                staff_id=alert.staff_id,
                salary_record_id=alert.salary_record_id,
                alert_type=alert.alert_type,
                alert_date=alert.alert_date,
                is_dismissed=alert.is_dismissed,
                created_at=alert.created_at,
                staff_name=name,
                month=month,
                year=year,
                salary_amount=salary_amount
            )
            for alert, name, month, year, salary_amount in alerts
        ]
    
    @staticmethod
    def update_overdue_status(db: Session):
        """Update overdue status for pending payments"""
        
        db.query(models.SalaryRecord).filter(
            and_(
                models.SalaryRecord.payment_status == models.PaymentStatus.PENDING.value,
                models.SalaryRecord.due_date < date.today()
            )
        ).update({"payment_status": models.PaymentStatus.OVERDUE.value})
        
        db.commit()
    
    @staticmethod
    def _create_alerts_for_record(db: Session, record: models.SalaryRecord):
        """Create alerts for salary record"""
        
        # Create upcoming alert (5 days before due date)
        alert_date = record.due_date - timedelta(days=5)
        if alert_date >= date.today():
            alert = models.SalaryAlert(
                staff_id=record.staff_id,
                salary_record_id=record.id,
                alert_type="upcoming",
                alert_date=alert_date
            )
            db.add(alert)
        
        # Create overdue alert if already overdue
        if record.due_date < date.today():
            alert = models.SalaryAlert(
                staff_id=record.staff_id,
                salary_record_id=record.id,
                alert_type="overdue",
                alert_date=date.today()
            )
            db.add(alert)
        
        db.commit()
    
    @staticmethod
    def _is_staff_eligible_for_salary(staff) -> bool:
        """Check if staff should receive salary (always true if they have joining date)"""
        return staff.joining_date is not None

class PaymentInfoService:
    
    @staticmethod
    def update_payment_info(db: Session, staff_id: int, payment_data: schemas.StaffPaymentInfoUpdate) -> models.StaffPaymentInfo:
        """Update staff payment information"""
        
        payment_info = db.query(models.StaffPaymentInfo).filter(
            models.StaffPaymentInfo.staff_id == staff_id
        ).first()
        
        if not payment_info:
            payment_info = models.StaffPaymentInfo(staff_id=staff_id)
            db.add(payment_info)
        
        # Update fields
        for field, value in payment_data.model_dump(exclude_unset=True).items():
            setattr(payment_info, field, value)
        
        payment_info.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(payment_info)
        
        return payment_info
    
    @staticmethod
    def upload_qr_code(db: Session, staff_id: int, file_content: bytes, filename: str) -> str:
        """Upload and save QR code image"""
        
        # Create uploads directory if not exists
        upload_dir = "uploads/qr_codes"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_extension = filename.split('.')[-1]
        unique_filename = f"{staff_id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Update payment info
        payment_info = db.query(models.StaffPaymentInfo).filter(
            models.StaffPaymentInfo.staff_id == staff_id
        ).first()
        
        if not payment_info:
            payment_info = models.StaffPaymentInfo(staff_id=staff_id)
            db.add(payment_info)
        
        payment_info.qr_code_path = file_path
        payment_info.updated_at = datetime.utcnow()
        db.commit()
        
        return file_path