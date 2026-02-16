"""
Migration to add staff_name columns for audit history
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    with engine.connect() as conn:
        print("Adding staff_name columns for audit history...")
        
        # Add staff_name to purchases_audit
        try:
            conn.execute(text("ALTER TABLE purchases_audit ADD COLUMN staff_name VARCHAR"))
            conn.commit()
            print("✓ Added staff_name to purchases_audit")
        except Exception as e:
            print(f"⚠ staff_name in purchases_audit: {e}")
        
        # Add staff_name to sales_audit
        try:
            conn.execute(text("ALTER TABLE sales_audit ADD COLUMN staff_name VARCHAR"))
            conn.commit()
            print("✓ Added staff_name to sales_audit")
        except Exception as e:
            print(f"⚠ staff_name in sales_audit: {e}")
        
        # Add staff_name to stock_audit_records
        try:
            conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN staff_name VARCHAR"))
            conn.commit()
            print("✓ Added staff_name to stock_audit_records")
        except Exception as e:
            print(f"⚠ staff_name in stock_audit_records: {e}")
        
        # Add resolved_by_staff_name to stock_audit_records
        try:
            conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN resolved_by_staff_name VARCHAR"))
            conn.commit()
            print("✓ Added resolved_by_staff_name to stock_audit_records")
        except Exception as e:
            print(f"⚠ resolved_by_staff_name: {e}")
        
        # Add staff_name to stock_audit_sessions
        try:
            conn.execute(text("ALTER TABLE stock_audit_sessions ADD COLUMN staff_name VARCHAR"))
            conn.commit()
            print("✓ Added staff_name to stock_audit_sessions")
        except Exception as e:
            print(f"⚠ staff_name in stock_audit_sessions: {e}")
        
        # Update stock_adjustments to add staff_name
        try:
            conn.execute(text("ALTER TABLE stock_adjustments ADD COLUMN staff_name VARCHAR NOT NULL DEFAULT 'Unknown'"))
            conn.commit()
            print("✓ Added staff_name to stock_adjustments")
        except Exception as e:
            print(f"⚠ staff_name in stock_adjustments: {e}")
        
        # Add last_audit_by_staff_name to stock_items_audit
        try:
            conn.execute(text("ALTER TABLE stock_items_audit ADD COLUMN last_audit_by_staff_name VARCHAR"))
            conn.commit()
            print("✓ Added last_audit_by_staff_name to stock_items_audit")
        except Exception as e:
            print(f"⚠ last_audit_by_staff_name: {e}")
        
        print("\n✅ Staff name columns migration completed!")

if __name__ == "__main__":
    run_migration()
