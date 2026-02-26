"""
Fix bill_items.mrp column type in Railway (FLOAT -> VARCHAR)
"""
from sqlalchemy import create_engine, text

railway_url = input("Enter Railway PostgreSQL URL: ").strip()

if railway_url.startswith("postgres://"):
    railway_url = railway_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(railway_url)

print("\n🔄 Fixing bill_items.mrp column type...\n")

with engine.connect() as conn:
    print("[1/1] Changing mrp from FLOAT to VARCHAR...")
    conn.execute(text("ALTER TABLE bill_items ALTER COLUMN mrp TYPE VARCHAR USING mrp::text"))
    conn.commit()
    print("✅ Success")

print("\n✅ Done! Railway bill_items.mrp is now VARCHAR")
