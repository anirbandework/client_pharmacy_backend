#!/bin/bash

# Local development startup script

echo "🚀 Starting Pharmacy Management System (Local Development)..."

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DATABASE_URL="postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"

echo "📊 Database: PostgreSQL (local)"
echo "🌐 Starting FastAPI server on http://localhost:8000..."

# Start FastAPI application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
