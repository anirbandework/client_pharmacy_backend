import sqlite3
from passlib.context import CryptContext

DATABASE = "pharmacy.db"
PHONE = "+919383169659"
PASSWORD = "test@123"
FULL_NAME = "Test Admin"
EMAIL = "test@example.com"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)

def setup_admin():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        # Check if admin exists
        cursor.execute("SELECT id, full_name, phone, email, is_active FROM admins WHERE phone = ?", (PHONE,))
        admin = cursor.fetchone()
        
        if admin:
            print(f"✅ Admin already exists!")
            print(f"📋 ID: {admin[0]}")
            print(f"📋 Name: {admin[1]}")
            print(f"📞 Phone: {admin[2]}")
            print(f"📧 Email: {admin[3]}")
            print(f"🟢 Active: {admin[4]}")
            
            # Update password
            hashed = pwd_context.hash(PASSWORD)
            cursor.execute("UPDATE admins SET password_hash = ? WHERE phone = ?", (hashed, PHONE))
            conn.commit()
            print(f"🔄 Password updated to: {PASSWORD}")
        else:
            print(f"Creating new admin...")
            hashed = pwd_context.hash(PASSWORD)
            cursor.execute(
                "INSERT INTO admins (phone, password_hash, full_name, email, is_active, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
                (PHONE, hashed, FULL_NAME, EMAIL, 1)
            )
            conn.commit()
            print(f"✅ Admin created successfully!")
            print(f"📋 Name: {FULL_NAME}")
            print(f"📞 Phone: {PHONE}")
            print(f"📧 Email: {EMAIL}")
        
        print(f"\n{'='*60}")
        print(f"✅ Ready to test OTP authentication!")
        print(f"Run: source venv/bin/activate && python test_my_otp.py")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    setup_admin()
