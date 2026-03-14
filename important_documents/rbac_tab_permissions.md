# RBAC Tab-Level Permissions — Implementation Guide

## Overview

The RBAC system has two levels:
1. **Module-level** — SuperAdmin enables/disables entire pages per org (existing system)
2. **Tab-level** — SuperAdmin enables/disables individual tabs within a page per org (added on top)

This document explains how to extend tab-level permissions to any new page.

---

## Architecture

### How it works end-to-end

1. SuperAdmin opens the RBAC page → selects an org → clicks **Tabs** on a module → toggles individual tabs ON/OFF
2. Each toggle calls `PUT /api/rbac/organization/{org_id}/module/{module_key}/tab/{tab_key}`
3. Toggle state is stored in the `organization_tab_permissions` DB table
4. When a user loads a page, the frontend hook `useTabPermissions(moduleKey)` calls `GET /api/rbac/my-permissions`
5. That endpoint now returns `tab_permissions: {tab_key: bool}` per module
6. The page filters its `tabs` array with `isTabEnabled(tab.id)` — disabled tabs simply don't render
7. **Default behaviour**: if no DB record exists for a tab → it defaults to `true` (visible). Fully backwards compatible.
8. **SuperAdmin** always sees all tabs regardless of settings.

---

## Files Changed (and what each one does)

### Backend

| File | What was changed |
|------|-----------------|
| `modules/auth/rbac/models.py` | Added `MODULE_TABS` dict (tab definitions) + `OrganizationTabPermission` SQLAlchemy model |
| `modules/auth/rbac/schemas.py` | Added `TabPermission`, `TabPermissionUpdate`, `ModuleTabsResponse` schemas; added `tab_permissions: Optional[dict]` field to `ModuleWithPermission` |
| `modules/auth/rbac/service.py` | Added `get_tab_permissions()` and `update_tab_permission()` static methods; updated `get_user_permissions()` to include `tab_permissions` in each module's response |
| `modules/auth/rbac/routes.py` | Added two new endpoints: `GET .../module/{module_key}/tabs` and `PUT .../module/{module_key}/tab/{tab_key}` |

### Frontend

| File | What was changed |
|------|-----------------|
| `src/features/RBAC/services/rbacApi.js` | Added `getModuleTabs(orgId, moduleKey)` and `updateTabPermission(orgId, moduleKey, tabKey, enabled)` |
| `src/features/RBAC/components/OrganizationPermissions.jsx` | Added state for expanded tabs, lazy tab loading, toggle handler; added purple **Tabs** button on each tabbed module that expands a grid of per-tab toggles |
| `src/hooks/useTabPermissions.js` | New reusable hook — fetches `/api/rbac/my-permissions`, exposes `isTabEnabled(tabKey)` |
| `src/features/PurchaseInvoice/admin_purchase_invoice_page.jsx` | Added `useTabPermissions('invoice_analytics')`, renamed `tabs` → `allTabs`, added filter + `useEffect` to reset `activeTab` |
| `src/features/PurchaseInvoice/staff_purchase_invoice_page.jsx` | Added `useTabPermissions('purchase_invoice')`, same pattern |
| `src/features/StockAudit/admin_stock_audit_page.jsx` | Added `useTabPermissions('stock_analytics')`, same pattern |
| `src/features/StockAudit/staff_stock_audit_page.jsx` | Added `useTabPermissions('stock_audit')`, same pattern |

---

## How to Add Tab Permissions to a NEW Page

Follow these 3 steps every time a new page needs tab-level permissions.

---

### Step 1 — Register the tabs in the backend

Open `modules/auth/rbac/models.py` and add an entry to `MODULE_TABS`:

```python
# ── STAFF MODULE ──────────────────────────────────────────────────────────
# My New Page (staff): /my-new-page
"my_module_key": [
    {"tab_key": "tab-one",   "tab_label": "Tab One"},
    {"tab_key": "tab-two",   "tab_label": "Tab Two"},
    {"tab_key": "tab-three", "tab_label": "Tab Three"},
],
```

Rules:
- `module_key` must exactly match the `module_key` value in the `modules` DB table (see `service.py` `get_or_create_default_modules`)
- `tab_key` must exactly match the `id` field used in the page's `tabs` array
- Comment whether it is a Staff or Admin module and include its route path

---

### Step 2 — Register in the RBAC UI

Open `src/features/RBAC/components/OrganizationPermissions.jsx` and add the new `module_key` to the `TABBED_MODULES` set:

```js
const TABBED_MODULES = new Set([
  'purchase_invoice',
  'invoice_analytics',
  'stock_analytics',
  'stock_audit',
  'my_module_key',   // ← add here
])
```

That's all for the UI — the **Tabs** button and the tab toggle grid are rendered automatically for any module in this set.

---

### Step 3 — Update the page component

Open the page JSX file and make these changes:

**A. Import the hook and `useEffect`** (at the top):
```jsx
import { useState, useEffect } from 'react'
import useTabPermissions from '../../hooks/useTabPermissions'
// adjust the relative path based on where the page file lives
```

**B. Add the hook call, filter, and active-tab reset** (inside the component, before the return):
```jsx
const { isTabEnabled, isLoaded } = useTabPermissions('my_module_key')

const allTabs = [
  { id: 'tab-one',   label: 'Tab One',   icon: SomeIcon },
  { id: 'tab-two',   label: 'Tab Two',   icon: OtherIcon },
  { id: 'tab-three', label: 'Tab Three', icon: AnotherIcon },
]
const tabs = allTabs.filter(t => isTabEnabled(t.id))  // ← was just `tabs = [...]` before

// Reset activeTab to first permitted tab if the current default is not permitted
useEffect(() => {
  if (isLoaded && tabs.length > 0 && !tabs.find(t => t.id === activeTab)) {
    setActiveTab(tabs[0].id)
  }
}, [isLoaded, tabs.length])
```

**Why the `useEffect` is required:** `activeTab` is initialized to a hardcoded default (e.g. `'list'`). If that tab is disabled for a user, the tab bar shows only their permitted tabs but the content area still renders the default tab's component — they go out of sync. The `useEffect` fires once permissions finish loading (`isLoaded` becomes `true`) and resets `activeTab` to the first available tab if the current one is no longer permitted.

The rest of the page (tab bar render, content render) uses `tabs` and works unchanged.

---

## DB Table Created

```
organization_tab_permissions
├── id                (PK)
├── organization_id   (indexed)
├── module_key        (e.g. "purchase_invoice")
├── tab_key           (e.g. "upload")
├── enabled           (boolean, default true)
├── configured_by     (SuperAdmin name, audit trail)
├── updated_at
└── created_at

Unique constraint: (organization_id, module_key, tab_key)
```

---

## API Endpoints Added

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/rbac/organization/{org_id}/module/{module_key}/tabs` | SuperAdmin | Get all tabs for a module with enabled state |
| `PUT` | `/api/rbac/organization/{org_id}/module/{module_key}/tab/{tab_key}` | SuperAdmin | Toggle a single tab on/off |

The existing `GET /api/rbac/my-permissions` endpoint now also returns `tab_permissions: {tab_key: bool}` inside each module object.

---

## The `useTabPermissions` Hook

Location: `src/hooks/useTabPermissions.js`

```js
const { isTabEnabled, isLoaded } = useTabPermissions('module_key')
```

- Calls `/api/rbac/my-permissions` once on mount
- `isTabEnabled(tabKey)` returns `true` if the tab is enabled (or has no DB record)
- While loading (`isLoaded = false`), `isTabEnabled` returns `true` — no flash of missing tabs
- SuperAdmin always gets `true` for all tabs (bypasses the fetch)

---

## Current Modules with Tab Permissions

| module_key | Role | Page | # Tabs |
|-----------|------|------|--------|
| `purchase_invoice` | Staff | `/purchase-invoice` | 5 |
| `stock_audit` | Staff | `/stock-audit` | 9 |
| `invoice_analytics` | Admin | `/invoice-analytics` | 7 |
| `stock_analytics` | Admin | `/stock-analytics` | 7 |

---

## Important Notes

- **No migration needed** for existing orgs — missing DB records default to `true` (all tabs visible)
- **Reset to Defaults** (`POST /api/rbac/organization/{org_id}/reset-defaults`) currently only deletes `OrganizationModulePermission` records. Tab permission records are NOT deleted on reset (tabs stay as-is). If you want reset to also clear tabs, update the reset endpoint in `routes.py` to also delete from `organization_tab_permissions`.
- Tab permissions only control **visibility** (the tab button disappears). They do not block direct URL navigation or API calls — this is frontend-only enforcement, consistent with the rest of the RBAC system.
- The `MODULE_TABS` dict in `models.py` is the single source of truth. If you rename a tab key here, update the corresponding page component too.
