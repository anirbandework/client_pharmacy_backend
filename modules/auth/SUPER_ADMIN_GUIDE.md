# SuperAdmin System - Complete Guide

## 🎯 Overview

The system now has a **4-tier hierarchy** with organization-based access control:

```
SuperAdmin (System Owner)
    └── Organization ID: "ORG-001"
         ├── Admin 1 (organization_id: "ORG-001")
         │    ├── Shop A
         │    │    ├── Staff 1
         │    │    └── Staff 2
         │    └── Shop B
         │         └── Staff 3
         │
         ├── Admin 2 (organization_id: "ORG-001") ← Shares visibility with Admin 1
         │    └── Shop C
         │         └── Staff 4
         │
         └── Admin 3 (organization_id: "ORG-001") ← Shares visibility with Admin 1 & 2
              └── Shop D
                   └── Staff 5

    └── Organization ID: "ORG-002"
         └── Admin 4 (organization_id: "ORG-002")
              └── Shop E
                   └── Staff 6
```

## 🔑 Key Concepts

### Organization ID
- **Purpose**: Groups multiple admins together
- **Visibility**: Admins with same `organization_id` can see each other's shops and staff
- **Format**: Any string (e.g., "ORG-001", "PHARMACY-GROUP-A", "CHAIN-NORTH")
- **Assignment**: Only SuperAdmin can assign organization_id when creating admins

### Access Levels

| User Type | Can See | Can Manage |
|-----------|---------|------------|
| **SuperAdmin** | Everything (all orgs, shops, staff) | Only admins (create/view) |
| **Admin** | Shops/staff in their organization | Shops/staff in their organization |
| **Staff** | Only their shop | Only their shop data |

**Note**: SuperAdmin has READ-ONLY access to shops and staff for monitoring purposes.

## 🚀 Setup & Migration

### 1. Run Migration
```bash
cd /Users/anirbande/Desktop/client\ backend
python -m modules.auth.migrate_super_admin
```

### 2. Create First SuperAdmin
```bash
POST /api/auth/super-admin/register
Content-Type: application/json

{
  "email": "superadmin@system.com",
  "password": "SuperSecure123!",
  "full_name": "System Administrator",
  "phone": "+919876543210"
}
```

### 3. Login as SuperAdmin (with OTP)
```bash
# Step 1: Send OTP
POST /api/auth/super-admin/send-otp
Content-Type: application/json

{
  "phone": "+919876543210",
  "password": "SuperSecure123!"
}

# Step 2: Verify OTP
POST /api/auth/super-admin/verify-otp
Content-Type: application/json

{
  "phone": "+919876543210",
  "otp_code": "123456"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_type": "super_admin"
}
```

## 📋 SuperAdmin Operations

### Create Admin with Organization ID
```bash
POST /api/auth/super-admin/admins
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "organization_id": "PHARMACY-CHAIN-NORTH",
  "phone": "+919876543211",
  "password": "Admin123!",
  "full_name": "John Doe",
  "email": "john@pharmacy.com"
}
```

### Create Multiple Admins with Same Organization ID
```bash
# Admin 1
POST /api/auth/super-admin/admins
{
  "organization_id": "PHARMACY-CHAIN-NORTH",
  "phone": "+919876543211",
  "password": "Admin123!",
  "full_name": "John Doe"
}

# Admin 2 (same organization_id)
POST /api/auth/super-admin/admins
{
  "organization_id": "PHARMACY-CHAIN-NORTH",
  "phone": "+919876543212",
  "password": "Admin456!",
  "full_name": "Jane Smith"
}

# Admin 3 (same organization_id)
POST /api/auth/super-admin/admins
{
  "organization_id": "PHARMACY-CHAIN-NORTH",
  "phone": "+919876543213",
  "password": "Admin789!",
  "full_name": "Bob Wilson"
}
```

Now John, Jane, and Bob can all see and manage each other's shops and staff!

### View All Admins
```bash
GET /api/auth/super-admin/admins
Authorization: Bearer <super_admin_token>
```

### View Admins by Organization
```bash
GET /api/auth/super-admin/admins/organization/PHARMACY-CHAIN-NORTH
Authorization: Bearer <super_admin_token>
```

### View All Shops (SuperAdmin - Read Only)
```bash
GET /api/auth/super-admin/shops
Authorization: Bearer <super_admin_token>

# Returns all shops from all organizations (read-only view)
```

### View All Staff (SuperAdmin - Read Only)
```bash
GET /api/auth/super-admin/staff
Authorization: Bearer <super_admin_token>

# Returns all staff from all shops (read-only view)
```

## 👥 Admin Operations (Organization-Scoped)

### Admin Login
```bash
# Step 1: Send OTP
POST /api/auth/admin/send-otp
{
  "phone": "+919876543211",
  "password": "Admin123!"
}

# Step 2: Verify OTP
POST /api/auth/admin/verify-otp
{
  "phone": "+919876543211",
  "otp_code": "123456"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_type": "admin",
  "organization_id": "PHARMACY-CHAIN-NORTH"
}
```

### View Shops (Organization-Scoped)
```bash
GET /api/auth/admin/shops
Authorization: Bearer <admin_token>

# Returns ALL shops created by admins with same organization_id
```

### Create Shop
```bash
POST /api/auth/admin/shops
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "shop_name": "Downtown Pharmacy",
  "shop_code": "DTP001",
  "address": "123 Main St",
  "phone": "+919876543220"
}
```

### View Staff (Organization-Scoped)
```bash
GET /api/auth/admin/all-staff
Authorization: Bearer <admin_token>

# Returns ALL staff from ALL shops in the organization
```

### Create Staff
```bash
POST /api/auth/admin/shops/{shop_id}/staff
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Alice Worker",
  "staff_code": "STF001",
  "phone": "+919876543230",
  "role": "staff",
  "monthly_salary": 25000
}
```

## 🔒 Access Control Examples

### Scenario 1: Same Organization
```
Organization: "PHARMACY-CHAIN-NORTH"

Admin 1 creates:
  - Shop A (id: 1)
  - Shop B (id: 2)

Admin 2 creates:
  - Shop C (id: 3)

Admin 1 can:
  ✅ View Shop A, B, C
  ✅ Update Shop A, B, C
  ✅ Create staff in Shop A, B, C
  ✅ View all staff from Shop A, B, C

Admin 2 can:
  ✅ View Shop A, B, C
  ✅ Update Shop A, B, C
  ✅ Create staff in Shop A, B, C
  ✅ View all staff from Shop A, B, C

SuperAdmin can:
  ✅ View Shop A, B, C (read-only)
  ✅ View all staff (read-only)
  ❌ Cannot create/update/delete shops or staff
```

### Scenario 2: Different Organizations
```
Organization: "PHARMACY-CHAIN-NORTH"
Admin 1 creates:
  - Shop A (id: 1)

Organization: "PHARMACY-CHAIN-SOUTH"
Admin 2 creates:
  - Shop B (id: 2)

Admin 1 can:
  ✅ View Shop A
  ❌ View Shop B (different organization)

Admin 2 can:
  ✅ View Shop B
  ❌ View Shop A (different organization)

SuperAdmin can:
  ✅ View Shop A and Shop B (read-only monitoring)
```

## 🔄 Migration for Existing Data

If you have existing admins, they will be assigned:
- `organization_id`: "ORG-DEFAULT-001"
- `created_by_super_admin`: "System Migration"

All existing admins will share visibility with each other.

To separate them:
1. SuperAdmin creates new admins with different organization_ids
2. Manually update existing admin's organization_id in database

## 🎯 Use Cases

### Use Case 1: Single Pharmacy Chain
```
SuperAdmin creates:
  - Admin 1 (organization_id: "CHAIN-001") - Owner
  - Admin 2 (organization_id: "CHAIN-001") - Co-owner
  - Admin 3 (organization_id: "CHAIN-001") - Manager

All 3 admins can manage all shops and staff together.
```

### Use Case 2: Multiple Independent Pharmacies
```
SuperAdmin creates:
  - Admin 1 (organization_id: "PHARMACY-A") - Pharmacy A owner
  - Admin 2 (organization_id: "PHARMACY-B") - Pharmacy B owner
  - Admin 3 (organization_id: "PHARMACY-C") - Pharmacy C owner

Each admin can only see their own shops and staff.
```

### Use Case 3: Regional Management
```
SuperAdmin creates:
  - Admin 1 (organization_id: "REGION-NORTH") - North region
  - Admin 2 (organization_id: "REGION-NORTH") - North region backup
  - Admin 3 (organization_id: "REGION-SOUTH") - South region
  - Admin 4 (organization_id: "REGION-SOUTH") - South region backup

North admins share visibility, South admins share visibility.
```

## 📊 Updated Hierarchy

```
Level 1: SuperAdmin
  ├── Creates admins with organization_id
  ├── Views all admins
  ├── Views all shops (read-only)
  └── Views all staff (read-only)

Level 2: Admin (Organization-scoped)
  ├── Views shops/staff in their organization
  ├── Creates shops
  └── Manages staff in organization shops

Level 3: Shop
  ├── Belongs to one admin
  └── Contains multiple staff

Level 4: Staff
  ├── Belongs to one shop
  └── Access only their shop data
```

## 🔐 Security Notes

1. **SuperAdmin credentials**: Store securely, only for system owner
2. **SuperAdmin authentication**: Phone + Password + OTP (two-factor authentication)
3. **SuperAdmin permissions**: Read-only for shops/staff (monitoring only)
4. **Organization ID**: Cannot be changed by admins, only SuperAdmin
5. **Data isolation**: Enforced at query level by organization_id
6. **Token includes**: `organization_id` for admins to enable filtering

## 🧪 Testing

```bash
# 1. Create SuperAdmin
POST /api/auth/super-admin/register

# 2. Login with OTP
POST /api/auth/super-admin/send-otp
POST /api/auth/super-admin/verify-otp

# 3. Create 2 admins with same org ID
POST /api/auth/super-admin/admins (organization_id: "TEST-ORG")
POST /api/auth/super-admin/admins (organization_id: "TEST-ORG")

# 4. Login as Admin 1, create Shop A
POST /api/auth/admin/send-otp
POST /api/auth/admin/verify-otp
POST /api/auth/admin/shops

# 5. Login as Admin 2, view shops
POST /api/auth/admin/send-otp
POST /api/auth/admin/verify-otp
GET /api/auth/admin/shops
# Should see Shop A created by Admin 1!
```

## 📝 API Summary

### SuperAdmin Endpoints
- `POST /api/auth/super-admin/register` - Register SuperAdmin
- `POST /api/auth/super-admin/send-otp` - Send OTP for login
- `POST /api/auth/super-admin/verify-otp` - Verify OTP and login
- `POST /api/auth/super-admin/login` - Login (legacy, use OTP instead)
- `GET /api/auth/super-admin/me` - Get profile
- `POST /api/auth/super-admin/admins` - Create admin with org ID
- `GET /api/auth/super-admin/admins` - List all admins
- `GET /api/auth/super-admin/admins/organization/{org_id}` - List admins by org
- `GET /api/auth/super-admin/shops` - List all shops (read-only)
- `GET /api/auth/super-admin/staff` - List all staff (read-only)

### Admin Endpoints (Organization-scoped)
- `GET /api/auth/admin/shops` - List organization shops
- `POST /api/auth/admin/shops` - Create shop
- `PUT /api/auth/admin/shops/{id}` - Update organization shop
- `GET /api/auth/admin/all-staff` - List organization staff
- `POST /api/auth/admin/shops/{id}/staff` - Create staff
- `PUT /api/auth/staff/{id}` - Update organization staff
- `DELETE /api/auth/staff/{id}` - Delete organization staff

All admin operations are automatically scoped to their `organization_id`!
