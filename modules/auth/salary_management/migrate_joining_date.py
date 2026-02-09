#!/usr/bin/env python3
"""
Database migration script to add joining date and salary eligibility fields to staff table
"""

import sqlite3
import sys
import os
from datetime import datetime

def run_migration():
    """Add joining date and salary eligibility fields to staff table"""
    
    # Database path
    db_path = "pharmacy.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting staff joining date migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(staff)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'joining_date' not in columns:
            cursor.execute("ALTER TABLE staff ADD COLUMN joining_date DATE")
            print("   - Added joining_date column")
        
        if 'salary_eligibility_days' not in columns:
            cursor.execute("ALTER TABLE staff ADD COLUMN salary_eligibility_days INTEGER DEFAULT 30")
            print("   - Added salary_eligibility_days column")
        
        # Commit changes
        conn.commit()
        print("✅ Staff joining date migration completed successfully!")
        
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