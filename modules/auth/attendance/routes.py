from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from datetime import datetime, date, timedelta
from typing import List, Optional
from . import schemas, models, service
from ..models import Staff
from .dependencies import get_current_attendance_user
from .wifi_heartbeat_service import WiFiHeartbeatService

router = APIRouter()

# ============= WIFI HEARTBEAT (AUTO CHECK-IN/OUT) =============

@router.post("/wifi/heartbeat")
def wifi_heartbeat(
    heartbeat_data: schemas.WiFiHeartbeat,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """
    WiFi heartbeat endpoint - Staff app calls this every 30-60 seconds when connected to shop WiFi.
    Automatically checks in on first heartbeat, updates last_seen on subsequent heartbeats.
    """
    
    user, shop_id, user_type = current_user
    
    # Only staff can send heartbeats
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Only staff can send heartbeats")
    
    result = WiFiHeartbeatService.process_heartbeat(
        db=db,
        staff_id=user.id,
        shop_id=shop_id,
        wifi_ssid=heartbeat_data.wifi_ssid,
        mac_address=heartbeat_data.mac_address,
        latitude=heartbeat_data.latitude,
        longitude=heartbeat_data.longitude
    )
    
    # If error, store it in today's attendance record for display
    if result.get('action') == 'error':
        today = date.today()
        attendance = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == user.id,
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today
        ).first()
        
        if attendance:
            attendance.last_error = result['message']
            db.commit()
    else:
        # Clear error on successful heartbeat
        today = date.today()
        attendance = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == user.id,
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today
        ).first()
        
        if attendance and attendance.last_error:
            attendance.last_error = None
            db.commit()
    
    return result

@router.post("/wifi/disconnect")
def wifi_disconnect(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """
    WiFi disconnect endpoint - Staff app calls this when disconnecting from shop WiFi.
    Automatically checks out the staff.
    """
    
    user, shop_id, user_type = current_user
    
    # Only staff can disconnect
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Only staff can disconnect")
    
    result = WiFiHeartbeatService.process_disconnect(
        db=db,
        staff_id=user.id,
        shop_id=shop_id
    )
    
    return result

@router.get("/wifi/status")
def get_wifi_status(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """
    Check current WiFi connection status and attendance record.
    Returns whether staff is checked in and can access modules.
    Admin can check status for any shop they manage.
    """
    
    user, shop_id, user_type = current_user
    
    # Admin checking shop status
    if user_type == "admin":
        # Return shop-level status for admin
        today = date.today()
        cutoff_time = datetime.now() - timedelta(minutes=2)
        
        connected_count = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today,
            models.AttendanceRecord.check_in_time.isnot(None),
            models.AttendanceRecord.check_out_time.is_(None),
            models.AttendanceRecord.updated_at >= cutoff_time
        ).count()
        
        settings = db.query(models.AttendanceSettings).filter(
            models.AttendanceSettings.shop_id == shop_id
        ).first()
        
        return {
            "is_checked_in": True,  # Admin is always "checked in"
            "can_access_modules": True,  # Admin can always access
            "is_inside_geofence": True,
            "allow_any_network": settings.allow_any_network if settings else False,
            "connected_staff_count": connected_count,
            "message": f"{connected_count} staff currently connected"
        }
    
    # Staff checking their own status
    
    # Get today's attendance
    today = date.today()
    attendance = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.staff_id == user.id,
        models.AttendanceRecord.shop_id == shop_id,
        models.AttendanceRecord.date == today
    ).first()
    
    # Get settings
    settings = db.query(models.AttendanceSettings).filter(
        models.AttendanceSettings.shop_id == shop_id
    ).first()
    
    is_checked_in = attendance and attendance.check_in_time and not attendance.check_out_time
    
    # Check if user is currently inside geofence (successful heartbeat within last 2 minutes)
    is_inside_geofence = False
    if attendance and attendance.updated_at:
        time_since_last_heartbeat = (datetime.now() - attendance.updated_at).total_seconds() / 60
        # User is inside if last heartbeat was successful (no error) and within 2 minutes
        is_inside_geofence = time_since_last_heartbeat < 2 and not attendance.last_error
    
    can_access_modules = is_inside_geofence or (settings and settings.allow_any_network)
    
    # Get location error from attendance record
    location_error = attendance.last_error if attendance else None
    
    return {
        "is_checked_in": is_checked_in,
        "can_access_modules": can_access_modules,
        "is_inside_geofence": is_inside_geofence,
        "allow_any_network": settings.allow_any_network if settings else False,
        "attendance": attendance,
        "location_error": location_error,
        "message": "Inside shop - Active session" if is_inside_geofence else "Outside shop"
    }

@router.get("/wifi/connected-staff")
def get_connected_staff(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """
    Get list of currently connected staff (for admin dashboard).
    Shows real-time who is in the shop.
    """
    
    user, shop_id, user_type = current_user
    
    # Only admin can view all connected staff
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    today = date.today()
    cutoff_time = datetime.now() - timedelta(minutes=2)  # Consider connected if heartbeat within 2 min
    
    # Get staff with active attendance and recent heartbeat
    connected = db.query(models.AttendanceRecord, Staff).join(Staff).filter(
        models.AttendanceRecord.shop_id == shop_id,
        models.AttendanceRecord.date == today,
        models.AttendanceRecord.check_in_time.isnot(None),
        models.AttendanceRecord.check_out_time.is_(None),
        models.AttendanceRecord.updated_at >= cutoff_time
    ).all()
    
    result = []
    for attendance, staff in connected:
        result.append({
            "staff_id": staff.id,
            "staff_name": staff.name,
            "staff_code": staff.staff_code,
            "check_in_time": attendance.check_in_time.isoformat() + 'Z',
            "is_late": attendance.is_late,
            "last_seen": attendance.updated_at.isoformat() + 'Z',
            "duration_minutes": int((datetime.now() - attendance.check_in_time).total_seconds() / 60)
        })
    
    return {
        "connected_count": len(result),
        "connected_staff": result
    }

# ============= WIFI & DEVICE MANAGEMENT =============

@router.post("/wifi/setup", response_model=schemas.ShopWiFi)
def setup_shop_wifi(
    wifi_data: schemas.ShopWiFiCreate,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Setup WiFi network for shop (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = db.query(models.ShopWiFi).filter(
        models.ShopWiFi.shop_id == shop_id
    ).first()
    
    if existing:
        existing.wifi_ssid = wifi_data.wifi_ssid
        existing.shop_latitude = wifi_data.shop_latitude
        existing.shop_longitude = wifi_data.shop_longitude
        existing.geofence_radius_meters = wifi_data.geofence_radius_meters or 100
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing
    
    shop_wifi = models.ShopWiFi(
        shop_id=shop_id,
        wifi_ssid=wifi_data.wifi_ssid,
        shop_latitude=wifi_data.shop_latitude,
        shop_longitude=wifi_data.shop_longitude,
        geofence_radius_meters=wifi_data.geofence_radius_meters or 100
    )
    db.add(shop_wifi)
    db.commit()
    db.refresh(shop_wifi)
    return shop_wifi

@router.get("/wifi/info", response_model=schemas.ShopWiFi)
def get_shop_wifi(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get shop WiFi info"""
    
    user, shop_id, user_type = current_user
    
    wifi = db.query(models.ShopWiFi).filter(
        models.ShopWiFi.shop_id == shop_id,
        models.ShopWiFi.is_active == True
    ).first()
    
    if not wifi:
        raise HTTPException(status_code=404, detail="WiFi not configured for this shop")
    
    return wifi

# NOTE: Device management endpoints commented out - devices are auto-registered on first heartbeat

# @router.post("/device/register", response_model=schemas.StaffDevice)
# def register_device(
#     device_data: schemas.StaffDeviceRegister,
#     current_user: tuple = Depends(get_current_attendance_user),
#     db: Session = Depends(get_db)
# ):
#     """Register staff device MAC address"""
#     
#     user, shop_id, user_type = current_user
#     
#     # Only staff can register their own devices
#     if user_type != "staff":
#         raise HTTPException(status_code=403, detail="Staff access required")
#     
#     # Check if MAC already registered
#     existing = db.query(models.StaffDevice).filter(
#         models.StaffDevice.mac_address == device_data.mac_address.upper(),
#         models.StaffDevice.shop_id == shop_id
#     ).first()
#     
#     if existing:
#         if existing.staff_id != user.id:
#             raise HTTPException(status_code=400, detail="Device already registered to another staff")
#         return existing
#     
#     device = models.StaffDevice(
#         staff_id=user.id,
#         shop_id=shop_id,
#         mac_address=device_data.mac_address.upper(),
#         device_name=device_data.device_name
#     )
#     
#     db.add(device)
#     db.commit()
#     db.refresh(device)
#     
#     return device

# @router.get("/device/my-devices", response_model=List[schemas.StaffDevice])
# def get_my_devices(
#     current_user: tuple = Depends(get_current_attendance_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current staff's registered devices"""
#     
#     user, shop_id, user_type = current_user
#     
#     # Only staff can view their own devices
#     if user_type != "staff":
#         raise HTTPException(status_code=403, detail="Staff access required")
#     
#     devices = db.query(models.StaffDevice).filter(
#         models.StaffDevice.staff_id == user.id,
#         models.StaffDevice.shop_id == shop_id
#     ).all()
#     
#     return devices

# ============= ATTENDANCE VIEWING =============

@router.get("/today")
def get_today_attendance(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get today's attendance for all staff (Admin) or own attendance (Staff)"""
    
    user, shop_id, user_type = current_user
    
    if user_type == "admin":
        # Admin sees all staff
        result = service.AttendanceService.get_today_attendance(db, shop_id)
    else:
        # Staff sees only their own
        today = date.today()
        attendance = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == user.id,
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today
        ).first()
        
        result = [{
            "staff_id": user.id,
            "staff_name": user.name,
            "staff_code": user.staff_code,
            "attendance": attendance,
            "on_leave": False,
            "status": attendance.status if attendance else "absent"
        }]
    
    # Convert attendance records to dict
    for item in result:
        if item.get('attendance'):
            attendance = item['attendance']
            item['attendance'] = {
                'id': attendance.id,
                'check_in_time': attendance.check_in_time.isoformat() + 'Z' if attendance.check_in_time else None,
                'check_out_time': attendance.check_out_time.isoformat() + 'Z' if attendance.check_out_time else None,
                'status': attendance.status,
                'is_late': attendance.is_late,
                'late_by_minutes': attendance.late_by_minutes,
                'total_hours': attendance.total_hours,
                'auto_checked_in': attendance.auto_checked_in
            }
    
    return result

@router.get("/summary", response_model=schemas.AttendanceSummary)
def get_attendance_summary(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get attendance summary dashboard (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can view summary
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return service.AttendanceService.get_attendance_summary(db, shop_id)

@router.get("/records")
def get_attendance_records(
    staff_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get attendance records with filters (Admin sees all, Staff sees own)"""
    
    user, shop_id, user_type = current_user
    
    query = db.query(models.AttendanceRecord, Staff).join(Staff).filter(
        models.AttendanceRecord.shop_id == shop_id
    )
    
    # Staff can only see their own records
    if user_type == "staff":
        query = query.filter(models.AttendanceRecord.staff_id == user.id)
    elif staff_id:  # Admin can filter by staff_id
        query = query.filter(models.AttendanceRecord.staff_id == staff_id)
    
    if from_date:
        query = query.filter(models.AttendanceRecord.date >= from_date)
    if to_date:
        query = query.filter(models.AttendanceRecord.date <= to_date)
    
    results = query.order_by(models.AttendanceRecord.date.desc()).all()
    
    # Convert to dict with staff info
    records = []
    for attendance, staff in results:
        record_dict = {
            'id': attendance.id,
            'staff_id': attendance.staff_id,
            'staff_name': staff.name,
            'staff_code': staff.staff_code,
            'shop_id': attendance.shop_id,
            'date': attendance.date.isoformat(),
            'check_in_time': attendance.check_in_time.isoformat() + 'Z' if attendance.check_in_time else None,
            'check_out_time': attendance.check_out_time.isoformat() + 'Z' if attendance.check_out_time else None,
            'status': attendance.status,
            'is_late': attendance.is_late,
            'late_by_minutes': attendance.late_by_minutes,
            'total_hours': attendance.total_hours,
            'total_break_minutes': attendance.total_break_minutes or 0,
            'auto_checked_in': attendance.auto_checked_in,
            'auto_checked_out': attendance.auto_checked_out,
            'notes': attendance.notes
        }
        records.append(record_dict)
    
    return records

@router.get("/my-attendance", response_model=List[schemas.AttendanceRecord])
def get_my_attendance(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get current staff's attendance records"""
    
    user, shop_id, user_type = current_user
    
    # Only staff can use this endpoint
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    query = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.staff_id == user.id,
        models.AttendanceRecord.shop_id == shop_id
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
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get monthly attendance report (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can view monthly reports
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return service.AttendanceService.get_monthly_report(db, shop_id, month, year)

# ============= ATTENDANCE SETTINGS =============

@router.get("/settings", response_model=schemas.AttendanceSettings)
def get_attendance_settings(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get attendance settings for shop"""
    
    user, shop_id, user_type = current_user
    
    settings = service.AttendanceService._get_or_create_settings(db, shop_id)
    return settings

@router.put("/settings", response_model=schemas.AttendanceSettings)
def update_attendance_settings(
    settings_data: schemas.AttendanceSettingsUpdate,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Update attendance settings (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can update settings
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = service.AttendanceService._get_or_create_settings(db, shop_id)
    
    for field, value in settings_data.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    
    settings.updated_at = datetime.now()
    db.commit()
    db.refresh(settings)
    
    return settings

# ============= LEAVE MANAGEMENT =============

@router.post("/leave/request", response_model=schemas.LeaveRequest)
def request_leave(
    leave_data: schemas.LeaveRequestCreate,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Staff requests leave"""
    
    user, shop_id, user_type = current_user
    
    # Only staff can request leave
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    total_days = (leave_data.to_date - leave_data.from_date).days + 1
    
    leave = models.LeaveRequest(
        staff_id=user.id,
        shop_id=shop_id,
        total_days=total_days,
        **leave_data.model_dump()
    )
    
    db.add(leave)
    db.commit()
    db.refresh(leave)
    
    return leave

@router.get("/leave/my-requests", response_model=List[schemas.LeaveRequest])
def get_my_leave_requests(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get current staff's leave requests"""
    
    user, shop_id, user_type = current_user
    
    # Only staff can view their own leave requests
    if user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    return db.query(models.LeaveRequest).filter(
        models.LeaveRequest.staff_id == user.id,
        models.LeaveRequest.shop_id == shop_id
    ).order_by(models.LeaveRequest.created_at.desc()).all()

@router.get("/leave/all", response_model=List[schemas.LeaveRequestWithStaff])
def get_all_leave_requests(
    staff_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get all leave requests for shop (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can view all leaves
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    query = db.query(models.LeaveRequest, Staff).join(Staff).filter(
        Staff.shop_id == shop_id,
        models.LeaveRequest.shop_id == shop_id
    )
    
    if staff_id:
        query = query.filter(models.LeaveRequest.staff_id == staff_id)
    if status:
        query = query.filter(models.LeaveRequest.status == status)
    
    requests = query.order_by(models.LeaveRequest.created_at.desc()).all()
    
    result = []
    for leave, staff in requests:
        result.append(schemas.LeaveRequestWithStaff(
            **leave.__dict__,
            staff_name=staff.name,
            staff_code=staff.staff_code
        ))
    
    return result

@router.get("/leave/pending", response_model=List[schemas.LeaveRequestWithStaff])
def get_pending_leave_requests(
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Get pending leave requests for shop (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can view all pending leaves
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    requests = db.query(models.LeaveRequest, Staff).join(Staff).filter(
        Staff.shop_id == shop_id,
        models.LeaveRequest.shop_id == shop_id,
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
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Approve leave request (Admin only)"""
    
    user, shop_id, user_type = current_user
    
    # Only admin can approve leaves
    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.id == leave_id,
        models.LeaveRequest.shop_id == shop_id
    ).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    leave.status = "approved"
    leave.approved_by = user.full_name
    leave.approved_at = datetime.now()
    
    db.commit()
    db.refresh(leave)
    
    return leave

@router.put("/leave/{leave_id}/reject", response_model=schemas.LeaveRequest)
def reject_leave(
    leave_id: int,
    update_data: schemas.LeaveRequestReject,
    current_user: tuple = Depends(get_current_attendance_user),
    db: Session = Depends(get_db)
):
    """Reject leave request (Admin only)"""

    user, shop_id, user_type = current_user

    if user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    leave = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.id == leave_id,
        models.LeaveRequest.shop_id == shop_id
    ).first()

    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")

    leave.status = "rejected"
    leave.approved_by = user.full_name
    leave.approved_at = datetime.now()
    leave.rejection_reason = update_data.rejection_reason

    db.commit()
    db.refresh(leave)

    return leave
