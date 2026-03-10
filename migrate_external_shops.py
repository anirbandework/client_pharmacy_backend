"""Migration: Add external shop support to distributor invoices"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return
    
    engine = create_engine(database_url)
    
    try:
        with engine.connect() as conn:
            print("🔄 Starting migration...")
            
            # Make shop_id nullable
            print("  - Making shop_id nullable...")
            conn.execute(text("""
                ALTER TABLE distributor_invoices 
                ALTER COLUMN shop_id DROP NOT NULL;
            """))
            
            # Add external shop fields
            print("  - Adding external shop fields...")
            conn.execute(text("""
                ALTER TABLE distributor_invoices 
                ADD COLUMN IF NOT EXISTS external_shop_name VARCHAR,
                ADD COLUMN IF NOT EXISTS external_shop_phone VARCHAR,
                ADD COLUMN IF NOT EXISTS external_shop_address TEXT,
                ADD COLUMN IF NOT EXISTS external_shop_license VARCHAR,
                ADD COLUMN IF NOT EXISTS external_shop_gst VARCHAR;
            """))
            
            conn.commit()
            print("✅ Migration completed successfully")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    migrate()
