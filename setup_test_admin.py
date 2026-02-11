from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.auth.models import Admin
from modules.auth.service import AuthService
from app.database.database import Base

DATABASE_URL = "sqlite:///./pharmacy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

PHONE = "+919383169659"
PASSWORD = "test@123"
FULL_NAME = "Test Admin"
EMAIL = "test@example.com"

def setup_test_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.phone == PHONE).first()
        
        if admin:
            print(f"✅ Admin already exists!")
            print(f"📋 Name: {admin.full_name}")
            print(f"📞 Phone: {admin.phone}")
            print(f"📧 Email: {admin.email}")
            print(f"🟢 Active: {admin.is_active}")
            
            # Update password if needed
            admin.password_hash = AuthService.hash_password(PASSWORD)
            db.commit()
            print(f"🔄 Password updated to: {PASSWORD}")
        else:
            print(f"Creating new admin...")
            hashed_password = AuthService.hash_password(PASSWORD)
            admin = Admin(
                phone=PHONE,
                password_hash=hashed_password,
                full_name=FULL_NAME,
                email=EMAIL,
                is_active=True
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"✅ Admin created successfully!")
            print(f"📋 Name: {admin.full_name}")
            print(f"📞 Phone: {admin.phone}")
            print(f"📧 Email: {admin.email}")
        
        print(f"\n{'='*60}")
        print(f"Ready to test OTP authentication!")
        print(f"Run: python test_my_otp.py")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_admin()
