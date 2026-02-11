# Staff OTP Authentication Guide

## Overview
Staff now login using **UUID + Phone Number + OTP** for enhanced security.

## Authentication Flow

### Step 1: Staff Sends OTP Request
```bash
POST /api/auth/staff/send-otp
{
  "uuid": "staff-uuid-here",
  "phone": "+919383169659"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "expires_in": 300,
  "can_resend_in": 30
}
```

### Step 2: Staff Receives SMS
Staff receives 6-digit OTP on their registered phone number.

### Step 3: Staff Verifies OTP
```bash
POST /api/auth/staff/verify-otp
{
  "uuid": "staff-uuid-here",
  "phone": "+919383169659",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_type": "staff",
  "shop_id": 1,
  "shop_name": "Main Pharmacy"
}
```

## Security Features

1. **UUID Verification**: Staff must have valid UUID
2. **Phone Verification**: Phone must match staff record
3. **OTP Expiry**: 5 minutes
4. **Resend Cooldown**: 30 seconds
5. **Shop Status Check**: Shop must be active
6. **Last Login Tracking**: Updates on successful login

## Legacy Support

Old UUID-only login still works:
```bash
POST /api/auth/staff/login
{
  "uuid": "staff-uuid-here"
}
```

## Comparison

| Feature | Admin Login | Staff Login |
|---------|-------------|-------------|
| Method | Phone + Password + OTP | UUID + Phone + OTP |
| OTP Expiry | 5 minutes | 5 minutes |
| SMS Cost | ₹0.25/SMS | ₹0.25/SMS |
| Security | High | High |

## Testing

See `test_staff_otp.py` for complete test examples.
