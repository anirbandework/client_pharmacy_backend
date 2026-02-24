# Stock Audit Module

Comprehensive inventory management system with rack/section organization, purchase/sale tracking, physical audits, and AI-powered analytics.

## Overview

This module manages complete stock lifecycle from purchase to sale, with physical audit capabilities, discrepancy tracking, and AI-powered insights using Gemini 2.0 Flash.

## Architecture

```
stock_audit/
├── models.py          # 10 database models for complete inventory system
├── schemas.py         # Pydantic validation schemas
├── routes.py          # 40+ FastAPI endpoints
├── services.py        # Business logic (calculations, audits, reports)
├── sync_service.py    # Invoice-to-stock synchronization
└── ai_service.py      # AI analytics with Gemini 2.0 Flash
```

## Database Schema

### 1. StockRack
Physical storage racks in the shop.
- `rack_number`: Unique identifier (e.g., "R1", "R2")
- `location`: Physical location description
- `description`: Additional notes

### 2. StockSection
Sections within racks for organized storage.
- `section_name`: Display name (e.g., "Antibiotics", "Pain Relief")
- `section_code`: Unique code (e.g., "R1-S1")
- `rack_id`: Foreign key to StockRack

### 3. StockItem
Core inventory items with complete tracking.
- **Product Info**: manufacturer, hsn_code, product_name, batch_number, package
- **Quantities**: quantity_software (calculated), quantity_physical (audited)
- **Pricing**: mrp, unit_price, expiry_date
- **Audit Tracking**: last_audit_date, last_audit_by_staff_id, audit_discrepancy
- **Source**: source_invoice_id (links to PurchaseInvoice)
- **Location**: section_id (can be null for unassigned items)

### 4. Purchase
Purchase transactions from suppliers.
- `purchase_date`, `supplier_name`, `invoice_number`
- `total_amount`, `staff_id`, `staff_name`

### 5. PurchaseItem
Line items for purchases.
- `stock_item_id`, `batch_number`
- `quantity`, `unit_cost`, `total_cost`

### 6. Sale
Sales transactions to customers.
- `sale_date`, `customer_phone`, `bill_number`
- `total_amount`, `staff_id`, `staff_name`

### 7. SaleItem
Line items for sales.
- `stock_item_id`, `batch_number`
- `quantity`, `unit_price`, `total_price`

### 8. StockAuditRecord
Physical audit records with discrepancy tracking.
- `audit_date`, `software_quantity`, `physical_quantity`, `discrepancy`
- `notes`, `reason_for_discrepancy`
- `resolved`, `resolved_date`, `resolution_notes`

### 9. StockAuditSession
Audit session tracking for staff.
- `session_date`, `sections_audited`, `items_audited`, `discrepancies_found`
- `status` (in_progress/completed), `started_at`, `completed_at`

### 10. StockAdjustment
Manual stock adjustments (damages, returns, corrections).
- `adjustment_type`, `quantity_change`, `reason`, `notes`
- `staff_id`, `staff_name`, `adjustment_date`

## API Endpoints

### Rack Management

#### POST /racks
Create new storage rack.
```json
{
  "rack_number": "R1",
  "location": "Main Store - Left Wall",
  "description": "Antibiotics and Pain Relief"
}
```

#### GET /racks
List all racks for shop.

#### PUT /racks/{rack_id}
Update rack details.

#### DELETE /racks/{rack_id}
Delete rack (cascades to sections and items).

### Section Management

#### POST /sections
Create new section within rack.
```json
{
  "rack_id": 1,
  "section_name": "Antibiotics",
  "section_code": "R1-S1"
}
```

#### GET /sections?rack_id={rack_id}
List sections, optionally filtered by rack.

#### PUT /sections/{section_id}
Update section details.

#### DELETE /sections/{section_id}
Delete section (cascades to items).

### Stock Item Management

#### POST /items
Add new stock item manually.
```json
{
  "manufacturer": "ELEG",
  "hsn_code": "30042064",
  "product_name": "Paracetamol 500mg",
  "batch_number": "4D116",
  "package": "10 X 6",
  "expiry_date": "2026-11-01",
  "mrp": "69.00/STRIP",
  "unit_price": 74.45,
  "section_id": 1,
  "quantity_software": 5
}
```

#### GET /items
List stock items with filters.
- Query params: `section_id`, `item_name`, `batch_number`, `skip`, `limit`
- Returns: Items with section_name, rack_name, total_value

#### GET /items/{item_id}
Get specific stock item with full details.

#### PUT /items/{item_id}
Update stock item details.

#### DELETE /items/{item_id}
Delete stock item.

#### GET /items/unassigned/list
Get items without assigned rack/section.

#### PATCH /items/{item_id}/assign-section
Assign section to unassigned item.
```json
{
  "section_id": 1
}
```

### Purchase Management

#### POST /purchases
Add purchase and auto-update stock.
```json
{
  "purchase": {
    "purchase_date": "2024-01-15",
    "supplier_name": "ABC Pharmaceuticals",
    "invoice_number": "INV-001",
    "total_amount": 15000.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "4D116",
      "quantity": 10,
      "unit_cost": 74.45,
      "total_cost": 744.50
    }
  ]
}
```
**Process**: Creates purchase record + items, increments quantity_software

#### GET /purchases
List purchases with filters.
- Query params: `start_date`, `end_date`, `supplier_name`, `skip`, `limit`

#### PUT /purchases/{purchase_id}
Update purchase record.

#### DELETE /purchases/{purchase_id}
Delete purchase (does NOT reverse stock).

### Sales Management

#### POST /sales
Add sale and auto-update stock.
```json
{
  "sale": {
    "sale_date": "2024-01-15",
    "customer_phone": "9876543210",
    "bill_number": "BILL-001",
    "total_amount": 500.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "4D116",
      "quantity": 2,
      "unit_price": 100.00,
      "total_price": 200.00
    }
  ]
}
```
**Process**: 
- Validates stock availability
- Creates sale record + items
- Decrements quantity_software
- Raises error if insufficient stock

#### GET /sales
List sales with filters.
- Query params: `start_date`, `end_date`, `customer_phone`, `skip`, `limit`

#### PUT /sales/{sale_id}
Update sale record.

#### DELETE /sales/{sale_id}
Delete sale (does NOT reverse stock).

### Audit Functionality

#### GET /audit/random-section
Get random section for audit (excludes recently audited).
```json
{
  "section": {...},
  "items_to_audit": [...],
  "total_items": 25,
  "message": "Audit section Antibiotics in rack R1"
}
```

#### POST /audit/sessions
Start new audit session.
```json
{
  "session_notes": "Monthly audit - January 2024"
}
```

#### PUT /items/{item_id}/audit
Record physical audit result.
```json
{
  "physical_quantity": 8,
  "notes": "Found 2 units missing"
}
```
**Process**:
- Creates StockAuditRecord
- Updates quantity_physical
- Calculates discrepancy (software - physical)
- Updates last_audit_date and audited_by

#### GET /audit/discrepancies?threshold=0
Get all discrepancies above threshold.
```json
{
  "total_discrepancies": 15,
  "threshold": 0,
  "discrepancies": [
    {
      "item": {...},
      "software_qty": 10,
      "physical_qty": 8,
      "difference": 2,
      "section_name": "Antibiotics",
      "rack_number": "R1"
    }
  ]
}
```

#### GET /audit/summary
Get overall audit summary.
```json
{
  "total_items": 500,
  "total_sections": 20,
  "items_with_discrepancies": 15,
  "last_audit_date": "2024-01-15T10:30:00",
  "last_audited_by": "John Doe",
  "pending_audits": 100,
  "audit_completion_rate": 80.0
}
```

### Stock Calculations

#### POST /calculate-stock
Recalculate software stock for all items.
**Formula**: quantity_software = total_purchased - total_sold

#### GET /items/{item_id}/stock-calculation
Get detailed calculation for specific item.
```json
{
  "item": {...},
  "calculated_stock": 8,
  "current_software_stock": 8,
  "total_purchased": 10,
  "total_sold": 2,
  "purchase_transactions": 1,
  "sale_transactions": 1
}
```

### Reports

#### GET /reports/low-stock?threshold=10
Get items below threshold.

#### GET /reports/expiring?days_ahead=30
Get items expiring within days.

#### GET /reports/stock-movement?start_date=2024-01-01&end_date=2024-01-31
Get stock movement report.
```json
{
  "period": "2024-01-01 to 2024-01-31",
  "total_purchases": 50,
  "total_purchase_value": 150000.00,
  "total_sales": 120,
  "total_sales_value": 180000.00,
  "net_movement": 30000.00
}
```

### Stock Adjustments

#### POST /adjustments
Create manual adjustment.
```json
{
  "stock_item_id": 1,
  "adjustment_type": "damage",
  "quantity_change": -2,
  "reason": "Expired items",
  "notes": "Found 2 expired strips"
}
```
**Types**: damage, return, correction, found, lost

#### GET /adjustments
List adjustments with filters.
- Query params: `stock_item_id`, `adjustment_type`, `skip`, `limit`

### AI Analytics

#### GET /ai-analytics/comprehensive?days=30
Get complete AI analysis.
```json
{
  "summary": {
    "total_audits": 150,
    "total_items": 500,
    "items_with_discrepancies": 15,
    "total_discrepancy_value": 50,
    "audit_completion_rate": 80.0
  },
  "charts": {
    "discrepancy_trend": {...},
    "section_discrepancies": {...},
    "staff_performance": {...}
  },
  "ai_insights": {
    "findings": [...],
    "risks": [...],
    "recommendations": [...],
    "predictions": [...]
  }
}
```

#### GET /ai-analytics/charts?days=30
Get chart data for visualization.

#### GET /ai-analytics/insights?days=30
Get AI-generated insights only.

### Excel Export

#### GET /export/stock-items
Export all stock items to Excel.

#### GET /export/audit-records?days=30
Export audit records to Excel.

#### GET /export/adjustments?days=30
Export adjustments to Excel.

## Data Flow

### Purchase Flow
```
1. POST /purchases
   ↓
2. Create Purchase record
   ↓
3. Create PurchaseItem records
   ↓
4. For each item:
   - Find StockItem by stock_item_id
   - Increment quantity_software
   - Update updated_at
   ↓
5. Commit transaction
```

### Sale Flow
```
1. POST /sales
   ↓
2. Validate stock availability
   ↓
3. Create Sale record
   ↓
4. Create SaleItem records
   ↓
5. For each item:
   - Find StockItem by stock_item_id
   - Check quantity_software >= quantity
   - Decrement quantity_software
   - Update updated_at
   ↓
6. Commit transaction
```

### Audit Flow
```
1. GET /audit/random-section
   ↓
2. Select section not audited in last 7 days
   ↓
3. Return section + items to audit
   ↓
4. Staff counts physical stock
   ↓
5. PUT /items/{item_id}/audit
   ↓
6. Create StockAuditRecord
   ↓
7. Update StockItem:
   - quantity_physical = counted value
   - audit_discrepancy = software - physical
   - last_audit_date = now
   - last_audit_by = staff
   ↓
8. Return audit record
```

### Invoice Sync Flow
```
1. Invoice verified (PUT /invoice-analyzer/{id})
   ↓
2. InvoiceStockSyncService.sync_invoice_to_stock()
   ↓
3. For each invoice item:
   - Check if StockItem exists (product_name + batch_number)
   - If exists: Add to quantity_software
   - If not: Create new StockItem with section_id=null
   ↓
4. Return sync result
   ↓
5. Staff assigns sections to unassigned items
```

## Invoice Analyzer Integration

### Overview
The Stock Audit system is tightly integrated with the Invoice Analyzer. Verified invoices automatically create or update stock items, eliminating manual data entry and ensuring accuracy.

### Connection Architecture
```
Invoice Analyzer          →          Stock Audit
─────────────────                    ────────────
PurchaseInvoice                      StockItem
PurchaseInvoiceItem                  (quantity_software)
     ↓                                    ↑
     └──── InvoiceStockSyncService ──────┘
```

### Automatic Sync Process

**Trigger**: When invoice is verified via `PUT /invoice-analyzer/{invoice_id}`

**Service**: `InvoiceStockSyncService.sync_invoice_to_stock()`

**Location**: `modules/stock_audit/sync_service.py`

### Sync Logic

For each `PurchaseInvoiceItem` in the verified invoice:

1. **Match Existing Stock**:
   ```python
   existing_item = db.query(StockItem).filter(
       StockItem.shop_id == shop_id,
       StockItem.product_name == invoice_item.product_name,
       StockItem.batch_number == invoice_item.batch_number
   ).first()
   ```

2. **If Item Exists**:
   - **Action**: Add to existing quantity
   - **Update**: `quantity_software += invoice_quantity`
   - **Log**: "Updated stock item {id}: +{quantity}"

3. **If Item is New**:
   - **Action**: Create new StockItem
   - **Fields Synced**:
     - manufacturer, hsn_code, product_name, batch_number
     - package, expiry_date, mrp, unit_price
     - quantity_software = invoice quantity
     - source_invoice_id = invoice.id
     - section_id = null (unassigned)
   - **Log**: "Created stock item {id}: {product_name}"

### Sync Result
```json
{
  "invoice_id": 1,
  "new_items": 15,
  "updated_items": 10,
  "synced_item_ids": [101, 102, 103],
  "updated_item_ids": [50, 51, 52]
}
```

### Unassigned Items Management

New items from invoices are created with `section_id=null`:

**Why?**
- Staff needs to physically place items in racks/sections
- Automatic assignment could be incorrect
- Allows for organized stock placement

**Workflow**:

1. **View Unassigned Items**:
   ```bash
   GET /stock-audit/items/unassigned/list
   ```
   Returns all items with `section_id=null`

2. **Assign Section**:
   ```bash
   PATCH /stock-audit/items/{item_id}/assign-section
   Body: {"section_id": 1}
   ```

3. **Item Now Available**:
   - Appears in section views
   - Included in audits
   - Shows in reports

### Stock Reversal on Invoice Deletion

When invoice is deleted via `DELETE /invoice-analyzer/{invoice_id}`:

```python
# Automatic reversal process
if invoice.is_verified:
    for invoice_item in invoice.items:
        stock_item = find_matching_stock_item(invoice_item)
        
        if stock_item:
            # Subtract quantity
            stock_item.quantity_software -= int(invoice_item.quantity)
            
            # Delete if quantity becomes 0 or negative
            if (stock_item.quantity_software <= 0 and 
                stock_item.source_invoice_id == invoice_id):
                db.delete(stock_item)
                logger.info(f"Deleted stock item {stock_item.id}")
            else:
                logger.info(f"Reversed stock: -{invoice_item.quantity}")
```

### Data Mapping

| Invoice Field | Stock Field | Notes |
|--------------|-------------|-------|
| manufacturer | manufacturer | 4-letter code (e.g., "ELEG") |
| hsn_code | hsn_code | 8-digit code |
| product_name | product_name | **Match key** |
| batch_number | batch_number | **Match key** |
| package | package | e.g., "10 X 6" |
| expiry_date | expiry_date | DATE format |
| mrp | mrp | String (e.g., "69.00/STRIP") |
| quantity | quantity_software | Integer |
| unit_price | unit_price | Float |
| invoice.id | source_invoice_id | Audit trail |

### Integration Points

| Invoice Event | Stock Action | Automatic? |
|--------------|--------------|------------|
| Upload PDF | None | - |
| Verify Invoice | **Create/Update StockItems** | ✅ Yes |
| Update Invoice | **Re-sync (delete old + create new)** | ✅ Yes |
| Delete Invoice | **Reverse quantities** | ✅ Yes |

### Complete Integration Workflow

```python
# Step 1: Upload and verify invoice
response = requests.post('/invoice-analyzer/upload', files={'file': pdf})
invoice = response.json()
# Status: Invoice created, NOT synced yet

response = requests.put(f'/invoice-analyzer/{invoice["id"]}', json=verified_data)
# Status: Invoice verified, AUTOMATICALLY synced to stock
# Result: 15 new StockItems created

# Step 2: View unassigned items from invoice
response = requests.get('/stock-audit/items/unassigned/list')
unassigned = response.json()  # 15 items

# Step 3: Assign sections (staff organizes physical stock)
for item in unassigned:
    section_id = determine_section_for_item(item)
    requests.patch(f'/stock-audit/items/{item["id"]}/assign-section',
                   json={"section_id": section_id})

# Step 4: Items now in stock system
response = requests.get('/stock-audit/items')
all_items = response.json()  # Includes invoice items

# Step 5: Conduct physical audit
response = requests.get('/stock-audit/audit/random-section')
section = response.json()
for item in section['items_to_audit']:
    physical_count = count_physical_stock(item)
    requests.put(f'/stock-audit/items/{item["id"]}/audit',
                 json={"physical_quantity": physical_count})

# Step 6: Track discrepancies
response = requests.get('/stock-audit/audit/discrepancies')
discrepancies = response.json()
# Shows: Software qty (from invoice) vs Physical qty (from audit)

# Step 7: If invoice needs correction
response = requests.delete(f'/invoice-analyzer/{invoice["id"]}')
# Status: Invoice deleted, stock quantities automatically reversed
```

### Stock Quantity Tracking

**quantity_software** (Calculated from invoices):
- Starts at 0
- **Increases** when invoice verified (+quantity)
- **Decreases** when sale recorded (-quantity)
- **Adjusts** when invoice deleted (-quantity)
- **Corrects** via manual adjustments

**quantity_physical** (From audits):
- Starts at null
- **Set** when physical audit conducted
- **Compared** to quantity_software
- **Discrepancy** = software - physical

### Error Handling

**Sync Failure**:
```python
# Invoice saves even if sync fails
try:
    sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)
    logger.info(f"✅ Synced: {sync_result}")
except Exception as e:
    logger.error(f"❌ Sync failed: {e}")
    # Invoice is saved, can retry sync manually
```

**Duplicate Batches**:
- Same product + batch → Updates existing quantity
- Same product + different batch → Creates new StockItem

**Reversal Failure**:
```python
# Deletion continues even if reversal fails
try:
    reverse_stock_quantities()
except Exception as e:
    logger.error(f"Reversal failed: {e}")
    # Invoice still deleted, stock can be corrected manually
```

### Benefits of Integration

1. **Zero Manual Entry**: Stock auto-populated from invoices
2. **Batch Tracking**: Separate stock items per batch number
3. **Expiry Management**: Expiry dates tracked from invoice
4. **Price Accuracy**: Unit prices and MRP from invoice
5. **Audit Trail**: source_invoice_id links stock to invoice
6. **Automatic Updates**: Quantities adjust with invoice changes
7. **Discrepancy Detection**: Compare invoice qty vs physical count

### Troubleshooting

**Items not appearing in stock**:
- Check if invoice is verified (is_verified=true)
- Check sync logs for errors
- Manually trigger sync if needed

**Duplicate items created**:
- Check product_name and batch_number match exactly
- Different batches create separate items (correct behavior)

**Stock quantities incorrect**:
- Run POST /stock-audit/calculate-stock to recalculate
- Check purchase/sale transactions
- Review stock adjustments

**Unassigned items piling up**:
- GET /stock-audit/items/unassigned/list
- Assign sections in bulk
- Train staff on section assignment workflow

## AI Analytics

### Gemini 2.0 Flash Integration
```python
from modules.stock_audit.ai_service import StockAuditAIService

# Get comprehensive analysis
analysis = StockAuditAIService.get_comprehensive_analysis(db, shop_id, days=30)
```

### Analytics Data
- **Audit trends**: Discrepancies over time
- **Section analysis**: Problem areas by location
- **Staff performance**: Audits completed vs discrepancies found
- **Completion rate**: % of items audited

### AI Insights
Gemini analyzes data and provides:
1. **Key Findings**: 3-5 bullet points summarizing audit status
2. **Risk Areas**: Sections/items needing attention
3. **Recommendations**: 3-5 actionable steps
4. **Predictions**: Potential issues if trends continue

### Fallback Mode
If Gemini unavailable:
- Uses statistical analysis
- Identifies worst sections
- Calculates discrepancy rates
- Provides basic recommendations

## Services

### StockCalculationService
- `calculate_software_stock()`: Purchases - Sales
- `update_all_software_stock()`: Recalculate all items
- `add_purchase()`: Create purchase + update stock
- `add_sale()`: Create sale + update stock (with validation)

### StockAuditService
- `get_random_section_for_audit()`: Select section for audit
- `start_audit_session()`: Begin audit session
- `record_audit()`: Record physical count + discrepancy
- `get_discrepancies()`: Find items with mismatches
- `get_audit_summary()`: Overall audit statistics

### StockReportService
- `get_low_stock_items()`: Items below threshold
- `get_expiring_items()`: Items expiring soon
- `get_stock_movement_report()`: Purchase/sale summary

### InvoiceStockSyncService
- `sync_invoice_to_stock()`: Sync verified invoice to stock

### StockAuditAIService
- `get_analytics_data()`: Gather audit statistics
- `get_chart_data()`: Format for frontend charts
- `get_ai_insights()`: Gemini-powered analysis
- `get_comprehensive_analysis()`: Complete report

## Authentication

All endpoints require staff authentication:
```python
def get_current_user(user_dict: dict, db: Session) -> tuple[Staff, int]:
    # Validates staff token
    # Resolves shop_id from shop_code
    # Returns (staff, shop_id)
```

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key  # Required for AI analytics
```

## Best Practices

### Stock Management
1. **Always use POST /purchases** to add stock (auto-updates quantities)
2. **Always use POST /sales** to sell stock (validates availability)
3. **Use adjustments** for damages, returns, corrections
4. **Assign sections** to unassigned items from invoices

### Audit Workflow
1. Start audit session: POST /audit/sessions
2. Get random section: GET /audit/random-section
3. Count physical stock
4. Record results: PUT /items/{item_id}/audit
5. Review discrepancies: GET /audit/discrepancies
6. Investigate and resolve issues

### Discrepancy Resolution
1. Check audit records for patterns
2. Review staff performance
3. Investigate high-discrepancy sections
4. Create adjustments if needed
5. Update training procedures

## Error Handling

### Insufficient Stock
```python
# POST /sales validates stock
if stock_item.quantity_software < quantity:
    raise ValueError("Insufficient stock")
```

### Duplicate Codes
```python
# Rack/section codes must be unique
if existing:
    raise HTTPException(status_code=409, detail="Code already exists")
```

### Negative Stock
```python
# Adjustments cannot result in negative stock
if item.quantity_software + adjustment.quantity_change < 0:
    raise HTTPException(status_code=400, detail="Would result in negative stock")
```

## Reporting

### Low Stock Alert
```python
GET /reports/low-stock?threshold=10
# Returns items with quantity_software ≤ 10
```

### Expiry Alert
```python
GET /reports/expiring?days_ahead=30
# Returns items expiring within 30 days
```

### Stock Movement
```python
GET /reports/stock-movement?start_date=2024-01-01&end_date=2024-01-31
# Returns purchase/sale summary for period
```

## Excel Export

All exports include:
- **Stock Items**: Complete inventory with values
- **Audit Records**: Discrepancies and resolutions
- **Adjustments**: Manual stock changes

Format: `.xlsx` with styled headers and auto-sized columns

## Usage Example

```python
# 1. Create rack and section
rack = requests.post('/stock-audit/racks', json={
    "rack_number": "R1",
    "location": "Main Store"
})

section = requests.post('/stock-audit/sections', json={
    "rack_id": rack['id'],
    "section_name": "Antibiotics",
    "section_code": "R1-S1"
})

# 2. Add stock via invoice (automatic)
# Invoice verified → auto-creates StockItems

# 3. Assign section to unassigned items
requests.patch(f'/stock-audit/items/{item_id}/assign-section', json={
    "section_id": section['id']
})

# 4. Record sale
requests.post('/stock-audit/sales', json={
    "sale": {
        "sale_date": "2024-01-15",
        "total_amount": 500.00
    },
    "items": [{
        "stock_item_id": item_id,
        "quantity": 2,
        "unit_price": 100.00,
        "total_price": 200.00
    }]
})

# 5. Conduct audit
section = requests.get('/stock-audit/audit/random-section')
for item in section['items_to_audit']:
    physical_count = count_physical_stock(item)
    requests.put(f'/stock-audit/items/{item["id"]}/audit', json={
        "physical_quantity": physical_count
    })

# 6. Get AI insights
insights = requests.get('/stock-audit/ai-analytics/comprehensive?days=30')
```

## Troubleshooting

### Stock mismatch
- Run POST /calculate-stock to recalculate
- Check purchase/sale transactions
- Review adjustments

### AI analytics not working
- Verify GEMINI_API_KEY is set
- Check google-genai package installed
- Falls back to statistical analysis

### Unassigned items piling up
- GET /items/unassigned/list
- Assign sections in bulk
- Review invoice sync process
