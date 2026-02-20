# Customer Tracking Deployment Guide

## Steps to Deploy to Railway

### 1. Push Code to Repository
```bash
git add .
git commit -m "Add Customer Tracking module with database migrations"
git push
```

### 2. After Railway Auto-Deploys
Railway will automatically deploy your code. Once deployment completes:

### 3. Run Migration on Railway Database
Connect to your Railway project and run:

```bash
# SSH into Railway or use Railway CLI
railway run alembic upgrade head
```

OR use Railway's PostgreSQL client to run the migration manually:

```bash
# Get Railway database URL from environment variables
railway variables

# Then run migration
DATABASE_URL="your-railway-postgres-url" alembic upgrade head
```

### 4. Verify Deployment
- Check Railway logs for any errors
- Test the Customer Tracking module in production
- Verify all tabs load correctly

## What This Migration Does

The migration `b3c4d5e6f7g8_fix_customer_tracking_columns.py` adds:

**contact_records table:**
- uploaded_by_staff_id (INTEGER, FK to staff)
- assigned_staff_id (INTEGER, FK to staff)
- created_at (TIMESTAMP)

**refill_reminders table:**
- whatsapp_sent (BOOLEAN)
- whatsapp_sent_date (TIMESTAMP)
- call_reminder_sent (BOOLEAN)
- call_reminder_date (TIMESTAMP)

**customer_purchases table:**
- bill_id (INTEGER, FK to bills)
- refill_reminder_date (DATE)
- created_at (TIMESTAMP)

**Indexes:**
- ix_refill_reminders_reminder_date
- ix_customer_purchases_purchase_date
- ix_customer_purchases_refill_reminder_date

## Safety Features
- Uses `IF NOT EXISTS` to avoid errors if columns already exist
- Safe to run multiple times
- Includes downgrade path for rollback if needed

## Troubleshooting

If migration fails on Railway:
1. Check Railway logs for specific error
2. Verify DATABASE_URL is set correctly
3. Ensure PostgreSQL version compatibility
4. Check if tables exist: `\dt` in psql
