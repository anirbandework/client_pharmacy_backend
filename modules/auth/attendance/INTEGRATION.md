# Quick Integration Guide

## Step 1: Register Routes in main.py

Add this to your `main.py`:

```python
from modules.auth.attendance.routes import router as attendance_router

app.include_router(
    attendance_router, 
    prefix="/api/attendance", 
    tags=["Attendance"]
)
```

## Step 2: Run Migration

```bash
cd /Users/anirbande/Desktop/client\ backend
python3 -m modules.auth.attendance.migrate_attendance
```

## Step 3: Setup Shop WiFi (Admin)

```bash
curl -X POST http://localhost:8000/api/attendance/wifi/setup \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": 1,
    "wifi_ssid": "MyPharmacy_WiFi",
    "wifi_password": "optional123"
  }'
```

## Step 4: Staff Registers Device

```bash
curl -X POST http://localhost:8000/api/attendance/device/register \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "iPhone 12"
  }'
```

## Step 5: WiFi Auto Check-in

When staff phone connects to WiFi, call:

```bash
curl -X POST http://localhost:8000/api/attendance/check-in/wifi \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "wifi_ssid": "MyPharmacy_WiFi"
  }'
```

## Step 6: View Dashboard

```bash
curl -X GET "http://localhost:8000/api/attendance/summary?shop_id=1" \
  -H "Authorization: Bearer <admin_token>"
```

## How to Get MAC Address

### On Android (Mobile App)
```java
WifiManager wifiManager = (WifiManager) getSystemService(Context.WIFI_SERVICE);
WifiInfo wifiInfo = wifiManager.getConnectionInfo();
String macAddress = wifiInfo.getMacAddress();
```

### On iOS (Mobile App)
```swift
// iOS doesn't allow direct MAC access, use device UUID instead
let deviceId = UIDevice.current.identifierForVendor?.uuidString
```

### On Router (Script)
```bash
# Get connected devices
arp -a | grep "192.168.1" | awk '{print $4}'
```

## Testing Without Mobile App

For testing, you can:

1. **Manual Check-in** (Admin marks attendance):
```bash
curl -X POST http://localhost:8000/api/attendance/check-in/manual \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "staff_id": 1,
    "notes": "Manual check-in for testing"
  }'
```

2. **Self Check-in** (Staff marks own attendance):
```bash
curl -X POST http://localhost:8000/api/attendance/check-in/self \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Self check-in"
  }'
```

## View Today's Attendance

```bash
curl -X GET "http://localhost:8000/api/attendance/today?shop_id=1" \
  -H "Authorization: Bearer <admin_token>"
```

Response:
```json
[
  {
    "staff_id": 1,
    "staff_name": "John Doe",
    "staff_code": "ST001",
    "attendance": {
      "id": 1,
      "check_in_time": "2024-01-15T09:05:00",
      "check_out_time": null,
      "status": "present",
      "is_late": false,
      "late_by_minutes": 0,
      "auto_checked_in": true
    },
    "on_leave": false,
    "status": "present"
  }
]
```

## Complete!

Your WiFi-based attendance system is now ready! 🎉
