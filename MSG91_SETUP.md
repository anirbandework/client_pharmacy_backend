# MSG91 Setup Guide (Free SMS for India)

## Why MSG91?
- ✅ 100 FREE SMS on signup
- ✅ Better delivery rates in India
- ✅ No credit card required for trial
- ✅ Easy setup

## Setup Steps:

### 1. Sign Up
1. Go to https://msg91.com/signup
2. Enter your details
3. Verify your email and phone

### 2. Get Auth Key
1. Login to MSG91 Dashboard
2. Go to **Settings** → **API Keys**
3. Copy your **Auth Key**

### 3. Create OTP Template (Optional)
1. Go to **SMS** → **Templates**
2. Create a new template:
   ```
   Your OTP code is ##OTP##. Valid for 30 seconds. Do not share.
   ```
3. Get the **Template ID**

### 4. Update .env File
```bash
MSG91_AUTH_KEY=your_actual_auth_key_here
MSG91_TEMPLATE_ID=your_template_id_here  # Optional
```

### 5. Restart Server
```bash
# Stop server (Ctrl+C)
./start.sh
```

### 6. Test OTP
```bash
source venv/bin/activate
python test_twilio_otp.py
```

## Alternative: Fast2SMS (Also Free for India)
If MSG91 doesn't work, try Fast2SMS:
- Sign up: https://www.fast2sms.com/
- Get API Key
- Add to .env: `FAST2SMS_API_KEY=your_key`

## Current Status
- ✅ Code updated to support MSG91
- ⏳ Waiting for your MSG91 credentials
- 📝 Once added, SMS will be sent automatically
