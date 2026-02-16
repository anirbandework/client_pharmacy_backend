"""
Migration script for stock_audit module fixes
Adds batch_number tracking and stock_adjustments table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import text
from app.database.database import engine

def run_migration():
    with engine.connect() as conn:
        print("Starting stock_audit migration...")
        
        # Add batch_number to purchase_items_audit
        try:
            conn.execute(text("""
                ALTER TABLE purchase_items_audit 
                ADD COLUMN batch_number VARCHAR
            """))
            conn.commit()
            print("✓ Added batch_number to purchase_items_audit")
        except Exception as e:
            print(f"⚠ batch_number in purchase_items_audit: {e}")
        
        # Add batch_number to sale_items_audit
        try:
            conn.execute(text("""
                ALTER TABLE sale_items_audit 
                ADD COLUMN batch_number VARCHAR
            """))
            conn.commit()
            print("✓ Added batch_number to sale_items_audit")
        except Exception as e:
            print(f"⚠ batch_number in sale_items_audit: {e}")
        
        # Create stock_adjustments table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stock_adjustments (
                    id INTEGER PRIMARY KEY,
                    shop_id INTEGER,
                    stock_item_id INTEGER NOT NULL,
                    adjustment_type VARCHAR NOT NULL,
                    quantity_change INTEGER NOT NULL,
                    reason VARCHAR NOT NULL,
                    notes TEXT,
                    adjusted_by VARCHAR NOT NULL,
                    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (shop_id) REFERENCES shops(id),
                    FOREIGN KEY (stock_item_id) REFERENCES stock_items_audit(id) ON DELETE CASCADE
                )
            """))
            conn.commit()
            print("✓ Created stock_adjustments table")
        except Exception as e:
            print(f"⚠ stock_adjustments table: {e}")
        
        # Create indexes
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_adjustments_shop ON stock_adjustments(shop_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_stock_adjustments_item ON stock_adjustments(stock_item_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_purchase_items_batch ON purchase_items_audit(batch_number)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sale_items_batch ON sale_items_audit(batch_number)"))
            conn.commit()
            print("✓ Created indexes")
        except Exception as e:
            print(f"⚠ Indexes: {e}")
        
        print("\n✅ Migration completed!")

if __name__ == "__main__":
    run_migration()
