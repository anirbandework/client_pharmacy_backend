# OTP Authentication Testing Guide

## 🚀 Quick Start

### 1. Restart Server
```bash
# Stop current server (Ctrl+C)
# Start server again
uvicorn main:app --reload
```

This will create the new `otp_verifications` table.

### 2. Register Admin with Phone
```bash
curl -X POST http://localhost:8000/api/auth/admin/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "password": "test123",
    "full_name": "Test Admin"
  }'
```

### 3. Request OTP
```bash
curl -X POST http://localhost:8000/api/auth/admin/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "password": "test123"
  }'
```

**Check server console** - OTP will be printed like:
```
==================================================
📱 SMS to +919876543210
Your OTP code is: 123456
Valid for 5 minutes
==================================================
```

### 4. Verify OTP and Login
```bash
curl -X POST http://localhost:8000/api/auth/admin/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "otp_code": "123456"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_type": "admin",
  "shop_id": null,
  "shop_name": null
}
```

### 5. Use Token for Authenticated Requests
```bash
curl -X GET http://localhost:8000/api/auth/admin/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📱 Frontend Integration

### Login Form
```javascript
// Step 1: Send OTP
const sendOTP = async (phone, password) => {
  const response = await fetch('/api/auth/admin/send-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, password })
  });
  return response.json();
};

// Step 2: Verify OTP
const verifyOTP = async (phone, otp_code) => {
  const response = await fetch('/api/auth/admin/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, otp_code })
  });
  const data = await response.json();
  localStorage.setItem('admin_token', data.access_token);
  return data;
};
```

### UI Flow
1. Show phone + password input
2. User clicks "Send OTP"
3. Show OTP input field
4. User enters 6-digit OTP
5. User clicks "Verify & Login"
6. Redirect to dashboard

## 🔧 SMS Integration (Production)

To integrate real SMS, update `modules/auth/otp/service.py`:

```python
import os
from twilio.rest import Client

def send_sms(phone: str, otp: str) -> bool:
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'Your OTP code is: {otp}. Valid for 5 minutes.',
        from_=from_number,
        to=phone
    )
    return message.sid is not None
```

## ✅ Test Checklist

- [ ] Server restarts successfully
- [ ] Admin registration with phone works
- [ ] OTP is sent (printed to console)
- [ ] OTP verification works
- [ ] JWT token is issued
- [ ] Authenticated requests work
- [ ] Invalid OTP is rejected
- [ ] Expired OTP is rejected (after 5 min)

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/admin/register` | POST | Register with phone |
| `/api/auth/admin/send-otp` | POST | Request OTP |
| `/api/auth/admin/verify-otp` | POST | Verify OTP & login |
| `/api/auth/admin/me` | GET | Get profile (auth required) |

## 📝 Notes

- OTP expires in 5 minutes
- OTP is 6 digits
- Phone format: `+[country_code][number]` (e.g., `+919876543210`)
- Old email login still works for backward compatibility
