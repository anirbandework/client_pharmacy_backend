# Pharmacy Management System - Modular Architecture

## Directory Structure

```
modules/
├── customer_tracking/     # Regular customer tracking & reminders
├── invoice_analyzer/      # Monthly invoice analysis with color coding
├── stock_audit/          # Random section auditing
├── daily_records/        # Daily business records with modification tracking
└── profit_analysis/      # Bill-wise profit margin calculation
```

## Module Details

### 1. Customer Tracking (`/api/customers`)
- Track repeat customers
- Record medicine purchase duration
- Send reminders 5 days before medicine exhaustion
- WhatsApp notifications + staff call list

### 2. Invoice Analyzer (`/api/invoices`)
- Monthly invoice recording
- Color-coded visualization based on stock sold percentage
- Red (<30%), Yellow (30-70%), Green (>70%)

### 3. Stock Audit (`/api/stock`)
- Database of all store sections and racks
- Random section audit requests
- Physical vs software stock reconciliation
- Discrepancy tracking

### 4. Daily Records (`/api/daily-records`)
- Robust daily business recording
- Modification tracking with history
- WhatsApp alerts for cash differences exceeding threshold
- Protection against accidental overwrites

### 5. Profit Analysis (`/api/profit`)
- Bill-wise profit margin calculation
- WINGS POS data import capability
- Top profitable items analysis
- Profit summary analytics

## Usage

Import all modules in `app.py`:
```python
from modules.customer_tracking.routes import router as customer_router
from modules.invoice_analyzer.routes import router as invoice_router
from modules.stock_audit.routes import router as stock_router
from modules.daily_records.routes import router as daily_records_router
from modules.profit_analysis.routes import router as profit_router
```