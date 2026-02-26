# Attendance System - Complete Summary

## Overview
WiFi-based automatic attendance tracking system for pharmacy staff with geofencing, real-time monitoring, and comprehensive reporting.

## Core Features

### 1. Automatic Check-In/Out
- **WiFi Heartbeat**: Staff app sends heartbeat every 30-60 seconds when connected to shop WiFi
- **Auto Check-In**: First heartbeat of the day automatically checks in staff
- **Auto Check-Out**: Checks out when WiFi disconnects or no heartbeat for 5 minutes
- **Geofencing**: Validates staff location within configurable radius (default 100m)

### 2. Location Validation
- **Strict Enforcement**: Requires GPS coordinates with every heartbeat
- **Distance Calculation**: Uses Haversine formula to calculate distance from shop
- **Real-time Feedback**: Returns error if outside geofence radius

### 3. Break Time Tracking
- **Automatic Detection**: Gaps >30 minutes between heartbeats counted as breaks
- **Cumulative Tracking**: Total break time accumulated throughout the day

### 4. Late Arrival Detection
- **Configurable Work Hours**: Shop-specific start time and grace period
- **Automatic Flagging**: Marks attendance as "late" if check-in after grace period
- **Minutes Calculation**: Tracks exact minutes late

## Database Models

### ShopWiFi
- Shop WiFi network configuration
- SSID, password (optional), location coordinates
- Geofence radius in meters
- Active/inactive status

### StaffDevice
- Staff registered devices (MAC addresses)
- Auto-registration on first heartbeat
- Last seen timestamp tracking
- Device name and active status

### AttendanceRecord
- Daily attendance records
- Check-in/out timestamps (UTC)
- Status: present, late, half_day, absent
- Total hours and break minutes
- Auto check-in/out flags
- Last error message for debugging

### AttendanceSettings
- Shop-specific configuration
- Work timings and grace period
- Auto checkout settings
- WiFi enforcement toggles
- Working days (Mon-Sun)

### LeaveRequest
- Staff leave applications
- Leave types: sick, casual, earned
- Approval workflow
- Date range and total days

## API Endpoints

### WiFi & Heartbeat
- `POST /wifi/heartbeat` - Process heartbeat, auto check-in
- `POST /wifi/disconnect` - Manual disconnect, auto check-out
- `GET /wifi/status` - Check connection status and module access
- `GET /wifi/connected-staff` - Real-time connected staff list (admin)
- `POST /wifi/setup` - Configure shop WiFi (admin)
- `GET /wifi/info` - Get shop WiFi configuration

### Attendance Viewing
- `GET /today` - Today's attendance (all staff for admin, own for staff)
- `GET /summary` - Dashboard summary (admin)
- `GET /records` - Filtered attendance records
- `GET /my-attendance` - Staff's own records
- `GET /monthly-report/{year}/{month}` - Monthly report (admin)

### Settings
- `GET /settings` - Get attendance settings
- `PUT /settings` - Update settings (admin)

### Leave Management
- `POST /leave/request` - Submit leave request (staff)
- `GET /leave/my-requests` - Staff's leave requests
- `GET /leave/all` - All leave requests (admin)
- `GET /leave/pending` - Pending approvals (admin)
- `PUT /leave/{id}/approve` - Approve leave (admin)
- `PUT /leave/{id}/reject` - Reject leave (admin)

## Services

### WiFiHeartbeatService
**Core attendance logic:**
- `process_heartbeat()` - Main heartbeat processing
  - Validates WiFi SSID against shop configuration
  - Enforces location requirement
  - Calculates distance using Haversine formula
  - Auto-registers devices
  - Creates/updates attendance records
  - Tracks break time
  - Handles resume after checkout
  
- `process_disconnect()` - Manual disconnect handling
  - Auto checks out active session
  - Calculates total work hours
  
- `check_stale_sessions()` - Background job
  - Runs every minute via scheduler
  - Auto checks out sessions with no heartbeat for 5+ minutes

### AttendanceService
**Reporting and analytics:**
- `get_today_attendance()` - Today's attendance with leave status
- `get_attendance_summary()` - Dashboard metrics
- `get_monthly_report()` - Detailed monthly analytics per staff
- `auto_checkout_staff()` - End-of-day auto checkout (scheduled)

## Middleware

### WiFiEnforcementMiddleware
- Restricts module access based on WiFi connection
- Protected modules: stock_audit, billing, profit_analysis, customer_tracking, purchase_invoices
- Exempt modules: auth, attendance, notifications, feedback
- Checks for active attendance record (checked in, not checked out)
- Respects `allow_any_network` emergency toggle

## Background Scheduler

### Scheduler Jobs
- **Stale Session Check**: Runs every 1 minute
  - Auto checks out sessions with no heartbeat for 5 minutes
  - Adds note explaining auto checkout reason

## Authentication & Authorization

### Dependencies
- `get_current_attendance_user()` - Dual auth for admin/staff
  - **Admin**: Requires `shop_code` query parameter
  - **Staff**: Uses `shop_code` from JWT token
  - Returns: (user_object, shop_id, user_type)

### Access Control
- **Admin**: Full access to all attendance data for selected shop
- **Staff**: Access only to own attendance records
- **Module Access**: Requires active WiFi connection (unless emergency toggle enabled)

## Key Workflows

### Staff Check-In Flow
1. Staff connects to shop WiFi
2. App sends heartbeat with SSID, MAC, GPS coordinates
3. System validates WiFi SSID matches shop
4. System validates GPS location within geofence
5. System creates attendance record with check-in time
6. System determines if late based on work start time + grace period
7. Returns success with attendance details

### Heartbeat Update Flow
1. Staff already checked in
2. App sends periodic heartbeat
3. System clears any previous errors
4. System checks gap since last heartbeat
5. If gap >30 min, adds to break time
6. If checked out, resumes session (clears checkout)
7. Updates `updated_at` timestamp
8. Returns heartbeat updated status

### Auto Checkout Flow
1. Background scheduler runs every minute
2. Finds attendance records with no checkout
3. Checks if last heartbeat >5 minutes ago
4. Auto checks out with current time
5. Calculates total work hours
6. Adds explanatory note

### Module Access Check Flow
1. Staff tries to access protected module
2. Middleware extracts JWT token
3. Checks if staff user type
4. Queries attendance settings
5. If `allow_any_network` enabled, allows access
6. Otherwise, checks for active attendance record today
7. Denies access if not checked in or already checked out

## Configuration Options

### Attendance Settings
- `work_start_time`: Default 09:00
- `work_end_time`: Default 18:00
- `grace_period_minutes`: Default 15 minutes
- `auto_checkout_enabled`: Default true
- `auto_checkout_time`: Default 19:00
- `allow_any_network`: Emergency toggle, default false
- `require_wifi_for_modules`: Enforce WiFi, default true
- Working days: Individual toggles for each day

### Shop WiFi Settings
- `wifi_ssid`: Network name (required)
- `wifi_password`: Optional, for staff reference
- `shop_latitude`: Required for geofencing
- `shop_longitude`: Required for geofencing
- `geofence_radius_meters`: Default 100m

## Timezone Handling
- **Storage**: All timestamps stored in UTC
- **Check-In**: Uses Asia/Kolkata (IST) for late calculation
- **Display**: Serialized as ISO 8601 with 'Z' suffix

## Error Handling
- Location errors stored in `attendance.last_error`
- Cleared on successful heartbeat
- Displayed to staff for troubleshooting
- Common errors:
  - WiFi not registered
  - Location services disabled
  - Outside geofence radius

## Reporting Metrics

### Daily Summary
- Total staff count
- Present today
- Absent today
- Late today
- On leave today
- Pending leave requests

### Monthly Report (Per Staff)
- Total working days in month
- Present days
- Absent days
- Late days
- Leave days
- Attendance percentage
- Average check-in time
- Total work hours

## Security Features
- Shop-level data isolation
- Role-based access control
- JWT token validation
- MAC address validation
- Location verification
- Geofence enforcement

## Integration Points
- **Staff Model**: Relationship with attendance records, devices, leave requests
- **Shop Model**: Relationship with WiFi config, attendance settings
- **Auth Module**: Token validation, user authentication
- **Database**: SQLAlchemy ORM with PostgreSQL

## Monitoring Script
`wifi_monitor.py` - Optional network-level monitoring
- Scans ARP table for connected devices
- Auto check-in based on MAC address
- Can run on router, Raspberry Pi, or server
- Useful for shops without mobile app

## Best Practices
1. Configure geofence radius based on shop size
2. Set appropriate grace period for local traffic conditions
3. Enable `allow_any_network` only for emergencies
4. Review monthly reports for attendance patterns
5. Monitor stale session auto-checkouts for WiFi issues
6. Regularly check pending leave requests
7. Use break time data to optimize shift schedules

## Technical Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Scheduler**: APScheduler (AsyncIO)
- **Timezone**: zoneinfo (Python 3.9+)
- **Validation**: Pydantic v2
- **Authentication**: JWT tokens
