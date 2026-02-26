"""
Add shop_id columns to attendance tables for shop-level data isolation
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    database_url = settings.database_url
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url)
    
    migrations = [
        # Add shop_id to staff_devices
        "ALTER TABLE staff_devices ADD COLUMN IF NOT EXISTS shop_id INTEGER REFERENCES shops(id)",
        "CREATE INDEX IF NOT EXISTS idx_staff_devices_shop_id ON staff_devices(shop_id)",
        
        # Update existing staff_devices with shop_id from staff table
        """UPDATE staff_devices 
           SET shop_id = staff.shop_id 
           FROM staff 
           WHERE staff_devices.staff_id = staff.id 
           AND staff_devices.shop_id IS NULL""",
        
        # Add shop_id to leave_requests
        "ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS shop_id INTEGER REFERENCES shops(id)",
        "CREATE INDEX IF NOT EXISTS idx_leave_requests_shop_id ON leave_requests(shop_id)",
        
        # Update existing leave_requests with shop_id from staff table
        """UPDATE leave_requests 
           SET shop_id = staff.shop_id 
           FROM staff 
           WHERE leave_requests.staff_id = staff.id 
           AND leave_requests.shop_id IS NULL""",
        
        # Add indexes to existing shop_id columns
        "CREATE INDEX IF NOT EXISTS idx_shop_wifi_shop_id ON shop_wifi(shop_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_records_shop_id ON attendance_records(shop_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_records_staff_id ON attendance_records(staff_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_settings_shop_id ON attendance_settings(shop_id)",
        "CREATE INDEX IF NOT EXISTS idx_staff_devices_staff_id ON staff_devices(staff_id)",
        "CREATE INDEX IF NOT EXISTS idx_leave_requests_staff_id ON leave_requests(staff_id)",
    ]
    
    print("\n🔄 Running attendance module data privacy migration...\n")
    
    with engine.connect() as conn:
        for i, cmd in enumerate(migrations, 1):
            try:
                print(f"[{i}/{len(migrations)}] {cmd[:70]}...")
                conn.execute(text(cmd))
                conn.commit()
                print("✅ Success")
            except Exception as e:
                print(f"⚠️  {e}")
    
    print("\n✅ Migration completed!")
    print("📝 Attendance module now has shop-level data isolation")

if __name__ == "__main__":
    migrate()
