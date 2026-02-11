# WiFi-Based Automatic Attendance System

## 🎯 Overview

Automatic attendance tracking system that marks staff attendance when their device connects to the shop's WiFi network. Zero manual intervention required!

## 🚀 How It Works

1. **Admin Setup**: Configure shop WiFi SSID in system
2. **Staff Registration**: Staff registers their device MAC address
3. **Auto Check-in**: When staff phone connects to shop WiFi → Attendance marked automatically
4. **Timestamp Tracking**: System records exact check-in/check-out times
5. **Admin Dashboard**: Real-time view of who's present, late, or absent

## 📋 Features

### Core Features
- ✅ **WiFi Auto-Detection**: Automatic check-in when device connects to shop WiFi
- ✅ **MAC Address Tracking**: Each staff device registered by MAC address
- ✅ **Late Arrival Detection**: Automatic late marking with grace period
- ✅ **Auto Check-out**: Configurable auto check-out at end of day
- ✅ **Manual Override**: Admin can manually mark attendance
- ✅ **Real-time Dashboard**: See who's present right now
- ✅ **Leave Management**: Staff can request leaves, admin approves
- ✅ **Monthly Reports**: Comprehensive attendance analytics

### Admin Features
- View today's attendance (present/absent/late)
- See exact check-in/check-out timestamps
- Monthly attendance reports per staff
- Configure work timings and grace periods
- Approve/reject leave requests
- Manual attendance marking
- Export reports

### Staff Features
- Auto check-in via WiFi
- Register multiple devices
- View own attendance history
- Request leaves
- Self check-in (if WiFi fails)
- Check-out manually

## 🔧 Technical Implementation

### Database Tables

**shop_wifi** - Shop WiFi configuration
```sql
- shop_id (FK to shops)
- wifi_ssid (e.g., "MyPharmacy_WiFi")
- wifi_password (optional, for staff reference)
- is_active
```

**staff_devices** - Registered staff devices
```sql
- staff_id (FK to staff)
- mac_address (unique, e.g., "AA:BB:CC:DD:EE:FF")
- device_name (e.g., "iPhone 12")
- last_seen (last WiFi connection time)
```

**attendance_records** - Daily attendance
```sql
- staff_id, shop_id, device_id, wifi_id
- date, check_in_time, check_out_time
- status (present/late/absent)
- is_late, late_by_minutes
- total_hours (work duration in minutes)
- auto_checked_in (true if WiFi auto-detected)
```

**attendance_settings** - Shop-specific settings
```sql
- work_start_time (default: 09:00)
- work_end_time (default: 18:00)
- grace_period_minutes (default: 15)
- auto_checkout_enabled, auto_checkout_time
- working_days (monday-sunday booleans)
```

**leave_requests** - Leave management
```sql
- staff_id, leave_type (sick/casual/earned)
- from_date, to_date, total_days
- status (pending/approved/rejected)
- approved_by, approved_at
```

## 📡 API Endpoints

### WiFi & Device Setup

#### Setup Shop WiFi (Admin)
```http
POST /api/attendance/wifi/setup
Authorization: Bearer <admin_token>

{
  "shop_id": 1,
  "wifi_ssid": "MyPharmacy_WiFi",
  "wifi_password": "optional123"
}
```

#### Register Device (Staff)
```http
POST /api/attendance/device/register
Authorization: Bearer <staff_token>

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_name": "iPhone 12"
}
```

#### Get My Devices (Staff)
```http
GET /api/attendance/device/my-devices
Authorization: Bearer <staff_token>
```

### Attendance Check-in/out

#### WiFi Auto Check-in (Called by app/script)
```http
POST /api/attendance/check-in/wifi

{
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "wifi_ssid": "MyPharmacy_WiFi"
}

Response:
{
  "id": 1,
  "staff_id": 5,
  "date": "2024-01-15",
  "check_in_time": "2024-01-15T09:05:00",
  "status": "present",
  "is_late": false,
  "auto_checked_in": true
}
```

#### Manual Check-in (Admin)
```http
POST /api/attendance/check-in/manual
Authorization: Bearer <admin_token>

{
  "staff_id": 5,
  "notes": "Manually marked by admin"
}
```

#### Self Check-in (Staff)
```http
POST /api/attendance/check-in/self
Authorization: Bearer <staff_token>

{
  "notes": "WiFi not working"
}
```

#### Check-out (Staff)
```http
POST /api/attendance/check-out
Authorization: Bearer <staff_token>

{
  "notes": "Leaving early - doctor appointment"
}
```

### Attendance Viewing

#### Today's Attendance (Admin)
```http
GET /api/attendance/today?shop_id=1
Authorization: Bearer <admin_token>

Response:
[
  {
    "staff_id": 5,
    "staff_name": "John Doe",
    "staff_code": "ST001",
    "attendance": {
      "check_in_time": "2024-01-15T09:05:00",
      "status": "present",
      "is_late": false
    },
    "on_leave": false,
    "status": "present"
  },
  {
    "staff_id": 6,
    "staff_name": "Jane Smith",
    "staff_code": "ST002",
    "attendance": null,
    "on_leave": false,
    "status": "absent"
  }
]
```

#### Attendance Summary Dashboard (Admin)
```http
GET /api/attendance/summary?shop_id=1
Authorization: Bearer <admin_token>

Response:
{
  "total_staff": 10,
  "present_today": 8,
  "absent_today": 1,
  "late_today": 2,
  "on_leave_today": 1,
  "pending_leave_requests": 3
}
```

#### Attendance Records (Admin)
```http
GET /api/attendance/records?shop_id=1&staff_id=5&from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <admin_token>
```

#### My Attendance (Staff)
```http
GET /api/attendance/my-attendance?from_date=2024-01-01&to_date=2024-01-31
Authorization: Bearer <staff_token>
```

#### Monthly Report (Admin)
```http
GET /api/attendance/monthly-report/2024/1?shop_id=1
Authorization: Bearer <admin_token>

Response:
{
  "month": 1,
  "year": 2024,
  "staff_summaries": [
    {
      "staff_id": 5,
      "staff_name": "John Doe",
      "staff_code": "ST001",
      "total_days": 31,
      "present_days": 28,
      "absent_days": 2,
      "late_days": 3,
      "leave_days": 1,
      "attendance_percentage": 90.32,
      "average_check_in_time": "09:12",
      "total_work_hours": 12960  // in minutes
    }
  ]
}
```

### Settings Management

#### Get Settings (Admin)
```http
GET /api/attendance/settings/1
Authorization: Bearer <admin_token>
```

#### Update Settings (Admin)
```http
PUT /api/attendance/settings/1
Authorization: Bearer <admin_token>

{
  "work_start_time": "09:00:00",
  "work_end_time": "18:00:00",
  "grace_period_minutes": 15,
  "auto_checkout_enabled": true,
  "auto_checkout_time": "19:00:00",
  "sunday": false
}
```

### Leave Management

#### Request Leave (Staff)
```http
POST /api/attendance/leave/request
Authorization: Bearer <staff_token>

{
  "leave_type": "sick",
  "from_date": "2024-01-20",
  "to_date": "2024-01-22",
  "reason": "Medical appointment"
}
```

#### My Leave Requests (Staff)
```http
GET /api/attendance/leave/my-requests
Authorization: Bearer <staff_token>
```

#### Pending Leaves (Admin)
```http
GET /api/attendance/leave/pending?shop_id=1
Authorization: Bearer <admin_token>
```

#### Approve Leave (Admin)
```http
PUT /api/attendance/leave/123/approve
Authorization: Bearer <admin_token>
```

#### Reject Leave (Admin)
```http
PUT /api/attendance/leave/123/reject
Authorization: Bearer <admin_token>

{
  "status": "rejected",
  "rejection_reason": "Insufficient staff during this period"
}
```

## 🔌 WiFi Auto-Detection Implementation

### Option 1: Mobile App (Recommended)

**iOS/Android App:**
```javascript
// Detect WiFi connection
const wifiSSID = await getConnectedWiFiSSID();
const macAddress = await getDeviceMACAddress();

if (wifiSSID === "MyPharmacy_WiFi") {
  // Auto check-in
  await fetch('https://api.pharmacy.com/api/attendance/check-in/wifi', {
    method: 'POST',
    body: JSON.stringify({
      mac_address: macAddress,
      wifi_ssid: wifiSSID
    })
  });
}
```

### Option 2: Router Script

**DD-WRT/OpenWRT Router Script:**
```bash
#!/bin/sh
# Monitor WiFi connections and auto check-in

while true; do
  # Get connected devices
  iw dev wlan0 station dump | grep "Station" | while read line; do
    MAC=$(echo $line | awk '{print $2}')
    
    # Call API
    curl -X POST https://api.pharmacy.com/api/attendance/check-in/wifi \
      -H "Content-Type: application/json" \
      -d "{\"mac_address\":\"$MAC\",\"wifi_ssid\":\"MyPharmacy_WiFi\"}"
  done
  
  sleep 60  # Check every minute
done
```

### Option 3: Network Monitoring Tool

Use tools like:
- **Fing** - Network scanner
- **Wireshark** - Packet analyzer
- **arp-scan** - ARP scanner

## 🎯 Usage Workflow

### Initial Setup (One-time)

1. **Admin configures WiFi**
   ```
   POST /api/attendance/wifi/setup
   ```

2. **Staff registers device**
   ```
   POST /api/attendance/device/register
   ```

### Daily Operation (Automatic)

1. **Staff arrives at shop**
   - Phone connects to shop WiFi
   - App/script detects connection
   - Calls WiFi check-in API
   - Attendance marked automatically ✅

2. **Admin monitors**
   - Opens dashboard
   - Sees real-time attendance
   - Views timestamps

3. **Staff leaves**
   - Manually checks out OR
   - Auto check-out at 7 PM

## 📊 Admin Dashboard Views

### Today's Attendance
```
Total Staff: 10
Present: 8 (80%)
Late: 2 (20%)
Absent: 1 (10%)
On Leave: 1 (10%)

Staff List:
✅ John Doe - 09:05 AM (On time)
⚠️ Jane Smith - 09:20 AM (Late by 20 min)
❌ Bob Wilson - Absent
🏖️ Alice Brown - On Leave
```

### Monthly Report
```
John Doe (ST001)
- Present: 28/31 days (90.3%)
- Late: 3 days
- Avg Check-in: 09:12 AM
- Total Hours: 216 hours
```

## 🔒 Security Features

- MAC address validation
- WiFi SSID verification
- Staff-shop association check
- Device registration required
- Admin-only manual override
- Audit trail for all changes

## 🚀 Integration with Existing System

The attendance system integrates seamlessly with:
- **Auth System**: Uses existing admin/staff authentication
- **Salary System**: Attendance data can be used for salary calculation
- **Shop Management**: Multi-tenant support with shop_id

## 📱 Mobile App Requirements

For full automation, mobile app needs:
- WiFi SSID detection permission
- MAC address access (Android) or device ID (iOS)
- Background location (optional, for geofencing)
- Push notifications for check-in confirmation

## 🎉 Benefits

1. **Zero Manual Work**: Completely automatic
2. **Accurate Timestamps**: Exact check-in/out times
3. **No Buddy Punching**: MAC address tied to device
4. **Real-time Monitoring**: Admin sees live status
5. **Comprehensive Reports**: Monthly analytics
6. **Leave Management**: Integrated leave system
7. **Flexible Settings**: Customizable per shop

## 🔧 Next Steps

1. Run database migration to create tables
2. Register routes in main.py
3. Setup shop WiFi via API
4. Staff registers devices
5. Implement mobile app or router script
6. Monitor attendance dashboard!
