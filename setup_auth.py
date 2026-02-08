"""
Quick Setup Script for Authentication System

Creates initial admin and first shop
"""

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from modules.auth.service import AuthService
from modules.auth import schemas

def setup_initial_data():
    db = SessionLocal()
    
    try:
        print("🚀 Pharmacy Management System - Initial Setup\n")
        
        # Check if admin already exists
        from modules.auth.models import Admin
        existing_admin = db.query(Admin).first()
        
        if existing_admin:
            print("⚠️  Admin already exists. Skipping setup.")
            print(f"   Email: {existing_admin.email}")
            return
        
        # Create admin
        print("📝 Creating Admin Account...")
        admin_data = schemas.AdminCreate(
            email="admin@pharmacy.com",
            password="admin123",
            full_name="Admin User",
            phone="+1234567890"
        )
        
        admin = AuthService.create_admin(db, admin_data)
        print(f"✓ Admin created: {admin.email}")
        print(f"  Password: admin123 (CHANGE THIS IN PRODUCTION!)\n")
        
        # Create first shop
        print("🏪 Creating First Shop...")
        shop_data = schemas.ShopCreate(
            shop_name="Main Pharmacy",
            shop_code="MAIN001",
            address="123 Main Street",
            phone="+1234567890",
            email="main@pharmacy.com"
        )
        
        shop = AuthService.create_shop(db, admin.id, shop_data)
        print(f"✓ Shop created: {shop.shop_name}")
        print(f"  Shop Code: {shop.shop_code}\n")
        
        # Create shop manager
        print("👤 Creating Shop Manager...")
        manager_data = schemas.StaffCreate(
            full_name="Shop Manager",
            phone="+1234567890",
            email="manager@pharmacy.com",
            role="shop_manager",
            can_manage_staff=True,
            can_view_analytics=True,
            can_manage_inventory=True,
            can_manage_customers=True
        )
        
        manager = AuthService.create_staff(db, shop.id, manager_data)
        print(f"✓ Shop Manager created: {manager.full_name}")
        print(f"  UUID: {manager.uuid}")
        print(f"  (Save this UUID for login!)\n")
        
        # Create regular staff
        print("👤 Creating Regular Staff...")
        staff_data = schemas.StaffCreate(
            full_name="Staff Member",
            phone="+1234567890",
            email="staff@pharmacy.com",
            role="staff",
            can_manage_staff=False,
            can_view_analytics=True,
            can_manage_inventory=True,
            can_manage_customers=True
        )
        
        staff = AuthService.create_staff(db, shop.id, staff_data)
        print(f"✓ Staff created: {staff.full_name}")
        print(f"  UUID: {staff.uuid}")
        print(f"  (Save this UUID for login!)\n")
        
        print("=" * 60)
        print("✅ Setup Complete!\n")
        print("Login Credentials:")
        print("-" * 60)
        print(f"Admin Login:")
        print(f"  Email: {admin.email}")
        print(f"  Password: admin123")
        print(f"\nShop Manager Login:")
        print(f"  UUID: {manager.uuid}")
        print(f"\nRegular Staff Login:")
        print(f"  UUID: {staff.uuid}")
        print("=" * 60)
        print("\n⚠️  IMPORTANT: Change admin password in production!")
        print("📚 See modules/auth/README.md for full documentation\n")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_initial_data()
