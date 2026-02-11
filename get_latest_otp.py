import sqlite3
from datetime import datetime

DATABASE = "pharmacy.db"
PHONE = "+919383169659"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

cursor.execute("""
    SELECT otp_code, expires_at, is_verified, created_at 
    FROM otp_verifications 
    WHERE phone = ? 
    ORDER BY created_at DESC 
    LIMIT 1
""", (PHONE,))

result = cursor.fetchone()

if result:
    otp_code, expires_at, is_verified, created_at = result
    print("="*60)
    print("📱 Latest OTP for", PHONE)
    print("="*60)
    print(f"🔢 OTP Code: {otp_code}")
    print(f"⏰ Created: {created_at}")
    print(f"⏱️  Expires: {expires_at}")
    print(f"✅ Verified: {'Yes' if is_verified else 'No'}")
    print("="*60)
else:
    print("❌ No OTP found. Send OTP first!")

conn.close()
