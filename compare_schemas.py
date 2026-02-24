"""
Compare local PostgreSQL schema with Railway PostgreSQL schema
Shows all differences in tables, columns, and constraints
"""
from sqlalchemy import create_engine, inspect, text
from app.core.config import settings
import sys

def get_schema_info(engine):
    """Extract complete schema information from database"""
    inspector = inspect(engine)
    schema = {}
    
    for table_name in inspector.get_table_names():
        columns = {}
        for col in inspector.get_columns(table_name):
            columns[col['name']] = {
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': str(col['default']) if col['default'] else None
            }
        
        schema[table_name] = {
            'columns': columns,
            'primary_keys': inspector.get_pk_constraint(table_name),
            'foreign_keys': inspector.get_foreign_keys(table_name),
            'indexes': inspector.get_indexes(table_name),
            'unique_constraints': inspector.get_unique_constraints(table_name)
        }
    
    return schema

def compare_schemas(local_schema, railway_schema):
    """Compare two schemas and return differences"""
    differences = {
        'tables_only_in_local': [],
        'tables_only_in_railway': [],
        'column_differences': {},
        'constraint_differences': {}
    }
    
    # Find tables only in local
    local_tables = set(local_schema.keys())
    railway_tables = set(railway_schema.keys())
    
    differences['tables_only_in_local'] = list(local_tables - railway_tables)
    differences['tables_only_in_railway'] = list(railway_tables - local_tables)
    
    # Compare common tables
    common_tables = local_tables & railway_tables
    
    for table in common_tables:
        local_cols = set(local_schema[table]['columns'].keys())
        railway_cols = set(railway_schema[table]['columns'].keys())
        
        cols_only_local = local_cols - railway_cols
        cols_only_railway = railway_cols - local_cols
        
        if cols_only_local or cols_only_railway:
            differences['column_differences'][table] = {
                'only_in_local': list(cols_only_local),
                'only_in_railway': list(cols_only_railway),
                'type_differences': []
            }
            
            # Check type differences for common columns
            common_cols = local_cols & railway_cols
            for col in common_cols:
                local_type = local_schema[table]['columns'][col]['type']
                railway_type = railway_schema[table]['columns'][col]['type']
                local_nullable = local_schema[table]['columns'][col]['nullable']
                railway_nullable = railway_schema[table]['columns'][col]['nullable']
                
                if local_type != railway_type or local_nullable != railway_nullable:
                    differences['column_differences'][table]['type_differences'].append({
                        'column': col,
                        'local_type': local_type,
                        'railway_type': railway_type,
                        'local_nullable': local_nullable,
                        'railway_nullable': railway_nullable
                    })
    
    return differences

def print_differences(differences):
    """Pretty print schema differences"""
    print("\n" + "="*80)
    print("DATABASE SCHEMA COMPARISON: LOCAL vs RAILWAY")
    print("="*80)
    
    # Tables only in local
    if differences['tables_only_in_local']:
        print("\n🔵 TABLES ONLY IN LOCAL DATABASE:")
        for table in differences['tables_only_in_local']:
            print(f"  - {table}")
    
    # Tables only in railway
    if differences['tables_only_in_railway']:
        print("\n🟠 TABLES ONLY IN RAILWAY DATABASE:")
        for table in differences['tables_only_in_railway']:
            print(f"  - {table}")
    
    # Column differences
    if differences['column_differences']:
        print("\n🔴 COLUMN DIFFERENCES:")
        for table, diffs in differences['column_differences'].items():
            print(f"\n  Table: {table}")
            
            if diffs['only_in_local']:
                print(f"    ✓ Columns only in LOCAL:")
                for col in diffs['only_in_local']:
                    print(f"      - {col}")
            
            if diffs['only_in_railway']:
                print(f"    ✗ Columns only in RAILWAY:")
                for col in diffs['only_in_railway']:
                    print(f"      - {col}")
            
            if diffs['type_differences']:
                print(f"    ⚠️  Type/Nullable differences:")
                for diff in diffs['type_differences']:
                    print(f"      - {diff['column']}:")
                    print(f"        Local:   {diff['local_type']} (nullable={diff['local_nullable']})")
                    print(f"        Railway: {diff['railway_type']} (nullable={diff['railway_nullable']})")
    
    # Summary
    print("\n" + "="*80)
    print("MIGRATION NEEDED:")
    print("="*80)
    
    has_differences = (
        differences['tables_only_in_local'] or 
        differences['tables_only_in_railway'] or 
        differences['column_differences']
    )
    
    if not has_differences:
        print("✅ No differences found! Schemas are in sync.")
    else:
        print("⚠️  Differences found! You need to migrate Railway database.")
        print("\nGenerate migration SQL? (This will create migration commands)")

def generate_migration_sql(differences, local_schema):
    """Generate SQL migration commands"""
    sql_commands = []
    
    # Add missing columns to Railway
    for table, diffs in differences['column_differences'].items():
        if diffs['only_in_local']:
            for col in diffs['only_in_local']:
                col_info = local_schema[table]['columns'][col]
                nullable = "NULL" if col_info['nullable'] else "NOT NULL"
                default = f"DEFAULT {col_info['default']}" if col_info['default'] else ""
                sql_commands.append(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_info['type']} {default};"
                )
        
        # Drop columns that exist in Railway but not in local
        if diffs['only_in_railway']:
            for col in diffs['only_in_railway']:
                sql_commands.append(
                    f"ALTER TABLE {table} DROP COLUMN IF EXISTS {col};"
                )
    
    return sql_commands

def main():
    print("Connecting to databases...")
    
    # Local database
    local_url = settings.database_url
    if local_url.startswith("postgres://"):
        local_url = local_url.replace("postgres://", "postgresql://", 1)
    
    # Railway database - get from user input
    print("\nEnter Railway PostgreSQL connection string:")
    print("(Get it from Railway Dashboard → PostgreSQL → Connect → Connection URL)")
    railway_url = input("Railway URL: ").strip()
    
    if not railway_url:
        print("❌ Railway URL is required!")
        sys.exit(1)
    
    if railway_url.startswith("postgres://"):
        railway_url = railway_url.replace("postgres://", "postgresql://", 1)
    
    try:
        # Connect to both databases
        print("\n🔄 Connecting to local database...")
        local_engine = create_engine(local_url)
        
        print("🔄 Connecting to Railway database...")
        railway_engine = create_engine(railway_url)
        
        # Get schemas
        print("🔄 Extracting local schema...")
        local_schema = get_schema_info(local_engine)
        
        print("🔄 Extracting Railway schema...")
        railway_schema = get_schema_info(railway_engine)
        
        # Compare
        print("🔄 Comparing schemas...")
        differences = compare_schemas(local_schema, railway_schema)
        
        # Print results
        print_differences(differences)
        
        # Generate migration SQL
        if differences['column_differences']:
            print("\n" + "="*80)
            print("MIGRATION SQL COMMANDS:")
            print("="*80)
            sql_commands = generate_migration_sql(differences, local_schema)
            for cmd in sql_commands:
                print(cmd)
            
            print("\n💾 Save migration SQL to file? (y/n): ", end="")
            save = input().strip().lower()
            if save == 'y':
                with open('railway_migration.sql', 'w') as f:
                    f.write("-- Railway Database Migration\n")
                    f.write("-- Generated automatically\n\n")
                    for cmd in sql_commands:
                        f.write(cmd + "\n")
                print("✅ Saved to railway_migration.sql")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
