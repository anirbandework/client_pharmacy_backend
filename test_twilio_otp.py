#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://localhost:8000/api/auth"
PHONE = "+919383169659"
PASSWORD = "test@123"

print("="*70)
print("🔐 Testing OTP with Twilio SMS")
print("="*70)

# Send OTP
print(f"\n📤 Sending OTP to {PHONE}...")
response = requests.post(
    f"{BASE_URL}/admin/send-otp",
    json={"phone": PHONE, "password": PASSWORD}
)

if response.status_code == 200:
    print("✅ OTP sent! Check your phone for SMS")
    print(f"⏱️  You have 30 seconds to enter the OTP")
    
    otp = input("\n🔢 Enter the 6-digit OTP from SMS: ").strip()
    
    # Verify OTP
    print(f"\n🔍 Verifying OTP...")
    response = requests.post(
        f"{BASE_URL}/admin/verify-otp",
        json={"phone": PHONE, "otp_code": otp}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! You're logged in!")
        print(f"🎫 Token: {data['access_token'][:50]}...")
    else:
        print(f"\n❌ Failed: {response.json()}")
else:
    print(f"❌ Failed to send OTP: {response.json()}")
