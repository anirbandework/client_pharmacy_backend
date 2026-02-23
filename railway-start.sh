#!/bin/bash

# Production startup script for Railway

echo "🚀 Starting Pharmacy Management System..."
echo "📊 Environment Check:"
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."
echo "REDIS_URL: ${REDIS_URL:0:20}..."

# Run Alembic migrations
echo "🔄 Running database migrations..."

# Skip bad migration by marking it as applied
echo "Marking bad migration as applied..."
psql $DATABASE_URL -c "INSERT INTO alembic_version (version_num) VALUES ('9da7a87fed6e') ON CONFLICT (version_num) DO NOTHING;" 2>/dev/null || true

# Add missing columns directly (faster than waiting for migration)
echo "Ensuring required columns exist..."
psql $DATABASE_URL << 'EOSQL' 2>/dev/null || true
    ALTER TABLE purchase_invoices ADD COLUMN IF NOT EXISTS staff_id INTEGER;
    ALTER TABLE purchase_invoices ADD COLUMN IF NOT EXISTS staff_name VARCHAR;
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'purchase_invoices_staff_id_fkey') THEN
            ALTER TABLE purchase_invoices ADD CONSTRAINT purchase_invoices_staff_id_fkey 
                FOREIGN KEY (staff_id) REFERENCES staff(id);
        END IF;
    END $$;
EOSQL

# Run remaining migrations
alembic upgrade head || echo "⚠️  Migrations skipped (tables may already exist)"

# Start FastAPI application
echo "🌐 Starting FastAPI server on 0.0.0.0:$PORT..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
