# Railway Deployment Instructions for Split Payment Feature

## Database Migration Required

Before deploying the new code to Railway, you need to run the database migration on the Railway PostgreSQL database.

### Option 1: Run Migration via Railway CLI (Recommended)

1. Install Railway CLI if not already installed:
   ```bash
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Link to your project:
   ```bash
   railway link
   ```

4. Run the migration script:
   ```bash
   railway run python migrate_split_payments.py
   ```

### Option 2: Manual SQL Execution via Railway Dashboard

1. Go to Railway Dashboard → Your Project → PostgreSQL Database
2. Click on "Query" tab
3. Run these SQL commands:

```sql
-- Add split payment columns
ALTER TABLE bills 
ADD COLUMN IF NOT EXISTS cash_amount FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS card_amount FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS online_amount FLOAT DEFAULT 0.0;

-- Drop old payment_method column
ALTER TABLE bills DROP COLUMN IF EXISTS payment_method;
```

### Option 3: Connect to Railway PostgreSQL and Run Migration

1. Get database connection string from Railway Dashboard
2. Update your local `.env` with Railway database URL temporarily
3. Run migration locally:
   ```bash
   python migrate_split_payments.py
   ```

## After Migration

1. Push your code to Railway:
   ```bash
   git add .
   git commit -m "feat: implement split payment system"
   git push
   ```

2. Railway will automatically deploy the new code

## Changes Summary

### Database Schema Changes:
- Added `cash_amount` FLOAT column to bills table
- Added `card_amount` FLOAT column to bills table  
- Added `online_amount` FLOAT column to bills table
- Removed `payment_method` ENUM column from bills table

### Code Changes:
- Updated Bill model to use split payment fields
- Updated BillCreate schema to accept cash/card/online amounts
- Updated billing services to calculate amount_paid from split amounts
- Updated daily records service to use split payment fields
- Updated frontend CreateBill component with split payment UI

## Rollback Plan (if needed)

If you need to rollback:

```sql
-- Add back payment_method column
ALTER TABLE bills ADD COLUMN payment_method VARCHAR(20);

-- Set default values based on split amounts
UPDATE bills 
SET payment_method = CASE 
    WHEN cash_amount > 0 AND card_amount = 0 AND online_amount = 0 THEN 'cash'
    WHEN card_amount > 0 AND cash_amount = 0 AND online_amount = 0 THEN 'card'
    WHEN online_amount > 0 AND cash_amount = 0 AND card_amount = 0 THEN 'online'
    ELSE 'cash'
END;

-- Drop split payment columns
ALTER TABLE bills 
DROP COLUMN cash_amount,
DROP COLUMN card_amount,
DROP COLUMN online_amount;
```
