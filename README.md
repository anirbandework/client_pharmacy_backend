# Pharmacy Management System Backend

A Python FastAPI microservice for pharmacy operations management.

## 🚀 Production Deployment

**Ready to deploy?** See [DEPLOYMENT_READY.md](DEPLOYMENT_READY.md) for quick start!

### Deployment Guides
- 📘 [Complete Deployment Guide](DEPLOYMENT_GUIDE.md) - Full Railway + Vercel setup
- 🎨 [Frontend Deployment](FRONTEND_DEPLOYMENT.md) - React + Vite on Vercel
- ⚡ [Quick Reference](QUICK_REFERENCE.md) - Commands & checklist

**Cost**: $20/month for 500 users (Railway Pro + Vercel Free)

---

## Features

1. **Customer Tracking**: Track repeat customers and medicine purchase duration
2. **Invoice Analysis**: Monthly invoice tracking with visual color coding
3. **Stock Audit**: Random section auditing with discrepancy tracking
4. **Daily Records**: Robust daily business recording with modification tracking
5. **Profit Analysis**: Bill-wise profit margin calculation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env` file

3. Install and start Redis:
```bash
brew install redis  # macOS
redis-server
```

4. Run the application:
```bash
./start.sh
```

Or manually:
```bash
# Start Celery worker
celery -A celery_app worker --loglevel=info &

# Start Celery beat
celery -A celery_app beat --loglevel=info &

# Start FastAPI
uvicorn main:app --reload
```

## API Endpoints

### Customers
- `POST /api/customers/` - Create customer
- `GET /api/customers/{id}` - Get customer
- `POST /api/customers/{id}/purchases` - Add purchase
- `GET /api/customers/reminders/pending` - Get pending reminders

### Invoices
- `POST /api/invoices/` - Create invoice
- `GET /api/invoices/monthly/{year}/{month}` - Monthly invoices
- `GET /api/invoices/analytics/{year}/{month}` - Monthly analytics

### Stock
- `POST /api/stock/sections` - Create section
- `POST /api/stock/items` - Add stock item
- `GET /api/stock/audit/random-section` - Random audit
- `PUT /api/stock/items/{id}/audit` - Update physical stock

### Daily Records
- `POST /api/daily-records/` - Create daily record
- `GET /api/daily-records/` - Get all records (with filters)
- `GET /api/daily-records/{id}` - Get specific record
- `GET /api/daily-records/date/{date}` - Get record by date
- `PUT /api/daily-records/{id}` - Update record (tracks modifications)
- `DELETE /api/daily-records/{id}` - Delete record
- `GET /api/daily-records/{id}/modifications` - View modification history
- `POST /api/daily-records/bulk` - Bulk create records
- `GET /api/daily-records/analytics/monthly/{year}/{month}` - Monthly analytics
- `GET /api/daily-records/analytics/variances` - Variance report
- `GET /api/daily-records/analytics/dashboard` - Dashboard summary (last 7 days)
- `POST /api/daily-records/import/excel` - Import from Excel (GMTR0003 format)
- `GET /api/daily-records/export/excel/{year}/{month}` - Export to Excel
- `GET /api/daily-records/audit/logs` - Get audit logs (who created/updated when)
- `GET /api/daily-records/audit/users` - Get all users with activity counts
- `GET /api/daily-records/audit/activity/{id}` - Get complete activity timeline for record

#### AI Analytics (Powered by Gemini AI)
- `GET /api/daily-records/ai-analytics/comprehensive` - Complete AI analysis with trends, predictions, and insights
- `GET /api/daily-records/ai-analytics/trends` - Statistical trends and patterns analysis
- `GET /api/daily-records/ai-analytics/predictions` - Future predictions using machine learning
- `GET /api/daily-records/ai-analytics/chart-data` - Data formatted for frontend charts
- `GET /api/daily-records/ai-analytics/insights` - AI-generated business insights and recommendations
- `GET /api/daily-records/ai-analytics/dashboard` - AI-powered dashboard with key metrics and alerts

### Profit Analysis
- `POST /api/profit/sales-bills` - Create sales bill
- `GET /api/profit/analytics/profit-summary` - Profit summary
- `GET /api/profit/analytics/top-profitable-items` - Top items

## AI Analytics Integration

The system now includes comprehensive AI-powered analytics using Google's Gemini AI:

### Features
- **Trend Analysis**: Statistical analysis of sales patterns, cash management, and bill trends
- **Future Predictions**: Machine learning-based forecasting for sales and cash differences
- **Business Insights**: AI-generated recommendations and improvement suggestions
- **Chart Data**: Ready-to-use data for frontend visualizations
- **Risk Assessment**: Automated alerts for cash discrepancies and performance issues

### Configuration
Add your Gemini API key to `.env`:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### Frontend Integration
See `modules/daily_records/AI_INTEGRATION_GUIDE.md` for complete frontend integration examples with React.js and Vue.js.

## WhatsApp Integration

Configure WhatsApp Business API credentials in `.env`:
- `WHATSAPP_API_URL`: Your WhatsApp Business API endpoint
- `WHATSAPP_TOKEN`: Your access token

## Database

Uses SQLite by default. For production, change `DATABASE_URL` to PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost/pharmacy_db
```

## Background Tasks

- Daily reminder checks
- WhatsApp notifications for cash differences
- Automatic customer reminders

Access API documentation at: http://localhost:8000/docs