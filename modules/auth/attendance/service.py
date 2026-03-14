from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict
from . import models, schemas
from ..models import Staff, Shop

LOCAL_TZ = ZoneInfo("Asia/Kolkata")

class AttendanceService:
    """Service for attendance viewing and reporting - check-in/out handled by WiFiHeartbeatService"""
    
    @staticmethod
    def get_today_attendance(db: Session, shop_id: int) -> List[Dict]:
        """Get today's attendance for all staff in shop"""
        
        today = date.today()
        
        # Get all active staff for this shop
        staff_list = db.query(Staff).filter(
            Staff.shop_id == shop_id,
            Staff.is_active == True
        ).all()
        
        result = []
        for staff in staff_list:
            attendance = db.query(models.AttendanceRecord).filter(
                models.AttendanceRecord.staff_id == staff.id,
                models.AttendanceRecord.shop_id == shop_id,
                models.AttendanceRecord.date == today
            ).first()
            
            # Check if on leave
            on_leave = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.staff_id == staff.id,
                models.LeaveRequest.shop_id == shop_id,
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
            models.LeaveRequest.shop_id == shop_id,
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
                models.AttendanceRecord.shop_id == shop_id,
                extract('month', models.AttendanceRecord.date) == month,
                extract('year', models.AttendanceRecord.date) == year
            ).all()
            
            # Calculate leave days that fall within this month
            from calendar import monthrange
            _, last_day = monthrange(year, month)
            month_start = date(year, month, 1)
            month_end = date(year, month, last_day)
            
            leaves = db.query(models.LeaveRequest).filter(
                models.LeaveRequest.staff_id == staff.id,
                models.LeaveRequest.shop_id == shop_id,
                models.LeaveRequest.status == "approved",
                models.LeaveRequest.from_date <= month_end,
                models.LeaveRequest.to_date >= month_start
            ).all()
            
            # Count leave days within the month
            leave_days = 0
            for leave in leaves:
                leave_start = max(leave.from_date, month_start)
                leave_end = min(leave.to_date, month_end)
                leave_days += (leave_end - leave_start).days + 1
            
            total_days = len(records)
            present_days = len([r for r in records if r.status in ["present", "late"]])
            late_days = len([r for r in records if r.is_late])

            # Calculate actual working days using shop's configured working days
            settings = AttendanceService._get_or_create_settings(db, shop_id)
            day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            working_days = sum(
                1 for d in range(1, last_day + 1)
                if getattr(settings, day_names[date(year, month, d).weekday()], False)
            ) or last_day  # fallback to calendar days if nothing configured

            absent_days = max(0, working_days - present_days - leave_days)
            
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
            
            # Build timezone-aware checkout time, then strip tz for DB storage (naive UTC-equivalent)
            auto_checkout_dt = datetime.combine(today, settings.auto_checkout_time, tzinfo=LOCAL_TZ).replace(tzinfo=None)

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
