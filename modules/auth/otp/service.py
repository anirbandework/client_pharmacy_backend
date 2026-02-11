import random
import os
import threading
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .models import OTPVerification
from ..models import Admin
from ..service import AuthService

class OTPService:
    OTP_EXPIRY_MINUTES = 5  # 5 minutes for testing
    RESEND_COOLDOWN_SECONDS = 30  # Can resend after 30 seconds
    
    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def send_sms_async(phone: str, otp: str):
        """Send SMS in background thread to avoid blocking"""
        thread = threading.Thread(target=OTPService.send_sms, args=(phone, otp))
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def send_sms(phone: str, otp: str) -> bool:
        """Send OTP via SMS using Fast2SMS"""
        try:
            fast2sms_key = os.getenv('FAST2SMS_API_KEY')
            
            # Debug: Check if API key is loaded
            if fast2sms_key:
                print(f"✓ Fast2SMS API key loaded (length: {len(fast2sms_key)})")
            else:
                print("✗ Fast2SMS API key NOT found in environment")
            
            if fast2sms_key and fast2sms_key != 'your_fast2sms_api_key_here':
                print(f"📤 Attempting to send SMS via Fast2SMS to {phone}...")
                
                clean_phone = phone.replace('+91', '').replace('+', '').replace('-', '').replace(' ', '')
                
                url = "https://www.fast2sms.com/dev/bulkV2"
                params = {
                    "authorization": fast2sms_key,
                    "route": "otp",
                    "variables_values": otp,
                    "flash": "0",
                    "numbers": clean_phone
                }
                
                try:
                    response = requests.get(url, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('return'):
                            print(f"✅ SMS sent to {phone} via Fast2SMS")
                            print(f"   Response: {result}")
                            return True
                        else:
                            print(f"⚠️  Fast2SMS failed: {result}")
                    else:
                        print(f"⚠️  Fast2SMS HTTP error: {response.status_code} - {response.text}")
                except requests.Timeout:
                    print(f"⚠️  Fast2SMS timeout - API not responding")
                except requests.RequestException as e:
                    print(f"⚠️  Fast2SMS request failed: {e}")
            
            print(f"\n{'='*50}")
            print(f"📱 OTP for {phone}: {otp}")
            print(f"Valid for 5 minutes")
            print(f"{'='*50}\n")
            return True
                
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
            print(f"\n{'='*50}")
            print(f"📱 OTP for {phone}: {otp}")
            print(f"Valid for 5 minutes")
            print(f"{'='*50}\n")
            return True
    
    @staticmethod
    def create_otp(db: Session, phone: str, password: str) -> OTPVerification:
        """Create and send OTP for admin"""
        # Verify admin exists with this phone and password
        admin = db.query(Admin).filter(Admin.phone == phone).first()
        if not admin or not admin.is_active:
            raise ValueError("Invalid phone number")
        
        if not AuthService.verify_password(password, admin.password_hash):
            raise ValueError("Invalid password")
        
        # Check if recent OTP exists (resend cooldown)
        recent_otp = db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.is_verified == False,
            OTPVerification.created_at > datetime.utcnow() - timedelta(seconds=OTPService.RESEND_COOLDOWN_SECONDS)
        ).first()
        
        if recent_otp:
            seconds_left = int((recent_otp.created_at + timedelta(seconds=OTPService.RESEND_COOLDOWN_SECONDS) - datetime.utcnow()).total_seconds())
            if seconds_left > 0:
                raise ValueError(f"Please wait {seconds_left} seconds before requesting a new OTP")
        
        # Invalidate old OTPs
        db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.is_verified == False
        ).delete()
        db.commit()  # Commit deletion immediately
        
        # Generate new OTP
        otp_code = OTPService.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
        
        otp = OTPVerification(
            phone=phone,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        db.add(otp)
        db.commit()
        db.refresh(otp)
        
        # Always print OTP in logs (for debugging in production too)
        print(f"\n{'='*50}")
        print(f"🔐 ADMIN OTP for {phone}: {otp_code}")
        print(f"Valid for {OTPService.OTP_EXPIRY_MINUTES} minutes")
        print(f"{'='*50}\n")
        
        # Send SMS synchronously for debugging
        OTPService.send_sms(phone, otp_code)
        
        return otp
    
    @staticmethod
    def create_staff_otp(db: Session, uuid: str, phone: str):
        """Create and send OTP for staff login"""
        from ..models import Staff
        import re
        
        # Normalize input phone
        normalized_phone = phone
        
        # Verify staff exists with this UUID
        staff = db.query(Staff).filter(Staff.uuid == uuid).first()
        if not staff or not staff.is_active:
            raise ValueError("Invalid UUID")
        
        # Normalize staff phone from database
        if staff.phone:
            staff_phone = re.sub(r'[^\d+]', '', staff.phone)
            staff_phone = staff_phone.replace('+', '')
            if not staff_phone.startswith('91') and len(staff_phone) == 10:
                staff_phone = '91' + staff_phone
            staff_phone = '+' + staff_phone
        else:
            raise ValueError("Staff has no phone number")
        
        # Compare normalized phones
        if staff_phone != normalized_phone:
            raise ValueError("Phone number does not match")
        
        # Use normalized phone
        phone = normalized_phone
        
        # Check if recent OTP exists (resend cooldown)
        recent_otp = db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.is_verified == False,
            OTPVerification.created_at > datetime.utcnow() - timedelta(seconds=OTPService.RESEND_COOLDOWN_SECONDS)
        ).first()
        
        if recent_otp:
            seconds_left = int((recent_otp.created_at + timedelta(seconds=OTPService.RESEND_COOLDOWN_SECONDS) - datetime.utcnow()).total_seconds())
            if seconds_left > 0:
                raise ValueError(f"Please wait {seconds_left} seconds before requesting a new OTP")
        
        # Invalidate old OTPs
        db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.is_verified == False
        ).delete()
        db.commit()  # Commit deletion immediately
        
        # Generate new OTP
        otp_code = OTPService.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=OTPService.OTP_EXPIRY_MINUTES)
        
        otp = OTPVerification(
            phone=phone,
            otp_code=otp_code,
            expires_at=expires_at
        )
        
        db.add(otp)
        db.commit()
        db.refresh(otp)
        
        # Always print OTP in logs (for debugging in production too)
        print(f"\n{'='*50}")
        print(f"🔐 STAFF OTP for {phone}: {otp_code}")
        print(f"Valid for {OTPService.OTP_EXPIRY_MINUTES} minutes")
        print(f"{'='*50}\n")
        
        # Send SMS synchronously for debugging
        OTPService.send_sms(phone, otp_code)
        
        return otp
    
    @staticmethod
    def verify_staff_otp(db: Session, uuid: str, phone: str, otp_code: str):
        """Verify OTP and return staff"""
        from ..models import Staff
        import re
        
        otp = db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.otp_code == otp_code,
            OTPVerification.is_verified == False
        ).first()
        
        if not otp:
            raise ValueError("Invalid OTP code")
        
        if otp.is_expired():
            raise ValueError("OTP has expired")
        
        # Mark as verified
        otp.is_verified = True
        db.commit()
        
        # Get staff by UUID only (phone already verified via OTP)
        staff = db.query(Staff).filter(Staff.uuid == uuid).first()
        
        if not staff:
            raise ValueError("Staff not found")
        
        # Update last login
        staff.last_login = datetime.utcnow()
        db.commit()
        
        return staff
    
    @staticmethod
    def verify_otp(db: Session, phone: str, otp_code: str) -> Admin:
        """Verify OTP and return admin"""
        otp = db.query(OTPVerification).filter(
            OTPVerification.phone == phone,
            OTPVerification.otp_code == otp_code,
            OTPVerification.is_verified == False
        ).first()
        
        if not otp:
            raise ValueError("Invalid OTP code")
        
        if otp.is_expired():
            raise ValueError("OTP has expired")
        
        # Mark as verified
        otp.is_verified = True
        db.commit()
        
        # Get admin
        admin = db.query(Admin).filter(Admin.phone == phone).first()
        if not admin:
            raise ValueError("Admin not found")
        
        return admin
