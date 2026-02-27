"""
WiFi Heartbeat Service
Handles automatic check-in/out based on WiFi connection status
"""
from sqlalchemy.orm import Session
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from . import models
from ..models import Staff, Shop
from typing import Optional

# Use IST timezone
LOCAL_TZ = ZoneInfo("Asia/Kolkata")

class WiFiHeartbeatService:
    """
    Service to handle automatic attendance tracking based on WiFi heartbeat signals.
    Staff apps send periodic heartbeats when connected to shop WiFi.
    """
    
    @staticmethod
    def process_heartbeat(
        db: Session,
        staff_id: int,
        shop_id: int,
        wifi_ssid: str,
        mac_address: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> dict:
        """
        Process WiFi heartbeat from staff device.
        Auto check-in if not already checked in.
        Update last_seen timestamp.
        Track breaks (gaps >30 min between heartbeats).
        
        Returns:
            dict: {
                "action": "checked_in" | "heartbeat_updated" | "already_checked_in" | "error",
                "attendance_record": AttendanceRecord,
                "message": str
            }
        """
        
        # Verify WiFi belongs to shop
        shop_wifi = db.query(models.ShopWiFi).filter(
            models.ShopWiFi.shop_id == shop_id,
            models.ShopWiFi.wifi_ssid == wifi_ssid,
            models.ShopWiFi.is_active == True
        ).first()
        
        if not shop_wifi:
            return {
                "action": "error",
                "message": f"WiFi '{wifi_ssid}' not registered for this shop"
            }
        
        # STRICT: Require location
        if latitude is None or longitude is None:
            return {
                "action": "error",
                "message": "Location is required for attendance. Please enable location services."
            }
        
        # STRICT: Validate location is within geofence
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371000  # Earth radius in meters
        lat1, lon1 = radians(float(shop_wifi.shop_latitude)), radians(float(shop_wifi.shop_longitude))
        lat2, lon2 = radians(latitude), radians(longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        
        if distance > shop_wifi.geofence_radius_meters:
            return {
                "action": "error",
                "message": f"You are {int(distance)}m away from shop. Must be within {shop_wifi.geofence_radius_meters}m to check in."
            }
        
        # Get or create device record
        device = None
        if mac_address:
            device = db.query(models.StaffDevice).filter(
                models.StaffDevice.mac_address == mac_address.upper(),
                models.StaffDevice.shop_id == shop_id
            ).first()
            
            if not device:
                # Auto-register device
                device = models.StaffDevice(
                    staff_id=staff_id,
                    shop_id=shop_id,
                    mac_address=mac_address.upper(),
                    device_name="Auto-registered"
                )
                db.add(device)
                db.flush()
            
            # Update last_seen
            device.last_seen = datetime.now()
        
        # Check if already checked in today
        today = date.today()
        existing_record = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == staff_id,
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today
        ).first()
        
        if existing_record:
            # Clear any previous errors on successful heartbeat
            existing_record.last_error = None
            
            # Calculate break time if gap >30 minutes
            time_since_last_heartbeat = (datetime.now() - existing_record.updated_at).total_seconds() / 60
            if time_since_last_heartbeat > 30:
                # Add break time
                break_minutes = int(time_since_last_heartbeat)
                existing_record.total_break_minutes = (existing_record.total_break_minutes or 0) + break_minutes
            
            # If already checked out, resume session (clear check-out)
            if existing_record.check_out_time:
                existing_record.check_out_time = None
                existing_record.auto_checked_out = False
                existing_record.total_hours = None
            
            # Update heartbeat timestamp - force update
            existing_record.updated_at = datetime.now()
            db.add(existing_record)  # Mark as modified
            db.commit()
            db.refresh(existing_record)
            
            return {
                "action": "heartbeat_updated",
                "attendance_record": existing_record,
                "message": "Heartbeat updated"
            }
        
        # Auto check-in
        check_in_time = datetime.now(LOCAL_TZ)  # Use local time
        
        # Get attendance settings to determine if late
        settings = db.query(models.AttendanceSettings).filter(
            models.AttendanceSettings.shop_id == shop_id
        ).first()
        
        is_late = False
        late_by_minutes = 0
        
        if settings:
            # Compare times in local timezone
            work_start_local = datetime.combine(check_in_time.date(), settings.work_start_time, tzinfo=LOCAL_TZ)
            grace_end_local = work_start_local + timedelta(minutes=settings.grace_period_minutes)
            
            if check_in_time > grace_end_local:
                is_late = True
                late_by_minutes = int((check_in_time - grace_end_local).total_seconds() / 60)
        
        # Store in UTC for database
        check_in_time_utc = check_in_time.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
        
        # Create attendance record
        attendance = models.AttendanceRecord(
            staff_id=staff_id,
            shop_id=shop_id,
            device_id=device.id if device else None,
            wifi_id=shop_wifi.id,
            date=today,
            check_in_time=check_in_time_utc,
            is_late=is_late,
            late_by_minutes=late_by_minutes,
            auto_checked_in=True,
            status="late" if is_late else "present"
        )
        
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        
        return {
            "action": "checked_in",
            "attendance_record": attendance,
            "message": f"Auto checked-in at {check_in_time.strftime('%H:%M:%S')}"
        }
    
    @staticmethod
    def process_disconnect(
        db: Session,
        staff_id: int,
        shop_id: int
    ) -> dict:
        """
        Process WiFi disconnect event.
        Auto check-out if currently checked in.
        """
        
        today = date.today()
        attendance = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.staff_id == staff_id,
            models.AttendanceRecord.shop_id == shop_id,
            models.AttendanceRecord.date == today,
            models.AttendanceRecord.check_out_time.is_(None)
        ).first()
        
        if not attendance:
            return {
                "action": "no_active_session",
                "message": "No active attendance session found"
            }
        
        # Auto check-out
        check_out_time = datetime.now()
        attendance.check_out_time = check_out_time
        attendance.auto_checked_out = True
        
        # Calculate total hours
        if attendance.check_in_time:
            duration = check_out_time - attendance.check_in_time
            attendance.total_hours = int(duration.total_seconds() / 60)
        
        db.commit()
        db.refresh(attendance)
        
        return {
            "action": "checked_out",
            "attendance_record": attendance,
            "message": f"Auto checked-out at {check_out_time.strftime('%H:%M:%S')}"
        }
    
    @staticmethod
    def check_stale_sessions(db: Session, stale_minutes: int = 5):
        """
        Check for stale attendance sessions (no heartbeat for X minutes).
        Auto check-out stale sessions.
        
        This should be run periodically (e.g., every minute via cron/scheduler).
        """
        
        cutoff_time = datetime.now() - timedelta(minutes=stale_minutes)
        today = date.today()
        
        stale_sessions = db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.date == today,
            models.AttendanceRecord.check_out_time.is_(None),
            models.AttendanceRecord.updated_at < cutoff_time
        ).all()
        
        checked_out_count = 0
        for session in stale_sessions:
            session.check_out_time = datetime.now()
            session.auto_checked_out = True
            session.notes = f"Auto checked-out due to WiFi disconnect (no heartbeat for {stale_minutes} min)"
            
            if session.check_in_time:
                duration = session.check_out_time - session.check_in_time
                session.total_hours = int(duration.total_seconds() / 60)
            
            checked_out_count += 1
        
        if checked_out_count > 0:
            db.commit()
        
        return {
            "checked_out_count": checked_out_count,
            "message": f"Auto checked-out {checked_out_count} stale sessions"
        }
