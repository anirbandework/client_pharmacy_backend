# Fast2SMS Setup Guide (FREE SMS for India)

## ✅ Why Fast2SMS?
- 50 FREE SMS on signup
- No credit card required
- Instant activation
- Best delivery rates in India
- Simple API integration

---

## 📝 Step-by-Step Setup:

### Step 1: Sign Up (2 minutes)
1. Go to: **https://www.fast2sms.com/**
2. Click **"Sign Up"** (top right)
3. Fill in:
   - Name: Your name
   - Email: Your email
   - Mobile: +91-9383169659
   - Password: Create a password
4. Click **"Sign Up"**
5. Verify your email (check inbox)
6. Verify your phone (you'll get an OTP)

### Step 2: Get API Key (1 minute)
1. After login, go to **Dashboard**
2. Click **"Dev API"** in the left menu
3. You'll see your **API Key** - Copy it!
   - It looks like: `xxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 3: Update .env File
Open your `.env` file and add:
```bash
# Fast2SMS Configuration (Free for India)
FAST2SMS_API_KEY=paste_your_api_key_here
```

### Step 4: Restart Server
```bash
# Stop your current server (Ctrl+C in terminal)
# Then restart:
./start.sh
```

### Step 5: Test OTP! 🎉
```bash
source venv/bin/activate
python test_twilio_otp.py
```

You'll receive SMS on your phone: **+91-9383169659**

---

## 🔧 What I've Already Done:
✅ Updated OTP service to support Fast2SMS
✅ Fast2SMS is now the PRIMARY SMS provider
✅ Automatic fallback to console if API key missing
✅ Test scripts ready

## 📱 What You Need to Do:
1. Sign up at https://www.fast2sms.com/
2. Copy your API Key
3. Paste it in `.env` file
4. Restart server
5. Test!

---

## 🆘 Troubleshooting:

**Issue: Not receiving SMS**
- Check API key is correct in `.env`
- Verify phone number is correct: +919383169659
- Check Fast2SMS dashboard for credits

**Issue: API Error**
- Make sure you verified your email
- Check if you have remaining credits (50 free)

**Need Help?**
- Fast2SMS Support: https://www.fast2sms.com/contact
- Check server console for error messages

---

## 💡 After Setup:
Once configured, every OTP request will:
1. Generate 6-digit OTP
2. Send SMS via Fast2SMS to your phone
3. OTP valid for 30 seconds
4. You can resend after 30 seconds

**Ready? Go to https://www.fast2sms.com/ and sign up now!** 🚀
