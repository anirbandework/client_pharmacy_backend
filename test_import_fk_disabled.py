#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/anirbande/Desktop/client backend')

import asyncio
import sqlite3
from modules.daily_records.service import import_excel_data
from fastapi import UploadFile

async def test_import_with_fk_disabled():
    # Connect to database and disable foreign key checks
    conn = sqlite3.connect('/Users/anirbande/Desktop/client backend/pharmacy.db')
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.close()
    
    # Now test the import
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    DATABASE_URL = "sqlite:///./pharmacy.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Read the Excel file
        file_path = '/Users/anirbande/Desktop/client backend/modules/daily_records/GMTR0003 business records .xlsx'
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Create a mock UploadFile
        class MockUploadFile:
            def __init__(self, content):
                self.content = content
            
            async def read(self):
                return self.content
        
        mock_file = MockUploadFile(file_content)
        
        print("Testing improved Excel import with formulas...")
        result = await import_excel_data(mock_file, db)
        
        print(f"Import result: {result.message}")
        print(f"Records imported: {result.records_imported}")
        print(f"Success: {result.success}")
        
        if result.errors:
            print(f"First 3 errors: {result.errors[:3]}")
        
        # Check some imported data
        from modules.daily_records.models import DailyRecord
        records = db.query(DailyRecord).filter(
            DailyRecord.date >= '2025-12-10',
            DailyRecord.date <= '2025-12-15'
        ).order_by(DailyRecord.date).all()
        
        print(f"\nSample imported records:")
        for record in records[:5]:  # Show first 5
            print(f"Date: {record.date}, Day: {record.day}")
            print(f"  Actual Cash: ₹{record.actual_cash}, Online: ₹{record.online_sales}")
            print(f"  Total Sales: ₹{record.total_sales}, Bills: {record.no_of_bills}")
            print()
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        
        # Re-enable foreign key checks
        conn = sqlite3.connect('/Users/anirbande/Desktop/client backend/pharmacy.db')
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

if __name__ == "__main__":
    asyncio.run(test_import_with_fk_disabled())