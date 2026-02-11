import requests
import sys

BASE_URL = "http://localhost:8000/api/auth"
PHONE = "+919383169659"
PASSWORD = "test@123"

print("="*70)
print("🔐 OTP Authentication Test")
print("="*70)

# Step 1: Send OTP
print(f"\n📤 Step 1: Sending OTP to {PHONE}...")
try:
    response = requests.post(
        f"{BASE_URL}/admin/send-otp",
        json={"phone": PHONE, "password": PASSWORD}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed: {response.json()}")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ {data['message']}")
    print(f"⏱️  Expires in: {data['expires_in']} seconds")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Step 2: Get OTP from user
print("\n" + "="*70)
print("📱 CHECK YOUR SERVER TERMINAL FOR THE OTP CODE!")
print("   Look for a message like:")
print("   📱 SMS to +919383169659")
print("   Your OTP code is: XXXXXX")
print("="*70)

otp_code = input("\n🔢 Enter the 6-digit OTP: ").strip()

if len(otp_code) != 6 or not otp_code.isdigit():
    print("❌ Invalid OTP format. Must be 6 digits.")
    sys.exit(1)

# Step 3: Verify OTP
print(f"\n🔍 Step 2: Verifying OTP...")
try:
    response = requests.post(
        f"{BASE_URL}/admin/verify-otp",
        json={"phone": PHONE, "otp_code": otp_code}
    )
    
    if response.status_code != 200:
        print(f"❌ Verification failed: {response.json()}")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ Login successful!")
    print(f"\n🎫 Token Details:")
    print(f"   Type: {data['user_type']}")
    print(f"   Token: {data['access_token'][:50]}...")
    
    # Step 4: Test authenticated endpoint
    print(f"\n👤 Step 3: Fetching profile...")
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    response = requests.get(f"{BASE_URL}/admin/me", headers=headers)
    
    if response.status_code == 200:
        admin = response.json()
        print(f"✅ Profile retrieved!")
        print(f"\n📋 Admin Details:")
        print(f"   ID: {admin['id']}")
        print(f"   Name: {admin['full_name']}")
        print(f"   Phone: {admin['phone']}")
        print(f"   Email: {admin.get('email', 'N/A')}")
        print(f"   Active: {admin['is_active']}")
        
        print("\n" + "="*70)
        print("🎉 OTP AUTHENTICATION TEST PASSED!")
        print("="*70)
    else:
        print(f"❌ Failed to get profile: {response.json()}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
