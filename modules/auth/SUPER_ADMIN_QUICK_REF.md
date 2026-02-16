# SuperAdmin System - Quick Reference

## 🏗️ New Hierarchy (4 Levels)

```
┌─────────────────────────────────────────────────────────────┐
│                      SUPER ADMIN                            │
│  - Creates admins with organization_id                      │
│  - Views all shops and staff (READ-ONLY)                    │
│  - CANNOT create/update/delete shops or staff               │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐           ┌────────▼───────┐
│  ORG-001       │           │  ORG-002       │
│                │           │                │
│  Admin 1       │           │  Admin 4       │
│  Admin 2       │           │  (isolated)    │
│  Admin 3       │           │                │
│  (shared view) │           └────────┬───────┘
└───────┬────────┘                    │
        │                             │
   ┌────┴─────┬──────────┐      ┌────▼────┐
   │          │          │      │ Shop E  │
┌──▼──┐  ┌───▼──┐  ┌────▼──┐   └────┬────┘
│Shop │  │Shop  │  │Shop   │        │
│  A  │  │  B   │  │  C    │   ┌────▼────┐
└──┬──┘  └───┬──┘  └────┬──┘   │Staff 6  │
   │         │          │      └─────────┘
┌──▼──┐  ┌──▼──┐  ┌────▼──┐
│Staff│  │Staff│  │Staff  │
│ 1,2 │  │  3  │  │  4,5  │
└─────┘  └─────┘  └───────┘

All admins in ORG-001 can see/manage Shops A, B, C and all their staff
Admin 4 in ORG-002 can only see/manage Shop E and its staff
```

## 🔑 Key Changes

| Before | After |
|--------|-------|
| Admin → Shops → Staff | SuperAdmin → Admin (org_id) → Shops → Staff |
| All admins see all shops | Admins see only their organization's shops |
| No admin grouping | Multiple admins per organization |
| Admin self-registration | SuperAdmin creates admins |
| No oversight role | SuperAdmin has read-only view of everything |

## 📊 Access Matrix

| Action | SuperAdmin | Admin (same org) | Admin (diff org) | Staff |
|--------|-----------|------------------|------------------|-------|
| Create Admin | ✅ | ❌ | ❌ | ❌ |
| View All Admins | ✅ | ❌ | ❌ | ❌ |
| View All Shops | ✅ (read-only) | ✅ (org only) | ❌ | ❌ |
| Create Shop | ❌ | ✅ | ❌ | ❌ |
| Update Shop | ❌ | ✅ (org only) | ❌ | ❌ |
| Delete Shop | ❌ | ✅ (org only) | ❌ | ❌ |
| View All Staff | ✅ (read-only) | ✅ (org only) | ❌ | ❌ |
| Create Staff | ❌ | ✅ (org shops) | ❌ | ❌ |
| Update Staff | ❌ | ✅ (org only) | ❌ | ❌ |
| Delete Staff | ❌ | ✅ (org only) | ❌ | ❌ |
| View Shop Data | ✅ (read-only) | ✅ (org only) | ❌ | ✅ (own shop) |

## 🚀 Quick Start

### 1. Create SuperAdmin
```bash
POST /api/auth/super-admin/register
{
  "email": "super@admin.com",
  "password": "SuperPass123!",
  "full_name": "Super Admin",
  "phone": "+919999999999"
}
```

### 2. Login SuperAdmin with OTP
```bash
# Step 1: Send OTP
POST /api/auth/super-admin/send-otp
{
  "phone": "+919999999999",
  "password": "SuperPass123!"
}

# Step 2: Verify OTP
POST /api/auth/super-admin/verify-otp
{
  "phone": "+919999999999",
  "otp_code": "123456"
}
```

### 2. Create Admins with Same Org ID
```bash
# Admin 1
POST /api/auth/super-admin/admins
Authorization: Bearer <super_admin_token>
{
  "organization_id": "PHARMACY-CHAIN-A",
  "phone": "+919876543211",
  "password": "Admin123!",
  "full_name": "John Doe"
}

# Admin 2 (same org)
POST /api/auth/super-admin/admins
{
  "organization_id": "PHARMACY-CHAIN-A",
  "phone": "+919876543212",
  "password": "Admin456!",
  "full_name": "Jane Smith"
}
```

### 3. Admins Create Shops
```bash
# Admin 1 creates Shop A
POST /api/auth/admin/shops
Authorization: Bearer <admin1_token>
{
  "shop_name": "Shop A",
  "shop_code": "SHOP-A"
}

# Admin 2 creates Shop B
POST /api/auth/admin/shops
Authorization: Bearer <admin2_token>
{
  "shop_name": "Shop B",
  "shop_code": "SHOP-B"
}
```

### 4. Both Admins See Both Shops
```bash
# Admin 1
GET /api/auth/admin/shops
Authorization: Bearer <admin1_token>
# Returns: Shop A, Shop B ✅

# Admin 2
GET /api/auth/admin/shops
Authorization: Bearer <admin2_token>
# Returns: Shop A, Shop B ✅
```

## 🔄 Migration Steps

1. **Backup database**
2. **Run migration**: `python -m modules.auth.migrate_super_admin`
3. **Create SuperAdmin account**
4. **Existing admins** get `organization_id: "ORG-DEFAULT-001"`
5. **Create new admins** with custom organization_ids

## 💡 Common Scenarios

### Scenario 1: Pharmacy Chain with 3 Partners
```
SuperAdmin creates:
- Admin 1 (org: "CHAIN-XYZ") - Partner 1
- Admin 2 (org: "CHAIN-XYZ") - Partner 2  
- Admin 3 (org: "CHAIN-XYZ") - Partner 3

Result: All 3 partners can manage all shops together
```

### Scenario 2: Independent Pharmacies
```
SuperAdmin creates:
- Admin 1 (org: "PHARMACY-A")
- Admin 2 (org: "PHARMACY-B")
- Admin 3 (org: "PHARMACY-C")

Result: Each pharmacy is completely isolated
```

### Scenario 3: Regional Chains
```
SuperAdmin creates:
- Admin 1 (org: "NORTH-REGION")
- Admin 2 (org: "NORTH-REGION")
- Admin 3 (org: "SOUTH-REGION")
- Admin 4 (org: "SOUTH-REGION")

Result: North admins share, South admins share, no cross-region access
```

## 📝 Database Changes

### New Table: `super_admins`
```sql
- id
- email (unique)
- password_hash
- full_name
- phone (unique)
- is_active
- created_at
```

### Updated Table: `admins`
```sql
+ organization_id (indexed)
+ created_by_super_admin
```

### JWT Token Changes
```json
{
  "user_id": 1,
  "user_type": "admin",
  "organization_id": "PHARMACY-CHAIN-A",  // NEW
  "email": "admin@example.com"
}
```

## 🎯 Benefits

1. **Shared Management**: Multiple admins can collaborate
2. **Data Isolation**: Organizations are completely separated
3. **Scalability**: Easy to add new admins to existing organizations
4. **Flexibility**: SuperAdmin controls organization structure
5. **Security**: Organization-level access control enforced at query level
6. **Oversight**: SuperAdmin can monitor all operations without interfering

## ⚠️ Important Notes

- **organization_id** is immutable (only SuperAdmin can set it)
- **Admins cannot self-register** (must be created by SuperAdmin)
- **All queries** are automatically filtered by organization_id
- **Staff access** remains unchanged (shop-level only)
- **Existing data** is preserved with default organization_id
- **SuperAdmin is read-only** for shops and staff (monitoring only)
