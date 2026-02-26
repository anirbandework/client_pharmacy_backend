from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from typing import List
from modules.auth.dependencies import get_current_user as get_user_dict, get_current_super_admin
from modules.auth.models import SuperAdmin
from . import schemas, service

router = APIRouter()

# USER ENDPOINTS - Get their accessible modules
@router.get("/my-permissions", response_model=schemas.UserPermissionsResponse)
def get_my_permissions(
    user_dict: dict = Depends(get_user_dict),
    db: Session = Depends(get_db)
):
    """Get modules accessible to current user"""
    
    token_data = user_dict["token_data"]
    user_type = token_data.user_type
    organization_id = token_data.organization_id
    
    modules = service.RBACService.get_user_permissions(db, user_type, organization_id)
    
    return schemas.UserPermissionsResponse(
        user_type=user_type,
        organization_id=organization_id,
        modules=modules
    )

# SUPERADMIN ENDPOINTS - Manage permissions
@router.get("/modules", response_model=List[schemas.Module])
def get_all_modules(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get all available modules (SuperAdmin only)"""
    return service.RBACService.get_or_create_default_modules(db)

@router.get("/organization/{organization_id}/permissions")
def get_organization_permissions(
    organization_id: str,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get module permissions for an organization (SuperAdmin only)"""
    permissions = service.RBACService.get_organization_permissions(db, organization_id)
    
    return {
        "organization_id": organization_id,
        "permissions": [
            {
                "module_key": p["module"].module_key,
                "module_name": p["module"].module_name,
                "icon": p["module"].icon,
                "path": p["module"].path,
                "admin_enabled": p["admin_enabled"],
                "staff_enabled": p["staff_enabled"],
                "configured_by": p["configured_by"]
            }
            for p in permissions
        ]
    }

@router.put("/organization/{organization_id}/module/{module_key}")
def update_module_permission(
    organization_id: str,
    module_key: str,
    permission_data: schemas.OrganizationModulePermissionUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Update module permissions for an organization (SuperAdmin only)"""
    
    # Get module by key
    module = db.query(service.models.Module).filter(
        service.models.Module.module_key == module_key
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    # Get current values if not provided
    existing = db.query(service.models.OrganizationModulePermission).filter(
        service.models.OrganizationModulePermission.organization_id == organization_id,
        service.models.OrganizationModulePermission.module_id == module.id
    ).first()
    
    admin_enabled = permission_data.admin_enabled if permission_data.admin_enabled is not None else (existing.admin_enabled if existing else True)
    staff_enabled = permission_data.staff_enabled if permission_data.staff_enabled is not None else (existing.staff_enabled if existing else True)
    
    permission = service.RBACService.update_organization_permissions(
        db=db,
        organization_id=organization_id,
        module_id=module.id,
        admin_enabled=admin_enabled,
        staff_enabled=staff_enabled,
        configured_by=super_admin.full_name
    )
    
    return {
        "message": "Permissions updated successfully",
        "permission": permission
    }

@router.post("/organization/{organization_id}/reset-defaults")
def reset_to_defaults(
    organization_id: str,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Reset organization permissions to defaults (SuperAdmin only)"""
    
    # Delete all custom permissions for this organization
    db.query(service.models.OrganizationModulePermission).filter(
        service.models.OrganizationModulePermission.organization_id == organization_id
    ).delete()
    
    db.commit()
    
    return {"message": "Permissions reset to defaults"}
