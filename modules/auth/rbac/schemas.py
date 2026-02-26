from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ModuleBase(BaseModel):
    module_key: str
    module_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    path: str
    default_enabled: bool = True

class ModuleCreate(ModuleBase):
    pass

class Module(ModuleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class OrganizationModulePermissionBase(BaseModel):
    admin_enabled: bool = True
    staff_enabled: bool = True

class OrganizationModulePermissionCreate(BaseModel):
    organization_id: str
    module_id: int
    admin_enabled: bool = True
    staff_enabled: bool = True

class OrganizationModulePermissionUpdate(BaseModel):
    admin_enabled: Optional[bool] = None
    staff_enabled: Optional[bool] = None

class OrganizationModulePermission(BaseModel):
    id: int
    organization_id: str
    module_id: int
    admin_enabled: bool
    staff_enabled: bool
    configured_by: Optional[str]
    updated_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class ModuleWithPermission(Module):
    admin_enabled: bool
    staff_enabled: bool

class UserPermissionsResponse(BaseModel):
    user_type: str
    organization_id: Optional[str]
    modules: List[ModuleWithPermission]
