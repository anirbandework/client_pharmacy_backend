#!/bin/bash

# Production startup script for Railway

echo "🚀 Starting Pharmacy Management System..."

# Start FastAPI application
echo "🌐 Starting FastAPI server on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
