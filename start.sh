#!/bin/bash

# Start Redis (if not running)
redis-server --daemonize yes

# Start Celery worker in background
celery -A celery_app worker --loglevel=info &

# Start Celery beat scheduler in background
celery -A celery_app beat --loglevel=info &

# Start FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload