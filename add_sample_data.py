#!/usr/bin/env python3

import sys
import os
sys.path.append('/Users/anirbande/Desktop/client backend')

import asyncio
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.daily_records.models import DailyRecord

# Database setup
DATABASE_URL = "sqlite:///./pharmacy.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def add_sample_data():
    db = SessionLocal()
    
    try:
        # Sample data based on your Excel file
        sample_records = [
            {
                'date': date(2025, 12, 10),
                'day': 'Wednesday',
                'cash_balance': 1000.0,
                'no_of_bills': 90,
                'actual_cash': 11500.0,  # 9500+2000
                'online_sales': 14693.0,
                'unbilled_sales': 213.0,  # 69+50+94
                'software_figure': 27804.0,
                'cash_reserve': -120.0,  # -70-20-50-50+70
                'expense_amount': 700.0,
                'created_by': 'manual_entry'
            },
            {
                'date': date(2025, 12, 11),
                'day': 'Thursday',
                'cash_balance': 1000.0,
                'no_of_bills': 88,
                'actual_cash': 10000.0,
                'online_sales': 10880.0,  # 7962+2918
                'unbilled_sales': 865.0,
                'software_figure': 19677.0,
                'cash_reserve': -674.0,  # Complex formula result
                'expense_amount': 30.0,
                'reserve_comments': 'Check settlement',
                'created_by': 'manual_entry'
            },
            {
                'date': date(2025, 12, 12),
                'day': 'Friday',
                'cash_balance': 1000.0,
                'no_of_bills': 66,
                'actual_cash': 9400.0,
                'online_sales': 3873.0,
                'unbilled_sales': 50.0,  # 33+17
                'software_figure': 13774.0,
                'cash_reserve': -18.0,  # -13-40+35
                'expense_amount': 0.0,
                'created_by': 'manual_entry'
            }
        ]
        
        for record_data in sample_records:
            # Calculate derived fields
            total_cash = record_data['actual_cash'] + record_data['cash_reserve'] + record_data['expense_amount']
            total_sales = record_data['actual_cash'] + record_data['online_sales']
            recorded_sales = record_data['unbilled_sales'] + record_data['software_figure']
            sales_difference = total_sales - recorded_sales
            average_bill = recorded_sales / record_data['no_of_bills'] if record_data['no_of_bills'] > 0 else 0
            
            record_data.update({
                'total_cash': round(total_cash, 2),
                'total_sales': round(total_sales, 2),
                'recorded_sales': round(recorded_sales, 2),
                'sales_difference': round(sales_difference, 2),
                'average_bill': round(average_bill, 2),
                'shop_id': None  # Set shop_id to None since it's nullable
            })
            
            # Check if record already exists
            existing = db.query(DailyRecord).filter(DailyRecord.date == record_data['date']).first()
            if existing:
                print(f"Record for {record_data['date']} already exists, updating...")
                for field, value in record_data.items():
                    if field != 'date':
                        setattr(existing, field, value)
                existing.modified_at = datetime.utcnow()
                existing.modified_by = 'manual_update'
            else:
                print(f"Creating new record for {record_data['date']}")
                db_record = DailyRecord(**record_data)
                db.add(db_record)
        
        db.commit()
        print("Sample data added successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error adding sample data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()