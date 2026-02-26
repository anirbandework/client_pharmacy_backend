-- Migration: Create RBAC tables for dynamic permissions
-- Run this on both LOCAL and PRODUCTION databases

-- Create modules table
CREATE TABLE modules (
    id SERIAL PRIMARY KEY,
    module_key VARCHAR UNIQUE NOT NULL,
    module_name VARCHAR NOT NULL,
    description VARCHAR,
    icon VARCHAR,
    path VARCHAR NOT NULL,
    default_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_modules_module_key ON modules(module_key);

-- Create organization_module_permissions table
CREATE TABLE organization_module_permissions (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR NOT NULL,
    module_id INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    admin_enabled BOOLEAN DEFAULT TRUE,
    staff_enabled BOOLEAN DEFAULT TRUE,
    configured_by VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_org_module UNIQUE (organization_id, module_id)
);

CREATE INDEX idx_org_permissions_org_id ON organization_module_permissions(organization_id);
CREATE INDEX idx_org_permissions_module_id ON organization_module_permissions(module_id);

-- Insert default modules
INSERT INTO modules (module_key, module_name, icon, path, description, default_enabled) VALUES
('billing', 'Billing', 'Receipt', '/billing', 'Billing and invoicing', TRUE),
('customer_tracking', 'Customer Tracking', 'UserCheck', '/customer-tracking', 'Track customer purchases', TRUE),
('purchase_invoice', 'Purchase Invoice', 'ShoppingCart', '/purchase-invoice', 'Manage purchase invoices', TRUE),
('stock_audit', 'Stock Audit', 'Package', '/stock-audit', 'Stock management and audit', TRUE),
('attendance', 'Attendance', 'Clock', '/attendance', 'Staff attendance tracking', TRUE),
('my_notifications', 'Notifications', 'Bell', '/my-notifications', 'View notifications', TRUE),
('my_salary', 'My Salary', 'Wallet', '/my-salary', 'View salary details', TRUE),
('admin_panel', 'Admin Panel', 'Settings', '/admin', 'Admin management', TRUE),
('notifications_admin', 'Notifications', 'Bell', '/notifications', 'Send notifications', TRUE),
('salary_management', 'Salary Management', 'Wallet', '/salary-management', 'Manage staff salaries', TRUE);

-- Verification
SELECT * FROM modules;
SELECT COUNT(*) FROM modules;
