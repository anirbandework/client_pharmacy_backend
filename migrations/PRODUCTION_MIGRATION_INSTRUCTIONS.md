# Production Database Migration Instructions

## Database Details
- Host: nozomi.proxy.rlwy.net:12024
- Database: railway
- User: postgres
- Password: HEAHpjfIJVvRPOwgtcbLnATZUGPCYVLA

## Run Migration on Production

### Option 1: Using psql command
```bash
psql postgresql://postgres:HEAHpjfIJVvRPOwgtcbLnATZUGPCYVLA@nozomi.proxy.rlwy.net:12024/railway -f migrations/add_shop_id_to_salary_tables.sql
```

### Option 2: Copy-paste SQL directly
Connect to production database and run the SQL from `migrations/add_shop_id_to_salary_tables.sql`

## Migration Status

### Local Database: ✅ COMPLETED
- salary_records: shop_id column added
- staff_payment_info: shop_id column added (1 row updated)
- salary_alerts: shop_id column added
- All foreign keys and indexes created

### Production Database: ✅ COMPLETED
- salary_records: shop_id column added
- staff_payment_info: shop_id column added (2 rows updated)
- salary_alerts: shop_id column added
- All foreign keys and indexes created

## Verification
After running on production, verify with:
```sql
SELECT COUNT(*) FROM salary_records WHERE shop_id IS NULL;
SELECT COUNT(*) FROM staff_payment_info WHERE shop_id IS NULL;
SELECT COUNT(*) FROM salary_alerts WHERE shop_id IS NULL;
```
All should return 0.
