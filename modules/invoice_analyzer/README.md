# Purchase Invoice Analyzer

A comprehensive system for tracking purchase invoices, monitoring stock movement, managing expiry alerts, and providing AI-powered analytics for pharmacy inventory management.

## 🎯 Features

### Core Functionality
- **Invoice Tracking**: Complete purchase invoice management with automatic calculations
- **Color-Coded Status**: Visual representation of invoice status (Green/Yellow/Red)
- **Item Movement Analysis**: Track sales velocity and movement patterns
- **Expiry Management**: Automated alerts for items approaching expiry (45 days, 1 year)
- **Monthly Summaries**: Comprehensive monthly analytics with color coding
- **AI Analytics**: Machine learning-powered insights and predictions

### Visual Color Coding System
- 🟢 **Green**: Invoice completely sold out (95%+ sold)
- 🟡 **Yellow**: Invoice partially sold (30-94% sold)
- 🔴 **Red**: Invoice not sold or slow moving (<30% sold)

### Monthly Color Coding
- 🟢 **Green Month**: All invoices in the month are sold out
- 🟡 **Yellow Month**: 70%+ invoices are green or yellow
- 🔴 **Red Month**: Less than 70% invoices are performing well

## 📊 AI Analytics - 5 Parameter Learning System

The AI system analyzes item movement using 5 key parameters:

1. **Velocity**: Average movement rate (items sold per day)
2. **Seasonality**: Seasonal demand patterns and trends
3. **Profitability**: Profit margins and financial performance
4. **Expiry Risk**: Risk assessment based on expiry dates
5. **Demand Consistency**: Consistency of demand over time

## 🚀 API Endpoints

### Purchase Invoice Management

#### Create Purchase Invoice
```http
POST /api/invoices/
```
**Request Body:**
```json
{
  \"invoice_number\": \"INV-2024-001\",
  \"supplier_name\": \"ABC Pharmaceuticals\",
  \"invoice_date\": \"2024-01-15\",
  \"received_date\": \"2024-01-16\",
  \"items\": [
    {
      \"item_code\": \"MED001\",
      \"item_name\": \"Paracetamol 500mg\",
      \"batch_number\": \"BATCH001\",
      \"purchased_quantity\": 100,
      \"unit_cost\": 5.50,
      \"selling_price\": 8.00,
      \"expiry_date\": \"2025-12-31\"
    }
  ]
}
```

#### Get Monthly Invoices
```http
GET /api/invoices/monthly/{year}/{month}?shop_id=1
```

#### Get Invoice Details
```http
GET /api/invoices/{invoice_id}
```

### Sales Recording

#### Record Item Sale
```http
POST /api/invoices/sales
```
**Request Body:**
```json
{
  \"item_id\": 1,
  \"quantity_sold\": 10,
  \"sale_price\": 8.00,
  \"customer_type\": \"regular\"
}
```

### Expiry Management

#### Get Expiry Alerts
```http
GET /api/invoices/expiry/alerts?days_ahead=45&shop_id=1
```

#### Acknowledge Expiry Alert
```http
PUT /api/invoices/expiry/alerts/{alert_id}/acknowledge
```
**Request Body:**
```json
{
  \"acknowledged_by\": \"pharmacist_name\"
}
```

### Analytics

#### Monthly Analytics
```http
GET /api/invoices/analytics/{year}/{month}?shop_id=1
```

#### Monthly Summary
```http
GET /api/invoices/analytics/monthly-summary/{year}/{month}?shop_id=1
```

### AI Analytics

#### Comprehensive AI Analysis
```http
GET /api/invoices/ai-analytics/comprehensive?shop_id=1
```

#### Item Movement Analysis (5 Parameters)
```http
GET /api/invoices/ai-analytics/item-movement/{item_code}?shop_id=1
```

#### Stock Predictions
```http
GET /api/invoices/ai-analytics/stock-predictions?months_ahead=3&shop_id=1
```

### Dashboard

#### Dashboard Summary
```http
GET /api/invoices/dashboard?shop_id=1
```

### Utility Endpoints

#### Slow Moving Items
```http
GET /api/invoices/items/slow-moving?threshold=1.0&shop_id=1
```

#### Expiring Items
```http
GET /api/invoices/items/expiring-soon?days=45&shop_id=1
```

## 🔧 Setup Instructions

### 1. Database Setup

Add the new models to your database initialization:

```python
# In create_tables.py or init_db.py
from modules.invoice_analyzer.models import (
    PurchaseInvoice, PurchaseInvoiceItem, ItemSale, 
    ExpiryAlert, MonthlyInvoiceSummary
)

# The tables will be created automatically
```

### 2. Environment Configuration

Add to your `.env` file:
```env
# AI Analytics (Optional but recommended)
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Router Integration

Add to your `main.py`:
```python
from modules.invoice_analyzer.routes import router as invoice_analyzer_router

app.include_router(invoice_analyzer_router)
```

### 4. Background Tasks (Optional)

Add daily expiry check task to your Celery configuration:
```python
from celery import Celery
from modules.invoice_analyzer.service import PurchaseInvoiceService

@celery.task
def daily_expiry_check():
    # Check for items expiring in 45 days and send alerts
    pass
```

## 📈 Usage Examples

### 1. Creating a Purchase Invoice

```python
import requests

invoice_data = {
    \"invoice_number\": \"INV-2024-001\",
    \"supplier_name\": \"MediSupply Co.\",
    \"invoice_date\": \"2024-01-15\",
    \"received_date\": \"2024-01-16\",
    \"items\": [
        {
            \"item_code\": \"PARA500\",
            \"item_name\": \"Paracetamol 500mg\",
            \"purchased_quantity\": 500,
            \"unit_cost\": 2.50,
            \"selling_price\": 4.00,
            \"expiry_date\": \"2025-12-31\"
        }
    ]
}

response = requests.post(\"http://localhost:8000/api/invoices/\", json=invoice_data)
print(response.json())
```

### 2. Recording Sales

```python
sale_data = {
    \"item_id\": 1,
    \"quantity_sold\": 50,
    \"sale_price\": 4.00,
    \"customer_type\": \"walk-in\"
}

response = requests.post(\"http://localhost:8000/api/invoices/sales\", json=sale_data)
```

### 3. Getting Monthly Analytics

```python
response = requests.get(\"http://localhost:8000/api/invoices/analytics/2024/1\")
analytics = response.json()

print(f\"Total Invoices: {analytics['total_invoices']}\")
print(f\"Sold Out: {analytics['sold_out_invoices']}\")
print(f\"Average Sold %: {analytics['average_sold_percentage']:.1f}%\")
```

## 🤖 AI Integration

### Setting up Gemini AI

1. Get API key from Google AI Studio
2. Add to environment variables
3. The system will automatically use AI for:
   - Movement pattern analysis
   - Seasonal trend detection
   - Stock requirement predictions
   - Business insights generation

### AI Response Format

```json
{
  \"movement_patterns\": [
    {
      \"pattern_type\": \"fast_moving\",
      \"items\": [\"MED001\", \"MED002\"],
      \"description\": \"High turnover items\",
      \"recommendation\": \"Increase stock levels\"
    }
  ],
  \"seasonal_trends\": [...],
  \"expiry_predictions\": [...],
  \"stock_recommendations\": [...],
  \"profit_optimization\": [...]
}
```

## 📊 Dashboard Integration

The system provides a comprehensive dashboard endpoint that returns:

- Current month summary with color coding
- Pending expiry alerts (prioritized)
- Recent invoices with status
- Top moving items analytics
- AI-powered insights and recommendations

## 🔔 Alert System

### Automatic Alerts

1. **45-Day Expiry Alert**: Items expiring within 45 days
2. **1-Year Alert**: Items with less than 1 year shelf life on receipt
3. **Expired Alert**: Items that have already expired
4. **Daily Notifications**: WhatsApp integration for critical alerts

### Alert Priorities

- **Critical**: Expired items
- **High**: Items expiring within 15 days
- **Medium**: Items expiring within 45 days
- **Low**: Items with less than 1 year shelf life

## 🎨 Frontend Integration

### Color Coding CSS Classes

```css
.invoice-green { background-color: #d4edda; border-color: #c3e6cb; }
.invoice-yellow { background-color: #fff3cd; border-color: #ffeaa7; }
.invoice-red { background-color: #f8d7da; border-color: #f5c6cb; }

.month-green { background: linear-gradient(135deg, #d4edda, #c3e6cb); }
.month-yellow { background: linear-gradient(135deg, #fff3cd, #ffeaa7); }
.month-red { background: linear-gradient(135deg, #f8d7da, #f5c6cb); }
```

### React Component Example

```jsx
function InvoiceCard({ invoice }) {
  const getColorClass = (colorCode) => {
    return `invoice-${colorCode}`;
  };

  return (
    <div className={`invoice-card ${getColorClass(invoice.color_code)}`}>
      <h3>{invoice.invoice_number}</h3>
      <p>Sold: {invoice.sold_percentage.toFixed(1)}%</p>
      <p>Status: {invoice.status}</p>
      {invoice.has_expiring_items && (
        <div className=\"expiry-warning\">
          ⚠️ Items expiring soon
        </div>
      )}
    </div>
  );
}
```

## 🔍 Monitoring & Maintenance

### Daily Tasks
- Check expiry alerts
- Review slow-moving items
- Monitor invoice status changes
- Update AI analytics

### Weekly Tasks
- Review monthly summaries
- Analyze movement patterns
- Update stock predictions
- Generate business reports

### Monthly Tasks
- Complete month-end analysis
- Update seasonal factors
- Review AI insights
- Plan inventory adjustments

## 🚨 Troubleshooting

### Common Issues

1. **AI Analytics Not Working**
   - Check GEMINI_API_KEY in environment
   - Verify API key permissions
   - Check network connectivity

2. **Color Coding Not Updating**
   - Ensure sales are being recorded properly
   - Check invoice status calculation logic
   - Verify database updates

3. **Expiry Alerts Not Showing**
   - Check expiry_date format in items
   - Verify alert creation logic
   - Check database constraints

### Performance Optimization

- Index frequently queried fields
- Implement caching for analytics
- Use background tasks for heavy calculations
- Optimize AI API calls

## 📝 License

This module is part of the Pharmacy Management System and follows the same licensing terms.