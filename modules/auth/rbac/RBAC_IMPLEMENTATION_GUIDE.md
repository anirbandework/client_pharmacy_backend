# RBAC (Role-Based Access Control) Implementation Guide

## Overview
Dynamic permission system where SuperAdmin can configure which modules are accessible to Admin and Staff users per organization.

## Backend Implementation ✅ COMPLETE

### Database Tables Created:
1. **modules** - Available modules in the system
2. **organization_module_permissions** - Per-organization module access control

### API Endpoints:

#### User Endpoints:
- `GET /api/rbac/my-permissions` - Get accessible modules for current user

#### SuperAdmin Endpoints:
- `GET /api/rbac/modules` - Get all available modules
- `GET /api/rbac/organization/{org_id}/permissions` - Get org permissions
- `PUT /api/rbac/organization/{org_id}/module/{module_id}` - Update permissions
- `POST /api/rbac/organization/{org_id}/reset-defaults` - Reset to defaults

### How It Works:

1. **Default Behavior**: All modules enabled for all organizations
2. **SuperAdmin Configuration**: Can disable specific modules for specific organizations
3. **User Access**: Users only see modules enabled for their organization

### Module Keys:
- `billing` - Staff only
- `customer_tracking` - Staff only
- `purchase_invoice` - Staff only
- `stock_audit` - Staff only
- `attendance` - Both Admin & Staff
- `my_notifications` - Staff only
- `my_salary` - Staff only
- `admin_panel` - Admin only
- `notifications_admin` - Admin only
- `salary_management` - Admin only

## Frontend Implementation Required

### 1. Update Sidebar Component

Replace hardcoded nav items with dynamic API call:

```javascript
// In Sidebar.jsx
import { useState, useEffect } from 'react'
import axios from 'axios'

const [navItems, setNavItems] = useState([])

useEffect(() => {
  fetchPermissions()
}, [])

const fetchPermissions = async () => {
  try {
    const { data } = await axios.get('/api/rbac/my-permissions')
    
    // Map modules to nav items
    const items = data.modules.map(module => ({
      id: module.module_key,
      label: module.module_name,
      path: module.path,
      icon: getIconComponent(module.icon), // Map icon string to component
      roles: [] // Not needed anymore
    }))
    
    setNavItems(items)
  } catch (error) {
    console.error('Failed to fetch permissions:', error)
  }
}

const getIconComponent = (iconName) => {
  const icons = {
    Receipt, UserCheck, ShoppingCart, Package, 
    Clock, Bell, Wallet, Settings
  }
  return icons[iconName] || Settings
}
```

### 2. Create SuperAdmin Permission Management UI

Create a new component for SuperAdmin to manage permissions:

```javascript
// SuperAdminPermissions.jsx
- List all organizations
- For each organization, show all modules with toggle switches
- Toggle admin_enabled / staff_enabled per module
- Save changes via API
```

### 3. Update Main App Routes

Add RBAC routes to main.py:

```python
from modules.auth.rbac import routes as rbac_routes

app.include_router(
    rbac_routes.router,
    prefix="/api/rbac",
    tags=["RBAC"]
)
```

## Migration Status

### Local Database: ✅ COMPLETED
- modules table created with 10 default modules
- organization_module_permissions table created

### Production Database: ✅ COMPLETED
- modules table created with 10 default modules
- organization_module_permissions table created

## Benefits

1. **Flexible**: SuperAdmin can enable/disable modules per organization
2. **Scalable**: Easy to add new modules
3. **Secure**: Backend enforces permissions
4. **Dynamic**: No frontend code changes needed for new modules
5. **Granular**: Separate controls for admin and staff

## Next Steps

1. ✅ Backend RBAC system created
2. ✅ Database tables created
3. ⏳ Add RBAC routes to main.py
4. ⏳ Update frontend Sidebar to use dynamic permissions
5. ⏳ Create SuperAdmin permission management UI
6. ⏳ Test with different organizations

## Example Usage

### SuperAdmin disables "Stock Audit" for Organization A:
```bash
PUT /api/rbac/organization/ORG_A/module/4
{
  "admin_enabled": false,
  "staff_enabled": false
}
```

### Staff from Organization A logs in:
```bash
GET /api/rbac/my-permissions
Response: {
  "modules": [
    // Stock Audit NOT included
    {"module_key": "billing", ...},
    {"module_key": "attendance", ...}
  ]
}
```

Sidebar automatically hides Stock Audit for this organization!
