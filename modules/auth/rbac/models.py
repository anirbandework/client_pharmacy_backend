from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

# Tab definitions per module — source of truth for all tab-level permissions.
# Each key maps to a module_key in the modules table.
# Staff modules: purchase_invoice, stock_audit
# Admin modules: invoice_analytics, stock_analytics
MODULE_TABS = {
    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Purchase Invoice (staff): /purchase-invoice
    "purchase_invoice": [
        {"tab_key": "list",          "tab_label": "Invoice List"},
        {"tab_key": "upload",        "tab_label": "Upload Invoice"},
        {"tab_key": "expiry-alerts", "tab_label": "Expiry Alerts"},
        {"tab_key": "suppliers",     "tab_label": "Suppliers"},
        {"tab_key": "dashboard",     "tab_label": "Dashboard"},
    ],

    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Stock Audit (staff): /stock-audit
    "stock_audit": [
        {"tab_key": "items",        "tab_label": "Items"},
        {"tab_key": "racks",        "tab_label": "Racks"},
        {"tab_key": "upload",       "tab_label": "Excel Upload"},
        {"tab_key": "verification", "tab_label": "Upload Verification"},
        {"tab_key": "audit",        "tab_label": "Audit"},
        {"tab_key": "adjustments",  "tab_label": "Adjustments"},
        {"tab_key": "reports",      "tab_label": "Reports"},
        {"tab_key": "ai-analytics",  "tab_label": "AI Analytics"},
        {"tab_key": "dashboard",     "tab_label": "Dashboard"},
        {"tab_key": "consolidated",  "tab_label": "Stock View"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Invoice Analytics (admin): /invoice-analytics
    "invoice_analytics": [
        {"tab_key": "dashboard",     "tab_label": "Dashboard"},
        {"tab_key": "verification",  "tab_label": "Verification"},
        {"tab_key": "expiry-alerts", "tab_label": "Expiry Alerts"},
        {"tab_key": "suppliers",     "tab_label": "Suppliers"},
        {"tab_key": "margins",       "tab_label": "Margin Playground"},
        {"tab_key": "simulator",     "tab_label": "Margin Simulator"},
        {"tab_key": "ai-insights",   "tab_label": "AI Insights"},
    ],

    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Salary (staff): /my-salary
    "my_salary": [
        {"tab_key": "profile", "tab_label": "Profile"},
        {"tab_key": "payment", "tab_label": "Payment Info"},
        {"tab_key": "history", "tab_label": "History"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Salary (admin): /salary-management
    "salary_management": [
        {"tab_key": "dashboard", "tab_label": "Dashboard"},
        {"tab_key": "records",   "tab_label": "Salary Records"},
    ],

    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Attendance (staff): /my-attendance
    "attendance_staff": [
        {"tab_key": "status",  "tab_label": "Status & Today"},
        {"tab_key": "leaves",  "tab_label": "Leave Requests"},
        {"tab_key": "history", "tab_label": "History"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Attendance (admin): /attendance
    "attendance_admin": [
        {"tab_key": "dashboard", "tab_label": "Dashboard"},
        {"tab_key": "connected", "tab_label": "Connected Staff"},
        {"tab_key": "records",   "tab_label": "Attendance Records"},
        {"tab_key": "wifi",      "tab_label": "WiFi Setup"},
        {"tab_key": "report",    "tab_label": "Monthly Report"},
        {"tab_key": "leaves",    "tab_label": "Leave Management"},
        {"tab_key": "settings",  "tab_label": "Settings"},
    ],

    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Notifications (staff): /my-notifications
    "my_notifications": [
        {"tab_key": "inbox",    "tab_label": "Inbox"},
        {"tab_key": "requests", "tab_label": "My Requests"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Notifications (admin): /notifications
    "notifications_admin": [
        {"tab_key": "sent",     "tab_label": "Sent"},
        {"tab_key": "requests", "tab_label": "Staff Requests"},
    ],

    # ── STAFF MODULE ──────────────────────────────────────────────────────────
    # Billing (staff): /billing
    "billing": [
        {"tab_key": "create",    "tab_label": "New Bill"},
        {"tab_key": "history",   "tab_label": "Bill History"},
        {"tab_key": "reports",   "tab_label": "Reports"},
        {"tab_key": "daily",     "tab_label": "Daily Records"},
        {"tab_key": "config",    "tab_label": "Bill Config"},
        {"tab_key": "dashboard", "tab_label": "Dashboard"},
        {"tab_key": "profit",    "tab_label": "Profit Analysis"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Billing Analytics (admin): /billing-analytics
    "billing_analytics": [
        {"tab_key": "analytics", "tab_label": "Analytics"},
        {"tab_key": "insights",  "tab_label": "AI Insights"},
        {"tab_key": "history",   "tab_label": "Bill History"},
        {"tab_key": "reports",   "tab_label": "Reports"},
        {"tab_key": "dashboard", "tab_label": "Dashboard"},
        {"tab_key": "config",    "tab_label": "Bill Config"},
        {"tab_key": "profit",    "tab_label": "Profit Analysis"},
    ],

    # ── ADMIN MODULE ──────────────────────────────────────────────────────────
    # Stock Analytics (admin): /stock-analytics
    "stock_analytics": [
        {"tab_key": "items",               "tab_label": "Items"},
        {"tab_key": "racks",               "tab_label": "Racks"},
        {"tab_key": "reports",             "tab_label": "Reports"},
        {"tab_key": "ai-analytics",        "tab_label": "AI Analytics"},
        {"tab_key": "dashboard",           "tab_label": "Dashboard"},
        {"tab_key": "discrepancies",       "tab_label": "Discrepancies"},
        {"tab_key": "excel-verification",  "tab_label": "Excel Verification"},
        {"tab_key": "consolidated",        "tab_label": "Stock View"},
    ],
}

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
    created_at = Column(DateTime, default=datetime.now)
    
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
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    module = relationship("Module", back_populates="org_permissions")


class OrganizationTabPermission(Base):
    """Tab-level permissions per organization per module"""
    __tablename__ = "organization_tab_permissions"
    __table_args__ = (
        UniqueConstraint('organization_id', 'module_key', 'tab_key', name='unique_org_module_tab'),
    )

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(String, nullable=False, index=True)
    module_key = Column(String, nullable=False)
    tab_key = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)

    # Audit
    configured_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
