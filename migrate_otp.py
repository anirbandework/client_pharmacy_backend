#!/usr/bin/env python3
"""
Migration script for OTP authentication
- Updates Admin table (phone required, email optional)
- Creates OTP verification table
"""

import sqlite3
import sys

def migrate_database():
    try:
        conn = sqlite3.connect('pharmacy.db')
        cursor = conn.cursor()
        
        print("🔄 Starting migration...")
        
        # Step 1: Create OTP table
        print("\n1. Creating otp_verifications table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone VARCHAR(15) NOT NULL,
                otp_code VARCHAR(6) NOT NULL,
                is_verified BOOLEAN DEFAULT 0,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_otp_phone ON otp_verifications(phone)")
        print("   ✅ OTP table created")
        
        # Step 2: Check if admins table needs migration
        print("\n2. Checking admins table...")
        cursor.execute("PRAGMA table_info(admins)")
        columns = {col[1]: col for col in cursor.fetchall()}
        
        # Step 3: Update existing admins with phone if NULL
        print("\n3. Updating existing admin records...")
        cursor.execute("SELECT id, email, phone FROM admins WHERE phone IS NULL OR phone = ''")
        admins_to_update = cursor.fetchall()
        
        if admins_to_update:
            print(f"   Found {len(admins_to_update)} admins without phone numbers")
            for admin_id, email, phone in admins_to_update:
                # Generate phone from email or use default
                default_phone = f"+91{9000000000 + admin_id}"
                cursor.execute("UPDATE admins SET phone = ? WHERE id = ?", (default_phone, admin_id))
                print(f"   ✅ Updated admin {admin_id}: phone = {default_phone}")
        else:
            print("   ✅ All admins have phone numbers")
        
        # Step 4: Make email nullable if not already
        print("\n4. Checking email column...")
        if 'email' in columns and columns['email'][3] == 1:  # NOT NULL
            print("   Email column is NOT NULL, recreating table...")
            
            # Create new table with correct schema
            cursor.execute("""
                CREATE TABLE admins_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR UNIQUE,
                    password_hash VARCHAR NOT NULL,
                    full_name VARCHAR NOT NULL,
                    phone VARCHAR(15) UNIQUE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Copy data
            cursor.execute("""
                INSERT INTO admins_new (id, email, password_hash, full_name, phone, is_active, created_at)
                SELECT id, email, password_hash, full_name, phone, is_active, created_at FROM admins
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE admins")
            cursor.execute("ALTER TABLE admins_new RENAME TO admins")
            
            # Recreate indexes
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_email ON admins(email)")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_admin_phone ON admins(phone)")
            
            print("   ✅ Table recreated with nullable email")
        else:
            print("   ✅ Email column is already nullable")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\n📋 Summary:")
        print("   - OTP verification table created")
        print("   - Admin phone numbers updated")
        print("   - Email made optional")
        print("\n🚀 You can now use OTP authentication!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
