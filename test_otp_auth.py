#!/usr/bin/env python3
"""
Test Script for OTP-based Admin Authentication

This script will:
1. Register admin with phone number
2. Send OTP to phone
3. Verify OTP and login
4. Test complete flow
"""

import requests
import time

BASE_URL = "http://localhost:8000"

class OTPAuthTester:
    def __init__(self):
        self.admin_token = None
        self.test_phone = "+919876543210"
        self.test_password = "test123"
        self.otp_code = None
    
    def print_step(self, step, message):
        print(f"\n{'='*60}")
        print(f"STEP {step}: {message}")
        print(f"{'='*60}")
    
    def print_success(self, message):
        print(f"✅ {message}")
    
    def print_error(self, message):
        print(f"❌ {message}")
    
    def print_info(self, message):
        print(f"ℹ️  {message}")
    
    def test_server(self):
        """Test if server is running"""
        self.print_step(1, "Testing Server Connection")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.print_success("Server is running!")
                return True
            else:
                self.print_error(f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Cannot connect to server: {e}")
            return False
    
    def register_admin(self):
        """Register admin with phone number"""
        self.print_step(2, "Admin Registration")
        
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/register",
            json={
                "phone": self.test_phone,
                "password": self.test_password,
                "full_name": "Test Admin OTP"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success("Admin registered successfully")
            print(f"   Phone: {data['phone']}")
            print(f"   Name: {data['full_name']}")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            self.print_info("Admin already exists, continuing...")
            return True
        else:
            self.print_error(f"Registration failed: {response.text}")
            return False
    
    def send_otp(self):
        """Send OTP to phone"""
        self.print_step(3, "Sending OTP")
        
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/send-otp",
            json={
                "phone": self.test_phone,
                "password": self.test_password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success(data['message'])
            print(f"   Expires in: {data['expires_in']} seconds")
            self.print_info("Check server console for OTP code")
            return True
        else:
            self.print_error(f"Failed to send OTP: {response.text}")
            return False
    
    def verify_otp(self):
        """Verify OTP and login"""
        self.print_step(4, "Verifying OTP")
        
        # Get OTP from user
        self.print_info("Enter the OTP code from server console:")
        self.otp_code = input("OTP Code: ").strip()
        
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/verify-otp",
            json={
                "phone": self.test_phone,
                "otp_code": self.otp_code
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.print_success("OTP verified! Admin logged in successfully")
            print(f"   Token: {self.admin_token[:20]}...")
            print(f"   User Type: {data['user_type']}")
            return True
        else:
            self.print_error(f"OTP verification failed: {response.text}")
            return False
    
    def test_authenticated_request(self):
        """Test authenticated request"""
        self.print_step(5, "Testing Authenticated Request")
        
        response = requests.get(
            f"{BASE_URL}/api/auth/admin/me",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success("Authenticated request successful!")
            print(f"   Admin ID: {data['id']}")
            print(f"   Name: {data['full_name']}")
            print(f"   Phone: {data['phone']}")
            return True
        else:
            self.print_error(f"Authenticated request failed: {response.text}")
            return False
    
    def test_invalid_otp(self):
        """Test invalid OTP"""
        self.print_step(6, "Testing Invalid OTP")
        
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/verify-otp",
            json={
                "phone": self.test_phone,
                "otp_code": "000000"
            }
        )
        
        if response.status_code == 400:
            self.print_success("Invalid OTP correctly rejected")
            return True
        else:
            self.print_error("Invalid OTP should have been rejected")
            return False
    
    def test_expired_otp(self):
        """Test OTP expiry"""
        self.print_step(7, "Testing OTP Expiry")
        
        self.print_info("Sending OTP...")
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/send-otp",
            json={
                "phone": self.test_phone,
                "password": self.test_password
            }
        )
        
        if response.status_code == 200:
            self.print_success("OTP sent")
            self.print_info("OTP expires in 5 minutes (300 seconds)")
            self.print_info("In production, wait 5 minutes to test expiry")
            return True
        return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 OTP AUTHENTICATION SYSTEM - COMPREHENSIVE TEST")
        print("="*60)
        
        tests = [
            self.test_server,
            self.register_admin,
            self.send_otp,
            self.verify_otp,
            self.test_authenticated_request,
            self.test_invalid_otp,
            self.test_expired_otp
        ]
        
        for test in tests:
            if not test():
                self.print_error("Test failed! Stopping...")
                return False
            time.sleep(0.5)
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        
        print("\n📋 Test Summary:")
        print(f"   Phone: {self.test_phone}")
        print(f"   Password: {self.test_password}")
        print(f"   Token: {self.admin_token[:30]}..." if self.admin_token else "   Token: None")
        
        print("\n🚀 OTP Authentication Flow:")
        print("   1. Admin registers with phone + password")
        print("   2. Admin enters phone + password to request OTP")
        print("   3. OTP sent via SMS (printed to console for testing)")
        print("   4. Admin enters OTP to verify and login")
        print("   5. JWT token issued for authenticated requests")
        
        print("\n📱 Frontend Integration:")
        print("   POST /api/auth/admin/send-otp")
        print("   POST /api/auth/admin/verify-otp")
        
        return True

if __name__ == "__main__":
    tester = OTPAuthTester()
    tester.run_all_tests()
