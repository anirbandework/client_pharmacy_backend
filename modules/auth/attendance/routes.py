from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import datetime, date
from typing import List, Optional
from . import schemas, models, service
from ..models import Staff
from ..dependencies import get_current_admin, get_current_staff

router = APIRouter()

# ============= WIFI & DEVICE MANAGEMENT =============

@router.post("/wifi/setup", response_model=schemas.ShopWiFi)
def setup_shop_wifi(
    wifi_data: schemas.ShopWiFiSetup,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Setup WiFi network for shop (Admin only)"""
    
    # Check if WiFi already exists
    existing = db.query(models.ShopWiFi).filter(
        models.ShopWiFi.shop_id == wifi_data.shop_id
    ).first()
    
    if existing:
        # Update existing
        existing.wifi_ssid = wifi_data.wifi_ssid
        existing.wifi_password = wifi_data.wifi_password
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing
    
    # Create new
    shop_wifi = models.ShopWiFi(
        shop_id=wifi_data.shop_id,
        wifi_ssid=wifi_data.wifi_ssid,
        wifi_password=wifi_data.wifi_password
    )
    db.add(shop_wifi)
    db.commit()
    db.refresh(shop_wifi)
    
    return shop_wifi

@router.post("/device/register", response_model=schemas.StaffDevice)
def register_device(
    device_data: schemas.StaffDeviceRegister,
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Register staff device MAC address"""
    
    # Check if MAC already registered
    existing = db.query(models.StaffDevice).filter(
        models.StaffDevice.mac_address == device_data.mac_address.upper()
    ).first()
    
    if existing:
        if existing.staff_id != staff.id:
            raise HTTPException(status_code=400, detail="Device already registered to another staff")
        return existing
    
    device = models.StaffDevice(
        staff_id=staff.id,
        mac_address=device_data.mac_address.upper(),
        device_name=device_data.device_name
    )
    
    db.add(device)
    db.commit()
    db.refresh(device)
    
    return device

@router.get("/device/my-devices", response_model=List[schemas.StaffDevice])
def get_my_devices(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's registered devices"""
    
    devices = db.query(models.StaffDevice).filter(
        models.StaffDevice.staff_id == staff.id
    ).all()
    
    return devices

# ============= ATTENDANCE CHECK-IN/OUT =============

@router.post("/check-in/wifi", response_model=schemas.AttendanceRecord)
def wifi_check_in(
    checkin_data: schemas.WiFiCheckIn,
    db: Session = Depends(get_db)
):
    """Auto check-in via WiFi connection (called by mobile app/script)"""
    
    try:
        attendance = service.AttendanceService.wifi_check_in(
            db, 
            checkin_data.mac_address, 
            checkin_data.wifi_ssid
        )
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check-in/manual", response_model=schemas.AttendanceRecord)
def manual_check_in(
    checkin_data: schemas.ManualCheckIn,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manual check-in by admin"""
    
    try:
        attendance = service.AttendanceService.manual_check_in(
            db,
            checkin_data.staff_id,
            checkin_data.notes
        )
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check-in/self", response_model=schemas.AttendanceRecord)
def self_check_in(
    notes: Optional[str] = None,
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Staff self check-in (if WiFi auto-detection fails)"""
    
    try:
        attendance = service.AttendanceService.manual_check_in(
            db,
            staff.id,
            notes
        )
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check-out", response_model=schemas.AttendanceRecord)
def check_out(
    checkout_data: schemas.CheckOut,
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Staff check-out"""
    
    try:
        attendance = service.AttendanceService.check_out(
            db,
            staff.id,
            checkout_data.notes
        )
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/check-out/staff/{staff_id}", response_model=schemas.AttendanceRecord)
def admin_check_out_staff(
    staff_id: int,
    checkout_data: schemas.CheckOut,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin checks out staff"""
    
    try:
        attendance = service.AttendanceService.check_out(
            db,
            staff_id,
            checkout_data.notes
        )
        return attendance
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============= ATTENDANCE VIEWING =============

@router.get("/today")
def get_today_attendance(
    shop_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get today's attendance for all staff (Admin)"""
    
    result = service.AttendanceService.get_today_attendance(db, shop_id)
    
    # Convert attendance records to dict
    for item in result:
        if item.get('attendance'):
            attendance = item['attendance']
            item['attendance'] = {
                'id': attendance.id,
                'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
                'status': attendance.status,
                'is_late': attendance.is_late,
                'late_by_minutes': attendance.late_by_minutes,
                'total_hours': attendance.total_hours,
                'auto_checked_in': attendance.auto_checked_in
            }
    
    return result

@router.get("/summary", response_model=schemas.AttendanceSummary)
def get_attendance_summary(
    shop_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get attendance summary dashboard (Admin)"""
    
    return service.AttendanceService.get_attendance_summary(db, shop_id)

@router.get("/records", response_model=List[schemas.AttendanceRecord])
def get_attendance_records(
    shop_id: int,
    staff_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get attendance records with filters (Admin)"""
    
    query = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.shop_id == shop_id
    )
    
    if staff_id:
        query = query.filter(models.AttendanceRecord.staff_id == staff_id)
    if from_date:
        query = query.filter(models.AttendanceRecord.date >= from_date)
    if to_date:
        query = query.filter(models.AttendanceRecord.date <= to_date)
    
    return query.order_by(models.AttendanceRecord.date.desc()).all()

@router.get("/my-attendance", response_model=List[schemas.AttendanceRecord])
def get_my_attendance(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's attendance records"""
    
    query = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.staff_id == staff.id
    )
    
    if from_date:
        query = query.filter(models.AttendanceRecord.date >= from_date)
    if to_date:
        query = query.filter(models.AttendanceRecord.date <= to_date)
    
    return query.order_by(models.AttendanceRecord.date.desc()).all()

@router.get("/monthly-report/{year}/{month}", response_model=schemas.MonthlyAttendanceReport)
def get_monthly_report(
    year: int,
    month: int,
    shop_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get monthly attendance report (Admin)"""
    
    return service.AttendanceService.get_monthly_report(db, shop_id, month, year)

# ============= ATTENDANCE SETTINGS =============

@router.get("/settings/{shop_id}", response_model=schemas.AttendanceSettings)
def get_attendance_settings(
    shop_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get attendance settings for shop"""
    
    settings = service.AttendanceService._get_or_create_settings(db, shop_id)
    return settings

@router.put("/settings/{shop_id}", response_model=schemas.AttendanceSettings)
def update_attendance_settings(
    shop_id: int,
    settings_data: schemas.AttendanceSettingsUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update attendance settings"""
    
    settings = service.AttendanceService._get_or_create_settings(db, shop_id)
    
    for field, value in settings_data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    return settings

# ============= LEAVE MANAGEMENT =============

@router.post("/leave/request", response_model=schemas.LeaveRequest)
def request_leave(
    leave_data: schemas.LeaveRequestCreate,
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Staff requests leave"""
    
    total_days = (leave_data.to_date - leave_data.from_date).days + 1
    
    leave = models.LeaveRequest(
        staff_id=staff.id,
        total_days=total_days,
        **leave_data.model_dump()
    )
    
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    return leave

@router.get("/leave/my-requests", response_model=List[schemas.LeaveRequest])
def get_my_leave_requests(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get current staff's leave requests"""
    
    return db.query(models.LeaveRequest).filter(
        models.LeaveRequest.staff_id == staff.id
    ).order_by(models.LeaveRequest.created_at.desc()).all()

@router.get("/leave/pending", response_model=List[schemas.LeaveRequestWithStaff])
def get_pending_leave_requests(
    shop_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get pending leave requests for shop (Admin)"""
    
    requests = db.query(models.LeaveRequest, Staff).join(Staff).filter(
        Staff.shop_id == shop_id,
        models.LeaveRequest.status == "pending"
    ).all()
    
    result = []
    for leave, staff in requests:
        result.append(schemas.LeaveRequestWithStaff(
            **leave.__dict__,
            staff_name=staff.name,
            staff_code=staff.staff_code
        ))
    
    return result

@router.put("/leave/{leave_id}/approve", response_model=schemas.LeaveRequest)
def approve_leave(
    leave_id: int,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve leave request (Admin)"""
    
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.id == leave_id
    ).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave.status = "approved"
    leave.approved_by = admin.full_name
    leave.approved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(leave)
    
    return leave

@router.put("/leave/{leave_id}/reject", response_model=schemas.LeaveRequest)
def reject_leave(
    leave_id: int,
    update_data: schemas.LeaveRequestUpdate,
    admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Reject leave request (Admin)"""
    
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.id == leave_id
    ).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave.status = "rejected"
    leave.approved_by = admin.full_name
    leave.approved_at = datetime.utcnow()
    leave.rejection_reason = update_data.rejection_reason
    
    db.commit()
    db.refresh(leave)
    
    return leave
