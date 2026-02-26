# Attendance System - Complete Flow & Improvements

## ✅ Fixed Issues

### 1. **Admin Access** (CRITICAL FIX)
- **Before**: Only staff could access attendance endpoints
- **After**: Both admin and staff can access with proper role-based permissions
- **Implementation**: Updated `get_current_attendance_user()` to return `(user, shop_id, user_type)`

### 2. **Role-Based Access Control**
**Admin Can:**
- Setup shop WiFi
- View all staff attendance (real-time & historical)
- View attendance summary dashboard
- View monthly reports
- Toggle "Allow any network" for emergencies
- Approve/reject leave requests
- View currently connected staff (real-time)

**Staff Can:**
- View shop WiFi info (to know which network to connect)
- Send WiFi heartbeats (automatic)
- View their own attendance records
- Request leave
- View their leave requests
- Register devices (optional)

### 3. **Real-Time Monitoring**
- **New Endpoint**: `GET /api/attendance/wifi/connected-staff`
- Shows which staff are currently connected (heartbeat within 2 minutes)
- Displays: staff name, check-in time, duration, last seen
- Admin dashboard can show live connection status

### 4. **Automatic WiFi Detection**
- Staff app sends heartbeat every 30-60 seconds
- First heartbeat → Auto check-in with timestamp
- Subsequent heartbeats → Update last_seen
- No heartbeat for 2+ minutes → Considered disconnected
- WiFi disconnect → Auto check-out with timestamp

### 5. **Module Access Control**
- **WiFiEnforcementMiddleware** blocks access to:
  - Stock Audit
  - Billing
  - Profit Analysis
  - Customer Tracking
  - Purchase Invoices
- **Bypass**: Admin can enable "allow_any_network" for emergencies
- **Check**: Staff app calls `/api/attendance/wifi/status` before accessing modules

## 📊 Complete User Flow

### Admin Flow:
1. **Setup** (One-time):
   - Login as admin
   - Navigate to Attendance → WiFi Setup
   - Enter WiFi SSID and password
   - Configure work timings, grace period, etc.

2. **Daily Monitoring**:
   - View Dashboard → See summary (present, late, absent, on leave)
   - View "Connected Staff" → Real-time list of who's in shop
   - View Today's Attendance → All staff with timestamps
   - View Records → Historical attendance with filters

3. **Emergency Override**:
   - Power outage? → Toggle "Allow any network" ON
   - Staff can now access modules from any network
   - After emergency → Toggle OFF

4. **Leave Management**:
   - View pending leave requests
   - Approve or reject with reason
   - View leave calendar

### Staff Flow:
1. **First Time** (Optional):
   - Login as staff
   - View WiFi info to know which network to connect
   - Optionally register device MAC address

2. **Daily Automatic**:
   - Connect to shop WiFi
   - App automatically sends heartbeat every 30-60 seconds
   - First heartbeat → Auto check-in (timestamp recorded)
   - Continue working → Heartbeat keeps updating
   - Disconnect WiFi → Auto check-out (timestamp recorded)

3. **Module Access**:
   - Try to access Stock Audit/Billing
   - If connected to WiFi → Access granted
   - If not connected → "WiFi connection required" error
   - If admin enabled "allow any network" → Access granted

4. **View Own Data**:
   - View own attendance records
   - View own leave requests
   - Request new leave

## 🔒 Data Privacy

### Shop-Level Isolation:
- All queries filter by `shop_id` from JWT token
- Staff can only see their own shop's data
- Admin can see all shops in their organization

### Organization-Level:
- Multiple admins with same `organization_id` can manage same shops
- Each shop has unique `shop_code`
- Staff belongs to one shop only

### Zero Cross-Shop Leakage:
- Staff A (Shop 1) cannot see Staff B (Shop 2) data
- Admin A (Org 1) cannot see Admin B (Org 2) data
- All endpoints validate shop_id from token

## 🎯 Key Endpoints

### WiFi Management:
- `POST /api/attendance/wifi/setup` - Admin sets up WiFi (SSID + password)
- `GET /api/attendance/wifi/info` - Staff gets WiFi info
- `POST /api/attendance/wifi/heartbeat` - Staff sends connection heartbeat
- `POST /api/attendance/wifi/disconnect` - Staff notifies disconnection
- `GET /api/attendance/wifi/status` - Staff checks if can access modules
- `GET /api/attendance/wifi/connected-staff` - Admin views currently connected staff

### Viewing:
- `GET /api/attendance/today` - Today's attendance (admin: all, staff: own)
- `GET /api/attendance/summary` - Dashboard summary (admin only)
- `GET /api/attendance/records` - Historical records (admin: all, staff: own)
- `GET /api/attendance/my-attendance` - Staff's own records
- `GET /api/attendance/monthly-report/{year}/{month}` - Monthly report (admin only)

### Settings:
- `GET /api/attendance/settings` - Get settings (both)
- `PUT /api/attendance/settings` - Update settings (admin only)
  - Includes `allow_any_network` toggle
  - Includes `require_wifi_for_modules` toggle

### Leave Management:
- `POST /api/attendance/leave/request` - Staff requests leave
- `GET /api/attendance/leave/my-requests` - Staff views own requests
- `GET /api/attendance/leave/pending` - Admin views pending requests
- `PUT /api/attendance/leave/{id}/approve` - Admin approves
- `PUT /api/attendance/leave/{id}/reject` - Admin rejects

## 🚀 Frontend Requirements

### Staff App:
1. **WiFi Detection Service**:
   ```javascript
   // On WiFi connect
   setInterval(() => {
     if (connectedToShopWiFi) {
       attendanceAPI.wifiHeartbeat({ wifi_ssid, mac_address })
     }
   }, 30000) // Every 30 seconds
   
   // On WiFi disconnect
   attendanceAPI.wifiDisconnect()
   ```

2. **Module Access Guard**:
   ```javascript
   // Before accessing protected modules
   const status = await attendanceAPI.getWifiStatus()
   if (!status.can_access_modules) {
     showError("Please connect to shop WiFi")
     return
   }
   // Proceed to module
   ```

3. **UI Components**:
   - WiFi connection status indicator (green/red)
   - Own attendance timeline
   - Leave request form
   - Own leave requests list

### Admin Dashboard:
1. **WiFi Setup Form**:
   - SSID input
   - Password input (optional)
   - Save button

2. **Real-Time Dashboard**:
   - Summary cards (total, present, late, absent, on leave)
   - "Currently Connected" section (live updates every 30s)
   - Today's attendance list with timestamps

3. **Emergency Toggle**:
   - Prominent "Allow Any Network" switch (red/green)
   - Warning message when enabled
   - Auto-disable after X hours (optional)

4. **Reports**:
   - Date range filter
   - Staff filter
   - Export to CSV
   - Monthly summary

5. **Leave Management**:
   - Pending requests list
   - Approve/Reject buttons
   - Leave calendar view

## 🔧 Database Migration

Run this SQL to add WiFi enforcement fields:
```bash
psql $DATABASE_URL < migrations/add_wifi_enforcement_fields.sql
```

## ✨ Benefits

1. **Zero Manual Effort**: No check-in/out buttons
2. **Accurate Timestamps**: Exact WiFi connect/disconnect times
3. **Module Security**: Ensures physical presence
4. **Emergency Flexibility**: Admin override for power outages
5. **Complete Privacy**: Shop-level data isolation
6. **Real-Time Monitoring**: Admin sees live connections
7. **Role-Based Access**: Admin and staff see appropriate data
8. **Audit Trail**: All events logged with timestamps
