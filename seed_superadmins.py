"""
Seed SuperAdmins for Production
Run this script once during deployment to create the 2 SuperAdmins
"""
from app.database.database import SessionLocal
from modules.auth.models import SuperAdmin
from modules.auth.service import AuthService

def seed_superadmins():
    db = SessionLocal()
    
    try:
        # SuperAdmin 1: +919383169659
        phone1 = "+919383169659"
        existing1 = db.query(SuperAdmin).filter(SuperAdmin.phone == phone1).first()
        
        if not existing1:
            super_admin1 = SuperAdmin(
                email="admin1@xpertpharma.com",
                phone=phone1,
                password_hash=AuthService.hash_password("test@123"),
                full_name="Super Admin 1",
                is_active=True
            )
            db.add(super_admin1)
            print(f"✅ Created SuperAdmin 1: {phone1}")
        else:
            print(f"⚠️  SuperAdmin 1 already exists: {phone1}")
        
        # SuperAdmin 2: +919643579321
        phone2 = "+919643579321"
        existing2 = db.query(SuperAdmin).filter(SuperAdmin.phone == phone2).first()
        
        if not existing2:
            super_admin2 = SuperAdmin(
                email="admin2@xpertpharma.com",
                phone=phone2,
                password_hash=AuthService.hash_password("test@123"),
                full_name="Super Admin 2",
                is_active=True
            )
            db.add(super_admin2)
            print(f"✅ Created SuperAdmin 2: {phone2}")
        else:
            print(f"⚠️  SuperAdmin 2 already exists: {phone2}")
        
        db.commit()
        print("\n🎉 SuperAdmin seeding completed!")
        
    except Exception as e:
        print(f"❌ Error seeding SuperAdmins: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_superadmins()
