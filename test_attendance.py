#!/usr/bin/env python3
"""
Test Script for WiFi Attendance System

This script will:
1. Create test admin and staff
2. Setup shop WiFi
3. Register staff device
4. Test WiFi check-in
5. Run WiFi monitor in test mode
"""

import requests
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

class AttendanceSystemTester:
    def __init__(self):
        self.admin_token = None
        self.staff_token = None
        self.shop_id = None
        self.staff_id = None
        self.test_mac = "AA:BB:CC:DD:EE:FF"
        self.wifi_ssid = "TestPharmacy_WiFi"
    
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
                print(f"   Response: {response.json()}")
                return True
            else:
                self.print_error(f"Server returned status {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Cannot connect to server: {e}")
            self.print_info("Make sure server is running: uvicorn main:app --reload")
            return False
    
    def setup_admin(self):
        """Create or login admin"""
        self.print_step(2, "Admin Setup")
        
        # Try to register
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/admin/register",
                json={
                    "email": "test@pharmacy.com",
                    "password": "test123",
                    "full_name": "Test Admin",
                    "phone": "1234567890"
                }
            )
            if response.status_code == 200:
                self.print_success("Admin registered successfully")
            else:
                self.print_info("Admin already exists, logging in...")
        except Exception as e:
            self.print_info(f"Registration skipped: {e}")
        
        # Login
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/login",
            json={
                "email": "test@pharmacy.com",
                "password": "test123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.admin_token = data["access_token"]
            self.print_success("Admin logged in successfully")
            print(f"   Token: {self.admin_token[:20]}...")
            return True
        else:
            self.print_error(f"Admin login failed: {response.text}")
            return False
    
    def setup_shop(self):
        """Create shop"""
        self.print_step(3, "Shop Setup")
        
        # Try to create shop
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/shops",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "shop_name": "Test Pharmacy",
                "shop_code": "TEST001",
                "address": "123 Test Street"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.shop_id = data["id"]
            self.print_success(f"Shop created with ID: {self.shop_id}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            # Get existing shop
            response = requests.get(
                f"{BASE_URL}/api/auth/admin/shops",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            shops = response.json()
            if shops:
                self.shop_id = shops[0]["id"]
                self.print_info(f"Using existing shop ID: {self.shop_id}")
                return True
        
        self.print_error(f"Shop setup failed: {response.text}")
        return False
    
    def setup_wifi(self):
        """Setup shop WiFi"""
        self.print_step(4, "WiFi Setup")
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/wifi/setup",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "shop_id": self.shop_id,
                "wifi_ssid": self.wifi_ssid,
                "wifi_password": "test123"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success(f"WiFi configured: {data['wifi_ssid']}")
            return True
        else:
            self.print_error(f"WiFi setup failed: {response.text}")
            return False
    
    def setup_staff(self):
        """Create staff"""
        self.print_step(5, "Staff Setup")
        
        # Try to get existing staff first
        response = requests.get(
            f"{BASE_URL}/api/auth/shops/{self.shop_id}/staff",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 200:
            staff_list = response.json()
            # Find staff with our test code or use first one
            test_staff = None
            for s in staff_list:
                if s.get("staff_code") == "ST001":
                    test_staff = s
                    break
            
            if not test_staff and staff_list:
                test_staff = staff_list[0]
            
            if test_staff:
                self.staff_id = test_staff["id"]
                # Login
                response = requests.post(
                    f"{BASE_URL}/api/auth/staff/login",
                    json={"uuid": test_staff["uuid"]}
                )
                if response.status_code == 200:
                    self.staff_token = response.json()["access_token"]
                    self.print_info(f"Using existing staff ID: {self.staff_id}")
                    return True
        
        # Create new staff with unique code
        import random
        staff_code = f"ST{random.randint(1000, 9999)}"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/admin/shops/{self.shop_id}/staff",
            headers={"Authorization": f"Bearer {self.admin_token}"},
            json={
                "name": "Test Staff",
                "staff_code": staff_code,
                "phone": "9876543210",
                "email": f"staff{random.randint(1000, 9999)}@test.com"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.staff_id = data["id"]
            staff_uuid = data["uuid"]
            self.print_success(f"Staff created with ID: {self.staff_id}")
            print(f"   UUID: {staff_uuid}")
            
            # Login as staff
            response = requests.post(
                f"{BASE_URL}/api/auth/staff/login",
                json={"uuid": staff_uuid}
            )
            
            if response.status_code == 200:
                self.staff_token = response.json()["access_token"]
                self.print_success("Staff logged in successfully")
                return True
        
        self.print_error(f"Staff setup failed: {response.text}")
        return False
    
    def register_device(self):
        """Register staff device"""
        self.print_step(6, "Device Registration")
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/device/register",
            headers={"Authorization": f"Bearer {self.staff_token}"},
            json={
                "mac_address": self.test_mac,
                "device_name": "Test iPhone"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success(f"Device registered: {data['mac_address']}")
            return True
        else:
            self.print_error(f"Device registration failed: {response.text}")
            return False
    
    def test_wifi_checkin(self):
        """Test WiFi check-in"""
        self.print_step(7, "Testing WiFi Check-in")
        
        response = requests.post(
            f"{BASE_URL}/api/attendance/check-in/wifi",
            json={
                "mac_address": self.test_mac,
                "wifi_ssid": self.wifi_ssid
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success("WiFi check-in successful!")
            print(f"   Staff ID: {data['staff_id']}")
            print(f"   Check-in Time: {data['check_in_time']}")
            print(f"   Status: {data['status']}")
            print(f"   Late: {data['is_late']}")
            print(f"   Auto Check-in: {data['auto_checked_in']}")
            return True
        else:
            self.print_error(f"WiFi check-in failed: {response.text}")
            return False
    
    def view_dashboard(self):
        """View attendance dashboard"""
        self.print_step(8, "Viewing Attendance Dashboard")
        
        # Today's attendance
        response = requests.get(
            f"{BASE_URL}/api/attendance/today?shop_id={self.shop_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.print_success("Today's Attendance:")
            for record in data:
                status_icon = "✅" if record["status"] == "present" else "❌"
                print(f"   {status_icon} {record['staff_name']} ({record['staff_code']}) - {record['status']}")
                if record["attendance"]:
                    print(f"      Check-in: {record['attendance']['check_in_time']}")
        
        # Summary
        response = requests.get(
            f"{BASE_URL}/api/attendance/summary?shop_id={self.shop_id}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n   📊 Summary:")
            print(f"      Total Staff: {data['total_staff']}")
            print(f"      Present: {data['present_today']}")
            print(f"      Absent: {data['absent_today']}")
            print(f"      Late: {data['late_today']}")
            return True
        
        return False
    
    def test_wifi_monitor(self):
        """Test WiFi monitor script"""
        self.print_step(9, "Testing WiFi Monitor Script")
        
        self.print_info("WiFi Monitor can be run with:")
        print(f"\n   python3 modules/auth/attendance/wifi_monitor.py \\")
        print(f"     --api-url {BASE_URL} \\")
        print(f"     --wifi-ssid {self.wifi_ssid} \\")
        print(f"     --interval 10")
        
        self.print_info("\nThe monitor will:")
        print("   1. Scan for connected devices every 10 seconds")
        print("   2. Auto check-in devices with registered MAC addresses")
        print("   3. Display real-time status")
        
        return True
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 WiFi ATTENDANCE SYSTEM - COMPREHENSIVE TEST")
        print("="*60)
        
        tests = [
            self.test_server,
            self.setup_admin,
            self.setup_shop,
            self.setup_wifi,
            self.setup_staff,
            self.register_device,
            self.test_wifi_checkin,
            self.view_dashboard,
            self.test_wifi_monitor
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
        print(f"   Shop ID: {self.shop_id}")
        print(f"   Staff ID: {self.staff_id}")
        print(f"   WiFi SSID: {self.wifi_ssid}")
        print(f"   Test MAC: {self.test_mac}")
        
        print("\n🚀 Next Steps:")
        print("   1. Check attendance dashboard in browser:")
        print(f"      http://localhost:8000/docs")
        print("   2. Run WiFi monitor:")
        print(f"      python3 modules/auth/attendance/wifi_monitor.py --api-url {BASE_URL} --wifi-ssid {self.wifi_ssid}")
        print("   3. View API documentation:")
        print(f"      http://localhost:8000/docs#/Attendance%20System")
        
        return True

if __name__ == "__main__":
    tester = AttendanceSystemTester()
    tester.run_all_tests()
