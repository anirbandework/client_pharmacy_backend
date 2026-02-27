"""Update SuperAdmin in PRODUCTION database"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

PROD_DATABASE_URL = os.getenv('PRODUCTION_DATABASE_URL')

def update_production_superadmin():
    if not PROD_DATABASE_URL:
        print("❌ PRODUCTION_DATABASE_URL not found in .env")
        return
    
    print("⚠️  WARNING: This will update PRODUCTION database!")
    confirm = input("Type 'yes' to continue: ")
    
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    engine = create_engine(PROD_DATABASE_URL)
    
    with engine.connect() as conn:
        # Show current SuperAdmins
        result = conn.execute(text("SELECT id, phone, full_name, email, is_active FROM super_admins"))
        print("\n🌐 PRODUCTION - Current SuperAdmins:")
        for row in result:
            status = "✅" if row.is_active else "❌"
            print(f"{status} ID:{row.id} | {row.phone} | {row.full_name} | {row.email}")
        
        # Update the name and email for phone +919383169659
        conn.execute(
            text("UPDATE super_admins SET full_name = :name, email = :email WHERE phone = :phone"),
            {"name": "Anirban De", "email": "anirban.de5468@gmail.com", "phone": "+919383169659"}
        )
        conn.commit()
        
        print("\n✅ Updated PRODUCTION SuperAdmin name to 'Anirban De' and email to 'anirban.de5468@gmail.com'")
        
        # Show updated SuperAdmins
        result = conn.execute(text("SELECT id, phone, full_name, email, is_active FROM super_admins"))
        print("\n🌐 PRODUCTION - Updated SuperAdmins:")
        for row in result:
            status = "✅" if row.is_active else "❌"
            print(f"{status} ID:{row.id} | {row.phone} | {row.full_name} | {row.email}")
    
    engine.dispose()

if __name__ == "__main__":
    update_production_superadmin()
