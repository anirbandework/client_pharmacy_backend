# Attendance Backend Changes Summary

## Key Changes Made:

### 1. **Admin + Staff Access** (CRITICAL)
- Both admin and staff can now access attendance
- Admin must pass `shop_code` as query parameter
- Staff gets `shop_code` automatically from JWT token

### 2. **Removed Endpoints** (No longer needed):
- ❌ `POST /check-in/wifi` - Replaced by heartbeat
- ❌ `POST /check-in/manual` - Replaced by heartbeat
- ❌ `POST /check-in/self` - Replaced by heartbeat
- ❌ `POST /check-out` - Replaced by disconnect
- ❌ `POST /check-out/staff/{staff_id}` - Replaced by disconnect

### 3. **New Endpoints**:
- ✅ `POST /wifi/heartbeat` - Staff sends every 30-60s (auto check-in)
- ✅ `POST /wifi/disconnect` - Staff notifies disconnect (auto check-out)
- ✅ `GET /wifi/status` - Staff checks if can access modules
- ✅ `GET /wifi/connected-staff` - Admin sees who's currently connected
- ✅ `GET /wifi/info` - Staff gets WiFi SSID/password

### 4. **Updated Endpoints**:
All endpoints now return `(user, shop_id, user_type)` tuple

## API Reference for Frontend:

### Admin Endpoints (require `?shop_code=SHOP001`):
```
GET /api/attendance/today?shop_code=SHOP001
GET /api/attendance/summary?shop_code=SHOP001
GET /api/attendance/records?shop_code=SHOP001&staff_id=1&from_date=2024-01-01
GET /api/attendance/monthly-report/2024/1?shop_code=SHOP001
GET /api/attendance/wifi/connected-staff?shop_code=SHOP001
GET /api/attendance/settings?shop_code=SHOP001
PUT /api/attendance/settings?shop_code=SHOP001
POST /api/attendance/wifi/setup?shop_code=SHOP001
GET /api/attendance/leave/pending?shop_code=SHOP001
PUT /api/attendance/leave/{id}/approve?shop_code=SHOP001
PUT /api/attendance/leave/{id}/reject?shop_code=SHOP001
```

### Staff Endpoints (no shop_code needed):
```
POST /api/attendance/wifi/heartbeat
POST /api/attendance/wifi/disconnect
GET /api/attendance/wifi/status
GET /api/attendance/wifi/info
GET /api/attendance/today
GET /api/attendance/my-attendance?from_date=2024-01-01
GET /api/attendance/settings
POST /api/attendance/device/register
GET /api/attendance/device/my-devices
POST /api/attendance/leave/request
GET /api/attendance/leave/my-requests
```

## Frontend Integration Requirements:

### Admin Dashboard:
1. **Shop Selector** - Dropdown to select shop (gets shop_code)
2. **Pass shop_code** - Add `?shop_code=${selectedShop}` to all API calls
3. **Real-Time Connected Staff** - Poll `/wifi/connected-staff` every 30s
4. **Emergency Toggle** - "Allow Any Network" switch in settings
5. **WiFi Setup Form** - SSID + Password inputs

### Staff App:
1. **WiFi Heartbeat Service** - Send heartbeat every 30-60s when connected
2. **WiFi Disconnect Handler** - Call on WiFi loss
3. **Module Access Guard** - Check `/wifi/status` before accessing modules
4. **WiFi Info Display** - Show SSID/password from `/wifi/info`
5. **Connection Status Indicator** - Green/red based on heartbeat

## Settings Schema:
```json
{
  "work_start_time": "09:00",
  "work_end_time": "18:00",
  "grace_period_minutes": 15,
  "auto_checkout_enabled": true,
  "auto_checkout_time": "19:00",
  "allow_any_network": false,  // Emergency toggle
  "require_wifi_for_modules": true,  // WiFi enforcement
  "monday": true,
  "tuesday": true,
  ...
}
```

## Attendance Record Schema:
```json
{
  "id": 1,
  "staff_id": 1,
  "shop_id": 1,
  "date": "2024-01-15",
  "check_in_time": "2024-01-15T09:05:00",
  "check_out_time": "2024-01-15T18:00:00",
  "status": "present",  // present, late, absent, on_leave
  "is_late": false,
  "late_by_minutes": 0,
  "total_hours": 535,  // in minutes
  "auto_checked_in": true,
  "auto_checked_out": true,
  "notes": null
}
```
