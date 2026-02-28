"""
Set default permissions for stock_analytics module
This will enable stock_analytics for admins in all organizations
"""
import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from modules.auth.rbac.models import Module, OrganizationModulePermission
from modules.auth.models import Organization

def set_stock_analytics_permissions():
    db: Session = SessionLocal()
    try:
        # Get stock_analytics module
        module = db.query(Module).filter(Module.module_key == "stock_analytics").first()
        
        if not module:
            print("✗ stock_analytics module not found")
            return
        
        print(f"✓ Found module: {module.module_name} (ID: {module.id})")
        
        # Get all organizations
        organizations = db.query(Organization).all()
        print(f"✓ Found {len(organizations)} organizations")
        
        for org in organizations:
            # Check if permission already exists
            existing = db.query(OrganizationModulePermission).filter(
                OrganizationModulePermission.organization_id == org.id,
                OrganizationModulePermission.module_id == module.id
            ).first()
            
            if existing:
                print(f"  - {org.organization_name}: Permission already exists (admin={existing.admin_enabled}, staff={existing.staff_enabled})")
            else:
                # Create permission with admin=True, staff=False (default for analytics modules)
                permission = OrganizationModulePermission(
                    organization_id=org.id,
                    module_id=module.id,
                    admin_enabled=True,
                    staff_enabled=False,
                    configured_by="system"
                )
                db.add(permission)
                print(f"  + {org.organization_name}: Added permission (admin=True, staff=False)")
        
        db.commit()
        print("\n✓ Successfully configured stock_analytics permissions for all organizations")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    set_stock_analytics_permissions()
