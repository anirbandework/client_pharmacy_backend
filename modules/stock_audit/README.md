# Stock Audit Module

**Production-ready** inventory management system with authentication, batch tracking, staff audit trails, and automated stock calculations.

## ✅ Features

- **🔐 Authentication Required**: All endpoints require JWT token
- **🏪 Shop Isolation**: Complete data isolation between shops
- **👤 Staff Audit Trail**: Tracks staff_id + staff_name for all operations
- **📦 Batch Tracking**: Full traceability from purchase to sale
- **🔄 Auto Stock Calculations**: Purchases increment, sales decrement automatically
- **🎲 Random Audit System**: Intelligent section selection for physical verification
- **⚠️ Discrepancy Tracking**: Compare software vs physical stock
- **🔧 Stock Adjustments**: Handle damages, returns, corrections, theft
- **🗑️ Cascade Deletes**: Clean automatic deletion of related records
- **📊 Comprehensive Reports**: Low stock, expiring items, movement reports

## Database Models

### StockRack
Physical storage racks.
- `rack_number` (unique per shop)
- `location`, `description`
- `shop_id` (FK to shops)
- **Cascade**: Deleting rack auto-deletes sections and items

### StockSection
Sections within racks.
- `section_name`, `section_code` (unique per shop)
- `rack_id` (FK to stock_racks)
- `shop_id` (FK to shops)
- **Cascade**: Deleting section auto-deletes items

### StockItem
Inventory items with batch tracking.
- `item_name`, `generic_name`, `brand_name`
- `batch_number` (indexed)
- `quantity_software` (calculated from transactions)
- `quantity_physical` (from audits)
- `unit_price`, `expiry_date`, `manufacturer`
- `last_audit_date`, `last_audit_by_staff_id`, `last_audit_by_staff_name`
- `audit_discrepancy` (software - physical)
- `section_id` (FK), `shop_id` (FK)
- **Cascade**: Deleting item auto-deletes all transactions

### Purchase
Purchase transactions with staff tracking.
- `purchase_date`, `supplier_name`, `invoice_number`, `total_amount`
- `staff_id` (FK to staff), `staff_name` (audit trail)
- `shop_id` (FK to shops)
- **Cascade**: Deleting purchase auto-deletes purchase items

### PurchaseItem
Purchase line items with batch tracking.
- `purchase_id` (FK), `stock_item_id` (FK)
- `batch_number` (indexed) - **NEW: Track which batch purchased**
- `quantity`, `unit_cost`, `total_cost`
- `shop_id` (FK)
- **Auto-updates**: Increments stock_item.quantity_software

### Sale
Sales transactions with staff tracking.
- `sale_date`, `customer_phone`, `bill_number`, `total_amount`
- `staff_id` (FK to staff), `staff_name` (audit trail)
- `shop_id` (FK to shops)
- **Cascade**: Deleting sale auto-deletes sale items

### SaleItem
Sale line items with batch tracking.
- `sale_id` (FK), `stock_item_id` (FK)
- `batch_number` (indexed) - **NEW: Track which batch sold**
- `quantity`, `unit_price`, `total_price`
- `shop_id` (FK)
- **Auto-updates**: Decrements stock_item.quantity_software (with validation)

### StockAuditRecord
Physical audit records with staff tracking.
- `stock_item_id` (FK)
- `staff_id` (FK to staff), `staff_name` (who audited)
- `audit_date`, `software_quantity`, `physical_quantity`, `discrepancy`
- `notes`, `reason_for_discrepancy`
- `resolved`, `resolved_date`, `resolved_by_staff_id`, `resolved_by_staff_name`
- `resolution_notes`
- `shop_id` (FK)

### StockAuditSession
Audit session tracking with staff.
- `staff_id` (FK to staff), `staff_name` (auditor)
- `session_date`, `status` (in_progress/completed)
- `sections_audited`, `items_audited`, `discrepancies_found`
- `started_at`, `completed_at`, `session_notes`
- `shop_id` (FK)

### StockAdjustment (NEW)
Stock corrections/damages/returns with staff tracking.
- `stock_item_id` (FK)
- `staff_id` (FK to staff), `staff_name` (who adjusted)
- `adjustment_type` (correction, damage, return, expired, theft, found)
- `quantity_change` (positive or negative)
- `reason`, `notes`, `adjustment_date`
- `shop_id` (FK)
- **Auto-updates**: Modifies stock_item.quantity_software

## API Endpoints

**All endpoints require authentication**: `Authorization: Bearer <token>`

### Rack Management
```
POST   /api/stock-audit/racks              - Create rack (shop-scoped)
GET    /api/stock-audit/racks              - List racks (shop-scoped)
PUT    /api/stock-audit/racks/{id}         - Update rack
DELETE /api/stock-audit/racks/{id}         - Delete rack (cascade deletes sections/items)
```

### Section Management
```
POST   /api/stock-audit/sections           - Create section (shop-scoped)
GET    /api/stock-audit/sections?rack_id=  - List sections (shop-scoped)
PUT    /api/stock-audit/sections/{id}      - Update section
DELETE /api/stock-audit/sections/{id}      - Delete section (cascade deletes items)
```

### Stock Item Management
```
POST   /api/stock-audit/items              - Add item (shop-scoped)
GET    /api/stock-audit/items?section_id=&item_name=&batch_number= - List items
GET    /api/stock-audit/items/{id}         - Get specific item
PUT    /api/stock-audit/items/{id}         - Update item
DELETE /api/stock-audit/items/{id}         - Delete item (cascade deletes transactions)
```

### Purchase Management (with Batch Tracking)
```
POST   /api/stock-audit/purchases          - Add purchase (auto-updates stock)
GET    /api/stock-audit/purchases?start_date=&end_date=&supplier_name= - List
PUT    /api/stock-audit/purchases/{id}     - Update purchase
DELETE /api/stock-audit/purchases/{id}     - Delete purchase (cascade)
```

**Request Body:**
```json
{
  "purchase": {
    "purchase_date": "2024-02-08",
    "supplier_name": "ABC Pharma",
    "invoice_number": "INV-001",
    "total_amount": 5000.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "BATCH-2024-001",
      "quantity": 100,
      "unit_cost": 10.00,
      "total_cost": 1000.00
    }
  ]
}
```
**Auto-captures**: `staff_id` and `staff_name` from authenticated user

### Sales Management (with Batch Tracking)
```
POST   /api/stock-audit/sales              - Add sale (validates & deducts stock)
GET    /api/stock-audit/sales?start_date=&end_date=&customer_phone= - List
PUT    /api/stock-audit/sales/{id}         - Update sale
DELETE /api/stock-audit/sales/{id}         - Delete sale (cascade)
```

**Request Body:**
```json
{
  "sale": {
    "sale_date": "2024-02-08",
    "customer_phone": "+1234567890",
    "bill_number": "BILL-001",
    "total_amount": 500.00
  },
  "items": [
    {
      "stock_item_id": 1,
      "batch_number": "BATCH-2024-001",
      "quantity": 5,
      "unit_price": 15.00,
      "total_price": 75.00
    }
  ]
}
```
**Auto-captures**: `staff_id` and `staff_name` from authenticated user

### Audit Functionality
```
GET    /api/stock-audit/audit/random-section       - Get random section (shop-scoped)
POST   /api/stock-audit/audit/sessions             - Start audit session
PUT    /api/stock-audit/items/{id}/audit?physical_quantity=&notes= - Record audit
GET    /api/stock-audit/audit/discrepancies?threshold= - Get discrepancies
GET    /api/stock-audit/audit/summary              - Audit summary (shop-scoped)
```

**Audit captures**: `staff_id` and `staff_name` automatically

### Stock Adjustments (NEW)
```
POST   /api/stock-audit/adjustments        - Create adjustment
GET    /api/stock-audit/adjustments?stock_item_id=&adjustment_type= - List
```

**Request Body:**
```json
{
  "stock_item_id": 1,
  "adjustment_type": "damage",
  "quantity_change": -5,
  "reason": "Damaged during handling",
  "notes": "Broken bottles"
}
```

**Adjustment Types**: correction, damage, return, expired, theft, found

**Auto-captures**: `staff_id` and `staff_name` from authenticated user

### Stock Calculations
```
POST   /api/stock-audit/calculate-stock            - Recalculate all (shop-scoped)
GET    /api/stock-audit/items/{id}/stock-calculation - Detailed calculation
```

### Reports
```
GET    /api/stock-audit/reports/low-stock?threshold=     - Low stock (shop-scoped)
GET    /api/stock-audit/reports/expiring?days_ahead=     - Expiring items
GET    /api/stock-audit/reports/stock-movement?start_date=&end_date= - Movement
```

## Services

### StockCalculationService
- `calculate_software_stock(db, stock_item_id)` - Calculate from transactions
- `update_all_software_stock(db, shop_id)` - Recalculate all items
- `add_purchase(db, purchase_data, items_data, shop_id, staff_id, staff_name)` - Add & update
- `add_sale(db, sale_data, items_data, shop_id, staff_id, staff_name)` - Validate & deduct

### StockAuditService
- `get_random_section_for_audit(db, shop_id, exclude_recent_days=7)` - Random selection
- `start_audit_session(db, staff_id, staff_name, shop_id)` - Create session
- `record_audit(db, stock_item_id, physical_quantity, staff_id, staff_name, notes, shop_id)` - Record
- `get_discrepancies(db, threshold, shop_id)` - Get discrepancies
- `get_audit_summary(db, shop_id)` - Statistics

### StockReportService
- `get_low_stock_items(db, threshold, shop_id)` - Items below threshold
- `get_expiring_items(db, days_ahead, shop_id)` - Expiring soon
- `get_stock_movement_report(db, start_date, end_date, shop_id)` - Purchase/sale summary

## Security Features

1. **Authentication**: All endpoints require valid JWT token
2. **Shop Isolation**: Staff can only access their shop's data
3. **Automatic shop_id**: Extracted from authenticated user
4. **Staff Audit Trail**: Both staff_id (FK) and staff_name (preserved) tracked
5. **Validation**: Stock checks before sales, negative stock prevention
6. **Cascade Deletes**: Automatic cleanup of related records

## Migration

Run migrations to set up database:
```bash
# Add batch tracking and adjustments table
python modules/stock_audit/migrate_stock_audit_fixes.py

# Add staff_name columns for audit trail
python modules/stock_audit/migrate_add_staff_names.py
```

## Usage Examples

### 1. Record Purchase with Batch
```bash
curl -X POST http://localhost:8000/api/stock-audit/purchases \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "purchase": {
      "purchase_date": "2024-02-08",
      "supplier_name": "MedSupply Co",
      "invoice_number": "INV-2024-001",
      "total_amount": 10000.00
    },
    "items": [{
      "stock_item_id": 5,
      "batch_number": "BATCH-A123",
      "quantity": 200,
      "unit_cost": 50.00,
      "total_cost": 10000.00
    }]
  }'
```
**Result**: Stock updated, staff_id + staff_name auto-captured

### 2. Record Sale with Batch
```bash
curl -X POST http://localhost:8000/api/stock-audit/sales \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sale": {
      "sale_date": "2024-02-08",
      "customer_phone": "+919876543210",
      "bill_number": "BILL-001",
      "total_amount": 1000.00
    },
    "items": [{
      "stock_item_id": 5,
      "batch_number": "BATCH-A123",
      "quantity": 10,
      "unit_price": 100.00,
      "total_price": 1000.00
    }]
  }'
```
**Result**: Stock validated & deducted, staff_id + staff_name auto-captured

### 3. Record Audit
```bash
curl -X PUT "http://localhost:8000/api/stock-audit/items/5/audit?physical_quantity=185&notes=5+missing" \
  -H "Authorization: Bearer <token>"
```
**Result**: Discrepancy calculated, staff_id + staff_name auto-captured

### 4. Record Damage Adjustment
```bash
curl -X POST http://localhost:8000/api/stock-audit/adjustments \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_item_id": 5,
    "adjustment_type": "damage",
    "quantity_change": -10,
    "reason": "Water damage in storage",
    "notes": "Affected by roof leak"
  }'
```
**Result**: Stock reduced by 10, staff_id + staff_name auto-captured

### 5. Query by Batch
```bash
# Find all sales of specific batch
curl "http://localhost:8000/api/stock-audit/sales?batch_number=BATCH-A123" \
  -H "Authorization: Bearer <token>"
```

## Integration

Already integrated in `main.py`:
```python
from modules.stock_audit import router as stock_audit_router
app.include_router(stock_audit_router, prefix="/api/stock-audit", tags=["Stock Audit"])
```

## Benefits

✅ **Secure**: JWT authentication + shop isolation  
✅ **Auditable**: Complete staff tracking (ID + name)  
✅ **Traceable**: Batch tracking from purchase to sale  
✅ **Clean**: Cascade deletes prevent orphaned data  
✅ **Flexible**: Stock adjustments for all scenarios  
✅ **Accurate**: Automated stock calculations  
✅ **Reliable**: Stock validation before sales  
✅ **Scalable**: Multi-tenant with data isolation
