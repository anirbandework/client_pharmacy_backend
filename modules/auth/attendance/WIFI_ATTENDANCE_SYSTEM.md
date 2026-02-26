# WiFi-Based Automatic Attendance System

## Overview
Complete automatic attendance tracking system with WiFi-based check-in/out and module access control.

## Architecture

### 1. User Hierarchy
```
SuperAdmin
  └── Admin (organization_id)
       └── Shop (shop_code)
            └── Staff (UUID)
```

- **organization_id**: Shared by multiple admins managing same shops
- **shop_code**: Unique identifier for each shop within organization
- **Staff**: Belongs to one shop, logs in with UUID

### 2. Data Privacy
- **Shop-level isolation**: All attendance data filtered by shop_id from JWT token
- **Organization-level**: Admins with same organization_id can manage multiple shops
- **Zero cross-shop leakage**: Staff can only see their own shop's data

## Features

### 1. Automatic WiFi Detection
**How it works:**
1. Admin sets up shop WiFi (SSID + optional password)
2. Staff app connects to shop WiFi
3. Staff app sends heartbeat every 30-60 seconds to `/api/attendance/wifi/heartbeat`
4. First heartbeat → Auto check-in with timestamp
5. Subsequent heartbeats → Update last_seen timestamp
6. WiFi disconnect → Auto check-out with timestamp

**Endpoints:**
- `POST /api/attendance/wifi/heartbeat` - Send WiFi connection heartbeat
- `POST /api/attendance/wifi/disconnect` - Notify WiFi disconnection
- `GET /api/attendance/wifi/status` - Check current connection status

### 2. Module Access Control
**Protected Modules** (require WiFi connection):
- Stock Audit (`/api/stock-audit`)
- Billing (`/api/billing`)
- Profit Analysis (`/api/profit`)
- Customer Tracking (`/api/customer-tracking`)
- Purchase Invoices (`/api/purchase-invoices`)

**Exempt Modules** (always accessible):
- Auth (`/api/auth`)
- Attendance (`/api/attendance`)
- Notifications (`/api/notifications`)
- Feedback (`/api/feedback`)

**Enforcement:**
- `WiFiEnforcementMiddleware` checks if staff has active attendance record (checked in, not checked out)
- If not connected → HTTP 403 with message "WiFi connection required"
- Admin can toggle "Allow any network" for emergencies

### 3. Emergency Override
**Admin Controls:**
- `allow_any_network` (Boolean) - Emergency toggle to bypass WiFi requirement
- `require_wifi_for_modules` (Boolean) - Enable/disable WiFi enforcement globally

**Use Cases:**
- Power outage → Admin enables "allow_any_network"
- WiFi router failure → Staff can still access modules
- After emergency → Admin disables "allow_any_network"

### 4. Attendance Settings
```python
{
    "work_start_time": "09:00",
    "work_end_time": "18:00",
    "grace_period_minutes": 15,
    "auto_checkout_enabled": true,
    "auto_checkout_time": "19:00",
    "allow_any_network": false,  # Emergency toggle
    "require_wifi_for_modules": true,  # WiFi enforcement
    "monday": true,
    "tuesday": true,
    ...
}
```

## Database Schema

### New Fields in `attendance_settings`:
```sql
allow_any_network BOOLEAN DEFAULT FALSE
require_wifi_for_modules BOOLEAN DEFAULT TRUE
```

### Attendance Record:
```sql
- check_in_time: Auto-set on first WiFi heartbeat
- check_out_time: Auto-set on WiFi disconnect or stale session
- auto_checked_in: TRUE for WiFi-based check-in
- auto_checked_out: TRUE for WiFi-based check-out
- updated_at: Updated on every heartbeat (for stale detection)
```

## Frontend Implementation

### Staff App Requirements:
1. **WiFi Detection**: Monitor WiFi connection status
2. **Heartbeat Service**: Send heartbeat every 30-60 seconds when connected
3. **Disconnect Handler**: Call disconnect endpoint when WiFi lost
4. **Status Check**: Check `/api/attendance/wifi/status` before accessing modules
5. **Error Handling**: Show "Connect to WiFi" message if module access denied

### Admin Dashboard:
1. **WiFi Setup**: Configure shop WiFi SSID/password
2. **Emergency Toggle**: "Allow any network" button (prominent, red/green)
3. **Real-time Status**: Show which staff are currently connected
4. **Attendance Timeline**: View check-in/out timestamps for all staff

## API Endpoints

### WiFi Management:
- `POST /api/attendance/wifi/setup` - Admin sets up shop WiFi
- `POST /api/attendance/wifi/heartbeat` - Staff sends connection heartbeat
- `POST /api/attendance/wifi/disconnect` - Staff notifies disconnection
- `GET /api/attendance/wifi/status` - Check current WiFi status

### Settings:
- `GET /api/attendance/settings` - Get attendance settings
- `PUT /api/attendance/settings` - Update settings (including allow_any_network)

### Viewing:
- `GET /api/attendance/today` - Today's attendance for all staff
- `GET /api/attendance/summary` - Dashboard summary
- `GET /api/attendance/records` - Historical records
- `GET /api/attendance/my-attendance` - Staff's own records

## Security

### 1. JWT Token:
```json
{
    "user_id": 123,
    "user_type": "staff",
    "shop_code": "SHOP001",
    "organization_id": "ORG123"
}
```

### 2. Middleware Chain:
1. **ShopContextMiddleware**: Extracts shop context
2. **WiFiEnforcementMiddleware**: Checks WiFi requirement
3. **RateLimitMiddleware**: Prevents abuse

### 3. Data Isolation:
- All queries filter by `shop_id` from JWT token
- Staff can only access their own shop's data
- Admins can access all shops in their organization

## Stale Session Detection

### Background Job (Optional):
```python
# Run every minute via cron/scheduler
WiFiHeartbeatService.check_stale_sessions(db, stale_minutes=5)
```

- If no heartbeat for 5 minutes → Auto check-out
- Prevents "ghost" sessions from app crashes
- Adds note: "Auto checked-out due to WiFi disconnect"

## Migration

### Run SQL Migration:
```bash
psql $DATABASE_URL < migrations/add_wifi_enforcement_fields.sql
```

### Adds:
- `allow_any_network` column (default FALSE)
- `require_wifi_for_modules` column (default TRUE)

## Testing Checklist

### Staff Flow:
- [ ] Connect to shop WiFi → Auto check-in
- [ ] Stay connected → Heartbeat updates
- [ ] Disconnect → Auto check-out
- [ ] Try accessing stock_audit without WiFi → 403 error
- [ ] Admin enables "allow_any_network" → Can access modules

### Admin Flow:
- [ ] Setup shop WiFi
- [ ] View real-time attendance
- [ ] Toggle "allow_any_network"
- [ ] View attendance history
- [ ] Approve/reject leave requests

### Edge Cases:
- [ ] App crash → Stale session detection
- [ ] Multiple devices → Each device tracked separately
- [ ] WiFi password change → Update in settings
- [ ] Power outage → Emergency override works

## Benefits

1. **Zero Manual Effort**: No buttons to click for check-in/out
2. **Accurate Timestamps**: Exact WiFi connect/disconnect times
3. **Module Security**: Ensures staff are physically present
4. **Emergency Flexibility**: Admin can override for emergencies
5. **Complete Privacy**: Shop-level data isolation
6. **Real-time Monitoring**: Admin sees who's connected live
7. **Audit Trail**: All check-in/out events logged with timestamps
