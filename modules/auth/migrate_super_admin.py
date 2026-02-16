"""
Migration script to add SuperAdmin table and organization_id to Admin table
Run this once to update the database schema
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    # Fix Railway's postgres:// to postgresql://
    database_url = settings.database_url
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        print("🔄 Starting SuperAdmin migration...")
        
        # Create super_admins table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS super_admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR UNIQUE NOT NULL,
                    password_hash VARCHAR NOT NULL,
                    full_name VARCHAR NOT NULL,
                    phone VARCHAR(15) UNIQUE NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("✅ Created super_admins table")
        except Exception as e:
            print(f"⚠️  super_admins table: {e}")
        
        # Add organization_id to admins table
        try:
            conn.execute(text("""
                ALTER TABLE admins ADD COLUMN organization_id VARCHAR
            """))
            conn.commit()
            print("✅ Added organization_id to admins")
        except Exception as e:
            print(f"⚠️  organization_id column: {e}")
        
        # Add created_by_super_admin to admins table
        try:
            conn.execute(text("""
                ALTER TABLE admins ADD COLUMN created_by_super_admin VARCHAR
            """))
            conn.commit()
            print("✅ Added created_by_super_admin to admins")
        except Exception as e:
            print(f"⚠️  created_by_super_admin column: {e}")
        
        # Set default organization_id for existing admins
        try:
            conn.execute(text("""
                UPDATE admins 
                SET organization_id = 'ORG-DEFAULT-001',
                    created_by_super_admin = 'System Migration'
                WHERE organization_id IS NULL
            """))
            conn.commit()
            print("✅ Set default organization_id for existing admins")
        except Exception as e:
            print(f"⚠️  Setting defaults: {e}")
        
        # Create index on organization_id
        try:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_admins_organization_id 
                ON admins(organization_id)
            """))
            conn.commit()
            print("✅ Created index on organization_id")
        except Exception as e:
            print(f"⚠️  Index creation: {e}")
        
        print("\n✅ Migration completed!")
        print("\n📝 Next steps:")
        print("1. Create a SuperAdmin account using POST /api/auth/super-admin/register")
        print("2. Login as SuperAdmin")
        print("3. Create Admins with organization_id using POST /api/auth/super-admin/admins")

if __name__ == "__main__":
    migrate()
