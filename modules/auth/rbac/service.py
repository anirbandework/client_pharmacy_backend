from sqlalchemy.orm import Session
from typing import List, Optional
from . import models, schemas

class RBACService:
    
    @staticmethod
    def get_or_create_default_modules(db: Session) -> List[models.Module]:
        """Get all modules, create defaults if not exist"""
        
        # Staff-only modules (default: admin=False, staff=True)
        staff_modules = [
            {"module_key": "billing", "module_name": "Billing System", "icon": "Receipt", "path": "/billing", "description": "Billing and invoicing", "default_admin": False, "default_staff": True},
            {"module_key": "customer_tracking", "module_name": "Customer Management", "icon": "UserCheck", "path": "/customer-tracking", "description": "Track customer purchases", "default_admin": False, "default_staff": True},
            {"module_key": "purchase_invoice", "module_name": "Purchase Orders", "icon": "ShoppingCart", "path": "/purchase-invoice", "description": "Manage purchase invoices", "default_admin": False, "default_staff": True},
            {"module_key": "stock_audit", "module_name": "Inventory Control", "icon": "Package", "path": "/stock-audit", "description": "Stock management and audit", "default_admin": False, "default_staff": True},
            {"module_key": "attendance_staff", "module_name": "My Attendance", "icon": "Clock", "path": "/my-attendance", "description": "Track my attendance", "default_admin": False, "default_staff": True},
            {"module_key": "my_notifications", "module_name": "My Notifications", "icon": "Bell", "path": "/my-notifications", "description": "View notifications", "default_admin": False, "default_staff": True},
            {"module_key": "my_salary", "module_name": "My Salary Info", "icon": "Wallet", "path": "/my-salary", "description": "View salary details", "default_admin": False, "default_staff": True},
        ]
        
        # Admin-only modules (default: admin=True, staff=False)
        admin_modules = [
            {"module_key": "admin_panel", "module_name": "Admin Dashboard", "icon": "Settings", "path": "/admin", "description": "Admin management", "default_admin": True, "default_staff": False},
            {"module_key": "attendance_admin", "module_name": "Attendance Management", "icon": "Clock", "path": "/attendance", "description": "Manage staff attendance", "default_admin": True, "default_staff": False},
            {"module_key": "notifications_admin", "module_name": "Send Notifications", "icon": "Bell", "path": "/notifications", "description": "Send notifications", "default_admin": True, "default_staff": False},
            {"module_key": "salary_management", "module_name": "Payroll Management", "icon": "Wallet", "path": "/salary-management", "description": "Manage staff salaries", "default_admin": True, "default_staff": False},
        ]
        
        all_modules = staff_modules + admin_modules
        
        for module_data in all_modules:
            existing = db.query(models.Module).filter(
                models.Module.module_key == module_data["module_key"]
            ).first()
            
            if not existing:
                # Remove custom fields before creating
                default_admin = module_data.pop("default_admin")
                default_staff = module_data.pop("default_staff")
                module = models.Module(**module_data, default_enabled=False)
                db.add(module)
        
        db.commit()
        return db.query(models.Module).all()
    
    @staticmethod
    def get_user_permissions(db: Session, user_type: str, organization_id: Optional[str]) -> List[schemas.ModuleWithPermission]:
        """Get modules accessible to user based on their role and organization permissions"""
        
        # Ensure default modules exist
        RBACService.get_or_create_default_modules(db)
        
        if user_type == "super_admin":
            # SuperAdmin has access to all modules
            modules = db.query(models.Module).all()
            return [
                schemas.ModuleWithPermission(
                    **module.__dict__,
                    admin_enabled=True,
                    staff_enabled=True
                )
                for module in modules
            ]
        
        if not organization_id:
            return []
        
        # Get organization permissions
        permissions = db.query(
            models.Module,
            models.OrganizationModulePermission
        ).outerjoin(
            models.OrganizationModulePermission,
            (models.Module.id == models.OrganizationModulePermission.module_id) &
            (models.OrganizationModulePermission.organization_id == organization_id)
        ).all()
        
        result = []
        for module, permission in permissions:
            # If no permission record, use default
            if permission:
                admin_enabled = permission.admin_enabled
                staff_enabled = permission.staff_enabled
            else:
                admin_enabled = module.default_enabled
                staff_enabled = module.default_enabled
            
            # Filter based on user type
            if user_type == "admin" and not admin_enabled:
                continue
            if user_type == "staff" and not staff_enabled:
                continue
            
            result.append(schemas.ModuleWithPermission(
                **module.__dict__,
                admin_enabled=admin_enabled,
                staff_enabled=staff_enabled
            ))
        
        return result
    
    @staticmethod
    def update_organization_permissions(
        db: Session,
        organization_id: str,
        module_id: int,
        admin_enabled: bool,
        staff_enabled: bool,
        configured_by: str
    ) -> models.OrganizationModulePermission:
        """Update or create organization module permissions"""
        
        permission = db.query(models.OrganizationModulePermission).filter(
            models.OrganizationModulePermission.organization_id == organization_id,
            models.OrganizationModulePermission.module_id == module_id
        ).first()
        
        if permission:
            permission.admin_enabled = admin_enabled
            permission.staff_enabled = staff_enabled
            permission.configured_by = configured_by
        else:
            permission = models.OrganizationModulePermission(
                organization_id=organization_id,
                module_id=module_id,
                admin_enabled=admin_enabled,
                staff_enabled=staff_enabled,
                configured_by=configured_by
            )
            db.add(permission)
        
        db.commit()
        db.refresh(permission)
        return permission
    
    @staticmethod
    def get_organization_permissions(db: Session, organization_id: str) -> List[dict]:
        """Get all module permissions for an organization"""
        
        # Ensure default modules exist
        RBACService.get_or_create_default_modules(db)
        
        permissions = db.query(
            models.Module,
            models.OrganizationModulePermission
        ).outerjoin(
            models.OrganizationModulePermission,
            (models.Module.id == models.OrganizationModulePermission.module_id) &
            (models.OrganizationModulePermission.organization_id == organization_id)
        ).all()
        
        result = []
        for module, permission in permissions:
            result.append({
                "module": module,
                "admin_enabled": permission.admin_enabled if permission else module.default_enabled,
                "staff_enabled": permission.staff_enabled if permission else module.default_enabled,
                "configured_by": permission.configured_by if permission else None
            })
        
        return result
