"""
Database Migration Script for WiFi-Based Attendance System

Run this script to create all attendance-related tables:
- shop_wifi
- staff_devices
- attendance_records
- attendance_settings
- leave_requests
"""

from sqlalchemy import create_engine
from app.database.database import Base, engine
from modules.auth.attendance.models import (
    ShopWiFi, StaffDevice, AttendanceRecord, 
    AttendanceSettings, LeaveRequest
)

def migrate():
    """Create all attendance tables"""
    print("Creating attendance system tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All attendance tables created successfully!")
        
        print("\nCreated tables:")
        print("  - shop_wifi")
        print("  - staff_devices")
        print("  - attendance_records")
        print("  - attendance_settings")
        print("  - leave_requests")
        
        print("\n🎉 Migration completed!")
        print("\nNext steps:")
        print("1. Setup shop WiFi: POST /api/attendance/wifi/setup")
        print("2. Staff registers devices: POST /api/attendance/device/register")
        print("3. Start auto check-in via WiFi!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate()
