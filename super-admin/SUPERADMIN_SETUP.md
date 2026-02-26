# SuperAdmin Setup for Production

## 🔐 Security Configuration

### Master Bypass (Development Only)
- **Phone:** +919383169659
- **Password:** test@123
- **OTP:** 999999
- ⚠️ **Only works when `ENVIRONMENT=development`**

### Production SuperAdmins
Two SuperAdmins are automatically created on first deployment:

1. **SuperAdmin 1**
   - Phone: +919383169659
   - Password: test@123

2. **SuperAdmin 2**
   - Phone: +919643579321
   - Password: test@123

## 🚀 Deployment Steps

### 1. Set Environment Variable
In your production environment (Railway/Vercel/etc.), set:
```bash
ENVIRONMENT=production
```

### 2. Automatic Seeding
SuperAdmins are automatically created on first startup when `ENVIRONMENT=production`.

### 3. Manual Seeding (Optional)
If automatic seeding fails, run manually from project root:
```bash
cd /Users/anirbande/Desktop/client\ backend
python super-admin/seed_superadmins.py
```

## 📱 Login Flow

### Production
1. Go to login page
2. Select "Super" tab
3. Enter phone: `9383169659` or `7085144096`
4. Enter password: `test@123`
5. Receive real OTP via SMS
6. Enter OTP to login

### Development (Localhost)
1. Select "Super" tab
2. Enter phone: `9383169659`
3. Enter password: `test@123`
4. OTP is automatically `999999` (no SMS sent)

## 🔧 Environment Variables

### Required for Production
```env
ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
FAST2SMS_API_KEY=your_api_key
JWT_SECRET_KEY=your_secret_key
```

### Development
```env
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/pharmacy_db
REDIS_URL=redis://localhost:6379
```

## ⚠️ Security Notes

1. **Master Bypass Disabled in Production** - The bypass only works when `ENVIRONMENT=development`
2. **Change Passwords** - After first login, change the default passwords
3. **SMS Required** - Production requires valid Fast2SMS API key for OTP delivery
4. **Token Expiry** - JWT tokens expire after 24 hours

## 🔧 Manual Management

### List SuperAdmins
```bash
cd /Users/anirbande/Desktop/client\ backend
python super-admin/manage_superadmins.py list
```

### Add New SuperAdmin
```bash
python super-admin/manage_superadmins.py add +91XXXXXXXXXX "password" "Full Name"
```

### Reset Password
```bash
python super-admin/manage_superadmins.py reset-password +91XXXXXXXXXX "new_password"
```

### Manual Seeding
```bash
python super-admin/seed_superadmins.py
```

## 📊 Verification

Check if SuperAdmins exist:
```bash
# In Python shell
from app.database.database import SessionLocal
from modules.auth.models import SuperAdmin

db = SessionLocal()
admins = db.query(SuperAdmin).all()
for admin in admins:
    print(f"Phone: {admin.phone}, Name: {admin.full_name}")
```
