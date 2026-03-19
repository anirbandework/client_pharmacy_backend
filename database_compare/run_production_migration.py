"""Apply migration to production database"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

PROD_DB = os.getenv('PRODUCTION_DATABASE_URL')

def run_migration():
    print("🔄 Connecting to PRODUCTION database...")
    engine = create_engine(PROD_DB, connect_args={'connect_timeout': 10})
    
    migrations = [
        # Admins table
        "ALTER TABLE admins ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255)",
        "ALTER TABLE admins ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP",

        # Distributors table
        "ALTER TABLE distributors ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255)",
        "ALTER TABLE distributors ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP",

        # Staff table
        "ALTER TABLE staff ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255)",
        "ALTER TABLE staff ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP",

        # Super_admins table
        "ALTER TABLE super_admins ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255)",
        "ALTER TABLE super_admins ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP",

        # bill_items: track actual strips deducted (differs from quantity when sold by tablet)
        "ALTER TABLE bill_items ADD COLUMN IF NOT EXISTS strips_deducted INTEGER",
        "UPDATE bill_items SET strips_deducted = quantity WHERE strips_deducted IS NULL",

        # purchase_invoices: enforce unique invoice number per shop (prevents race-condition duplicates)
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_invoices_shop_number ON purchase_invoices (shop_id, invoice_number)",

        # bills: pay later support
        "ALTER TABLE bills ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'paid'",
        "ALTER TABLE bills ADD COLUMN IF NOT EXISTS amount_due FLOAT DEFAULT 0.0",
        "UPDATE bills SET payment_status = 'paid', amount_due = 0.0 WHERE payment_status IS NULL",

        # attendance_settings: make geofence optional
        "ALTER TABLE attendance_settings ADD COLUMN IF NOT EXISTS geofence_required BOOLEAN DEFAULT TRUE",
        "UPDATE attendance_settings SET geofence_required = TRUE WHERE geofence_required IS NULL",
    ]
    
    try:
        with engine.connect() as conn:
            print("✅ Connected to PRODUCTION database\n")
            
            for i, migration in enumerate(migrations, 1):
                print(f"Running migration {i}/{len(migrations)}...")
                print(f"  SQL: {migration}")
                conn.execute(text(migration))
                conn.commit()
                print("  ✅ Success\n")
            
            print("=" * 80)
            print("🎉 All migrations completed successfully!")
            print("=" * 80)
            
            # Verify the changes
            print("\n📋 Verifying changes...\n")
            verify_query = text("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('admins', 'distributors', 'staff', 'super_admins')
                  AND column_name IN ('reset_token', 'reset_token_expires')
                ORDER BY table_name, column_name
            """)
            
            result = conn.execute(verify_query)
            rows = result.fetchall()
            
            if rows:
                print("✅ Columns added successfully:\n")
                current_table = None
                for row in rows:
                    if current_table != row[0]:
                        current_table = row[0]
                        print(f"\n{current_table}:")
                    print(f"  - {row[1]}: {row[2]}")
            else:
                print("⚠️  No columns found (this shouldn't happen)")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 80)
    print("PRODUCTION DATABASE MIGRATION")
    print("=" * 80)
    print("\nThis will add reset_token columns to:")
    print("  - admins")
    print("  - distributors")
    print("  - staff")
    print("  - super_admins")
    print("\n" + "=" * 80)
    
    response = input("\n⚠️  Proceed with PRODUCTION migration? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        try:
            run_migration()
            print("\n✅ Migration completed! Run check_schema_diff.py to verify.")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n❌ Migration cancelled")
