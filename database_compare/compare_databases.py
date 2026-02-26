"""
Database Comparison Tool
Compares local and production databases to show differences

Usage:
  python compare_databases.py

Requirements:
  - Set PRODUCTION_DATABASE_URL in .env or pass as argument
  - Local DATABASE_URL should be in .env
"""
import os
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

# Database URLs
LOCAL_DB = os.getenv('DATABASE_URL')
PROD_DB = os.getenv('PRODUCTION_DATABASE_URL') or input("Enter Production DATABASE_URL: ")

def get_table_counts(engine):
    """Get row counts for all tables"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    counts = {}
    with engine.connect() as conn:
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar()
            except Exception as e:
                counts[table] = f"Error: {str(e)}"
    
    return counts

def get_superadmins(engine):
    """Get SuperAdmin details"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT phone, full_name, email, is_active, created_at 
                FROM super_admins 
                ORDER BY created_at
            """))
            return [dict(row._mapping) for row in result]
        except:
            return []

def get_admins(engine):
    """Get Admin details"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT phone, full_name, email, organization_id, is_active, is_password_set 
                FROM admins 
                ORDER BY created_at
            """))
            return [dict(row._mapping) for row in result]
        except:
            return []

def get_shops(engine):
    """Get Shop details"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT shop_code, shop_name, organization_id, is_active 
                FROM shops 
                ORDER BY created_at
            """))
            return [dict(row._mapping) for row in result]
        except:
            return []

def get_staff(engine):
    """Get Staff details"""
    with engine.connect() as conn:
        try:
            result = conn.execute(text("""
                SELECT s.phone, s.name, s.staff_code, sh.shop_name, s.is_active 
                FROM staff s
                LEFT JOIN shops sh ON s.shop_id = sh.id
                ORDER BY s.created_at
            """))
            return [dict(row._mapping) for row in result]
        except:
            return []

def compare_databases():
    print("\n" + "="*80)
    print("DATABASE COMPARISON: LOCAL vs PRODUCTION")
    print("="*80 + "\n")
    
    # Connect to databases
    print("🔌 Connecting to databases...")
    local_engine = create_engine(LOCAL_DB)
    prod_engine = create_engine(PROD_DB)
    print("✅ Connected!\n")
    
    # 1. Table Row Counts
    print("\n📊 TABLE ROW COUNTS")
    print("-" * 80)
    local_counts = get_table_counts(local_engine)
    prod_counts = get_table_counts(prod_engine)
    
    all_tables = sorted(set(list(local_counts.keys()) + list(prod_counts.keys())))
    
    comparison_data = []
    for table in all_tables:
        local_count = local_counts.get(table, "N/A")
        prod_count = prod_counts.get(table, "N/A")
        
        if local_count != prod_count:
            diff = "⚠️  DIFFERENT"
        else:
            diff = "✅ Same"
        
        comparison_data.append([table, local_count, prod_count, diff])
    
    print(tabulate(comparison_data, headers=["Table", "Local", "Production", "Status"], tablefmt="grid"))
    
    # 2. SuperAdmins Comparison
    print("\n\n👑 SUPERADMINS")
    print("-" * 80)
    local_superadmins = get_superadmins(local_engine)
    prod_superadmins = get_superadmins(prod_engine)
    
    print(f"\n📍 LOCAL ({len(local_superadmins)} SuperAdmins):")
    if local_superadmins:
        for sa in local_superadmins:
            status = "✅" if sa['is_active'] else "❌"
            print(f"  {status} {sa['phone']} | {sa['full_name']} | {sa['email']}")
    else:
        print("  (none)")
    
    print(f"\n🌐 PRODUCTION ({len(prod_superadmins)} SuperAdmins):")
    if prod_superadmins:
        for sa in prod_superadmins:
            status = "✅" if sa['is_active'] else "❌"
            print(f"  {status} {sa['phone']} | {sa['full_name']} | {sa['email']}")
    else:
        print("  (none)")
    
    # 3. Admins Comparison
    print("\n\n👔 ADMINS")
    print("-" * 80)
    local_admins = get_admins(local_engine)
    prod_admins = get_admins(prod_engine)
    
    print(f"\n📍 LOCAL ({len(local_admins)} Admins):")
    if local_admins:
        for admin in local_admins[:5]:  # Show first 5
            status = "✅" if admin['is_active'] else "❌"
            pwd = "🔑" if admin['is_password_set'] else "⚠️"
            print(f"  {status} {pwd} {admin['phone']} | {admin['full_name']} | Org: {admin['organization_id']}")
        if len(local_admins) > 5:
            print(f"  ... and {len(local_admins) - 5} more")
    else:
        print("  (none)")
    
    print(f"\n🌐 PRODUCTION ({len(prod_admins)} Admins):")
    if prod_admins:
        for admin in prod_admins[:5]:  # Show first 5
            status = "✅" if admin['is_active'] else "❌"
            pwd = "🔑" if admin['is_password_set'] else "⚠️"
            print(f"  {status} {pwd} {admin['phone']} | {admin['full_name']} | Org: {admin['organization_id']}")
        if len(prod_admins) > 5:
            print(f"  ... and {len(prod_admins) - 5} more")
    else:
        print("  (none)")
    
    # 4. Shops Comparison
    print("\n\n🏪 SHOPS")
    print("-" * 80)
    local_shops = get_shops(local_engine)
    prod_shops = get_shops(prod_engine)
    
    print(f"\n📍 LOCAL ({len(local_shops)} Shops):")
    if local_shops:
        for shop in local_shops[:5]:
            status = "✅" if shop['is_active'] else "❌"
            print(f"  {status} {shop['shop_code']} | {shop['shop_name']} | Org: {shop['organization_id']}")
        if len(local_shops) > 5:
            print(f"  ... and {len(local_shops) - 5} more")
    else:
        print("  (none)")
    
    print(f"\n🌐 PRODUCTION ({len(prod_shops)} Shops):")
    if prod_shops:
        for shop in prod_shops[:5]:
            status = "✅" if shop['is_active'] else "❌"
            print(f"  {status} {shop['shop_code']} | {shop['shop_name']} | Org: {shop['organization_id']}")
        if len(prod_shops) > 5:
            print(f"  ... and {len(prod_shops) - 5} more")
    else:
        print("  (none)")
    
    # 5. Staff Comparison
    print("\n\n👥 STAFF")
    print("-" * 80)
    local_staff = get_staff(local_engine)
    prod_staff = get_staff(prod_engine)
    
    print(f"\n📍 LOCAL ({len(local_staff)} Staff):")
    if local_staff:
        for staff in local_staff[:5]:
            status = "✅" if staff['is_active'] else "❌"
            print(f"  {status} {staff['phone']} | {staff['name']} | Shop: {staff['shop_name']}")
        if len(local_staff) > 5:
            print(f"  ... and {len(local_staff) - 5} more")
    else:
        print("  (none)")
    
    print(f"\n🌐 PRODUCTION ({len(prod_staff)} Staff):")
    if prod_staff:
        for staff in prod_staff[:5]:
            status = "✅" if staff['is_active'] else "❌"
            print(f"  {status} {staff['phone']} | {staff['name']} | Shop: {staff['shop_name']}")
        if len(prod_staff) > 5:
            print(f"  ... and {len(prod_staff) - 5} more")
    else:
        print("  (none)")
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    differences = []
    if len(local_superadmins) != len(prod_superadmins):
        differences.append(f"⚠️  SuperAdmins: Local={len(local_superadmins)}, Prod={len(prod_superadmins)}")
    if len(local_admins) != len(prod_admins):
        differences.append(f"⚠️  Admins: Local={len(local_admins)}, Prod={len(prod_admins)}")
    if len(local_shops) != len(prod_shops):
        differences.append(f"⚠️  Shops: Local={len(local_shops)}, Prod={len(prod_shops)}")
    if len(local_staff) != len(prod_staff):
        differences.append(f"⚠️  Staff: Local={len(local_staff)}, Prod={len(prod_staff)}")
    
    if differences:
        print("\n🔍 Key Differences Found:")
        for diff in differences:
            print(f"  {diff}")
    else:
        print("\n✅ Databases appear to be in sync!")
    
    print("\n" + "="*80 + "\n")
    
    # Close connections
    local_engine.dispose()
    prod_engine.dispose()

if __name__ == "__main__":
    try:
        compare_databases()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("  1. DATABASE_URL is set in .env (local)")
        print("  2. PRODUCTION_DATABASE_URL is set or provided")
        print("  3. Both databases are accessible")
