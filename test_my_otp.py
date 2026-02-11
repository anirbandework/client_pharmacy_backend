import requests
import time

BASE_URL = "http://localhost:8000/api"
PHONE = "+919383169659"
PASSWORD = "test@123"

def test_otp_flow():
    print("=" * 60)
    print("Testing OTP Authentication Flow")
    print("=" * 60)
    
    # Step 1: Send OTP
    print(f"\n1️⃣  Sending OTP to {PHONE}...")
    response = requests.post(
        f"{BASE_URL}/auth/admin/send-otp",
        json={"phone": PHONE, "password": PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"⏱️  Expires in: {data['expires_in']} seconds")
        print(f"🔄 Can resend in: {data['can_resend_in']} seconds")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"Error: {response.json()}")
        return
    
    # Step 2: Get OTP from user
    print("\n" + "=" * 60)
    print("📱 Check your console/SMS for the OTP code")
    print("=" * 60)
    otp_code = input("\nEnter the 6-digit OTP: ").strip()
    
    # Step 3: Verify OTP
    print(f"\n2️⃣  Verifying OTP...")
    response = requests.post(
        f"{BASE_URL}/auth/admin/verify-otp",
        json={"phone": PHONE, "otp_code": otp_code}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful!")
        print(f"\n🔑 Access Token: {data['access_token'][:50]}...")
        print(f"👤 User Type: {data['user_type']}")
        print(f"🏪 Shop ID: {data['shop_id']}")
        
        # Step 4: Test authenticated endpoint
        print(f"\n3️⃣  Testing authenticated endpoint...")
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        response = requests.get(f"{BASE_URL}/auth/admin/me", headers=headers)
        
        if response.status_code == 200:
            admin = response.json()
            print(f"✅ Profile retrieved!")
            print(f"📋 Name: {admin['full_name']}")
            print(f"📞 Phone: {admin['phone']}")
            print(f"📧 Email: {admin.get('email', 'N/A')}")
        else:
            print(f"❌ Failed to get profile: {response.status_code}")
    else:
        print(f"❌ Verification failed: {response.status_code}")
        print(f"Error: {response.json()}")

if __name__ == "__main__":
    try:
        test_otp_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to server")
        print("Make sure the server is running: ./start.sh or uvicorn main:app --reload")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
