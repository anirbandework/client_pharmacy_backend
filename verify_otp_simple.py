#!/usr/bin/env python3
import sys

otp = input("Enter the 6-digit OTP from SMS: ").strip()

if len(otp) != 6 or not otp.isdigit():
    print("❌ Invalid OTP")
    sys.exit(1)

import requests

response = requests.post(
    "http://localhost:8000/api/auth/admin/verify-otp",
    json={"phone": "+919383169659", "otp_code": otp}
)

if response.status_code == 200:
    print("\n🎉 SUCCESS! OTP Verified!")
    print(f"Token: {response.json()['access_token'][:50]}...")
else:
    print(f"\n❌ Failed: {response.json()}")
