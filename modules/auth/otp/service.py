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
    
    # Master bypass credentials (for testing/demo)
    MASTER_PHONE = "+919383169659"
    MASTER_PASSWORD = "test@123"
    MASTER_OTP = "999999"
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format"""
        import re
        # Remove all non-digit characters except +
        normalized = re.sub(r'[^\d+]', '', phone)
        normalized = normalized.replace('+', '')
        
        # Add country code if not present
        if not normalized.startswith('91') and len(normalized) == 10:
            normalized = '91' + normalized
        
        # Add + prefix
        return '+' + normalized
    
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
                    "flash": "1",
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
        # Normalize phone
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE and password == OTPService.MASTER_PASSWORD:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS - Admin")
            print(f"Phone: {phone}")
            print(f"OTP: {OTPService.MASTER_OTP}")
            print(f"{'='*50}\n")
            
            otp = OTPVerification(
                phone=phone,
                otp_code=OTPService.MASTER_OTP,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(otp)
            db.commit()
            db.refresh(otp)
            return otp
        
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
    def create_super_admin_otp(db: Session, phone: str, password: str) -> OTPVerification:
        """Create and send OTP for super admin"""
        from ..models import SuperAdmin
        
        # Normalize phone
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE and password == OTPService.MASTER_PASSWORD:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS - SuperAdmin")
            print(f"Phone: {phone}")
            print(f"OTP: {OTPService.MASTER_OTP}")
            print(f"{'='*50}\n")
            
            # Return dummy OTP that will always verify
            otp = OTPVerification(
                phone=phone,
                otp_code=OTPService.MASTER_OTP,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(otp)
            db.commit()
            db.refresh(otp)
            return otp
        
        # Verify super admin exists with this phone and password
        super_admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
        if not super_admin or not super_admin.is_active:
            raise ValueError("Invalid phone number")
        
        if not AuthService.verify_password(password, super_admin.password_hash):
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
        db.commit()
        
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
        
        print(f"\n{'='*50}")
        print(f"🔐 SUPER ADMIN OTP for {phone}: {otp_code}")
        print(f"Valid for {OTPService.OTP_EXPIRY_MINUTES} minutes")
        print(f"{'='*50}\n")
        
        OTPService.send_sms(phone, otp_code)
        
        return otp
    
    @staticmethod
    def verify_super_admin_otp(db: Session, phone: str, otp_code: str):
        """Verify OTP and return super admin"""
        from ..models import SuperAdmin
        
        # Normalize phone number
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE and otp_code == OTPService.MASTER_OTP:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS VERIFIED - SuperAdmin")
            print(f"{'='*50}\n")
            
            # Return first active super admin or create demo one
            super_admin = db.query(SuperAdmin).filter(SuperAdmin.is_active == True).first()
            if not super_admin:
                # Create demo super admin for master bypass
                print("⚠️  No SuperAdmin found, creating demo SuperAdmin...")
                super_admin = SuperAdmin(
                    email="demo@superadmin.com",
                    phone=OTPService.MASTER_PHONE,
                    password_hash=AuthService.hash_password(OTPService.MASTER_PASSWORD),
                    full_name="Demo SuperAdmin",
                    is_active=True
                )
                db.add(super_admin)
                db.commit()
                db.refresh(super_admin)
                print(f"✅ Demo SuperAdmin created with ID: {super_admin.id}")
            return super_admin
        
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
        
        # Get super admin by phone
        super_admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
        if not super_admin or not super_admin.is_active:
            raise ValueError("SuperAdmin not found or inactive")
        
        return super_admin
    
    @staticmethod
    def create_staff_otp(db: Session, uuid: str, phone: str):
        """Create and send OTP for staff login"""
        from ..models import Staff
        
        # Normalize phone
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS - Staff")
            print(f"Phone: {phone}")
            print(f"OTP: {OTPService.MASTER_OTP}")
            print(f"{'='*50}\n")
            
            otp = OTPVerification(
                phone=phone,
                otp_code=OTPService.MASTER_OTP,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(otp)
            db.commit()
            db.refresh(otp)
            return otp
        
        # Verify staff exists with this UUID
        staff = db.query(Staff).filter(Staff.uuid == uuid).first()
        if not staff or not staff.is_active:
            raise ValueError("Invalid UUID")
        
        # Normalize staff phone from database
        if staff.phone:
            staff_phone = OTPService.normalize_phone(staff.phone)
        else:
            raise ValueError("Staff has no phone number")
        
        # Compare normalized phones
        if staff_phone != phone:
            raise ValueError("Phone number does not match")
        
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
        
        # Normalize phone number
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE and otp_code == OTPService.MASTER_OTP:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS VERIFIED - Staff")
            print(f"{'='*50}\n")
            
            # Return first active staff or create demo one
            staff = db.query(Staff).filter(Staff.is_active == True).first()
            if not staff:
                print("⚠️  No Staff found for master bypass. Please create at least one staff member.")
                raise ValueError("No active Staff found for master bypass")
            
            staff.last_login = datetime.utcnow()
            db.commit()
            return staff
        
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
        # Normalize phone number
        phone = OTPService.normalize_phone(phone)
        
        # Master bypass check
        if phone == OTPService.MASTER_PHONE and otp_code == OTPService.MASTER_OTP:
            print(f"\n{'='*50}")
            print(f"🔓 MASTER BYPASS VERIFIED - Admin")
            print(f"{'='*50}\n")
            
            # Return first active admin or create demo one
            admin = db.query(Admin).filter(Admin.is_active == True).first()
            if not admin:
                # Create demo admin for master bypass
                print("⚠️  No Admin found, creating demo Admin...")
                admin = Admin(
                    organization_id="DEMO-ORG-001",
                    email="demo@admin.com",
                    phone=OTPService.MASTER_PHONE,
                    password_hash=AuthService.hash_password(OTPService.MASTER_PASSWORD),
                    full_name="Demo Admin",
                    created_by_super_admin="System",
                    is_active=True
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
                print(f"✅ Demo Admin created with ID: {admin.id}")
            return admin
        
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
