# 🔐 AUTHENTICATION SYSTEM DOCUMENTATION

## 📊 USER HIERARCHY

```
SuperAdmin (Top Level)
    ↓ creates
Admin (Organization Level)
    ↓ creates
Shop (Branch Level)
    ↓ creates
Staff (Employee Level)
```

---

## 1️⃣ SUPER ADMIN

### Fields
```python
id: int                    # Primary key
email: str                 # Unique, required
password_hash: str         # Bcrypt hashed
full_name: str            # Display name
phone: str(15)            # Unique, +91XXXXXXXXXX format
is_active: bool           # Default: True
created_at: datetime      # Auto-generated
```

### Login Methods
**Method 1: OTP Login (Recommended)**
1. POST `/api/auth/super-admin/send-otp`
   - Body: `{phone, password}`
   - Validates phone + password
   - Sends 6-digit OTP (expires in 5 min)
   
2. POST `/api/auth/super-admin/verify-otp`
   - Body: `{phone, otp_code}`
   - Returns JWT token

**Method 2: Direct Login (Legacy)**
- POST `/api/auth/super-admin/login`
- Body: `{email, password}`
- Returns JWT token

### Capabilities
- ✅ Create/Read/Update/Delete Admins
- ✅ View all organizations
- ✅ Manage all shops and staff
- ✅ Access hierarchical dashboard
- ✅ View plain passwords (security risk for support)

### Master Bypass (Testing)
- Phone: `+919383169659`
- Password: `test@123`
- OTP: `999999`

---

## 2️⃣ ADMIN

### Fields
```python
id: int                          # Primary key
organization_id: str             # SHARED between multiple admins
email: str                       # Unique, optional
password_hash: str               # Nullable until signup
plain_password: str              # ⚠️ Visible to SuperAdmin
full_name: str                   # Required
phone: str(15)                   # Unique, required for OTP
is_active: bool                  # Default: True
is_password_set: bool            # Default: False
created_by_super_admin: str      # SuperAdmin name
created_at: datetime             # Auto-generated
```

### Organization ID Concept
**Purpose**: Multiple admins can manage the same organization

**Example**:
```
Organization: "ABC Pharmacy Chain"
organization_id: "ABC-PHARMA-001"

Admin 1: John (organization_id: "ABC-PHARMA-001")
Admin 2: Sarah (organization_id: "ABC-PHARMA-001")
Admin 3: Mike (organization_id: "ABC-PHARMA-001")

All 3 admins can:
- See ALL shops in the organization
- Manage ALL staff in the organization
- Create new shops
- Update/delete any shop or staff
```

**Differentiation**:
- Each admin has unique `id`, `email`, `phone`
- Same `organization_id` = same organization
- Different `organization_id` = different organization (no access to each other's data)

### Lifecycle
1. **Creation** (by SuperAdmin)
   - SuperAdmin creates admin with organization_id
   - Admin receives phone number
   - `is_password_set = False`

2. **Signup** (First time)
   - POST `/api/auth/admin/signup`
   - Body: `{phone, password}`
   - Sets password, receives OTP
   - `is_password_set = True`

3. **Login** (Subsequent)
   - POST `/api/auth/admin/send-otp`
   - Body: `{phone, password}`
   - Receives OTP
   - POST `/api/auth/admin/verify-otp`
   - Body: `{phone, otp_code}`
   - Returns JWT token with `organization_id`

### Capabilities
- ✅ Create/manage shops (within organization)
- ✅ Create/manage staff (within organization)
- ✅ View all shops with same organization_id
- ✅ View all staff in organization shops
- ❌ Cannot access other organizations

### Deletion Behavior
**If last admin in organization:**
- Deletes ALL shops
- Deletes ALL staff
- Removes entire organization

**If other admins exist:**
- Only deletes that admin
- Shops and staff remain accessible to other admins

---

## 3️⃣ SHOP

### Fields
```python
id: int                    # Primary key (database ID)
admin_id: int              # Foreign key to Admin
shop_name: str             # Display name
shop_code: str             # Business identifier (NOT unique globally)
address: text              # Optional
phone: str                 # Optional
email: str                 # Optional
license_number: str        # Optional
gst_number: str            # Optional
created_by_admin: str      # Admin name who created
updated_by_admin: str      # Admin name who updated
updated_at: datetime       # Last update time
is_active: bool            # Default: True
created_at: datetime       # Auto-generated
```

### Shop Code vs Shop ID

**shop_id (Database ID)**
- Auto-incremented integer
- Unique across entire database
- Used internally for relationships
- Example: 1, 2, 3, 4...

**shop_code (Business Identifier)**
- String defined by admin
- NOT unique globally
- Unique per admin (constraint: unique_shop_code_per_admin)
- Used for business operations
- Example: "STORE-001", "BRANCH-A", "MUMBAI-CENTRAL"

**Why both exist?**
```
Admin A creates shop with code "STORE-001" → shop_id: 1
Admin B creates shop with code "STORE-001" → shop_id: 2 (allowed!)

Same shop_code, different admins = OK
Same shop_code, same admin = ERROR
```

### Access Control
- Admins with same `organization_id` can:
  - View all shops
  - Update any shop
  - Delete any shop
  - Create staff in any shop

---

## 4️⃣ STAFF

### Fields
```python
id: int                          # Primary key
shop_id: int                     # Foreign key to Shop (database ID)
uuid: str                        # Auto-generated, unique
name: str                        # Display name
staff_code: str                  # Unique identifier
phone: str(15)                   # Unique, required for OTP
password_hash: str               # Nullable until signup
plain_password: str              # ⚠️ Visible to SuperAdmin
email: str                       # Optional
role: str                        # "staff" or "shop_manager"
monthly_salary: float            # Optional
joining_date: date               # Optional
salary_eligibility_days: int    # Default: 30
can_manage_staff: bool           # Default: False
can_view_analytics: bool         # Default: True
can_manage_inventory: bool       # Default: True
can_manage_customers: bool       # Default: True
is_password_set: bool            # Default: False
created_by_admin: str            # Admin name
updated_by_admin: str            # Admin name
updated_at: datetime             # Last update
is_active: bool                  # Default: True
created_at: datetime             # Auto-generated
last_login: datetime             # Updated on login
```

### Shop Relationship
**Staff belongs to ONE shop**
- `shop_id` = database ID (integer)
- Staff can only access their shop's data
- Token contains `shop_code` (not shop_id)

**Why shop_code in token?**
```python
# Token payload for staff:
{
  "user_id": 5,
  "user_type": "staff",
  "shop_code": "STORE-001",  # Business identifier
  "user_name": "John Doe"
}

# Staff uses shop_code to:
# - Access shop-specific APIs
# - Filter data by shop
# - Identify which shop they work at
```

### Lifecycle
1. **Creation** (by Admin)
   - Admin creates staff for a shop
   - Uses shop_code to identify shop
   - Staff receives phone number
   - `is_password_set = False`

2. **Signup** (First time)
   - POST `/api/auth/staff/signup`
   - Body: `{phone, password}`
   - Sets password, receives OTP
   - `is_password_set = True`

3. **Login** (Subsequent)
   - POST `/api/auth/staff/send-otp`
   - Body: `{phone, password}`
   - Receives OTP
   - POST `/api/auth/staff/verify-otp`
   - Body: `{phone, otp_code}`
   - Returns JWT token with `shop_code`

### Login Methods
**Method 1: OTP Login (Recommended)**
- Phone + Password + OTP

**Method 2: UUID Login (Legacy)**
- POST `/api/auth/staff/login`
- Body: `{uuid}`
- No password required (less secure)

### Capabilities
- ✅ Access only their shop's data
- ✅ Manage inventory (if permission granted)
- ✅ View analytics (if permission granted)
- ✅ Manage customers (if permission granted)
- ✅ Manage other staff (if permission granted)
- ❌ Cannot access other shops

---

## 🔑 JWT TOKEN STRUCTURE

### SuperAdmin Token
```json
{
  "user_id": 1,
  "user_type": "super_admin",
  "email": "admin@example.com",
  "user_name": "Super Admin",
  "organization_id": null,
  "shop_code": null,
  "exp": 1234567890
}
```

### Admin Token
```json
{
  "user_id": 5,
  "user_type": "admin",
  "email": "john@pharmacy.com",
  "user_name": "John Doe",
  "organization_id": "ABC-PHARMA-001",
  "shop_code": null,
  "exp": 1234567890
}
```

### Staff Token
```json
{
  "user_id": 15,
  "user_type": "staff",
  "email": "staff@pharmacy.com",
  "user_name": "Jane Smith",
  "organization_id": null,
  "shop_code": "STORE-001",
  "exp": 1234567890
}
```

**Token Expiry**: 7 days

---

## 🔐 OTP SYSTEM

### Configuration
- **Expiry**: 5 minutes
- **Resend Cooldown**: 30 seconds
- **OTP Length**: 6 digits
- **Testing OTP**: Always `999999`

### Flow
1. User requests OTP with phone + password
2. System validates credentials
3. Generates 6-digit OTP
4. Stores in `otp_verifications` table
5. Sends via SMS (Fast2SMS)
6. Prints in console for testing
7. User submits OTP
8. System verifies and marks as used
9. Returns JWT token

### Master Bypass
- Phone: `+919383169659`
- Password: `test@123`
- OTP: `999999`
- Works for all user types

---

## 📋 PERMISSION SYSTEM

### SuperAdmin
- Full access to everything
- No restrictions

### Admin
- Access limited by `organization_id`
- Can manage:
  - All shops in organization
  - All staff in organization
- Cannot access other organizations

### Staff
- Access limited by `shop_id`
- Permissions controlled by flags:
  - `can_manage_staff`
  - `can_view_analytics`
  - `can_manage_inventory`
  - `can_manage_customers`

---

## 🔄 DATA RELATIONSHIPS

```
SuperAdmin (1)
    ↓
Admin (Many) [grouped by organization_id]
    ↓
Shop (Many) [admin_id + shop_code]
    ↓
Staff (Many) [shop_id]
    ↓
- Salary Records
- Payment Info
- Attendance Records
- Leave Requests
```

### Cascade Deletion
**Delete Shop:**
- Deletes all staff in shop
- Deletes all stock data
- Deletes all audit records

**Delete Admin (last in org):**
- Deletes all shops
- Deletes all staff
- Removes organization

**Delete Admin (others exist):**
- Only deletes admin
- Shops and staff remain

---

## 🔒 SECURITY NOTES

### ⚠️ Security Risks
1. **Plain Password Storage**
   - `plain_password` field stores unencrypted passwords
   - Visible to SuperAdmin
   - Purpose: Customer support
   - **Risk**: Database breach exposes passwords

2. **UUID Login**
   - Legacy staff login without password
   - Less secure
   - Should be deprecated

### ✅ Security Features
1. **Bcrypt Password Hashing**
   - All passwords hashed with bcrypt
   - Truncate error handling for long passwords

2. **JWT Tokens**
   - 7-day expiry
   - Contains user context
   - Stateless authentication

3. **OTP Verification**
   - Time-limited (5 min)
   - One-time use
   - Resend cooldown

4. **Phone Normalization**
   - Enforces +91XXXXXXXXXX format
   - Validates Indian phone numbers

---

## 📞 API ENDPOINTS SUMMARY

### SuperAdmin
- POST `/api/auth/super-admin/send-otp`
- POST `/api/auth/super-admin/verify-otp`
- POST `/api/auth/super-admin/register`
- POST `/api/auth/super-admin/login`
- GET `/api/auth/super-admin/me`
- POST `/api/auth/super-admin/admins`
- GET `/api/auth/super-admin/admins`
- GET `/api/auth/super-admin/dashboard`

### Admin
- POST `/api/auth/admin/signup`
- POST `/api/auth/admin/send-otp`
- POST `/api/auth/admin/verify-otp`
- GET `/api/auth/admin/me`
- POST `/api/auth/admin/shops`
- GET `/api/auth/admin/shops`
- POST `/api/auth/admin/shops/code/{shop_code}/staff`
- GET `/api/auth/admin/all-staff`

### Staff
- POST `/api/auth/staff/signup`
- POST `/api/auth/staff/send-otp`
- POST `/api/auth/staff/verify-otp`
- POST `/api/auth/staff/login` (UUID)
- GET `/api/auth/staff/me`
- GET `/api/auth/staff/shop`

---

## 🎯 KEY CONCEPTS SUMMARY

1. **organization_id**: Groups multiple admins together
2. **shop_code**: Business identifier (not unique globally)
3. **shop_id**: Database ID (unique, used for relationships)
4. **Admins with same organization_id**: Share all shops and staff
5. **Staff belongs to ONE shop**: Identified by shop_id
6. **Token contains shop_code**: For business operations
7. **OTP required**: For all modern logins
8. **Master bypass**: Testing credentials available
9. **Cascade deletion**: Deleting parent deletes children
10. **Plain passwords stored**: For SuperAdmin visibility (security risk)
