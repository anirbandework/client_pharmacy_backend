#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/anirbande/Desktop/client backend')

import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.daily_records.service import import_excel_data
from modules.daily_records.models import DailyRecord
from fastapi import UploadFile
import io

# Database setup
DATABASE_URL = "sqlite:///./pharmacy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_excel_import():
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
        
        # Clear existing data for December 2025
        db.query(DailyRecord).filter(
            DailyRecord.date >= '2025-12-01',
            DailyRecord.date <= '2025-12-31'
        ).delete()
        db.commit()
        
        print("Testing improved Excel import...")
        result = await import_excel_data(mock_file, db)
        
        print(f"Import result: {result.message}")
        print(f"Records imported: {result.records_imported}")
        if result.errors:
            print(f"Errors: {result.errors[:5]}")  # Show first 5 errors
        
        # Check the imported data
        records = db.query(DailyRecord).filter(
            DailyRecord.date >= '2025-12-10',
            DailyRecord.date <= '2025-12-15'
        ).order_by(DailyRecord.date).all()
        
        print(f"\nImported records for Dec 10-15, 2025:")
        for record in records:
            print(f"Date: {record.date}, Day: {record.day}")
            print(f"  Actual Cash: ₹{record.actual_cash}, Online: ₹{record.online_sales}")
            print(f"  Total Sales: ₹{record.total_sales}, Bills: {record.no_of_bills}")
            print(f"  Average Bill: ₹{record.average_bill}")
            print()
            
    except Exception as e:
        print(f"Error testing import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_excel_import())