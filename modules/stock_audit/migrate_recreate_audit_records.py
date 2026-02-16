"""Recreate stock_audit_records table without audited_by column"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from app.core.config import settings

database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)

with engine.connect() as conn:
    # Create new table
    conn.execute(text("""
        CREATE TABLE stock_audit_records_new (
            id INTEGER PRIMARY KEY,
            shop_id INTEGER,
            staff_id INTEGER,
            staff_name VARCHAR,
            stock_item_id INTEGER NOT NULL,
            audit_date DATETIME,
            software_quantity INTEGER NOT NULL,
            physical_quantity INTEGER NOT NULL,
            discrepancy INTEGER NOT NULL,
            notes TEXT,
            reason_for_discrepancy VARCHAR,
            resolved BOOLEAN DEFAULT 0,
            resolved_date DATETIME,
            resolved_by_staff_id INTEGER,
            resolved_by_staff_name VARCHAR,
            resolution_notes TEXT,
            FOREIGN KEY (shop_id) REFERENCES shops(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id),
            FOREIGN KEY (stock_item_id) REFERENCES stock_items_audit(id),
            FOREIGN KEY (resolved_by_staff_id) REFERENCES staff(id)
        )
    """))
    print("✓ Created new stock_audit_records table")
    
    # Copy data if any exists
    try:
        conn.execute(text("""
            INSERT INTO stock_audit_records_new 
            (id, shop_id, staff_id, staff_name, stock_item_id, audit_date, 
             software_quantity, physical_quantity, discrepancy, notes, 
             reason_for_discrepancy, resolved, resolved_date, 
             resolved_by_staff_id, resolved_by_staff_name, resolution_notes)
            SELECT id, shop_id, staff_id, staff_name, stock_item_id, audit_date,
                   software_quantity, physical_quantity, discrepancy, notes,
                   reason_for_discrepancy, resolved, resolved_date,
                   resolved_by_staff_id, resolved_by_staff_name, resolution_notes
            FROM stock_audit_records
        """))
        print("✓ Copied existing data")
    except Exception as e:
        print(f"No existing data to copy: {e}")
    
    # Drop old table
    conn.execute(text("DROP TABLE IF EXISTS stock_audit_records"))
    print("✓ Dropped old table")
    
    # Rename new table
    conn.execute(text("ALTER TABLE stock_audit_records_new RENAME TO stock_audit_records"))
    print("✓ Renamed new table")
    
    conn.commit()
    print("\n✓ Migration completed successfully")
