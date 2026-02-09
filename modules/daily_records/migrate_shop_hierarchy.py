#!/usr/bin/env python3
"""
Database migration script to add shop_id foreign keys to daily_records
"""

import sqlite3
import sys
import os
from datetime import datetime

def run_migration():
    """Add shop_id foreign keys to daily records tables"""
    
    # Database path
    db_path = "pharmacy.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Starting daily records shop hierarchy migration...")
        
        # 1. Check if shops table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shops'")
        if not cursor.fetchone():
            print("❌ Shops table not found. Please run auth migrations first.")
            return False
        
        # 2. Get the first shop ID as default
        cursor.execute("SELECT id FROM shops LIMIT 1")
        default_shop = cursor.fetchone()
        if not default_shop:
            print("❌ No shops found. Please create a shop first.")
            return False
        
        default_shop_id = default_shop[0]
        print(f"   - Using shop ID {default_shop_id} as default for existing records")
        
        # 3. Update daily_records table
        print("3. Updating daily_records table...")
        
        # Check current structure
        cursor.execute("PRAGMA table_info(daily_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'shop_id' in columns:
            # Update existing shop_id to be NOT NULL and add foreign key
            cursor.execute(f"UPDATE daily_records SET shop_id = {default_shop_id} WHERE shop_id IS NULL")
            print("   - Updated NULL shop_id values")
        else:
            # Add shop_id column
            cursor.execute(f"ALTER TABLE daily_records ADD COLUMN shop_id INTEGER DEFAULT {default_shop_id}")
            print("   - Added shop_id column")
        
        # 4. Update record_modifications table
        print("4. Updating record_modifications table...")
        
        cursor.execute("PRAGMA table_info(record_modifications)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'shop_id' in columns:
            # Update existing shop_id to be NOT NULL
            cursor.execute(f"UPDATE record_modifications SET shop_id = {default_shop_id} WHERE shop_id IS NULL")
            print("   - Updated NULL shop_id values in modifications")
        else:
            # Add shop_id column
            cursor.execute(f"ALTER TABLE record_modifications ADD COLUMN shop_id INTEGER DEFAULT {default_shop_id}")
            print("   - Added shop_id column to modifications")
        
        # 5. Remove unique constraint on date (SQLite doesn't support dropping constraints directly)
        print("5. Updating table constraints...")
        
        # Create new table with proper constraints
        cursor.execute("""
            CREATE TABLE daily_records_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shop_id INTEGER NOT NULL,
                date DATE NOT NULL,
                day TEXT,
                cash_balance REAL,
                average_bill REAL,
                no_of_bills INTEGER,
                total_cash REAL,
                actual_cash REAL,
                online_sales REAL,
                total_sales REAL,
                unbilled_sales REAL,
                software_figure REAL,
                recorded_sales REAL,
                sales_difference REAL,
                cash_reserve REAL,
                reserve_comments TEXT,
                expense_amount REAL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                modified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                modified_by TEXT,
                FOREIGN KEY (shop_id) REFERENCES shops (id),
                UNIQUE(shop_id, date)
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO daily_records_new 
            SELECT * FROM daily_records
        """)
        
        # Drop old table and rename
        cursor.execute("DROP TABLE daily_records")
        cursor.execute("ALTER TABLE daily_records_new RENAME TO daily_records")
        
        print("   - Updated daily_records with proper constraints")
        
        # 6. Create indexes
        print("6. Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_records_shop_id ON daily_records(shop_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_records_date ON daily_records(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_record_modifications_shop_id ON record_modifications(shop_id)")
        print("   - Created performance indexes")
        
        # Commit changes
        conn.commit()
        print("✅ Daily records shop hierarchy migration completed successfully!")
        
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