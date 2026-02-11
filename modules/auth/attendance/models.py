from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base
from datetime import datetime

class ShopWiFi(Base):
    """Shop WiFi network configuration"""
    __tablename__ = "shop_wifi"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    wifi_ssid = Column(String(100), nullable=False)
    wifi_password = Column(String(255), nullable=True)  # Optional, for staff reference
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    shop = relationship("Shop")
    attendance_records = relationship("AttendanceRecord", back_populates="shop_wifi")

class StaffDevice(Base):
    """Staff registered devices (MAC addresses)"""
    __tablename__ = "staff_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    mac_address = Column(String(17), unique=True, index=True, nullable=False)  # Format: AA:BB:CC:DD:EE:FF
    device_name = Column(String(100), nullable=True)  # e.g., "iPhone 12", "Samsung Galaxy"
    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=True)
    
    staff = relationship("Staff", back_populates="devices")
    attendance_records = relationship("AttendanceRecord", back_populates="device")

class AttendanceRecord(Base):
    """Daily attendance records with WiFi auto-detection"""
    __tablename__ = "attendance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("staff_devices.id"), nullable=True)
    wifi_id = Column(Integer, ForeignKey("shop_wifi.id"), nullable=True)
    
    date = Column(Date, nullable=False, index=True)
    check_in_time = Column(DateTime, nullable=False)
    check_out_time = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(String(20), default="present")  # present, late, half_day, absent
    is_late = Column(Boolean, default=False)
    late_by_minutes = Column(Integer, default=0)
    
    # Work hours
    total_hours = Column(Integer, nullable=True)  # In minutes
    
    # Auto-detection info
    auto_checked_in = Column(Boolean, default=True)  # WiFi auto-detected
    auto_checked_out = Column(Boolean, default=False)
    
    # Notes
    notes = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    staff = relationship("Staff", back_populates="attendance_records")
    shop = relationship("Shop")
    device = relationship("StaffDevice", back_populates="attendance_records")
    shop_wifi = relationship("ShopWiFi", back_populates="attendance_records")

class AttendanceSettings(Base):
    """Shop-specific attendance settings"""
    __tablename__ = "attendance_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), unique=True, nullable=False)
    
    # Work timings
    work_start_time = Column(Time, default=datetime.strptime("09:00", "%H:%M").time())
    work_end_time = Column(Time, default=datetime.strptime("18:00", "%H:%M").time())
    grace_period_minutes = Column(Integer, default=15)  # 15 min grace for late
    
    # Auto check-out
    auto_checkout_enabled = Column(Boolean, default=True)
    auto_checkout_time = Column(Time, default=datetime.strptime("19:00", "%H:%M").time())
    
    # Working days
    monday = Column(Boolean, default=True)
    tuesday = Column(Boolean, default=True)
    wednesday = Column(Boolean, default=True)
    thursday = Column(Boolean, default=True)
    friday = Column(Boolean, default=True)
    saturday = Column(Boolean, default=True)
    sunday = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    shop = relationship("Shop")

class LeaveRequest(Base):
    """Staff leave requests"""
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    
    leave_type = Column(String(20), nullable=False)  # sick, casual, earned
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    total_days = Column(Integer, nullable=False)
    reason = Column(String(500), nullable=True)
    
    status = Column(String(20), default="pending")  # pending, approved, rejected
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    staff = relationship("Staff", back_populates="leave_requests")
