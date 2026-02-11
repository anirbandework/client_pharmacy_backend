#!/usr/bin/env python3
import requests
import sys

PHONE = "+919383169659"
otp = input("Enter the 6-digit OTP from SMS: ").strip()

if len(otp) != 6 or not otp.isdigit():
    print("❌ Invalid OTP format")
    sys.exit(1)

print(f"\n🔍 Verifying OTP {otp}...")
response = requests.post(
    "http://localhost:8000/api/auth/admin/verify-otp",
    json={"phone": PHONE, "otp_code": otp}
)

if response.status_code == 200:
    data = response.json()
    print("\n" + "="*70)
    print("🎉 SUCCESS! OTP Authentication Complete!")
    print("="*70)
    print(f"✅ Logged in as Admin")
    print(f"🎫 Token: {data['access_token'][:60]}...")
    print(f"📱 Phone: {PHONE}")
    print("="*70)
else:
    print(f"\n❌ Verification failed: {response.json()}")
