#!/usr/bin/env python3
"""
Get current WiFi SSID
Works on macOS, Windows, and Linux
"""

import subprocess
import platform
import re

def get_wifi_ssid():
    """Get current WiFi SSID based on OS"""
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            cmd = ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-I"]
            output = subprocess.check_output(cmd).decode('utf-8')
            ssid = re.search(r' SSID: (.+)', output)
            return ssid.group(1) if ssid else None
            
        elif system == "Windows":
            cmd = ["netsh", "wlan", "show", "interfaces"]
            output = subprocess.check_output(cmd).decode('utf-8')
            ssid = re.search(r'SSID\s+:\s+(.+)', output)
            return ssid.group(1).strip() if ssid else None
            
        elif system == "Linux":
            # Try iwgetid first
            try:
                output = subprocess.check_output(["iwgetid", "-r"]).decode('utf-8').strip()
                return output if output else None
            except:
                # Fallback to nmcli
                cmd = ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]
                output = subprocess.check_output(cmd).decode('utf-8')
                for line in output.split('\n'):
                    if line.startswith('yes:'):
                        return line.split(':')[1]
                return None
        else:
            return None
            
    except Exception as e:
        print(f"Error getting WiFi SSID: {e}")
        return None

if __name__ == "__main__":
    ssid = get_wifi_ssid()
    if ssid:
        print(f"📶 Current WiFi SSID: {ssid}")
    else:
        print("❌ Not connected to WiFi or unable to detect SSID")
