# Twilio SMS Setup Guide

## 🚀 Quick Setup (5 minutes)

### 1. Create Twilio Account
1. Go to https://www.twilio.com/try-twilio
2. Sign up for free trial (includes $15 credit)
3. Verify your email and phone number

### 2. Get Credentials
1. Go to Twilio Console: https://console.twilio.com/
2. Copy these values:
   - **Account SID** (starts with AC...)
   - **Auth Token** (click to reveal)

### 3. Get Phone Number
1. In Twilio Console, go to **Phone Numbers** → **Manage** → **Buy a number**
2. Select your country (India: +91)
3. Choose a number with SMS capability
4. Buy the number (free with trial credit)

### 4. Configure Environment Variables
Add to your `.env` file:
```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### 5. Install Twilio SDK
```bash
pip install twilio
```

### 6. Test SMS
Restart your server and test OTP:
```bash
curl -X POST http://localhost:8000/api/auth/admin/send-otp \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "password": "test123"
  }'
```

You should receive SMS on your phone! 📱

## 💰 Pricing

### Trial Account (Free)
- $15 credit
- ~500 SMS messages
- Can only send to verified numbers

### Paid Account
- India SMS: ₹0.50 - ₹1.00 per SMS
- US SMS: $0.0079 per SMS
- No monthly fees, pay-as-you-go

## 🔒 Security Best Practices

1. **Never commit credentials** to git
2. **Use environment variables** for all secrets
3. **Rotate tokens** regularly
4. **Enable IP whitelisting** in Twilio console
5. **Monitor usage** to prevent abuse

## 🌍 International SMS

Twilio supports 180+ countries:
- India: +91
- US: +1
- UK: +44
- Australia: +61

Just use the correct country code in phone numbers!

## 🐛 Troubleshooting

### "Unable to create record: The number is unverified"
**Solution**: In trial mode, verify the recipient number in Twilio Console → Phone Numbers → Verified Caller IDs

### "Authentication Error"
**Solution**: Check your Account SID and Auth Token are correct

### "Invalid 'To' Phone Number"
**Solution**: Ensure phone number includes country code (e.g., +919876543210)

### SMS not received
**Solution**: 
1. Check phone number is correct
2. Check SMS logs in Twilio Console
3. Verify number is verified (trial accounts)
4. Check your Twilio balance

## 📊 Monitor Usage

View SMS logs in Twilio Console:
- **Monitor** → **Logs** → **Messaging**
- See delivery status, timestamps, errors

## 🔄 Alternative SMS Providers

If you prefer other providers:

### AWS SNS
```python
import boto3

sns = boto3.client('sns', region_name='us-east-1')
sns.publish(PhoneNumber=phone, Message=f'Your OTP: {otp}')
```

### MSG91 (India)
```python
import requests

requests.post('https://api.msg91.com/api/v5/flow/', json={
    'authkey': 'YOUR_AUTH_KEY',
    'mobiles': phone,
    'otp': otp
})
```

### Firebase Cloud Messaging
```python
from firebase_admin import messaging

message = messaging.Message(
    notification=messaging.Notification(body=f'Your OTP: {otp}'),
    token=device_token
)
```

## ✅ Production Checklist

- [ ] Twilio account created
- [ ] Phone number purchased
- [ ] Credentials added to .env
- [ ] .env added to .gitignore
- [ ] SMS tested successfully
- [ ] Error handling tested
- [ ] Usage monitoring enabled
- [ ] Budget alerts configured

## 🎉 Done!

Your OTP system is now production-ready with real SMS delivery! 🚀
