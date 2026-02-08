#!/bin/bash

# Production startup script for Railway

echo "🚀 Starting Pharmacy Management System..."

# Start Celery worker in background
echo "📦 Starting Celery worker..."
celery -A celery_app worker --loglevel=info --detach

# Start Celery beat scheduler in background
echo "⏰ Starting Celery beat..."
celery -A celery_app beat --loglevel=info --detach

# Wait a moment for workers to initialize
sleep 2

# Start FastAPI application
echo "🌐 Starting FastAPI server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
