# Auth System & Data Privacy Model

## 1. User Hierarchy

```
SuperAdmin
  └── creates → Admin (has organization_id)
                  └── creates → Shop (has organization_id)
                                  └── creates → Staff (has shop_id FK)
SuperAdmin (separate flow)
  └── creates → Distributor (many-to-many with Shops)
```

There are four user types: `super_admin`, `admin`, `staff`, `distributor`.

---

## 2. Model Definitions

### SuperAdmin (`super_admins` table)
- Global platform owner. No organization_id.
- Creates Admins and Distributors.
- Auth: email + password (no OTP, legacy flow).

### Admin (`admins` table)
| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `organization_id` | **string** | Shared across multiple admins of the same org. NOT a FK — a string tag. |
| `full_name` | string | |
| `phone` | string | Required for OTP login |
| `email` | string | Optional |
| `is_active` | bool | |
| `created_by_super_admin` | string | Name of SuperAdmin who created |

**Key point:** Multiple admins can share the same `organization_id`. They all see the same shops and data.

### Shop (`shops` table)
| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `organization_id` | **string** | Must match the admin's organization_id |
| `shop_name` | string | |
| `shop_code` | string | Unique within org |
| `is_active` | bool | |

**Key point:** One org can have many shops. `shop.organization_id` is the bridge between Admin and Shop.

### Staff (`staff` table)
| Field | Type | Notes |
|---|---|---|
| `id` | int | PK |
| `shop_id` | **int FK** | Points to `shops.id` — hard scoped to ONE shop |
| `name` | string | |
| `phone` | string | Required for OTP login |
| `role` | string | `"staff"` or `"shop_manager"` |
| `can_manage_staff` | bool | Permission flag |
| `can_view_analytics` | bool | Permission flag |
| `can_manage_inventory` | bool | Permission flag |
| `can_manage_customers` | bool | Permission flag |
| `is_active` | bool | |

**Key point:** Staff belongs to exactly one shop. They can NEVER access data from another shop.
`shop_manager` role bypasses all permission flag checks.

### Distributor (`distributors` table)
- Many-to-many with `shops` via `distributor_shops` association table.
- Can serve shops across different organizations.
- Created by SuperAdmin only.

---

## 3. JWT Token Payloads

```python
# Admin token
{
    "user_id": int,
    "user_type": "admin",
    "organization_id": str,   # admin's org
    "email": str,
    "user_name": str,
    "exp": datetime
}

# Staff token
{
    "user_id": int,
    "user_type": "staff",
    "organization_id": str,   # derived from staff.shop.organization_id
    "shop_code": str,          # staff's shop code
    "email": str,
    "user_name": str,
    "exp": datetime
}
```

Token algorithm: HS256. Expiry: 24 hours. Secret: `JWT_SECRET_KEY` env var.

---

## 4. Dependency Functions (FastAPI)

### `get_current_admin(current_user)` → `Admin`
Returns the `Admin` model instance. Available fields: `admin.id`, `admin.organization_id`, `admin.full_name`.

### `get_current_staff(current_user)` → `Staff`
Returns the `Staff` model instance. Available fields: `staff.id`, `staff.shop_id`, `staff.name`, `staff.role`, permission flags, `staff.shop` (relationship).

### `get_current_user(credentials, db)` → `dict | tuple`
Base dependency. In some modules (e.g. stock_audit_v2) this is wrapped to return `(staff, shop_id)` tuple for convenience. Always verify how the local module uses it.

### `require_permission(permission: str)`
Validates staff permission flags. `shop_manager` bypasses all checks.

---

## 5. Data Privacy Rules — The Golden Rules

### Staff endpoints — scope by `shop_id`
Staff can only see data belonging to their own shop.

```python
# CORRECT pattern for staff endpoints
staff, shop_id = current_user  # shop_id = staff.shop_id

db.query(SomeModel).filter(SomeModel.shop_id == shop_id)

# For related models (PurchaseItem, SaleItem, etc.) always add shop_id even if
# scoping through a FK is "technically safe" — be explicit
db.query(PurchaseItem).filter(
    PurchaseItem.stock_item_id == item_id,
    PurchaseItem.shop_id == shop_id   # defense-in-depth
)
```

### Admin endpoints — scope by `organization_id` via Shop join
Admin can only see data from shops in their organization. Because most tables store `shop_id` (not `organization_id`), you must JOIN through Shop.

```python
# CORRECT pattern for admin endpoints
admin = Depends(get_current_admin)  # admin.organization_id available

# For tables that have shop_id directly:
db.query(SomeModel)\
  .join(Shop, SomeModel.shop_id == Shop.id)\
  .filter(Shop.organization_id == admin.organization_id)

# For tables that store organization_id directly (rare):
db.query(SomeModel).filter(SomeModel.organization_id == admin.organization_id)
```

### Fetch-by-ID pattern — always add org/shop filter
Never fetch a record by bare `id` in admin or staff routes. Always scope:

```python
# WRONG — any admin can read any org's record by guessing the ID
upload = db.query(ExcelUpload).filter(ExcelUpload.id == upload_id).first()

# CORRECT
upload = db.query(ExcelUpload)\
  .join(Shop, ExcelUpload.shop_id == Shop.id)\
  .filter(ExcelUpload.id == upload_id, Shop.organization_id == admin.organization_id)\
  .first()
```

---

## 6. Organization ID — Important Quirks

- `organization_id` is a **string**, not an integer FK. Example: `"ORG-001"`, `"DEMO-ORG-001"`.
- It is shared across multiple admin accounts. Any admin with the same `organization_id` has equal access.
- `Shop.organization_id` is the bridge. Admin → Shop is NOT a foreign key; it's a string match.
- Staff do NOT have `organization_id` on their model directly. You get it via `staff.shop.organization_id` (relationship traversal).

---

## 7. Cross-Module Privacy Patterns

When module A queries data that belongs to module B, the same scoping rules apply.

### Example: invoice_analyzer_v2 → stock_audit_v2
Invoice endpoints scope by `shop_id` (staff) or by org via Shop join (admin). When syncing to stock, `shop_id` is passed explicitly so stock items are always created under the correct shop.

### Example: admin_routes.py in any module
Admin can optionally accept a `shop_id: Optional[int]` query param to narrow results to a specific shop — but the base filter MUST always be `Shop.organization_id == admin.organization_id` first, then optionally add `AND shop_id == shop_id`.

```python
# Pattern for admin endpoints that support optional shop_id filter
query = (
    db.query(SomeModel)
    .join(Shop, SomeModel.shop_id == Shop.id)
    .filter(Shop.organization_id == admin.organization_id)  # always required
)
if shop_id:
    query = query.filter(SomeModel.shop_id == shop_id)  # optional narrowing
```

---

## 8. Permission Flags (Staff)

| Flag | Default | Meaning |
|---|---|---|
| `can_manage_staff` | False | Can create/edit other staff |
| `can_view_analytics` | True | Can see reports and dashboards |
| `can_manage_inventory` | True | Can manage stock |
| `can_manage_customers` | True | Can manage customer records |

`role == "shop_manager"` bypasses all flags. Use `require_permission("manage_inventory")` etc. as FastAPI dependency where needed.

---

## 9. Master Bypass (Dev/Localhost Only)

```
MASTER_PHONE    = "+919383169659"
MASTER_PASSWORD = "test@123"
MASTER_OTP      = "999999"
```

Only active when `ENVIRONMENT` env var is `"development"` or `"localhost"`. Never expose in production.

---

## 10. Checklist — Before Writing Any New Endpoint

- [ ] Is this a staff route? → filter all queries by `shop_id`
- [ ] Is this a admin route? → filter all queries by `Shop.organization_id == admin.organization_id`
- [ ] Does the endpoint fetch a record by ID? → add org/shop scope to that fetch, not just subsequent queries
- [ ] Does the endpoint use a related model (PurchaseItem, SaleItem, etc.)? → add explicit `shop_id` filter even if scoped through FK
- [ ] Does admin accept optional `shop_id` param? → validate that shop belongs to the admin's org before using it
- [ ] Does the endpoint write data? → set `shop_id` (and `organization_id` if applicable) on the new record from the auth context, never from user input
