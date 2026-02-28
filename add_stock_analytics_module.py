"""
Add stock_analytics module to RBAC
Run this script to add the new module without restarting the server
"""
import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from modules.auth.rbac.models import Module

def add_stock_analytics_module():
    db: Session = SessionLocal()
    try:
        # Check if module already exists
        existing = db.query(Module).filter(Module.module_key == "stock_analytics").first()
        
        if existing:
            print("✓ stock_analytics module already exists")
            return
        
        # Create new module
        module = Module(
            module_key="stock_analytics",
            module_name="Stock Analytics",
            icon="BarChart3",
            path="/stock-analytics",
            description="Stock audit analytics & insights",
            default_enabled=False
        )
        
        db.add(module)
        db.commit()
        print("✓ Successfully added stock_analytics module")
        print(f"  ID: {module.id}")
        print(f"  Name: {module.module_name}")
        print(f"  Path: {module.path}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_stock_analytics_module()
