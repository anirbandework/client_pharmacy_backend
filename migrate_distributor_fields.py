import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env file")
    exit(1)

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

try:
    print("Adding new fields to distributor_invoices table...")
    
    # Add due_date and custom_fields to distributor_invoices
    cur.execute("ALTER TABLE distributor_invoices ADD COLUMN IF NOT EXISTS due_date DATE;")
    cur.execute("ALTER TABLE distributor_invoices ADD COLUMN IF NOT EXISTS custom_fields JSON;")
    
    print("Adding new fields to distributor_invoice_items table...")
    
    # Add discount and custom fields to distributor_invoice_items
    cur.execute("ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS discount_on_purchase REAL DEFAULT 0.0;")
    cur.execute("ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS discount_on_sales REAL DEFAULT 0.0;")
    cur.execute("ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS before_discount REAL DEFAULT 0.0;")
    cur.execute("ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS custom_fields JSON;")
    
    conn.commit()
    print("✓ Migration completed successfully!")
    
except Exception as e:
    conn.rollback()
    print(f"✗ Migration failed: {e}")
    
finally:
    cur.close()
    conn.close()
