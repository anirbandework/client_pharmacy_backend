#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Customer Tracking
Adds new columns and tables to existing database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database.database import get_db, engine
from modules.customer_tracking.models import Base

def migrate_database():
    """Migrate existing database to support enhanced customer tracking"""
    
    db = next(get_db())
    
    try:
        print("🔄 Starting database migration for enhanced customer tracking...")
        
        # Add new columns to customer_profiles table
        migration_queries = [
            "ALTER TABLE customer_profiles ADD COLUMN primary_doctor TEXT",
            "ALTER TABLE customer_profiles ADD COLUMN doctor_phone TEXT"
        ]
        
        for query in migration_queries:
            try:
                db.execute(text(query))
                print(f"✅ Executed: {query}")
            except Exception as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"⚠️  Column already exists: {query}")
                else:
                    print(f"❌ Error executing {query}: {str(e)}")
        
        # Create new tables
        print("\n🏗️  Creating new tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created/updated successfully")
        
        db.commit()
        print("\n✅ Database migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_database()