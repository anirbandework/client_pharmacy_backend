"""Add staff_id and staff_name to stock_audit_records table"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from app.core.config import settings

# Fix Railway's postgres:// to postgresql://
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(database_url, connect_args=connect_args)

with engine.connect() as conn:
    # Add staff_id column
    try:
        conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN staff_id INTEGER"))
        print("✓ Added staff_id column to stock_audit_records")
    except Exception as e:
        print(f"staff_id column may already exist: {e}")
    
    # Add staff_name column
    try:
        conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN staff_name VARCHAR"))
        print("✓ Added staff_name column to stock_audit_records")
    except Exception as e:
        print(f"staff_name column may already exist: {e}")
    
    # Add resolved_by_staff_id column
    try:
        conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN resolved_by_staff_id INTEGER"))
        print("✓ Added resolved_by_staff_id column to stock_audit_records")
    except Exception as e:
        print(f"resolved_by_staff_id column may already exist: {e}")
    
    # Add resolved_by_staff_name column
    try:
        conn.execute(text("ALTER TABLE stock_audit_records ADD COLUMN resolved_by_staff_name VARCHAR"))
        print("✓ Added resolved_by_staff_name column to stock_audit_records")
    except Exception as e:
        print(f"resolved_by_staff_name column may already exist: {e}")
    
    conn.commit()
    print("\n✓ Migration completed successfully")
