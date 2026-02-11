from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Dict
from . import models, schemas
from ..models import Staff, Shop

class AttendanceService:
    
    @staticmethod
    def wifi_check_in(db: Session, mac_address: str, wifi_ssid: str) -> models.AttendanceRecord:
        """Auto check-in when staff device connects to shop WiFi"""
        
        # Find device by MAC address
        device = db.query(models.StaffDevice).filter(
            models.StaffDevice.mac_address == mac_address.upper(),
            models.StaffDevice.is_active == True
        ).first()
        
        if not device:
            raise ValueError("Device not registered. Please register your device first.")
        
        # Find shop WiFi
        shop_wifi = db.query(models.ShopWiFi).filter(
            models.ShopWiFi.wifi_ssid == wifi_ssid,
            models.ShopWiFi.is_active == True
        ).first()
        
        if not shop_wifi:
            raise ValueError("WiFi network not recognized")
        
        # Get staff and verify they belong to this shop
        staff = db.query(Staff).filter(Staff.id == device.staff_id).first()
        if staff.shop_id != shop_wifi.shop_id:
            raise ValueError("Staff does not belong to this shop")
        
        # Check if already checked in today
        today = date.today()
        existing = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == staff.id,
            models.AttendanceRecord.date == today
        ).first()
        
        if existing:
            # Update last seen
            device.last_seen = datetime.now()
            db.commit()
            return existing
        
        # Get attendance settings
        settings = AttendanceService._get_or_create_settings(db, staff.shop_id)
        
        # Calculate if late
        now = datetime.now()
        check_in_time = now.time()
        grace_end = (datetime.combine(today, settings.work_start_time) + 
                     timedelta(minutes=settings.grace_period_minutes)).time()
        
        is_late = check_in_time > grace_end
        late_by_minutes = 0
        
        if is_late:
            start_dt = datetime.combine(today, settings.work_start_time)
            checkin_dt = datetime.combine(today, check_in_time)
            late_by_minutes = int((checkin_dt - start_dt).total_seconds() / 60)
        
        # Create attendance record
        attendance = models.AttendanceRecord(
            staff_id=staff.id,
            shop_id=staff.shop_id,
            device_id=device.id,
            wifi_id=shop_wifi.id,
            date=today,
            check_in_time=now,
            status="late" if is_late else "present",
            is_late=is_late,
            late_by_minutes=late_by_minutes,
            auto_checked_in=True
        )
        
        db.add(attendance)
        device.last_seen = now
        db.commit()
        db.refresh(attendance)
        
        return attendance
    
    @staticmethod
    def manual_check_in(db: Session, staff_id: int, notes: Optional[str] = None) -> models.AttendanceRecord:
        """Manual check-in by admin or staff"""
        
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            raise ValueError("Staff not found")
        
        today = date.today()
        existing = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == staff_id,
            models.AttendanceRecord.date == today
        ).first()
        
        if existing:
            raise ValueError("Already checked in today")
        
        settings = AttendanceService._get_or_create_settings(db, staff.shop_id)
        now = datetime.now()
        check_in_time = now.time()
        grace_end = (datetime.combine(today, settings.work_start_time) + 
                     timedelta(minutes=settings.grace_period_minutes)).time()
        
        is_late = check_in_time > grace_end
        late_by_minutes = 0
        
        if is_late:
            start_dt = datetime.combine(today, settings.work_start_time)
            checkin_dt = datetime.combine(today, check_in_time)
            late_by_minutes = int((checkin_dt - start_dt).total_seconds() / 60)
        
        attendance = models.AttendanceRecord(
            staff_id=staff_id,
            shop_id=staff.shop_id,
            date=today,
            check_in_time=now,
            status="late" if is_late else "present",
            is_late=is_late,
            late_by_minutes=late_by_minutes,
            auto_checked_in=False,
            notes=notes
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        return attendance
    
    @staticmethod
    def check_out(db: Session, staff_id: int, notes: Optional[str] = None) -> models.AttendanceRecord:
        """Check out staff"""
        
        today = date.today()
        attendance = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == staff_id,
            models.AttendanceRecord.date == today
        ).first()
        
        if not attendance:
            raise ValueError("No check-in record found for today")
        
        if attendance.check_out_time:
            raise ValueError("Already checked out")
        
        now = datetime.now()
        attendance.check_out_time = now
        
        # Calculate total hours
        time_diff = now - attendance.check_in_time
        attendance.total_hours = int(time_diff.total_seconds() / 60)
        
        if notes:
            attendance.notes = notes
        
        db.commit()
        db.refresh(attendance)
        
        return attendance
    
    @staticmethod
    def get_today_attendance(db: Session, shop_id: int) -> List[Dict]:
        """Get today's attendance for all staff in shop"""
        
        today = date.today()
        
        # Get all active staff
        staff_list = db.query(Staff).filter(
            Staff.shop_id == shop_id,
            Staff.is_active == True
        ).all()
        
        result = []
        for staff in staff_list:
            attendance = db.query(models.AttendanceRecord).filter(
                models.AttendanceRecord.staff_id == staff.id,
                models.AttendanceRecord.date == today
            ).first()
            
            # Check if on leave
            on_leave = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.staff_id == staff.id,
                models.LeaveRequest.status == "approved",
                models.LeaveRequest.from_date <= today,
                models.LeaveRequest.to_date >= today
            ).first()
            
            result.append({
                "staff_id": staff.id,
                "staff_name": staff.name,
                "staff_code": staff.staff_code,
                "attendance": attendance,
                "on_leave": on_leave is not None,
                "status": "on_leave" if on_leave else (attendance.status if attendance else "absent")
            })
        
        return result
    
    @staticmethod
    def get_attendance_summary(db: Session, shop_id: int) -> schemas.AttendanceSummary:
        """Get attendance summary for today"""
        
        today_attendance = AttendanceService.get_today_attendance(db, shop_id)
        
        total_staff = len(today_attendance)
        present = len([a for a in today_attendance if a["attendance"] and a["status"] != "on_leave"])
        late = len([a for a in today_attendance if a["attendance"] and a["attendance"].is_late])
        on_leave = len([a for a in today_attendance if a["on_leave"]])
        absent = total_staff - present - on_leave
        
        pending_leaves = db.query(models.LeaveRequest).join(Staff).filter(
            Staff.shop_id == shop_id,
            models.LeaveRequest.status == "pending"
        ).count()
        
        return schemas.AttendanceSummary(
            total_staff=total_staff,
            present_today=present,
            absent_today=absent,
            late_today=late,
            on_leave_today=on_leave,
            pending_leave_requests=pending_leaves
        )
    
    @staticmethod
    def get_monthly_report(db: Session, shop_id: int, month: int, year: int) -> schemas.MonthlyAttendanceReport:
        """Generate monthly attendance report"""
        
        staff_list = db.query(Staff).filter(
            Staff.shop_id == shop_id,
            Staff.is_active == True
        ).all()
        
        summaries = []
        
        for staff in staff_list:
            records = db.query(models.AttendanceRecord).filter(
                models.AttendanceRecord.staff_id == staff.id,
                extract('month', models.AttendanceRecord.date) == month,
                extract('year', models.AttendanceRecord.date) == year
            ).all()
            
            leaves = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.staff_id == staff.id,
                models.LeaveRequest.status == "approved",
                extract('month', models.LeaveRequest.from_date) <= month,
                extract('year', models.LeaveRequest.from_date) <= year
            ).all()
            
            total_days = len(records)
            present_days = len([r for r in records if r.status in ["present", "late"]])
            late_days = len([r for r in records if r.is_late])
            leave_days = sum(l.total_days for l in leaves)
            
            # Calculate working days in month
            from calendar import monthrange
            working_days = monthrange(year, month)[1]
            absent_days = working_days - present_days - leave_days
            
            attendance_percentage = (present_days / working_days * 100) if working_days > 0 else 0
            
            # Average check-in time
            avg_checkin = None
            if records:
                total_minutes = sum(r.check_in_time.hour * 60 + r.check_in_time.minute for r in records)
                avg_minutes = total_minutes // len(records)
                avg_checkin = f"{avg_minutes // 60:02d}:{avg_minutes % 60:02d}"
            
            total_work_hours = sum(r.total_hours or 0 for r in records)
            
            summaries.append(schemas.StaffAttendanceSummary(
                staff_id=staff.id,
                staff_name=staff.name,
                staff_code=staff.staff_code,
                total_days=working_days,
                present_days=present_days,
                absent_days=absent_days,
                late_days=late_days,
                leave_days=leave_days,
                attendance_percentage=round(attendance_percentage, 2),
                average_check_in_time=avg_checkin,
                total_work_hours=total_work_hours
            ))
        
        return schemas.MonthlyAttendanceReport(
            month=month,
            year=year,
            staff_summaries=summaries
        )
    
    @staticmethod
    def auto_checkout_staff(db: Session):
        """Auto checkout staff at end of day (run via cron/celery)"""
        
        today = date.today()
        
        # Get all shops with auto-checkout enabled
        settings_list = db.query(models.AttendanceSettings).filter(
            models.AttendanceSettings.auto_checkout_enabled == True
        ).all()
        
        for settings in settings_list:
            # Find staff who haven't checked out
            records = db.query(models.AttendanceRecord).filter(
                models.AttendanceRecord.shop_id == settings.shop_id,
                models.AttendanceRecord.date == today,
                models.AttendanceRecord.check_out_time.is_(None)
            ).all()
            
            auto_checkout_dt = datetime.combine(today, settings.auto_checkout_time)
            
            for record in records:
                record.check_out_time = auto_checkout_dt
                record.auto_checked_out = True
                time_diff = auto_checkout_dt - record.check_in_time
                record.total_hours = int(time_diff.total_seconds() / 60)
            
            db.commit()
    
    @staticmethod
    def _get_or_create_settings(db: Session, shop_id: int) -> models.AttendanceSettings:
        """Get or create default attendance settings for shop"""
        
        settings = db.query(models.AttendanceSettings).filter(
            models.AttendanceSettings.shop_id == shop_id
        ).first()
        
        if not settings:
            settings = models.AttendanceSettings(shop_id=shop_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings
