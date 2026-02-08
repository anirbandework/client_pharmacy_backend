# WhatsApp Integration Setup Guide

## Overview
This system uses WhatsApp Business API to send real messages to customers for refill reminders and promotional materials.

## Setup Steps

### 1. Get WhatsApp Business API Access

**Option A: Meta (Facebook) WhatsApp Business API** (Recommended)
1. Go to https://developers.facebook.com/
2. Create a Meta Developer Account
3. Create a new App → Select "Business" type
4. Add "WhatsApp" product to your app
5. Get your:
   - Phone Number ID
   - Access Token (Permanent token recommended)

**Option B: Third-Party Providers** (Easier)
- **Twilio**: https://www.twilio.com/whatsapp
- **MessageBird**: https://messagebird.com/whatsapp
- **Gupshup**: https://www.gupshup.io/
- **Interakt**: https://www.interakt.shop/
- **WATI**: https://www.wati.io/

### 2. Configure Environment Variables

Update your `.env` file:

```bash
# For Meta WhatsApp Business API
WHATSAPP_API_URL=https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_TOKEN=your_permanent_access_token

# For Twilio
WHATSAPP_API_URL=https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json
WHATSAPP_TOKEN=your_twilio_auth_token

# For other providers, check their documentation
```

### 3. Meta WhatsApp Business API Setup (Detailed)

#### Step 1: Create Meta App
```bash
1. Visit: https://developers.facebook.com/apps/
2. Click "Create App"
3. Select "Business" as app type
4. Fill in app details
```

#### Step 2: Add WhatsApp Product
```bash
1. In your app dashboard, click "Add Product"
2. Find "WhatsApp" and click "Set Up"
3. Follow the setup wizard
```

#### Step 3: Get Phone Number ID
```bash
1. Go to WhatsApp → Getting Started
2. Copy your "Phone Number ID"
3. This is what you'll use in WHATSAPP_API_URL
```

#### Step 4: Get Access Token
```bash
1. Go to WhatsApp → Getting Started
2. Copy the "Temporary access token" (valid 24 hours)
3. For production, generate a permanent token:
   - Go to Settings → Basic
   - Generate a System User Token
   - Give it whatsapp_business_messaging permission
```

#### Step 5: Test Your Setup
```bash
# In the Meta dashboard, use the API test tool
curl -X POST \
  'https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages' \
  -H 'Authorization: Bearer YOUR_ACCESS_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "messaging_product": "whatsapp",
    "to": "919876543210",
    "type": "text",
    "text": {
      "body": "Hello from Pharmacy!"
    }
  }'
```

### 4. Update .env File

Replace the placeholder values:

```bash
# Before
WHATSAPP_API_URL=https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID/messages
WHATSAPP_TOKEN=your_whatsapp_business_api_token

# After (example)
WHATSAPP_API_URL=https://graph.facebook.com/v18.0/123456789012345/messages
WHATSAPP_TOKEN=EAABsbCS1iHgBO7ZC8wZBmXqL9ZAz...
```

### 5. Restart Your Application

```bash
# Stop the server (Ctrl+C)
# Start again
uvicorn main:app --reload
```

### 6. Test the Integration

```bash
# Test refill reminder
curl -X POST "http://localhost:8000/api/customers/reminders/1/notify"

# Check logs for success/failure
```

## Message Templates (Meta WhatsApp)

For production use with Meta, you need to create approved message templates:

### 1. Create Template in Meta Dashboard
```
1. Go to WhatsApp → Message Templates
2. Click "Create Template"
3. Choose category: "UTILITY" (for reminders)
4. Add your message with variables
```

### 2. Example Template
```
Name: refill_reminder
Category: UTILITY
Language: English

Body:
Hello {{1}}! 👋

This is a friendly reminder that your medicine '{{2}}' is due for refill.

Visit us to refill your prescription and ensure uninterrupted treatment.

Thank you for choosing our pharmacy! 🏥
```

### 3. Update Code to Use Template
```python
# In services.py, modify send_refill_notification:
payload = {
    'messaging_product': 'whatsapp',
    'to': formatted_phone,
    'type': 'template',
    'template': {
        'name': 'refill_reminder',
        'language': {'code': 'en'},
        'components': [{
            'type': 'body',
            'parameters': [
                {'type': 'text', 'text': customer.name or 'Customer'},
                {'type': 'text', 'text': reminder.medicine_name}
            ]
        }]
    }
}
```

## Testing Without Real WhatsApp

If you don't have WhatsApp API yet, the system will print messages to console:

```bash
# You'll see in logs:
WhatsApp not configured. Message: Hello anirban! 👋...
```

## Cost Considerations

### Meta WhatsApp Business API
- First 1,000 conversations/month: FREE
- After that: ~$0.005 - $0.09 per conversation (varies by country)
- India: ~₹0.40 per conversation

### Third-Party Providers
- Twilio: ~$0.005 per message
- Gupshup: ~₹0.25 per message
- Interakt: Plans start at ₹999/month

## Troubleshooting

### Error: "WhatsApp not configured"
- Check if WHATSAPP_API_URL and WHATSAPP_TOKEN are set in .env
- Restart the server after updating .env

### Error: "Invalid access token"
- Token might be expired (temporary tokens last 24 hours)
- Generate a permanent System User Token

### Error: "Phone number not registered"
- The recipient must have WhatsApp installed
- For testing, use your own WhatsApp number first

### Error: "Template not approved"
- Wait for Meta to approve your template (usually 1-2 hours)
- Use pre-approved templates for testing

## Production Checklist

- [ ] Get permanent access token (not temporary)
- [ ] Create and approve message templates
- [ ] Set up webhook for delivery status
- [ ] Add error handling and retry logic
- [ ] Monitor API usage and costs
- [ ] Comply with WhatsApp Business Policy
- [ ] Add opt-out mechanism for customers

## Support

- Meta WhatsApp Docs: https://developers.facebook.com/docs/whatsapp
- Twilio WhatsApp Docs: https://www.twilio.com/docs/whatsapp
- WhatsApp Business Policy: https://www.whatsapp.com/legal/business-policy

## Quick Start (For Testing)

1. Use Twilio (easiest for testing):
   ```bash
   # Sign up at twilio.com
   # Get a WhatsApp-enabled number
   # Update .env with Twilio credentials
   ```

2. Or use Meta's test number:
   ```bash
   # In Meta dashboard, you get a test number
   # Can send to 5 numbers for free
   # Perfect for development
   ```

Your WhatsApp integration is ready! 🎉
