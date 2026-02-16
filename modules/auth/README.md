# Multi-Tenant Authentication System with SuperAdmin

## Overview

A comprehensive 4-tier authentication system for pharmacy management:
- **SuperAdmin** (System Owner) - Creates and manages admins with organization IDs
- **Admin** (Business Owner) - Manages shops within their organization
- **Shop Manager** - Manages staff and operations for their shop
- **Staff** - Access shop portal with role-based permissions

## Architecture

```
SuperAdmin
  └── Organization: "PHARMACY-CHAIN-A"
       ├── Admin 1 (Shares visibility with Admin 2 & 3)
       │    ├── Shop 1
       │    │    ├── Shop Manager
       │    │    └── Staff Member 1
       │    └── Shop 2
       │         └── Staff Member 2
       ├── Admin 2 (Shares visibility with Admin 1 & 3)
       │    └── Shop 3
       │         └── Staff Member 3
       └── Admin 3 (Shares visibility with Admin 1 & 2)
            └── Shop 4
                 └── Staff Member 4
  
  └── Organization: "PHARMACY-CHAIN-B"
       └── Admin 4 (Isolated from Chain A)
            └── Shop 5
                 └── Staff Member 5
```

## 🆕 What's New: SuperAdmin & Organization System

### Key Features
1. **SuperAdmin Role**: System-level administrator who creates admins
2. **Organization ID**: Groups multiple admins for shared visibility
3. **Shared Management**: Admins with same organization_id can see/manage each other's shops and staff
4. **Data Isolation**: Different organizations are completely isolated

### Quick Start
```bash
# 1. Run migration
python -m modules.auth.migrate_super_admin

# 2. Create SuperAdmin
POST /api/auth/super-admin/register

# 3. Create admins with organization_id
POST /api/auth/super-admin/admins
```

📖 **See [SUPER_ADMIN_GUIDE.md](SUPER_ADMIN_GUIDE.md) for complete documentation**

📋 **See [SUPER_ADMIN_QUICK_REF.md](SUPER_ADMIN_QUICK_REF.md) for quick reference**

## Key Features

### 1. Multi-Tenancy
- All data is scoped by `shop_id`
- Automatic data isolation per shop
- Staff can only access their shop's data

### 2. Role-Based Access Control
- **Admin**: Full access to all shops
- **Shop Manager**: Manage staff, view all analytics
- **Staff**: Configurable permissions per staff member

### 3. UUID-Based Staff Login
- Each staff gets a unique UUID
- No password needed - just UUID
- Secure and easy to manage

### 4. JWT Authentication
- Secure token-based authentication
- 7-day token expiry
- Shop context embedded in token

## API Endpoints

### Admin Authentication

#### Register Admin
```http
POST /api/auth/admin/register
Content-Type: application/json

{
  "email": "owner@pharmacy.com",
  "password": "securepassword",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

#### Admin Login
```http
POST /api/auth/admin/login
Content-Type: application/json

{
  "email": "owner@pharmacy.com",
  "password": "securepassword"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_type": "admin",
  "shop_id": null,
  "shop_name": null
}
```

### Shop Management (Admin Only)

#### Create Shop
```http
POST /api/auth/admin/shops
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "shop_name": "Main Street Pharmacy",
  "shop_code": "MSP001",
  "address": "123 Main St, City",
  "phone": "+1234567890",
  "email": "mainstreet@pharmacy.com",
  "license_number": "LIC123456",
  "gst_number": "GST123456"
}
```

#### Get All Shops
```http
GET /api/auth/admin/shops
Authorization: Bearer <admin_token>
```

#### Update Shop
```http
PUT /api/auth/admin/shops/{shop_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "shop_name": "Updated Name",
  "is_active": true
}
```

### Staff Management

#### Create Staff
```http
POST /api/auth/admin/shops/{shop_id}/staff
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "full_name": "Jane Smith",
  "phone": "+1234567890",
  "email": "jane@pharmacy.com",
  "role": "staff",
  "can_manage_staff": false,
  "can_view_analytics": true,
  "can_manage_inventory": true,
  "can_manage_customers": true
}

Response:
{
  "id": 1,
  "shop_id": 1,
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "full_name": "Jane Smith",
  "role": "staff",
  ...
}
```

**Important**: Save the `uuid` - staff will use this to login!

#### Get Shop Staff
```http
GET /api/auth/shops/{shop_id}/staff
Authorization: Bearer <admin_token>
```

#### Update Staff
```http
PUT /api/auth/staff/{staff_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "shop_manager",
  "can_manage_staff": true
}
```

### Staff Authentication

#### Staff Login (UUID-based)
```http
POST /api/auth/staff/login
Content-Type: application/json

{
  "uuid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_type": "staff",
  "shop_id": 1,
  "shop_name": "Main Street Pharmacy"
}
```

#### Get Staff Profile
```http
GET /api/auth/staff/me
Authorization: Bearer <staff_token>
```

#### Get Staff Shop Details
```http
GET /api/auth/staff/shop
Authorization: Bearer <staff_token>
```

## Permissions System

### Staff Permissions

| Permission | Description | Default |
|------------|-------------|---------|
| `can_manage_staff` | Create/update/delete staff | `false` |
| `can_view_analytics` | View analytics and reports | `true` |
| `can_manage_inventory` | Manage stock and inventory | `true` |
| `can_manage_customers` | Manage customer records | `true` |

### Roles

#### Staff (Default)
- Configurable permissions
- Access to assigned shop only

#### Shop Manager
- All permissions enabled
- Can manage other staff
- Full shop access

#### Admin
- Access to all shops
- Create/delete shops
- Manage all staff across shops

## Using Authentication in Routes

### Require Any Authenticated User
```python
from modules.auth.dependencies import get_current_user

@router.get("/protected")
def protected_route(current_user: dict = Depends(get_current_user)):
    user = current_user["user"]
    token_data = current_user["token_data"]
    return {"message": f"Hello {user.full_name}"}
```

### Require Admin Only
```python
from modules.auth.dependencies import get_current_admin

@router.get("/admin-only")
def admin_route(admin = Depends(get_current_admin)):
    return {"admin": admin.full_name}
```

### Require Staff Only
```python
from modules.auth.dependencies import get_current_staff

@router.get("/staff-only")
def staff_route(staff = Depends(get_current_staff)):
    return {"staff": staff.full_name, "shop_id": staff.shop_id}
```

### Require Specific Permission
```python
from modules.auth.dependencies import require_permission

@router.post("/manage-inventory")
def manage_inventory(staff = Depends(require_permission("manage_inventory"))):
    return {"message": "Inventory updated"}
```

### Get Shop Context
```python
from modules.auth.dependencies import get_shop_context

@router.get("/shop-data")
def get_shop_data(
    shop_id: int = Depends(get_shop_context),
    db: Session = Depends(get_db)
):
    # shop_id is automatically extracted from token
    # Filter all queries by shop_id
    records = db.query(DailyRecord).filter(DailyRecord.shop_id == shop_id).all()
    return records
```

## Multi-Tenant Data Filtering

### Automatic Filtering Pattern

Always filter by shop_id for staff:

```python
@router.get("/customers")
def get_customers(
    staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    # Always filter by staff's shop_id
    customers = db.query(CustomerProfile).filter(
        CustomerProfile.shop_id == staff.shop_id
    ).all()
    return customers
```

### Admin Access (All Shops)

```python
@router.get("/admin/all-customers")
def get_all_customers(
    admin = Depends(get_current_admin),
    shop_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(CustomerProfile)
    
    # Admin can filter by specific shop or see all
    if shop_id:
        query = query.filter(CustomerProfile.shop_id == shop_id)
    
    return query.all()
```

## Database Schema

### Auth Tables

```sql
-- Admins (Business Owners)
CREATE TABLE admins (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR NOT NULL,
    phone VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);

-- Shops
CREATE TABLE shops (
    id INTEGER PRIMARY KEY,
    admin_id INTEGER REFERENCES admins(id),
    shop_name VARCHAR NOT NULL,
    shop_code VARCHAR UNIQUE NOT NULL,
    address TEXT,
    phone VARCHAR,
    email VARCHAR,
    license_number VARCHAR,
    gst_number VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);

-- Staff
CREATE TABLE staff (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER REFERENCES shops(id),
    uuid VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    phone VARCHAR,
    email VARCHAR,
    role VARCHAR DEFAULT 'staff',
    can_manage_staff BOOLEAN DEFAULT FALSE,
    can_view_analytics BOOLEAN DEFAULT TRUE,
    can_manage_inventory BOOLEAN DEFAULT TRUE,
    can_manage_customers BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    last_login TIMESTAMP
);
```

### Adding shop_id to Existing Tables

All existing tables need `shop_id`:

```sql
ALTER TABLE contact_records ADD COLUMN shop_id INTEGER REFERENCES shops(id);
ALTER TABLE customer_profiles ADD COLUMN shop_id INTEGER REFERENCES shops(id);
ALTER TABLE daily_records ADD COLUMN shop_id INTEGER REFERENCES shops(id);
ALTER TABLE stock_items_audit ADD COLUMN shop_id INTEGER REFERENCES shops(id);
-- ... etc for all tables
```

Run the migration script:
```bash
python add_shop_id_migration.py
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install passlib[bcrypt] python-jose[cryptography]
```

### 2. Set Environment Variables
```bash
# .env
JWT_SECRET_KEY=your-super-secret-key-change-in-production
```

### 3. Create Auth Tables
```python
# In main.py
from modules.auth.models import Admin, Shop, Staff
Base.metadata.create_all(bind=engine)
```

### 4. Run Migration
```bash
python add_shop_id_migration.py
```

### 5. Register Routes
```python
# In main.py
from modules.auth.routes import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
```

### 6. Add Middleware (Optional)
```python
# In main.py
from modules.auth.middleware import ShopContextMiddleware
app.add_middleware(ShopContextMiddleware)
```

## Workflow Example

### 1. Admin Setup
```bash
# Register admin
POST /api/auth/admin/register
{
  "email": "owner@pharmacy.com",
  "password": "secure123",
  "full_name": "John Doe"
}

# Login
POST /api/auth/admin/login
# Save token
```

### 2. Create Shops
```bash
# Create Shop 1
POST /api/auth/admin/shops
Authorization: Bearer <admin_token>
{
  "shop_name": "Downtown Pharmacy",
  "shop_code": "DTP001"
}

# Create Shop 2
POST /api/auth/admin/shops
{
  "shop_name": "Uptown Pharmacy",
  "shop_code": "UTP001"
}
```

### 3. Add Staff
```bash
# Add staff to Shop 1
POST /api/auth/admin/shops/1/staff
{
  "full_name": "Alice Manager",
  "role": "shop_manager",
  "can_manage_staff": true
}
# Response: uuid = "abc-123-def"

# Add regular staff
POST /api/auth/admin/shops/1/staff
{
  "full_name": "Bob Staff",
  "role": "staff"
}
# Response: uuid = "xyz-789-ghi"
```

### 4. Staff Login
```bash
# Staff logs in with UUID
POST /api/auth/staff/login
{
  "uuid": "abc-123-def"
}

# Response includes shop_id and shop_name
# All subsequent requests are scoped to that shop
```

### 5. Staff Operations
```bash
# Staff can now access shop-specific data
GET /api/customers
Authorization: Bearer <staff_token>
# Returns only customers from their shop

GET /api/daily-records
Authorization: Bearer <staff_token>
# Returns only records from their shop
```

## Security Best Practices

1. **Change JWT Secret**: Set strong `JWT_SECRET_KEY` in production
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Expiry**: Tokens expire after 7 days
4. **UUID Security**: UUIDs are randomly generated and unique
5. **Password Hashing**: Bcrypt with automatic salt
6. **Shop Isolation**: Strict data isolation per shop

## Troubleshooting

### Staff Can't Login
- Check if staff is active: `is_active = true`
- Check if shop is active: `shop.is_active = true`
- Verify UUID is correct

### Permission Denied
- Check staff permissions in database
- Shop managers have all permissions
- Regular staff need specific permissions enabled

### Data Not Filtered by Shop
- Ensure all queries include `shop_id` filter
- Use `get_current_staff` dependency to get shop context
- Check token includes `shop_id`

## Next Steps

1. Update all existing routes to use authentication
2. Add shop_id filtering to all queries
3. Test multi-tenant data isolation
4. Create admin dashboard for shop management
5. Add staff activity logging
