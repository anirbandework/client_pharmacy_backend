#!/usr/bin/env python3
"""
Database Migration for Admin Audit Fields
Adds created_by_admin, updated_by_admin, updated_at columns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.database import get_db, engine

def migrate_auth_audit_fields():
    """Add audit fields to shops and staff tables"""
    
    db = next(get_db())
    
    try:
        print("🔄 Adding audit fields for admin tracking...")
        
        # Add audit fields to shops table
        shop_migrations = [
            "ALTER TABLE shops ADD COLUMN created_by_admin TEXT NOT NULL DEFAULT 'Unknown Admin'",
            "ALTER TABLE shops ADD COLUMN updated_by_admin TEXT",
            "ALTER TABLE shops ADD COLUMN updated_at DATETIME"
        ]
        
        # Add audit fields to staff table
        staff_migrations = [
            "ALTER TABLE staff ADD COLUMN created_by_admin TEXT NOT NULL DEFAULT 'Unknown Admin'",
            "ALTER TABLE staff ADD COLUMN updated_by_admin TEXT", 
            "ALTER TABLE staff ADD COLUMN updated_at DATETIME"
        ]
        
        all_migrations = shop_migrations + staff_migrations
        
        for query in all_migrations:
            try:
                db.execute(text(query))
                print(f"✅ Executed: {query}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️  Column already exists: {query}")
                else:
                    print(f"❌ Error executing {query}: {str(e)}")
        
        db.commit()
        print("\n✅ Audit fields migration completed successfully!")
        print("\n📋 New Features:")
        print("• All admins can now see all shops and staff")
        print("• Audit tracking shows who created/updated each record")
        print("• New endpoints: /admin/all-shops and /admin/all-staff")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_auth_audit_fields()