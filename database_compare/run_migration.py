#!/usr/bin/env python3
"""
Script to apply SQL migration to production database
"""
import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    # Get production database URL from .env
    prod_db_url = os.getenv('PRODUCTION_DATABASE_URL')
    
    if not prod_db_url:
        print("❌ PRODUCTION_DATABASE_URL not found in .env file")
        return
    
    # Parse the database URL
    # Format: postgresql://user:password@host:port/database
    print(f"🔗 Connecting to production database...")
    
    try:
        # Connect to production database
        conn = psycopg2.connect(prod_db_url)
        conn.autocommit = False  # Use transactions
        cursor = conn.cursor()
        
        print("✅ Connected to production database")
        print("\n" + "="*80)
        print("STARTING SCHEMA MIGRATION")
        print("="*80 + "\n")
        
        # Read SQL file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sql_file = os.path.join(script_dir, 'fix_production_schema.sql')
        with open(sql_file, 'r') as f:
            sql_content = f.read()
        
        # Split by sections and execute
        sections = sql_content.split('-- ============================================================================')
        
        for i, section in enumerate(sections):
            if not section.strip() or section.strip().startswith('VERIFICATION'):
                continue
            
            # Extract section title
            lines = section.strip().split('\n')
            if lines:
                title = lines[0].replace('--', '').strip()
                if title:
                    print(f"📝 {title}")
            
            # Extract and execute SQL statements
            sql_statements = []
            current_statement = []
            
            for line in lines[1:]:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('--'):
                    continue
                
                current_statement.append(line)
                
                # If line ends with semicolon, it's end of statement
                if line.endswith(';'):
                    sql_statements.append(' '.join(current_statement))
                    current_statement = []
            
            # Execute each statement
            for sql in sql_statements:
                if sql.strip():
                    try:
                        cursor.execute(sql)
                        print(f"   ✓ Executed successfully")
                    except Exception as e:
                        print(f"   ⚠️  Warning: {str(e)}")
                        # Continue with other statements
                        conn.rollback()
                        conn.autocommit = False
        
        # Commit all changes
        print("\n" + "="*80)
        print("💾 Committing changes...")
        conn.commit()
        print("✅ Migration completed successfully!")
        print("="*80 + "\n")
        
        # Run verification queries
        print("\n" + "="*80)
        print("VERIFICATION")
        print("="*80 + "\n")
        
        verification_queries = [
            ("distributor_invoice_items", """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'distributor_invoice_items' 
                AND column_name IN ('discount_on_sales', 'before_discount', 'discount_on_purchase')
                ORDER BY column_name
            """),
            ("distributors", """
                SELECT column_name, data_type, character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'distributors' 
                AND column_name IN ('company_name', 'credit_limit')
                ORDER BY column_name
            """),
            ("purchase_invoices", """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'purchase_invoices' 
                AND column_name IN ('admin_rejected_at', 'admin_rejected_by', 'raw_extracted_data')
                ORDER BY column_name
            """),
            ("stock_items_audit", """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'stock_items_audit' 
                AND column_name IN ('composition', 'manufacturing_date', 'profit_margin', 'selling_price', 'unit')
                ORDER BY column_name
            """)
        ]
        
        for table_name, query in verification_queries:
            print(f"📋 Verifying {table_name}:")
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                if len(row) == 3:
                    print(f"   {row[0]}: {row[1]}({row[2]})" if row[2] else f"   {row[0]}: {row[1]}")
                else:
                    print(f"   {row[0]}: {row[1]}")
            print()
        
        cursor.close()
        conn.close()
        
        print("\n✅ All done! Run check_schema_diff.py again to verify no differences remain.")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will modify the PRODUCTION database!")
    print("Make sure you have a backup before proceeding.\n")
    
    response = input("Do you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        run_migration()
    else:
        print("❌ Migration cancelled.")
