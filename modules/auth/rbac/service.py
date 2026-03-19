from sqlalchemy.orm import Session
from typing import List, Optional, Dict
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
            {"module_key": "attendance_admin", "module_name": "Attendance Handling", "icon": "Clock", "path": "/attendance", "description": "Manage staff attendance", "default_admin": True, "default_staff": False},
            {"module_key": "notifications_admin", "module_name": "Send Notifications", "icon": "Bell", "path": "/notifications", "description": "Send notifications", "default_admin": True, "default_staff": False},
            {"module_key": "salary_management", "module_name": "Payroll Management", "icon": "Wallet", "path": "/salary-management", "description": "Manage staff salaries", "default_admin": True, "default_staff": False},
            {"module_key": "invoice_analytics", "module_name": "Invoice Analytics", "icon": "Brain", "path": "/invoice-analytics", "description": "AI-powered invoice insights", "default_admin": True, "default_staff": False},
            {"module_key": "stock_analytics", "module_name": "Stock Analytics", "icon": "BarChart3", "path": "/stock-analytics", "description": "Stock audit analytics & insights", "default_admin": True, "default_staff": False},
            {"module_key": "billing_analytics", "module_name": "Billing Analytics", "icon": "LineChart", "path": "/billing-analytics", "description": "Revenue & expense analytics with AI insights", "default_admin": True, "default_staff": False},
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
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            # If commit fails (e.g., duplicate key), just continue
            pass
        
        return db.query(models.Module).all()
    
    @staticmethod
    def get_tab_permissions(db: Session, organization_id: str, module_key: str) -> Dict[str, bool]:
        """Get tab permissions for a module as {tab_key: enabled} dict. Defaults to True if not set."""
        tab_defs = models.MODULE_TABS.get(module_key, [])
        if not tab_defs:
            return {}

        tab_records = db.query(models.OrganizationTabPermission).filter(
            models.OrganizationTabPermission.organization_id == organization_id,
            models.OrganizationTabPermission.module_key == module_key
        ).all()

        tab_map = {r.tab_key: r.enabled for r in tab_records}

        # Fill defaults: if no record exists for a tab, it defaults to True
        return {t["tab_key"]: tab_map.get(t["tab_key"], True) for t in tab_defs}

    @staticmethod
    def update_tab_permission(
        db: Session,
        organization_id: str,
        module_key: str,
        tab_key: str,
        enabled: bool,
        configured_by: str
    ) -> models.OrganizationTabPermission:
        """Create or update a single tab permission."""
        record = db.query(models.OrganizationTabPermission).filter(
            models.OrganizationTabPermission.organization_id == organization_id,
            models.OrganizationTabPermission.module_key == module_key,
            models.OrganizationTabPermission.tab_key == tab_key
        ).first()

        if record:
            record.enabled = enabled
            record.configured_by = configured_by
        else:
            record = models.OrganizationTabPermission(
                organization_id=organization_id,
                module_key=module_key,
                tab_key=tab_key,
                enabled=enabled,
                configured_by=configured_by
            )
            db.add(record)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_user_permissions(db: Session, user_type: str, organization_id: Optional[str]) -> List[schemas.ModuleWithPermission]:
        """Get modules accessible to user based on their role and organization permissions"""

        # Ensure default modules exist
        RBACService.get_or_create_default_modules(db)

        if user_type == "super_admin":
            # SuperAdmin has access to all modules and all tabs
            modules = db.query(models.Module).all()
            return [
                schemas.ModuleWithPermission(
                    **module.__dict__,
                    admin_enabled=True,
                    staff_enabled=True,
                    tab_permissions={t["tab_key"]: True for t in models.MODULE_TABS.get(module.module_key, [])}
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

        # Modules that are relevant per user type (used to decide which locked modules to surface)
        ADMIN_MODULE_KEYS = {
            'admin_panel', 'attendance_admin', 'notifications_admin',
            'salary_management', 'invoice_analytics', 'stock_analytics', 'billing_analytics'
        }
        STAFF_MODULE_KEYS = {
            'billing', 'customer_tracking', 'purchase_invoice',
            'stock_audit', 'attendance_staff', 'my_notifications', 'my_salary'
        }

        result = []
        for module, permission in permissions:
            # If no permission record, use default
            if permission:
                admin_enabled = permission.admin_enabled
                staff_enabled = permission.staff_enabled
            else:
                admin_enabled = module.default_enabled
                staff_enabled = module.default_enabled

            # Determine if this module is relevant for the requesting user type
            if user_type == "admin" and module.module_key not in ADMIN_MODULE_KEYS:
                continue  # Don't show staff-only modules to admin
            if user_type == "staff" and module.module_key not in STAFF_MODULE_KEYS:
                continue  # Don't show admin-only modules to staff

            # Determine if this module is locked for the user (org doesn't have access)
            is_locked = (user_type == "admin" and not admin_enabled) or \
                        (user_type == "staff" and not staff_enabled)

            tab_permissions = RBACService.get_tab_permissions(db, organization_id, module.module_key)

            result.append(schemas.ModuleWithPermission(
                **module.__dict__,
                admin_enabled=admin_enabled,
                staff_enabled=staff_enabled,
                tab_permissions=tab_permissions,
                locked=is_locked
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
