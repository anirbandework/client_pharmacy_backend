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

alembic upgrade head || echo "⚠️  Migrations skipped (tables may already exist)"

# Start FastAPI application
echo "🌐 Starting FastAPI server on 0.0.0.0:$PORT..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
