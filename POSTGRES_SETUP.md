# PostgreSQL Setup Guide

## ✅ Setup Complete!

Your application is now configured to use PostgreSQL both locally and on Railway.

## Local Development

### Database Info
- **Database**: `pharmacy_db`
- **User**: `pharmacy_user`
- **Password**: `pharmacy_pass`
- **Connection**: `postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db`

### Start Application
```bash
./start_local.sh
```

Or manually:
```bash
source venv/bin/activate
export DATABASE_URL="postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"
uvicorn main:app --reload
```

### Reset Database
If you need to recreate the database:
```bash
./setup_postgres.sh
python init_postgres.py
```

## Railway Deployment

### Setup Steps
1. Go to your Railway project dashboard
2. Click "New" → "Database" → "Add PostgreSQL"
3. Railway automatically creates `DATABASE_URL` environment variable
4. Push your code - Railway will automatically connect to PostgreSQL

### Environment Variables on Railway
Railway automatically provides:
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Application port

Your code already handles the Railway PostgreSQL URL format conversion.

## Files Modified

1. **`.env`** - Updated to use PostgreSQL by default
2. **`alembic/env.py`** - Reads DATABASE_URL from environment
3. **`app/database/database.py`** - Already PostgreSQL-ready
4. **`setup_postgres.sh`** - Database initialization script
5. **`init_postgres.py`** - Creates all tables from models
6. **`start_local.sh`** - Local development startup script

## Switching Between SQLite and PostgreSQL

### Use SQLite (for testing)
```bash
export DATABASE_URL="sqlite:///./app/database/pharmacy.db"
```

### Use PostgreSQL
```bash
export DATABASE_URL="postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"
```

## Database Management

### Connect to PostgreSQL
```bash
psql pharmacy_db
```

### View Tables
```sql
\dt
```

### View Table Structure
```sql
\d table_name
```

### Backup Database
```bash
pg_dump pharmacy_db > backup.sql
```

### Restore Database
```bash
psql pharmacy_db < backup.sql
```

## Troubleshooting

### Connection Refused
Make sure PostgreSQL is running:
```bash
brew services start postgresql@14
```

### Permission Denied
Grant permissions:
```bash
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE pharmacy_db TO pharmacy_user;"
```

### Reset Everything
```bash
psql postgres -c "DROP DATABASE IF EXISTS pharmacy_db;"
psql postgres -c "CREATE DATABASE pharmacy_db OWNER pharmacy_user;"
python init_postgres.py
```
