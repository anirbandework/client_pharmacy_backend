"""
SuperAdmin Management Script
Usage:
  python manage_superadmins.py list
  python manage_superadmins.py add +91XXXXXXXXXX "password" "Full Name"
  python manage_superadmins.py deactivate +91XXXXXXXXXX
  python manage_superadmins.py activate +91XXXXXXXXXX
  python manage_superadmins.py delete +91XXXXXXXXXX
  python manage_superadmins.py reset-password +91XXXXXXXXXX "new_password"
"""
import sys
from app.database.database import SessionLocal

# Import all models to avoid relationship errors
from modules.auth.models import SuperAdmin, Admin, Shop, Staff
from modules.auth.salary_management.models import SalaryRecord, StaffPaymentInfo, SalaryAlert
from modules.auth.attendance.models import ShopWiFi, StaffDevice, AttendanceRecord, AttendanceSettings, LeaveRequest

from modules.auth.service import AuthService

def list_superadmins():
    db = SessionLocal()
    admins = db.query(SuperAdmin).all()
    
    print("\n📋 SuperAdmins List:")
    print("-" * 80)
    for admin in admins:
        status = "✅ Active" if admin.is_active else "❌ Inactive"
        print(f"{status} | {admin.phone} | {admin.full_name} | {admin.email}")
    print("-" * 80)
    print(f"Total: {len(admins)} SuperAdmins\n")
    db.close()

def add_superadmin(phone, password, full_name):
    db = SessionLocal()
    
    existing = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
    if existing:
        print(f"❌ SuperAdmin with phone {phone} already exists!")
        db.close()
        return
    
    email = f"admin{phone[-4:]}@xpertpharma.com"
    super_admin = SuperAdmin(
        email=email,
        phone=phone,
        password_hash=AuthService.hash_password(password),
        full_name=full_name,
        is_active=True
    )
    
    db.add(super_admin)
    db.commit()
    print(f"✅ Created SuperAdmin: {phone} ({full_name})")
    print(f"📧 Email: {email}")
    print(f"🔑 Password: {password}")
    print("\n⚠️  IMPORTANT: Update frontend auto-detection in src/features/Welcome/index.jsx")
    print(f"   Add: normalizedPhone.endsWith('{phone.replace('+91', '')}')")
    db.close()

def deactivate_superadmin(phone):
    db = SessionLocal()
    admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
    
    if not admin:
        print(f"❌ SuperAdmin with phone {phone} not found!")
        db.close()
        return
    
    admin.is_active = False
    db.commit()
    print(f"✅ Deactivated SuperAdmin: {phone}")
    db.close()

def activate_superadmin(phone):
    db = SessionLocal()
    admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
    
    if not admin:
        print(f"❌ SuperAdmin with phone {phone} not found!")
        db.close()
        return
    
    admin.is_active = True
    db.commit()
    print(f"✅ Activated SuperAdmin: {phone}")
    db.close()

def delete_superadmin(phone):
    db = SessionLocal()
    admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
    
    if not admin:
        print(f"❌ SuperAdmin with phone {phone} not found!")
        db.close()
        return
    
    confirm = input(f"⚠️  Are you sure you want to DELETE {phone}? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Deletion cancelled")
        db.close()
        return
    
    db.delete(admin)
    db.commit()
    print(f"✅ Deleted SuperAdmin: {phone}")
    print("\n⚠️  IMPORTANT: Update frontend auto-detection in src/features/Welcome/index.jsx")
    print(f"   Remove: normalizedPhone.endsWith('{phone.replace('+91', '')}')")
    db.close()

def reset_password(phone, new_password):
    db = SessionLocal()
    admin = db.query(SuperAdmin).filter(SuperAdmin.phone == phone).first()
    
    if not admin:
        print(f"❌ SuperAdmin with phone {phone} not found!")
        db.close()
        return
    
    admin.password_hash = AuthService.hash_password(new_password)
    db.commit()
    print(f"✅ Password reset for SuperAdmin: {phone}")
    print(f"🔑 New Password: {new_password}")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_superadmins()
    
    elif command == "add":
        if len(sys.argv) != 5:
            print("Usage: python manage_superadmins.py add +91XXXXXXXXXX 'password' 'Full Name'")
            sys.exit(1)
        add_superadmin(sys.argv[2], sys.argv[3], sys.argv[4])
    
    elif command == "deactivate":
        if len(sys.argv) != 3:
            print("Usage: python manage_superadmins.py deactivate +91XXXXXXXXXX")
            sys.exit(1)
        deactivate_superadmin(sys.argv[2])
    
    elif command == "activate":
        if len(sys.argv) != 3:
            print("Usage: python manage_superadmins.py activate +91XXXXXXXXXX")
            sys.exit(1)
        activate_superadmin(sys.argv[2])
    
    elif command == "delete":
        if len(sys.argv) != 3:
            print("Usage: python manage_superadmins.py delete +91XXXXXXXXXX")
            sys.exit(1)
        delete_superadmin(sys.argv[2])
    
    elif command == "reset-password":
        if len(sys.argv) != 4:
            print("Usage: python manage_superadmins.py reset-password +91XXXXXXXXXX 'new_password'")
            sys.exit(1)
        reset_password(sys.argv[2], sys.argv[3])
    
    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
