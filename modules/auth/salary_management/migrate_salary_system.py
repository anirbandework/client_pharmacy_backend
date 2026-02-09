#!/usr/bin/env python3
"""
Database migration script for Salary Management System
Adds salary-related tables and updates staff table
"""

import sqlite3
import sys
import os
from datetime import datetime

def run_migration():
    """Run the salary management migration"""
    
    # Database path
    db_path = "pharmacy.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting salary management migration...")
        
        # 1. Add salary fields to staff table
        print("1. Adding salary fields to staff table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(staff)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'monthly_salary' not in columns:
            cursor.execute("ALTER TABLE staff ADD COLUMN monthly_salary REAL")
            print("   - Added monthly_salary column")
        
        if 'name' not in columns and 'full_name' in columns:
            # Rename full_name to name
            cursor.execute("""
                CREATE TABLE staff_new (
                    id INTEGER PRIMARY KEY,
                    shop_id INTEGER NOT NULL,
                    uuid TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    staff_code TEXT UNIQUE,
                    phone TEXT,
                    email TEXT,
                    role TEXT DEFAULT 'staff',
                    monthly_salary REAL,
                    can_manage_staff BOOLEAN DEFAULT 0,
                    can_view_analytics BOOLEAN DEFAULT 1,
                    can_manage_inventory BOOLEAN DEFAULT 1,
                    can_manage_customers BOOLEAN DEFAULT 1,
                    created_by_admin TEXT NOT NULL,
                    updated_by_admin TEXT,
                    updated_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME,
                    FOREIGN KEY (shop_id) REFERENCES shops (id)
                )
            """)
            
            # Copy data from old table
            cursor.execute("""
                INSERT INTO staff_new (
                    id, shop_id, uuid, name, phone, email, role, 
                    can_manage_staff, can_view_analytics, can_manage_inventory, 
                    can_manage_customers, created_by_admin, updated_by_admin, 
                    updated_at, is_active, created_at, last_login
                )
                SELECT 
                    id, shop_id, uuid, full_name, phone, email, role,
                    can_manage_staff, can_view_analytics, can_manage_inventory,
                    can_manage_customers, created_by_admin, updated_by_admin,
                    updated_at, is_active, created_at, last_login
                FROM staff
            """)
            
            # Generate staff codes for existing staff
            cursor.execute("SELECT id, name FROM staff_new WHERE staff_code IS NULL")
            staff_without_codes = cursor.fetchall()
            
            for staff_id, name in staff_without_codes:
                # Generate staff code from name
                staff_code = name.upper().replace(' ', '')[:6] + str(staff_id).zfill(3)
                cursor.execute("UPDATE staff_new SET staff_code = ? WHERE id = ?", (staff_code, staff_id))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE staff")
            cursor.execute("ALTER TABLE staff_new RENAME TO staff")
            
            print("   - Renamed full_name to name and added staff_code")
        
        # 2. Create salary_records table
        print("2. Creating salary_records table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salary_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                salary_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                payment_date DATETIME,
                paid_by_admin TEXT,
                due_date DATE NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff (id),
                UNIQUE(staff_id, month, year)
            )
        """)
        print("   - Created salary_records table")
        
        # 3. Create staff_payment_info table
        print("3. Creating staff_payment_info table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff_payment_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER UNIQUE NOT NULL,
                upi_id TEXT,
                qr_code_path TEXT,
                bank_account TEXT,
                ifsc_code TEXT,
                account_holder_name TEXT,
                preferred_payment_method TEXT DEFAULT 'upi',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff (id)
            )
        """)
        print("   - Created staff_payment_info table")
        
        # 4. Create salary_alerts table
        print("4. Creating salary_alerts table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salary_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER NOT NULL,
                salary_record_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL,
                alert_date DATE NOT NULL,
                is_dismissed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (staff_id) REFERENCES staff (id),
                FOREIGN KEY (salary_record_id) REFERENCES salary_records (id)
            )
        """)
        print("   - Created salary_alerts table")
        
        # 5. Create indexes for better performance
        print("5. Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_records_staff_id ON salary_records(staff_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_records_status ON salary_records(payment_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_records_due_date ON salary_records(due_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_alerts_staff_id ON salary_alerts(staff_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_salary_alerts_dismissed ON salary_alerts(is_dismissed)")
        print("   - Created performance indexes")
        
        # Commit all changes
        conn.commit()
        print("✅ Salary management migration completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)