"""Check all schema differences between local and production"""
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

load_dotenv()

LOCAL_DB = os.getenv('DATABASE_URL')
PROD_DB = os.getenv('PRODUCTION_DATABASE_URL')

def get_table_columns(engine, table_name):
    inspector = inspect(engine)
    columns = {}
    for col in inspector.get_columns(table_name):
        columns[col['name']] = str(col['type'])
    return columns

def compare_schemas():
    # Add connection timeout and pool settings
    local_engine = create_engine(
        LOCAL_DB,
        connect_args={'connect_timeout': 10}
    )
    prod_engine = create_engine(
        PROD_DB,
        connect_args={'connect_timeout': 10},
        pool_pre_ping=True  # Verify connections before using
    )
    
    print("Connecting to LOCAL database...")
    try:
        local_inspector = inspect(local_engine)
        print("✅ Connected to LOCAL database")
    except Exception as e:
        print(f"❌ Failed to connect to LOCAL database: {e}")
        raise
    
    print("Connecting to PRODUCTION database...")
    try:
        prod_inspector = inspect(prod_engine)
        print("✅ Connected to PRODUCTION database")
    except Exception as e:
        print(f"\n❌ Failed to connect to PRODUCTION database")
        print(f"\nPossible causes:")
        print("  1. Database service is down or paused (check Railway dashboard)")
        print("  2. Network/firewall blocking the connection")
        print("  3. Incorrect credentials in PRODUCTION_DATABASE_URL")
        print("  4. IP whitelist restrictions on the database")
        print(f"\nOriginal error: {e}")
        local_engine.dispose()
        raise
    
    local_tables = set(local_inspector.get_table_names())
    prod_tables = set(prod_inspector.get_table_names())
    
    print("="*80)
    print("SCHEMA COMPARISON: LOCAL vs PRODUCTION")
    print("="*80)
    
    # Tables only in local
    if local_tables - prod_tables:
        print("\n❌ Tables missing in PRODUCTION:")
        for t in sorted(local_tables - prod_tables):
            print(f"  - {t}")
    
    # Tables only in production
    if prod_tables - local_tables:
        print("\n⚠️  Extra tables in PRODUCTION:")
        for t in sorted(prod_tables - local_tables):
            print(f"  - {t}")
    
    # Compare columns for common tables
    common_tables = local_tables & prod_tables
    differences = []
    
    for table in sorted(common_tables):
        local_cols = get_table_columns(local_engine, table)
        prod_cols = get_table_columns(prod_engine, table)
        
        missing_in_prod = set(local_cols.keys()) - set(prod_cols.keys())
        extra_in_prod = set(prod_cols.keys()) - set(local_cols.keys())
        
        if missing_in_prod or extra_in_prod:
            differences.append(table)
            print(f"\n❌ Table: {table}")
            
            if missing_in_prod:
                print("  Missing in PRODUCTION:")
                for col in sorted(missing_in_prod):
                    print(f"    - {col}: {local_cols[col]}")
            
            if extra_in_prod:
                print("  Extra in PRODUCTION:")
                for col in sorted(extra_in_prod):
                    print(f"    + {col}: {prod_cols[col]}")
        
        # Check type mismatches
        common_cols = set(local_cols.keys()) & set(prod_cols.keys())
        for col in common_cols:
            if local_cols[col] != prod_cols[col]:
                if table not in differences:
                    differences.append(table)
                    print(f"\n⚠️  Table: {table}")
                print(f"  Type mismatch for '{col}':")
                print(f"    Local:      {local_cols[col]}")
                print(f"    Production: {prod_cols[col]}")
    
    if not differences:
        print("\n✅ All schemas match!")
    else:
        print(f"\n\n📊 Summary: {len(differences)} tables have differences")
    
    print("\n" + "="*80)
    
    local_engine.dispose()
    prod_engine.dispose()

if __name__ == "__main__":
    try:
        compare_schemas()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
