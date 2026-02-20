#!/bin/bash

# Setup PostgreSQL for local development

echo "🔧 Setting up PostgreSQL for Pharmacy Management System..."

# Create database and user
psql postgres << EOF
-- Create user if not exists
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'pharmacy_user') THEN
    CREATE USER pharmacy_user WITH PASSWORD 'pharmacy_pass';
  END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE pharmacy_db OWNER pharmacy_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'pharmacy_db')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pharmacy_db TO pharmacy_user;

\c pharmacy_db
GRANT ALL ON SCHEMA public TO pharmacy_user;
EOF

echo "✅ PostgreSQL setup complete!"
echo ""
echo "Database: pharmacy_db"
echo "User: pharmacy_user"
echo "Password: pharmacy_pass"
echo ""
echo "Connection string: postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"
