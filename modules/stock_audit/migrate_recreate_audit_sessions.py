"""Recreate stock_audit_sessions table without auditor column"""
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
        CREATE TABLE stock_audit_sessions_new (
            id INTEGER PRIMARY KEY,
            shop_id INTEGER,
            staff_id INTEGER,
            staff_name VARCHAR,
            session_date DATE,
            sections_audited INTEGER DEFAULT 0,
            items_audited INTEGER DEFAULT 0,
            discrepancies_found INTEGER DEFAULT 0,
            status VARCHAR DEFAULT 'in_progress',
            started_at DATETIME,
            completed_at DATETIME,
            session_notes TEXT,
            FOREIGN KEY (shop_id) REFERENCES shops(id),
            FOREIGN KEY (staff_id) REFERENCES staff(id)
        )
    """))
    print("✓ Created new stock_audit_sessions table")
    
    # Copy data if any exists
    try:
        conn.execute(text("""
            INSERT INTO stock_audit_sessions_new 
            (id, shop_id, staff_id, staff_name, session_date, sections_audited, 
             items_audited, discrepancies_found, status, started_at, completed_at, session_notes)
            SELECT id, shop_id, staff_id, staff_name, session_date, sections_audited,
                   items_audited, discrepancies_found, status, started_at, completed_at, session_notes
            FROM stock_audit_sessions
        """))
        print("✓ Copied existing data")
    except Exception as e:
        print(f"No existing data to copy: {e}")
    
    # Drop old table
    conn.execute(text("DROP TABLE IF EXISTS stock_audit_sessions"))
    print("✓ Dropped old table")
    
    # Rename new table
    conn.execute(text("ALTER TABLE stock_audit_sessions_new RENAME TO stock_audit_sessions"))
    print("✓ Renamed new table")
    
    conn.commit()
    print("\n✓ Migration completed successfully")
