#!/bin/bash

# Migrate local PostgreSQL data to Railway

echo "📦 Exporting local database..."
PGPASSWORD=pharmacy_pass pg_dump -h localhost -U pharmacy_user -d pharmacy_db --data-only --inserts > data_backup.sql

echo "✅ Data exported to data_backup.sql"
echo ""
echo "📤 To import to Railway, run:"
echo "railway connect Postgres"
echo "Then in psql:"
echo "\\i data_backup.sql"
echo "\\q"
