from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class Module(Base):
    """Available modules in the system"""
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    module_key = Column(String, unique=True, nullable=False, index=True)  # e.g., 'billing', 'stock_audit'
    module_name = Column(String, nullable=False)  # Display name
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)  # Icon name for frontend
    path = Column(String, nullable=False)  # Route path
    default_enabled = Column(Boolean, default=False)  # Default state for new orgs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    org_permissions = relationship("OrganizationModulePermission", back_populates="module", cascade="all, delete-orphan")

class OrganizationModulePermission(Base):
    """Module permissions per organization"""
    __tablename__ = "organization_module_permissions"
    __table_args__ = (
        UniqueConstraint('organization_id', 'module_id', name='unique_org_module'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    
    # Permissions
    admin_enabled = Column(Boolean, default=True)  # Can admin access this module?
    staff_enabled = Column(Boolean, default=True)  # Can staff access this module?
    
    # Audit
    configured_by = Column(String, nullable=True)  # SuperAdmin who configured
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    module = relationship("Module", back_populates="org_permissions")
