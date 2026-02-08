# Stock Audit Module

Comprehensive inventory management system with purchase/sale tracking, automated stock calculations, and random section auditing.

## Features

- **Rack & Section Management**: Organize inventory by physical location
- **Stock Item Tracking**: Track items with batch numbers, expiry dates, and quantities
- **Purchase Management**: Record purchases and auto-update stock levels
- **Sales Management**: Process sales with stock validation and auto-deduction
- **Random Audit System**: Randomly select sections for physical stock verification
- **Discrepancy Tracking**: Compare software vs physical stock with audit trails
- **Multi-Tenant Support**: All tables include `shop_id` for data isolation
- **Stock Reports**: Low stock alerts, expiring items, and movement reports

## Database Models

### StockRack
Physical storage racks in the pharmacy.
- `rack_number` (unique): Rack identifier
- `location`: Physical location description
- `shop_id`: Multi-tenant foreign key

### StockSection
Sections within racks for organizing items.
- `section_name`: Section identifier
- `section_code` (unique): Code for quick reference
- `rack_id`: Parent rack reference
- `shop_id`: Multi-tenant foreign key

### StockItem
Individual inventory items with batch tracking.
- `item_name`: Medicine/product name
- `generic_name`, `brand_name`: Alternative names
- `batch_number`: Batch identifier
- `quantity_software`: Calculated stock (purchases - sales)
- `quantity_physical`: Last physical count from audit
- `unit_price`: Selling price
- `expiry_date`: Product expiration
- `audit_discrepancy`: Difference between software and physical stock
- `last_audit_date`, `last_audit_by`: Audit tracking
- `shop_id`: Multi-tenant foreign key

### Purchase & PurchaseItem
Purchase transactions with line items.
- Purchase: `purchase_date`, `supplier_name`, `invoice_number`, `total_amount`
- PurchaseItem: `stock_item_id`, `quantity`, `unit_cost`, `total_cost`
- Auto-updates `quantity_software` on stock items
- `shop_id`: Multi-tenant foreign key

### Sale & SaleItem
Sales transactions with line items.
- Sale: `sale_date`, `customer_phone`, `bill_number`, `total_amount`
- SaleItem: `stock_item_id`, `quantity`, `unit_price`, `total_price`
- Validates stock availability before sale
- Auto-deducts from `quantity_software`
- `shop_id`: Multi-tenant foreign key

### StockAuditRecord
Individual audit records for stock verification.
- `stock_item_id`: Item being audited
- `audit_date`: When audit was performed
- `audited_by`: Staff member name
- `software_quantity`: System calculated stock
- `physical_quantity`: Actual counted stock
- `discrepancy`: Difference (software - physical)
- `notes`, `reason_for_discrepancy`: Audit notes
- `resolved`: Whether discrepancy was resolved
- `shop_id`: Multi-tenant foreign key

### StockAuditSession
Audit session tracking for organized audits.
- `session_date`: Date of audit session
- `auditor`: Staff conducting audit
- `sections_audited`, `items_audited`: Progress counters
- `discrepancies_found`: Total discrepancies in session
- `status`: "in_progress" or "completed"
- `shop_id`: Multi-tenant foreign key

## API Endpoints

### Rack Management
```
POST   /api/stock/racks              - Create rack
GET    /api/stock/racks              - List all racks
PUT    /api/stock/racks/{id}         - Update rack
DELETE /api/stock/racks/{id}         - Delete rack (if no sections)
```

### Section Management
```
POST   /api/stock/sections           - Create section
GET    /api/stock/sections           - List sections (filter by rack_id)
PUT    /api/stock/sections/{id}      - Update section
DELETE /api/stock/sections/{id}      - Delete section (if no items)
```

### Stock Item Management
```
POST   /api/stock/items              - Add stock item
GET    /api/stock/items              - List items (filters: section_id, item_name, batch_number)
GET    /api/stock/items/{id}         - Get specific item
PUT    /api/stock/items/{id}         - Update item
DELETE /api/stock/items/{id}         - Delete item (if no transactions)
```

### Purchase Management
```
POST   /api/stock/purchases          - Add purchase (auto-updates stock)
GET    /api/stock/purchases          - List purchases (filters: date range, supplier)
PUT    /api/stock/purchases/{id}     - Update purchase
DELETE /api/stock/purchases/{id}     - Delete purchase
```

**Purchase Request Body:**
```json
{
  "purchase": {
    "purchase_date": "2024-02-08",
    "supplier_name": "ABC Pharma",
    "invoice_number": "INV-001",
    "total_amount": 5000.00,
    "recorded_by": "Staff Name"
  },
  "items": [
    {
      "stock_item_id": 1,
      "quantity": 100,
      "unit_cost": 10.00,
      "total_cost": 1000.00
    }
  ]
}
```

### Sales Management
```
POST   /api/stock/sales              - Add sale (validates & deducts stock)
GET    /api/stock/sales              - List sales (filters: date range, customer)
PUT    /api/stock/sales/{id}         - Update sale
DELETE /api/stock/sales/{id}         - Delete sale
```

**Sale Request Body:**
```json
{
  "sale": {
    "sale_date": "2024-02-08",
    "customer_phone": "+1234567890",
    "bill_number": "BILL-001",
    "total_amount": 500.00,
    "sold_by": "Staff Name"
  },
  "items": [
    {
      "stock_item_id": 1,
      "quantity": 5,
      "unit_price": 15.00,
      "total_price": 75.00
    }
  ]
}
```

### Audit Functionality
```
GET    /api/stock/audit/random-section       - Get random section for audit
POST   /api/stock/audit/sessions             - Start audit session
PUT    /api/stock/items/{id}/audit           - Record audit result
GET    /api/stock/audit/discrepancies        - Get all discrepancies (threshold param)
GET    /api/stock/audit/summary              - Overall audit summary
```

**Audit Item Request:**
```json
{
  "physical_quantity": 95,
  "audited_by": "Staff Name",
  "notes": "Found 5 units missing"
}
```

### Stock Calculations
```
POST   /api/stock/calculate-stock            - Recalculate all software stock
GET    /api/stock/items/{id}/stock-calculation - Detailed calculation for item
```

### Reports
```
GET    /api/stock/reports/low-stock          - Low stock items (threshold param)
GET    /api/stock/reports/expiring           - Expiring items (days_ahead param)
GET    /api/stock/reports/stock-movement     - Movement report (date range)
```

## Services

### StockCalculationService
Handles automated stock calculations.

**Methods:**
- `calculate_software_stock(db, stock_item_id)`: Calculate stock from purchases/sales
- `update_all_software_stock(db)`: Recalculate all items
- `add_purchase(db, purchase_data, items_data)`: Add purchase & update stock
- `add_sale(db, sale_data, items_data)`: Add sale & deduct stock (with validation)

### StockAuditService
Manages physical stock audits.

**Methods:**
- `get_random_section_for_audit(db, exclude_recent_days=7)`: Random section selection
- `start_audit_session(db, auditor)`: Create audit session
- `record_audit(db, stock_item_id, physical_quantity, audited_by, notes)`: Record audit
- `get_discrepancies(db, threshold=0)`: Get items with discrepancies
- `complete_audit_session(db, session_id, notes)`: Mark session complete
- `get_audit_summary(db)`: Overall audit statistics

### StockReportService
Generate inventory reports.

**Methods:**
- `get_low_stock_items(db, threshold=10)`: Items below threshold
- `get_expiring_items(db, days_ahead=30)`: Items expiring soon
- `get_stock_movement_report(db, start_date, end_date)`: Purchase/sale summary

## Multi-Tenant Integration

All models include `shop_id` foreign key for multi-tenant support. When using with authentication:

```python
from modules.auth.dependencies import get_shop_context

@router.get("/items")
def get_items(
    shop_id: int = Depends(get_shop_context),
    db: Session = Depends(get_db)
):
    return db.query(StockItem).filter(StockItem.shop_id == shop_id).all()
```

## Usage Examples

### 1. Setup Inventory Structure
```python
# Create rack
POST /api/stock/racks
{
  "rack_number": "R-001",
  "location": "Main Storage",
  "description": "Primary medicine storage"
}

# Create section
POST /api/stock/sections
{
  "rack_id": 1,
  "section_name": "Antibiotics",
  "section_code": "R001-AB"
}

# Add stock item
POST /api/stock/items
{
  "section_id": 1,
  "item_name": "Amoxicillin 500mg",
  "generic_name": "Amoxicillin",
  "brand_name": "Amoxil",
  "batch_number": "BATCH-2024-001",
  "quantity_software": 0,
  "unit_price": 15.00,
  "expiry_date": "2025-12-31",
  "manufacturer": "ABC Pharma"
}
```

### 2. Record Purchase
```python
POST /api/stock/purchases
{
  "purchase": {
    "purchase_date": "2024-02-08",
    "supplier_name": "ABC Pharma Distributors",
    "invoice_number": "INV-2024-001",
    "total_amount": 10000.00,
    "recorded_by": "John Doe"
  },
  "items": [
    {
      "stock_item_id": 1,
      "quantity": 500,
      "unit_cost": 10.00,
      "total_cost": 5000.00
    }
  ]
}
# Auto-updates stock_item.quantity_software to 500
```

### 3. Process Sale
```python
POST /api/stock/sales
{
  "sale": {
    "sale_date": "2024-02-08",
    "customer_phone": "+1234567890",
    "bill_number": "BILL-2024-001",
    "total_amount": 150.00,
    "sold_by": "Jane Smith"
  },
  "items": [
    {
      "stock_item_id": 1,
      "quantity": 10,
      "unit_price": 15.00,
      "total_price": 150.00
    }
  ]
}
# Validates stock (500 available) and deducts to 490
```

### 4. Conduct Random Audit
```python
# Get random section
GET /api/stock/audit/random-section
# Returns section with items needing audit

# Start audit session
POST /api/stock/audit/sessions
{
  "auditor": "Audit Team Lead",
  "session_notes": "Monthly audit - February 2024"
}

# Audit each item
PUT /api/stock/items/1/audit?physical_quantity=485&audited_by=Audit Team&notes=Found 5 units missing

# Check discrepancies
GET /api/stock/audit/discrepancies?threshold=5
```

### 5. Generate Reports
```python
# Low stock alert
GET /api/stock/reports/low-stock?threshold=50

# Expiring items
GET /api/stock/reports/expiring?days_ahead=60

# Stock movement
GET /api/stock/reports/stock-movement?start_date=2024-02-01&end_date=2024-02-28
```

## Key Features Explained

### Automated Stock Calculation
- `quantity_software` is automatically calculated: Total Purchases - Total Sales
- Every purchase adds to stock, every sale deducts
- Manual recalculation available via `/calculate-stock` endpoint

### Random Audit System
- Selects sections that haven't been audited in last 7 days
- Prevents audit fatigue by rotating sections
- Tracks audit history per item

### Discrepancy Management
- `audit_discrepancy = quantity_software - quantity_physical`
- Positive: Software shows more (possible theft/damage)
- Negative: Software shows less (possible unrecorded purchases)
- Tracks resolution status and notes

### Stock Validation
- Sales automatically validate stock availability
- Prevents overselling with real-time checks
- Returns clear error messages for insufficient stock

## Error Handling

Common errors and responses:

```python
# Insufficient stock
{
  "detail": "Insufficient stock for Amoxicillin 500mg. Available: 10, Required: 50"
}

# Duplicate rack/section
{
  "detail": "Rack number already exists"
}

# Cannot delete with dependencies
{
  "detail": "Cannot delete rack with existing sections"
}

# Item not found
{
  "detail": "Stock item not found"
}
```

## Best Practices

1. **Always use purchase/sale endpoints** instead of manually updating quantities
2. **Conduct regular audits** using the random section feature
3. **Monitor discrepancies** and investigate causes promptly
4. **Set appropriate thresholds** for low stock alerts based on item turnover
5. **Track expiring items** and plan promotions or returns
6. **Use batch numbers** for traceability and recalls
7. **Include shop_id** in all queries for multi-tenant deployments

## Integration with Other Modules

### With Authentication Module
```python
from modules.auth.dependencies import get_current_staff, require_permission

@router.post("/purchases")
def add_purchase(
    purchase_data: dict,
    current_user = Depends(get_current_staff),
    _permission = Depends(require_permission("can_manage_inventory")),
    db: Session = Depends(get_db)
):
    # Only staff with inventory permission can add purchases
    pass
```

### With Daily Records Module
Link daily sales totals with stock movements for reconciliation.

### With Customer Tracking Module
Track customer purchase history with stock items for refill reminders.

## Future Enhancements

- Barcode scanning integration
- Automated reorder point alerts
- Supplier performance tracking
- Batch-wise FIFO/LIFO stock management
- Integration with accounting systems
- Mobile app for quick audits
- Photo documentation for discrepancies

## Support

For issues or questions, refer to the main project README or contact the development team.
