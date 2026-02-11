from pydantic import BaseModel, field_validator
from datetime import datetime, date, time
from typing import Optional, List

# Shop WiFi Schemas
class ShopWiFiCreate(BaseModel):
    wifi_ssid: str
    wifi_password: Optional[str] = None

class ShopWiFiSetup(BaseModel):
    shop_id: int
    wifi_ssid: str
    wifi_password: Optional[str] = None

class ShopWiFi(BaseModel):
    id: int
    shop_id: int
    wifi_ssid: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Staff Device Schemas
class StaffDeviceRegister(BaseModel):
    mac_address: str
    device_name: Optional[str] = None
    
    @field_validator('mac_address')
    @classmethod
    def validate_mac(cls, v):
        # Basic MAC address validation
        v = v.upper().replace("-", ":").replace(".", ":")
        parts = v.split(":")
        if len(parts) != 6 or not all(len(p) == 2 for p in parts):
            raise ValueError('Invalid MAC address format. Use AA:BB:CC:DD:EE:FF')
        return v

class StaffDevice(BaseModel):
    id: int
    staff_id: int
    mac_address: str
    device_name: Optional[str]
    is_active: bool
    registered_at: datetime
    last_seen: Optional[datetime]
    
    class Config:
        from_attributes = True

# Attendance Schemas
class WiFiCheckIn(BaseModel):
    mac_address: str
    wifi_ssid: str

class ManualCheckIn(BaseModel):
    staff_id: int
    notes: Optional[str] = None

class CheckOut(BaseModel):
    notes: Optional[str] = None

class AttendanceRecord(BaseModel):
    id: int
    staff_id: int
    shop_id: int
    date: date
    check_in_time: datetime
    check_out_time: Optional[datetime]
    status: str
    is_late: bool
    late_by_minutes: int
    total_hours: Optional[int]
    auto_checked_in: bool
    auto_checked_out: bool
    notes: Optional[str]
    
    class Config:
        from_attributes = True

class AttendanceWithStaff(AttendanceRecord):
    staff_name: str
    staff_code: str

# Attendance Settings Schemas
class AttendanceSettingsUpdate(BaseModel):
    work_start_time: Optional[time] = None
    work_end_time: Optional[time] = None
    grace_period_minutes: Optional[int] = None
    auto_checkout_enabled: Optional[bool] = None
    auto_checkout_time: Optional[time] = None
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None

class AttendanceSettings(BaseModel):
    id: int
    shop_id: int
    work_start_time: time
    work_end_time: time
    grace_period_minutes: int
    auto_checkout_enabled: bool
    auto_checkout_time: time
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    
    class Config:
        from_attributes = True

# Leave Request Schemas
class LeaveRequestCreate(BaseModel):
    leave_type: str  # sick, casual, earned
    from_date: date
    to_date: date
    reason: Optional[str] = None
    
    @field_validator('leave_type')
    @classmethod
    def validate_leave_type(cls, v):
        if v not in ['sick', 'casual', 'earned']:
            raise ValueError('Leave type must be sick, casual, or earned')
        return v

class LeaveRequestUpdate(BaseModel):
    status: str  # approved, rejected
    rejection_reason: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v not in ['approved', 'rejected']:
            raise ValueError('Status must be approved or rejected')
        return v

class LeaveRequest(BaseModel):
    id: int
    staff_id: int
    leave_type: str
    from_date: date
    to_date: date
    total_days: int
    reason: Optional[str]
    status: str
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeaveRequestWithStaff(LeaveRequest):
    staff_name: str
    staff_code: str

# Dashboard Schemas
class AttendanceSummary(BaseModel):
    total_staff: int
    present_today: int
    absent_today: int
    late_today: int
    on_leave_today: int
    pending_leave_requests: int

class StaffAttendanceSummary(BaseModel):
    staff_id: int
    staff_name: str
    staff_code: str
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    leave_days: int
    attendance_percentage: float
    average_check_in_time: Optional[str]
    total_work_hours: int  # In minutes

class MonthlyAttendanceReport(BaseModel):
    month: int
    year: int
    staff_summaries: List[StaffAttendanceSummary]
