#!/usr/bin/env python3

import sqlite3
from datetime import date

def add_sample_data_direct():
    # Connect directly to SQLite database
    conn = sqlite3.connect('/Users/anirbande/Desktop/client backend/pharmacy.db')
    cursor = conn.cursor()
    
    try:
        # Sample data with actual calculated values
        from datetime import datetime
        now = datetime.utcnow().isoformat()
        
        sample_records = [
            (
                '2025-12-10', 'Wednesday', 1000.0, 90, 11500.0, 14693.0, 213.0, 27804.0, 
                -120.0, '', 700.0, '', 26193.0, 26193.0, 28017.0, -1824.0, 311.3,
                'manual_entry', 'manual_entry', None, now, now
            ),
            (
                '2025-12-11', 'Thursday', 1000.0, 88, 10000.0, 10880.0, 865.0, 19677.0,
                -674.0, 'Check settlement', 30.0, '', 9356.0, 20880.0, 20542.0, 338.0, 233.4,
                'manual_entry', 'manual_entry', None, now, now
            ),
            (
                '2025-12-12', 'Friday', 1000.0, 66, 9400.0, 3873.0, 50.0, 13774.0,
                -18.0, '', 0.0, '', 9382.0, 13273.0, 13824.0, -551.0, 209.5,
                'manual_entry', 'manual_entry', None, now, now
            )
        ]
        
        # Delete existing records for these dates
        cursor.execute("DELETE FROM daily_records WHERE date IN ('2025-12-10', '2025-12-11', '2025-12-12')")
        
        # Insert new records
        insert_sql = """
        INSERT INTO daily_records (
            date, day, cash_balance, no_of_bills, actual_cash, online_sales, 
            unbilled_sales, software_figure, cash_reserve, reserve_comments, 
            expense_amount, notes, total_cash, total_sales, recorded_sales, 
            sales_difference, average_bill, created_by, modified_by, shop_id,
            created_at, modified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(insert_sql, sample_records)
        conn.commit()
        
        print(f"Successfully added {len(sample_records)} sample records!")
        
        # Verify the data
        cursor.execute("SELECT date, day, actual_cash, total_sales FROM daily_records WHERE date >= '2025-12-10' ORDER BY date")
        results = cursor.fetchall()
        
        print("\nVerification - Added records:")
        for row in results:
            print(f"Date: {row[0]}, Day: {row[1]}, Actual Cash: ₹{row[2]}, Total Sales: ₹{row[3]}")
            
    except Exception as e:
        conn.rollback()
        print(f"Error adding sample data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_data_direct()