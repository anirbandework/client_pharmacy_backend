# Testing Guide - WiFi Attendance System

## 🧪 Complete Testing Workflow

### Prerequisites
1. Backend server running
2. Admin account created
3. Shop created
4. Staff account created

---

## Step 1: Setup Shop WiFi (Admin)

```bash
# Login as admin first
curl -X POST http://localhost:8000/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@pharmacy.com",
    "password": "admin123"
  }'

# Save the access_token from response
export ADMIN_TOKEN="<your_admin_token>"

# Setup shop WiFi
curl -X POST http://localhost:8000/api/attendance/wifi/setup \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": 1,
    "wifi_ssid": "TestPharmacy_WiFi",
    "wifi_password": "test123"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "shop_id": 1,
  "wifi_ssid": "TestPharmacy_WiFi",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00"
}
```

---

## Step 2: Register Staff Device

```bash
# Login as staff
curl -X POST http://localhost:8000/api/auth/staff/login \
  -H "Content-Type: application/json" \
  -d '{
    "uuid": "<staff_uuid>"
  }'

# Save the access_token
export STAFF_TOKEN="<your_staff_token>"

# Register device
curl -X POST http://localhost:8000/api/attendance/device/register \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "device_name": "Test iPhone"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "staff_id": 1,
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "device_name": "Test iPhone",
  "is_active": true,
  "registered_at": "2024-01-15T10:05:00",
  "last_seen": null
}
```

---

## Step 3: Test WiFi Auto Check-in

```bash
# Simulate WiFi connection (no auth needed)
curl -X POST http://localhost:8000/api/attendance/check-in/wifi \
  -H "Content-Type: application/json" \
  -d '{
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "wifi_ssid": "TestPharmacy_WiFi"
  }'
```

**Expected Response (On-time):**
```json
{
  "id": 1,
  "staff_id": 1,
  "shop_id": 1,
  "device_id": 1,
  "wifi_id": 1,
  "date": "2024-01-15",
  "check_in_time": "2024-01-15T09:05:00",
  "check_out_time": null,
  "status": "present",
  "is_late": false,
  "late_by_minutes": 0,
  "total_hours": null,
  "auto_checked_in": true,
  "auto_checked_out": false,
  "notes": null
}
```

**Expected Response (Late):**
```json
{
  "status": "late",
  "is_late": true,
  "late_by_minutes": 25
}
```

---

## Step 4: View Today's Attendance (Admin)

```bash
curl -X GET "http://localhost:8000/api/attendance/today?shop_id=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
[
  {
    "staff_id": 1,
    "staff_name": "John Doe",
    "staff_code": "ST001",
    "attendance": {
      "id": 1,
      "check_in_time": "2024-01-15T09:05:00",
      "status": "present",
      "is_late": false
    },
    "on_leave": false,
    "status": "present"
  }
]
```

---

## Step 5: View Dashboard Summary

```bash
curl -X GET "http://localhost:8000/api/attendance/summary?shop_id=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "total_staff": 10,
  "present_today": 8,
  "absent_today": 1,
  "late_today": 2,
  "on_leave_today": 1,
  "pending_leave_requests": 3
}
```

---

## Step 6: Staff Check-out

```bash
curl -X POST http://localhost:8000/api/attendance/check-out \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Leaving on time"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "check_in_time": "2024-01-15T09:05:00",
  "check_out_time": "2024-01-15T18:00:00",
  "total_hours": 535,
  "status": "present"
}
```

---

## Step 7: View Staff's Own Attendance

```bash
curl -X GET "http://localhost:8000/api/attendance/my-attendance?from_date=2024-01-01&to_date=2024-01-31" \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

---

## Step 8: Request Leave (Staff)

```bash
curl -X POST http://localhost:8000/api/attendance/leave/request \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type": "sick",
    "from_date": "2024-01-20",
    "to_date": "2024-01-22",
    "reason": "Medical appointment"
  }'
```

**Expected Response:**
```json
{
  "id": 1,
  "staff_id": 1,
  "leave_type": "sick",
  "from_date": "2024-01-20",
  "to_date": "2024-01-22",
  "total_days": 3,
  "reason": "Medical appointment",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}
```

---

## Step 9: View Pending Leaves (Admin)

```bash
curl -X GET "http://localhost:8000/api/attendance/leave/pending?shop_id=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Step 10: Approve Leave (Admin)

```bash
curl -X PUT http://localhost:8000/api/attendance/leave/1/approve \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "status": "approved",
  "approved_by": "Admin Name",
  "approved_at": "2024-01-15T10:35:00"
}
```

---

## Step 11: Monthly Report (Admin)

```bash
curl -X GET "http://localhost:8000/api/attendance/monthly-report/2024/1?shop_id=1" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Expected Response:**
```json
{
  "month": 1,
  "year": 2024,
  "staff_summaries": [
    {
      "staff_id": 1,
      "staff_name": "John Doe",
      "staff_code": "ST001",
      "total_days": 31,
      "present_days": 28,
      "absent_days": 2,
      "late_days": 3,
      "leave_days": 1,
      "attendance_percentage": 90.32,
      "average_check_in_time": "09:12",
      "total_work_hours": 12960
    }
  ]
}
```

---

## Step 12: Update Attendance Settings (Admin)

```bash
curl -X PUT http://localhost:8000/api/attendance/settings/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "work_start_time": "09:00:00",
    "work_end_time": "18:00:00",
    "grace_period_minutes": 15,
    "auto_checkout_enabled": true,
    "auto_checkout_time": "19:00:00"
  }'
```

---

## 🧪 Test Scenarios

### Scenario 1: On-time Check-in
- Time: 9:05 AM
- Expected: status="present", is_late=false

### Scenario 2: Late Check-in
- Time: 9:25 AM (grace period: 15 min)
- Expected: status="late", is_late=true, late_by_minutes=25

### Scenario 3: Duplicate Check-in
- Check-in twice same day
- Expected: Returns existing record, no duplicate

### Scenario 4: Unregistered Device
- MAC address not registered
- Expected: 400 error "Device not registered"

### Scenario 5: Wrong WiFi
- Different WiFi SSID
- Expected: 400 error "WiFi network not recognized"

### Scenario 6: Staff from Different Shop
- Staff tries to check-in at wrong shop
- Expected: 400 error "Staff does not belong to this shop"

---

## 🔍 Error Testing

### Test 1: Invalid MAC Address
```bash
curl -X POST http://localhost:8000/api/attendance/device/register \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -d '{"mac_address": "INVALID"}'
```
**Expected:** 422 Validation Error

### Test 2: Already Checked In
```bash
# Check-in twice
curl -X POST http://localhost:8000/api/attendance/check-in/wifi \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "wifi_ssid": "TestPharmacy_WiFi"}'

# Second attempt
curl -X POST http://localhost:8000/api/attendance/check-in/wifi \
  -d '{"mac_address": "AA:BB:CC:DD:EE:FF", "wifi_ssid": "TestPharmacy_WiFi"}'
```
**Expected:** Returns existing record

### Test 3: Check-out Without Check-in
```bash
curl -X POST http://localhost:8000/api/attendance/check-out \
  -H "Authorization: Bearer $STAFF_TOKEN"
```
**Expected:** 400 "No check-in record found for today"

---

## 📊 Performance Testing

### Load Test: Multiple Check-ins
```bash
# Simulate 100 staff checking in
for i in {1..100}; do
  MAC=$(printf "AA:BB:CC:DD:EE:%02X" $i)
  curl -X POST http://localhost:8000/api/attendance/check-in/wifi \
    -d "{\"mac_address\":\"$MAC\",\"wifi_ssid\":\"TestPharmacy_WiFi\"}" &
done
wait
```

---

## 🎯 Integration Testing

### Test WiFi Monitor Script
```bash
# Start monitor
python3 modules/auth/attendance/wifi_monitor.py \
  --api-url http://localhost:8000 \
  --wifi-ssid TestPharmacy_WiFi \
  --interval 10

# Monitor should detect devices and auto check-in
```

---

## ✅ Checklist

- [ ] Shop WiFi setup successful
- [ ] Device registration successful
- [ ] WiFi auto check-in works
- [ ] Late detection works correctly
- [ ] Check-out works
- [ ] Dashboard shows correct data
- [ ] Leave request/approval works
- [ ] Monthly report generates
- [ ] Settings update works
- [ ] Error handling works
- [ ] WiFi monitor script works

---

## 🐛 Common Issues

### Issue 1: "Device not registered"
**Solution:** Register device first using `/device/register`

### Issue 2: "WiFi network not recognized"
**Solution:** Setup shop WiFi using `/wifi/setup`

### Issue 3: "Already checked in"
**Solution:** This is expected behavior, returns existing record

### Issue 4: MAC address format error
**Solution:** Use format AA:BB:CC:DD:EE:FF (uppercase, colon-separated)

---

## 📝 Test Data

### Sample MAC Addresses
```
AA:BB:CC:DD:EE:01
AA:BB:CC:DD:EE:02
AA:BB:CC:DD:EE:03
```

### Sample WiFi SSIDs
```
TestPharmacy_WiFi
MainStreet_Pharmacy
Downtown_Pharmacy_5G
```

### Sample Leave Types
```
sick
casual
earned
```

---

## 🎉 Success Criteria

✅ All API endpoints return expected responses
✅ Timestamps are accurate
✅ Late detection works with grace period
✅ Dashboard shows real-time data
✅ Leave management works end-to-end
✅ Monthly reports are accurate
✅ Error handling is proper
✅ WiFi auto-detection works

**System is ready for production!** 🚀
