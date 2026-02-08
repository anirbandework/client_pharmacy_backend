"""Reset admin password"""

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from modules.auth.service import AuthService
from modules.auth.models import Admin

db = SessionLocal()

try:
    admin = db.query(Admin).filter(Admin.email == "admin@pharmacy.com").first()
    
    if admin:
        # Reset password to admin123
        admin.password_hash = AuthService.hash_password("admin123")
        db.commit()
        print("✅ Password reset successfully!")
        print(f"Email: {admin.email}")
        print(f"Password: admin123")
    else:
        print("❌ Admin not found")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    db.close()
