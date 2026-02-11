import sqlite3
from datetime import date

DATABASE = "pharmacy.db"
PHONE = "+919383169659"

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

# Get first shop
cursor.execute("SELECT id, shop_name FROM shops LIMIT 1")
shop = cursor.fetchone()

if not shop:
    print("❌ No shop found. Creating test shop first...")
    cursor.execute("""
        INSERT INTO shops (admin_id, shop_name, shop_code, created_by_admin, is_active, created_at)
        VALUES (7, 'Test Pharmacy', 'TEST001', 'Anirban De', 1, datetime('now'))
    """)
    conn.commit()
    shop_id = cursor.lastrowid
    shop_name = 'Test Pharmacy'
else:
    shop_id, shop_name = shop

# Check if staff exists
cursor.execute("SELECT uuid, name, phone FROM staff WHERE phone = ?", (PHONE,))
staff = cursor.fetchone()

if staff:
    uuid, name, phone = staff
    print(f"✅ Staff already exists!")
    print(f"📋 Name: {name}")
    print(f"📞 Phone: {phone}")
    print(f"🆔 UUID: {uuid}")
    print(f"🏪 Shop: {shop_name} (ID: {shop_id})")
else:
    print(f"Creating test staff...")
    import uuid as uuid_lib
    staff_uuid = str(uuid_lib.uuid4())
    
    cursor.execute("""
        INSERT INTO staff (
            shop_id, uuid, name, staff_code, phone, role,
            monthly_salary, joining_date, created_by_admin, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        shop_id, staff_uuid, 'Test Staff', 'STAFF001', PHONE, 'staff',
        25000.0, date.today().isoformat(), 'Anirban De', 1
    ))
    conn.commit()
    
    print(f"✅ Staff created successfully!")
    print(f"📋 Name: Test Staff")
    print(f"📞 Phone: {PHONE}")
    print(f"🆔 UUID: {staff_uuid}")
    print(f"🏪 Shop: {shop_name} (ID: {shop_id})")
    uuid = staff_uuid

print(f"\n{'='*60}")
print(f"Ready to test Staff OTP authentication!")
print(f"UUID: {uuid}")
print(f"Phone: {PHONE}")
print(f"{'='*60}")

conn.close()
