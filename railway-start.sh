#!/bin/bash

# Production startup script for Railway

echo "🚀 Starting Pharmacy Management System..."
echo "📊 Environment Check:"
echo "PORT: $PORT"
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."

# Skip Alembic migrations - tables created by SQLAlchemy
echo "⚠️  Skipping Alembic migrations (using SQLAlchemy create_all)"

# Start FastAPI application
echo "🌐 Starting FastAPI server on 0.0.0.0:$PORT..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info
