#!/usr/bin/env python3
"""
WiFi Attendance Monitor Script

This script monitors WiFi connections and automatically marks attendance.
Can be run on:
- Router (DD-WRT/OpenWRT)
- Raspberry Pi connected to network
- Server with network access

Usage:
    python3 wifi_monitor.py --api-url http://localhost:8000 --wifi-ssid MyPharmacy_WiFi
"""

import subprocess
import requests
import time
import argparse
from datetime import datetime

class WiFiAttendanceMonitor:
    def __init__(self, api_url, wifi_ssid):
        self.api_url = api_url
        self.wifi_ssid = wifi_ssid
        self.checked_in_today = set()
    
    def get_connected_devices(self):
        """Get list of connected device MAC addresses"""
        try:
            # For macOS/Linux - using arp
            result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
            devices = []
            
            for line in result.stdout.split('\n'):
                if '(' in line and ')' in line:
                    # Extract MAC address
                    parts = line.split()
                    for part in parts:
                        if ':' in part and len(part) == 17:
                            devices.append(part.upper())
            
            return devices
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []
    
    def check_in_device(self, mac_address):
        """Send check-in request to API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/attendance/check-in/wifi",
                json={
                    "mac_address": mac_address,
                    "wifi_ssid": self.wifi_ssid
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                staff_id = data.get('staff_id')
                check_in_time = data.get('check_in_time')
                status = data.get('status')
                
                print(f"✅ Check-in successful: Staff ID {staff_id} at {check_in_time} - {status}")
                return True
            elif response.status_code == 400:
                # Device not registered or already checked in
                error = response.json().get('detail', 'Unknown error')
                if 'already checked in' not in error.lower():
                    print(f"⚠️  {mac_address}: {error}")
                return False
            else:
                print(f"❌ Check-in failed for {mac_address}: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return False
    
    def monitor(self, interval=60):
        """Monitor WiFi connections and auto check-in"""
        print(f"🔍 Starting WiFi Attendance Monitor")
        print(f"📡 API URL: {self.api_url}")
        print(f"📶 WiFi SSID: {self.wifi_ssid}")
        print(f"⏱️  Check interval: {interval} seconds")
        print(f"{'='*50}\n")
        
        while True:
            try:
                current_date = datetime.now().date()
                
                # Reset checked-in list at midnight
                if not hasattr(self, 'last_date') or self.last_date != current_date:
                    self.checked_in_today.clear()
                    self.last_date = current_date
                    print(f"\n📅 New day: {current_date}")
                
                # Get connected devices
                devices = self.get_connected_devices()
                print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - Found {len(devices)} devices")
                
                # Try to check-in each device
                for mac in devices:
                    if mac not in self.checked_in_today:
                        if self.check_in_device(mac):
                            self.checked_in_today.add(mac)
                
                # Wait before next check
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n\n👋 Stopping monitor...")
                break
            except Exception as e:
                print(f"❌ Error in monitor loop: {e}")
                time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='WiFi Attendance Monitor')
    parser.add_argument('--api-url', required=True, help='API base URL (e.g., http://localhost:8000)')
    parser.add_argument('--wifi-ssid', required=True, help='Shop WiFi SSID')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    
    args = parser.parse_args()
    
    monitor = WiFiAttendanceMonitor(args.api_url, args.wifi_ssid)
    monitor.monitor(args.interval)

if __name__ == "__main__":
    main()
