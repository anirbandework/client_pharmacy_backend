"""Remove plain_password columns from database"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

LOCAL_DATABASE_URL = os.getenv('DATABASE_URL')
PROD_DATABASE_URL = os.getenv('PRODUCTION_DATABASE_URL')

def remove_plain_password(database_url, db_name):
    if not database_url:
        print(f"❌ {db_name} database URL not found")
        return
    
    print(f"\n{'='*60}")
    print(f"🔒 Removing plain_password columns from {db_name}")
    print(f"{'='*60}\n")
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Drop plain_password from admins
        try:
            conn.execute(text("ALTER TABLE admins DROP COLUMN IF EXISTS plain_password"))
            conn.commit()
            print(f"✅ Removed plain_password from admins table")
        except Exception as e:
            print(f"⚠️  Error removing plain_password from admins: {e}")
        
        # Drop plain_password from staff
        try:
            conn.execute(text("ALTER TABLE staff DROP COLUMN IF EXISTS plain_password"))
            conn.commit()
            print(f"✅ Removed plain_password from staff table")
        except Exception as e:
            print(f"⚠️  Error removing plain_password from staff: {e}")
    
    engine.dispose()
    print(f"\n✅ {db_name} migration completed\n")

if __name__ == "__main__":
    print("\n🔐 SECURITY MIGRATION: Removing plain password storage\n")
    
    # Local database
    if LOCAL_DATABASE_URL:
        remove_plain_password(LOCAL_DATABASE_URL, "LOCAL")
    
    # Production database
    if PROD_DATABASE_URL:
        confirm = input("⚠️  Apply to PRODUCTION database? Type 'yes' to continue: ")
        if confirm.lower() == 'yes':
            remove_plain_password(PROD_DATABASE_URL, "PRODUCTION")
        else:
            print("❌ Production migration cancelled")
    
    print("\n✅ Security migration completed!")
    print("📝 Plain passwords removed from database")
    print("🔒 System is now more secure\n")
