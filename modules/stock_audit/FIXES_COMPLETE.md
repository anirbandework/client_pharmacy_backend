# Stock Audit Module - Complete & Production-Ready

## ✅ All Issues Resolved + Bonus Features

### 1. Authentication Integration ✓
- All routes require authentication via `get_current_user` dependency
- Staff can only access their own shop's data
- Shop-scoped filtering enforced on all queries
- Automatic extraction of shop_id, staff_id, staff_name from JWT token

### 2. Multi-tenant Support ✓
- `shop_id` filtering enforced on all endpoints
- Service methods updated to accept and filter by `shop_id`
- Data isolation between shops guaranteed
- No cross-shop data access possible

### 3. Cascade Deletes ✓
- All relationships have `cascade="all, delete-orphan"`
- Deleting rack → auto-deletes sections → auto-deletes items → auto-deletes transactions
- Deleting purchase/sale → auto-deletes line items
- No orphaned records possible

### 4. Batch Tracking ✓
- Added `batch_number` field to `PurchaseItem` and `SaleItem`
- Track which batch was purchased/sold
- Query transactions by batch number
- Full traceability from supplier to customer

### 5. Stock Adjustment Endpoint ✓
- New `StockAdjustment` model for corrections/damages/returns
- Adjustment types: correction, damage, return, expired, theft, found
- Tracks staff_id + staff_name for who made adjustment
- Updates software stock automatically with validation
- Complete audit trail

### 6. Staff Audit Trail ✓ (BONUS)
- All operations track both `staff_id` (FK) and `staff_name` (preserved)
- Models updated: Purchase, Sale, StockAuditRecord, StockAuditSession, StockAdjustment, StockItem
- Staff name preserved even if staff account deleted
- Can query by staff_id or display staff_name for reports
- Automatic capture from authenticated user

## API Endpoints

### Authentication
All endpoints require Bearer token in Authorization header:
```
Authorization: Bearer <staff_token>
```

### Racks
- `POST /api/stock-audit/racks` - Create rack (shop-scoped, auto shop_id)
- `GET /api/stock-audit/racks` - Get all racks (shop-scoped)
- `PUT /api/stock-audit/racks/{id}` - Update rack (shop-scoped)
- `DELETE /api/stock-audit/racks/{id}` - Delete rack (cascade deletes sections/items)

### Sections
- `POST /api/stock-audit/sections` - Create section (shop-scoped, auto shop_id)
- `GET /api/stock-audit/sections?rack_id={id}` - Get sections (shop-scoped)
- `PUT /api/stock-audit/sections/{id}` - Update section (shop-scoped)
- `DELETE /api/stock-audit/sections/{id}` - Delete section (cascade deletes items)

### Stock Items
- `POST /api/stock-audit/items` - Add stock item (shop-scoped, auto shop_id)
- `GET /api/stock-audit/items?section_id={id}&item_name={name}&batch_number={batch}` - Get items (shop-scoped)
- `GET /api/stock-audit/items/{id}` - Get specific item (shop-scoped)
- `PUT /api/stock-audit/items/{id}` - Update item (shop-scoped)
- `DELETE /api/stock-audit/items/{id}` - Delete item (cascade deletes transactions)

### Purchases (with Batch Tracking + Staff Tracking)
```json
POST /api/stock-audit/purchases
Authorization: Bearer <token>

{
  "purchase": {
    "purchase_date": "2024-01-15",
    "supplier_name": "ABC Pharma",
    "invoice_number": "INV-001",
    "total_amount": 5000.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "BATCH-2024-001",
      "quantity": 100,
      "unit_cost": 50.00,
      "total_cost": 5000.00
    }
  ]
}

Response includes:
{
  "id": 1,
  "staff_id": 5,
  "staff_name": "John Doe",
  "shop_id": 2,
  ...
}
```

- `GET /api/stock-audit/purchases?start_date={date}&end_date={date}&supplier_name={name}` - Get purchases (shop-scoped)
- `PUT /api/stock-audit/purchases/{id}` - Update purchase (shop-scoped)
- `DELETE /api/stock-audit/purchases/{id}` - Delete purchase (cascade deletes items)

### Sales (with Batch Tracking + Staff Tracking)
```json
POST /api/stock-audit/sales
Authorization: Bearer <token>

{
  "sale": {
    "sale_date": "2024-01-15",
    "customer_phone": "+919876543210",
    "bill_number": "BILL-001",
    "total_amount": 1000.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "BATCH-2024-001",
      "quantity": 10,
      "unit_price": 100.00,
      "total_price": 1000.00
    }
  ]
}

Response includes:
{
  "id": 1,
  "staff_id": 5,
  "staff_name": "John Doe",
  "shop_id": 2,
  ...
}
```

- `GET /api/stock-audit/sales?start_date={date}&end_date={date}&customer_phone={phone}` - Get sales (shop-scoped)
- `PUT /api/stock-audit/sales/{id}` - Update sale (shop-scoped)
- `DELETE /api/stock-audit/sales/{id}` - Delete sale (cascade deletes items)

### Stock Adjustments (NEW)
```json
POST /api/stock-audit/adjustments
Authorization: Bearer <token>

{
  "stock_item_id": 1,
  "adjustment_type": "damage",
  "quantity_change": -5,
  "reason": "Damaged during handling",
  "notes": "Broken bottles"
}

Response includes:
{
  "id": 1,
  "staff_id": 5,
  "staff_name": "John Doe",
  "shop_id": 2,
  ...
}
```

Adjustment types:
- `correction` - Fix incorrect stock count
- `damage` - Damaged goods
- `return` - Customer returns
- `expired` - Expired items removed
- `theft` - Stolen items
- `found` - Found missing items (positive adjustment)

- `GET /api/stock-audit/adjustments?stock_item_id={id}&adjustment_type={type}` - Get adjustments (shop-scoped)

### Audit
- `GET /api/stock-audit/audit/random-section` - Get random section for audit (shop-scoped)
- `POST /api/stock-audit/audit/sessions` - Start audit session (auto-captures staff)
- `PUT /api/stock-audit/items/{id}/audit?physical_quantity={qty}&notes={text}` - Record audit (auto-captures staff)
- `GET /api/stock-audit/audit/discrepancies?threshold={num}` - Get discrepancies (shop-scoped)
- `GET /api/stock-audit/audit/summary` - Get audit summary (shop-scoped)

### Stock Calculations
- `POST /api/stock-audit/calculate-stock` - Recalculate all stock (shop-scoped)
- `GET /api/stock-audit/items/{id}/stock-calculation` - Get item calculation details (shop-scoped)

### Reports
- `GET /api/stock-audit/reports/low-stock?threshold={num}` - Low stock report (shop-scoped)
- `GET /api/stock-audit/reports/expiring?days_ahead={num}` - Expiring items (shop-scoped)
- `GET /api/stock-audit/reports/stock-movement?start_date={date}&end_date={date}` - Movement report (shop-scoped)

## Database Schema

### New/Updated Tables

#### purchase_items_audit
- Added `batch_number` VARCHAR (indexed)

#### sale_items_audit
- Added `batch_number` VARCHAR (indexed)

#### purchases_audit
- Added `staff_id` INTEGER (FK to staff, indexed)
- Added `staff_name` VARCHAR
- Removed `recorded_by` VARCHAR

#### sales_audit
- Added `staff_id` INTEGER (FK to staff, indexed)
- Added `staff_name` VARCHAR
- Removed `sold_by` VARCHAR

#### stock_audit_records
- Added `staff_id` INTEGER (FK to staff, indexed)
- Added `staff_name` VARCHAR
- Added `resolved_by_staff_id` INTEGER (FK to staff)
- Added `resolved_by_staff_name` VARCHAR
- Removed `audited_by` VARCHAR
- Removed `resolved_by` VARCHAR

#### stock_audit_sessions
- Added `staff_id` INTEGER (FK to staff, indexed)
- Added `staff_name` VARCHAR
- Removed `auditor` VARCHAR

#### stock_items_audit
- Added `last_audit_by_staff_id` INTEGER (FK to staff)
- Added `last_audit_by_staff_name` VARCHAR
- Removed `last_audit_by` VARCHAR

#### stock_adjustments (NEW)
```sql
CREATE TABLE stock_adjustments (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER,
    staff_id INTEGER NOT NULL,
    staff_name VARCHAR NOT NULL,
    stock_item_id INTEGER NOT NULL,
    adjustment_type VARCHAR NOT NULL,
    quantity_change INTEGER NOT NULL,
    reason VARCHAR NOT NULL,
    notes TEXT,
    adjustment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    FOREIGN KEY (stock_item_id) REFERENCES stock_items_audit(id) ON DELETE CASCADE
)
```

### Cascade Relationships
- `StockRack.sections` → CASCADE DELETE
- `StockSection.items` → CASCADE DELETE
- `StockItem.purchase_items` → CASCADE DELETE
- `StockItem.sale_items` → CASCADE DELETE
- `StockItem.audit_records` → CASCADE DELETE
- `StockItem.adjustments` → CASCADE DELETE
- `Purchase.items` → CASCADE DELETE
- `Sale.items` → CASCADE DELETE

## Migration

Run migrations to add new fields and table:
```bash
# Migration 1: Add batch tracking and adjustments table
python modules/stock_audit/migrate_stock_audit_fixes.py

# Migration 2: Add staff_name columns for audit trail
python modules/stock_audit/migrate_add_staff_names.py
```

## Security Features

1. **Authentication Required**: All endpoints require valid JWT token
2. **Shop Isolation**: Staff can only access their shop's data
3. **Automatic shop_id**: Extracted from authenticated user, not from request
4. **Automatic staff tracking**: staff_id + staff_name captured from token
5. **Validation**: Stock checks before sales, negative stock prevention
6. **Audit Trail**: All operations tracked with who/when/why
7. **Foreign Keys**: staff_id as FK for relational integrity
8. **Preserved Names**: staff_name preserved even if account deleted

## Usage Examples

### Example 1: Record Purchase with Batch
```python
import requests

headers = {"Authorization": "Bearer <staff_token>"}
data = {
    "purchase": {
        "purchase_date": "2024-01-15",
        "supplier_name": "MedSupply Co",
        "invoice_number": "INV-2024-001",
        "total_amount": 10000.00
    },
    "items": [
        {
            "stock_item_id": 5,
            "batch_number": "BATCH-A123",
            "quantity": 200,
            "unit_cost": 50.00,
            "total_cost": 10000.00
        }
    ]
}

response = requests.post(
    "http://localhost:8000/api/stock-audit/purchases",
    json=data,
    headers=headers
)

# Response includes staff_id and staff_name automatically
print(response.json())
# {
#   "id": 1,
#   "staff_id": 5,
#   "staff_name": "John Doe",
#   "shop_id": 2,
#   "purchase_date": "2024-01-15",
#   ...
# }
```

### Example 2: Record Damage Adjustment
```python
data = {
    "stock_item_id": 5,
    "adjustment_type": "damage",
    "quantity_change": -10,
    "reason": "Water damage in storage",
    "notes": "Affected by roof leak"
}

response = requests.post(
    "http://localhost:8000/api/stock-audit/adjustments",
    json=data,
    headers=headers
)

# Staff info auto-captured
print(response.json())
# {
#   "id": 1,
#   "staff_id": 5,
#   "staff_name": "John Doe",
#   "adjustment_type": "damage",
#   ...
# }
```

### Example 3: Track Batch Sales
```python
# Query sales by batch
response = requests.get(
    "http://localhost:8000/api/stock-audit/sales?batch_number=BATCH-A123",
    headers=headers
)

# See which staff sold which batch
for sale in response.json():
    print(f"Sold by {sale['staff_name']} (ID: {sale['staff_id']})")
```

### Example 4: Audit with Staff Tracking
```python
# Record audit
response = requests.put(
    "http://localhost:8000/api/stock-audit/items/5/audit?physical_quantity=185&notes=5+missing",
    headers=headers
)

# Staff who audited is auto-captured
print(response.json())
# {
#   "id": 1,
#   "staff_id": 5,
#   "staff_name": "John Doe",
#   "software_quantity": 190,
#   "physical_quantity": 185,
#   "discrepancy": 5,
#   ...
# }
```

## Benefits

✅ **Secure**: Authentication + shop isolation + staff tracking  
✅ **Clean**: Cascade deletes prevent orphaned data  
✅ **Traceable**: Batch tracking for full traceability  
✅ **Flexible**: Stock adjustments for all scenarios  
✅ **Accurate**: Automated stock calculations  
✅ **Auditable**: Complete history with staff ID + name  
✅ **Reliable**: Stock validation before sales  
✅ **Preserved**: Staff names kept even after account deletion  
✅ **Queryable**: Can filter/report by staff_id  
✅ **Automatic**: No manual input of shop/staff info needed

## Integration with Main App

Already integrated in `main.py`:
```python
from modules.stock_audit import router as stock_audit_router
app.include_router(stock_audit_router, prefix="/api/stock-audit", tags=["Stock Audit"])
```

All endpoints automatically protected by authentication middleware.

## Staff Tracking Summary

| Model | Staff Fields | Purpose |
|-------|-------------|---------|
| Purchase | staff_id, staff_name | Who recorded purchase |
| Sale | staff_id, staff_name | Who made sale |
| StockAuditRecord | staff_id, staff_name | Who performed audit |
| StockAuditRecord | resolved_by_staff_id, resolved_by_staff_name | Who resolved discrepancy |
| StockAuditSession | staff_id, staff_name | Who conducted audit session |
| StockAdjustment | staff_id, staff_name | Who made adjustment |
| StockItem | last_audit_by_staff_id, last_audit_by_staff_name | Last auditor |

All captured automatically from JWT token - no manual input required!
