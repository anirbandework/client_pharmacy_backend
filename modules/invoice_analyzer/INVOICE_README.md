# Invoice Analyzer Module

AI-powered purchase invoice processing system with automatic data extraction and stock management integration.

## Overview

This module processes PDF purchase invoices using Gemini 2.5 Flash AI, extracts structured data, and syncs with the stock audit system. It includes a fallback regex parser for reliability.

## Architecture

```
invoice_analyzer/
├── models.py          # Database models (PurchaseInvoice, PurchaseInvoiceItem)
├── schemas.py         # Pydantic validation schemas
├── routes.py          # FastAPI endpoints
├── ai_extractor.py    # AI + fallback extraction logic
└── pdf_service.py     # Legacy PDF parser (deprecated)
```

## Database Schema

### PurchaseInvoice
- **Invoice Details**: invoice_number, invoice_date, due_date
- **Supplier Info**: name, address, GSTIN, DL numbers, phone
- **Financial Summary**: gross_amount, discount, taxable_amount, total_gst, net_amount
- **Verification**: is_verified, verified_by, verified_at
- **Storage**: pdf_filename, pdf_path, raw_extracted_data (JSON)

### PurchaseInvoiceItem
- **Product Info**: manufacturer, hsn_code, product_name, batch_number, package
- **Quantities**: quantity, free_quantity
- **Pricing**: unit_price, mrp, expiry_date
- **Tax Breakdown**: cgst_percent, cgst_amount, sgst_percent, sgst_amount, igst_percent, igst_amount
- **Totals**: discount_amount, taxable_amount, total_amount

## API Endpoints

### POST /upload
Upload and process invoice PDF.

**Request**: `multipart/form-data` with PDF file

**Response**:
```json
{
  "id": 1,
  "invoice_number": "SW000106",
  "invoice_date": "2024-01-15",
  "supplier_name": "ABC Pharmaceuticals",
  "net_amount": 15000.50,
  "items": [...]
}
```

**Process**:
1. Validate PDF file
2. Save to `uploads/invoices/{shop_id}_{timestamp}_{filename}.pdf`
3. Extract text with pdfplumber
4. Parse with Gemini AI (or fallback regex)
5. Check for duplicates (by invoice_number)
6. Create invoice + items records
7. Return structured data

### GET /
List all invoices for shop.

**Query Params**:
- `skip`: Pagination offset (default: 0)
- `limit`: Results per page (default: 100)
- `supplier_name`: Filter by supplier (partial match)
- `start_date`: Filter by date range (YYYY-MM-DD)
- `end_date`: Filter by date range (YYYY-MM-DD)

**Response**:
```json
[
  {
    "id": 1,
    "invoice_number": "SW000106",
    "invoice_date": "2024-01-15",
    "supplier_name": "ABC Pharmaceuticals",
    "net_amount": 15000.50,
    "total_items": 25,
    "is_verified": true,
    "verified_by_name": "John Doe",
    "staff_name": "Jane Smith",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

### GET /{invoice_id}
Get single invoice with all items.

**Response**: Full invoice object with items array

### PUT /{invoice_id}
Update invoice after manual verification.

**Request**:
```json
{
  "invoice_number": "SW000106",
  "invoice_date": "2024-01-15",
  "supplier_name": "ABC Pharmaceuticals",
  "gross_amount": 14000.00,
  "discount_amount": 500.00,
  "taxable_amount": 13500.00,
  "total_gst": 1620.00,
  "net_amount": 15120.00,
  "items": [...]
}
```

**Process**:
1. Update invoice fields
2. Delete old items
3. Create new items
4. Set is_verified=true, verified_by, verified_at
5. **Sync to stock audit system**
6. Return updated invoice

### DELETE /{invoice_id}
Delete invoice and reverse stock quantities.

**Process**:
1. Find matching stock items (by product_name + batch_number)
2. Subtract quantities from stock
3. Delete stock items if quantity ≤ 0
4. Delete PDF file
5. Delete invoice record

**Response**:
```json
{
  "message": "Invoice deleted successfully",
  "stock_reversed": true
}
```

### GET /stats/summary
Get invoice statistics.

**Query Params**: `start_date`, `end_date`

**Response**:
```json
{
  "total_invoices": 150,
  "total_amount": 450000.00,
  "total_items": 3750,
  "average_invoice_amount": 3000.00,
  "top_suppliers": [
    {"name": "ABC Pharma", "total": 125000.00}
  ]
}
```

### GET /items/search
Search invoice items.

**Query Params**: `product_name`, `batch_number`, `skip`, `limit`

## AI Extraction

### Gemini 2.5 Flash
- **Model**: `gemini-2.5-flash` (fastest, most cost-effective)
- **Input**: Full invoice text from PDF
- **Output**: Structured JSON with all fields

**Extraction Features**:
- Separates Mfg (4 letters) from HSN (8 digits)
- Extracts package info (e.g., "10 X 6")
- Preserves MRP format (e.g., "69.00/STRIP")
- Handles date formats (MM/YYYY and DD/MM/YYYY)
- Calculates GST breakdown (CGST + SGST + IGST)
- Auto-fixes concatenated Mfg+HSN

### Fallback Regex Parser
Activates when:
- AI API unavailable
- AI returns invalid JSON
- AI returns no items

**Extraction Logic**:
- Invoice number (handles multi-line patterns)
- Dates (DD/MM/YYYY format)
- Supplier info (GSTIN, DL numbers, phone)
- Items (parses table rows with regex)
- Financial totals

## Data Flow

```
1. Upload PDF
   ↓
2. Save to uploads/invoices/
   ↓
3. Extract text (pdfplumber)
   ↓
4. Parse with AI (Gemini 2.5 Flash)
   ↓
5. Validate & fix data
   ↓
6. Check duplicates
   ↓
7. Create invoice + items
   ↓
8. Return response
   ↓
9. User verifies/edits
   ↓
10. Update invoice (PUT)
   ↓
11. Sync to stock audit
   ↓
12. Stock quantities updated
```

## Stock Audit Integration

### Overview
The Invoice Analyzer and Stock Audit systems are tightly integrated. When invoices are verified, they automatically sync to the stock management system, creating or updating inventory records.

### Connection Architecture
```
Invoice Analyzer          →          Stock Audit
─────────────────                    ────────────
PurchaseInvoice                      StockItem
PurchaseInvoiceItem                  (quantity_software)
     ↓                                    ↑
     └──── InvoiceStockSyncService ──────┘
```

### Automatic Sync on Verification

When invoice is verified via `PUT /invoice-analyzer/{invoice_id}`:

```python
# In routes.py - update_invoice()
from modules.stock_audit.sync_service import InvoiceStockSyncService

# After invoice update
try:
    sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)
    logger.info(f"✅ Synced invoice {invoice_id} to stock: {sync_result}")
except Exception as e:
    logger.error(f"❌ Failed to sync invoice to stock: {e}")
    # Invoice still saves, sync can be retried
```

### Sync Logic (InvoiceStockSyncService)

**For each PurchaseInvoiceItem**:

1. **Check if StockItem exists**:
   ```python
   existing_item = db.query(StockItem).filter(
       StockItem.shop_id == shop_id,
       StockItem.product_name == invoice_item.product_name,
       StockItem.batch_number == invoice_item.batch_number
   ).first()
   ```

2. **If exists → Update quantity**:
   ```python
   existing_item.quantity_software += int(invoice_item.quantity)
   existing_item.updated_at = datetime.utcnow()
   ```

3. **If new → Create StockItem**:
   ```python
   stock_item = StockItem(
       shop_id=shop_id,
       manufacturer=invoice_item.manufacturer,
       hsn_code=invoice_item.hsn_code,
       product_name=invoice_item.product_name,
       batch_number=invoice_item.batch_number,
       package=invoice_item.package,
       expiry_date=invoice_item.expiry_date,
       mrp=invoice_item.mrp,
       quantity_software=int(invoice_item.quantity),
       unit_price=invoice_item.unit_price,
       source_invoice_id=invoice_id,
       section_id=None  # Unassigned - staff assigns later
   )
   ```

### Sync Result
```json
{
  "invoice_id": 1,
  "new_items": 15,
  "updated_items": 10,
  "synced_item_ids": [101, 102, 103, ...],
  "updated_item_ids": [50, 51, 52, ...]
}
```

### Unassigned Items Workflow

New items from invoices are created with `section_id=null`:

1. **View unassigned items**:
   ```bash
   GET /stock-audit/items/unassigned/list
   ```

2. **Assign section to item**:
   ```bash
   PATCH /stock-audit/items/{item_id}/assign-section
   Body: {"section_id": 1}
   ```

3. **Item now appears in section**:
   - Shows in rack/section views
   - Available for physical audits
   - Included in stock reports

### Stock Reversal on Deletion

When invoice is deleted via `DELETE /invoice-analyzer/{invoice_id}`:

```python
# In routes.py - delete_invoice()
if invoice.is_verified:
    for invoice_item in invoice.items:
        # Find matching stock item
        stock_item = db.query(StockItem).filter(
            StockItem.shop_id == shop_id,
            StockItem.product_name == invoice_item.product_name,
            StockItem.batch_number == invoice_item.batch_number
        ).first()
        
        if stock_item:
            # Reverse the quantity
            stock_item.quantity_software -= int(invoice_item.quantity)
            
            # Delete if quantity becomes 0 or negative
            if stock_item.quantity_software <= 0 and stock_item.source_invoice_id == invoice_id:
                db.delete(stock_item)
```

### Integration Points

| Invoice Event | Stock Action | Details |
|--------------|--------------|----------|
| **Upload PDF** | None | Invoice created, not synced yet |
| **Verify Invoice** | **Sync to Stock** | Creates/updates StockItems |
| **Update Invoice** | **Re-sync** | Deletes old items, creates new ones |
| **Delete Invoice** | **Reverse Stock** | Subtracts quantities, deletes if needed |

### Data Mapping

| PurchaseInvoiceItem | → | StockItem |
|---------------------|---|------------|
| manufacturer | → | manufacturer |
| hsn_code | → | hsn_code |
| product_name | → | product_name |
| batch_number | → | batch_number |
| package | → | package |
| expiry_date | → | expiry_date |
| mrp | → | mrp |
| quantity | → | quantity_software |
| unit_price | → | unit_price |
| invoice.id | → | source_invoice_id |

### Complete Workflow Example

```python
# 1. Upload invoice PDF
response = requests.post('/invoice-analyzer/upload', files={'file': pdf})
invoice = response.json()
# Status: Invoice created, NOT synced to stock yet

# 2. Review and verify invoice
response = requests.put(f'/invoice-analyzer/{invoice["id"]}', json=invoice_data)
# Status: Invoice verified, AUTOMATICALLY synced to stock
# Result: 15 new StockItems created with section_id=null

# 3. View unassigned items
response = requests.get('/stock-audit/items/unassigned/list')
unassigned = response.json()
# Shows: 15 items from invoice waiting for section assignment

# 4. Assign sections
for item in unassigned:
    requests.patch(f'/stock-audit/items/{item["id"]}/assign-section', 
                   json={"section_id": determine_section(item)})
# Status: Items now organized in racks/sections

# 5. Conduct physical audit
response = requests.get('/stock-audit/audit/random-section')
section = response.json()
for item in section['items_to_audit']:
    physical_count = count_physical_stock(item)
    requests.put(f'/stock-audit/items/{item["id"]}/audit',
                 json={"physical_quantity": physical_count})
# Status: Physical counts recorded, discrepancies tracked

# 6. If invoice needs to be deleted
response = requests.delete(f'/invoice-analyzer/{invoice["id"]}')
# Status: Invoice deleted, stock quantities reversed automatically
```

### Error Handling

**Sync Failure**:
```python
# Invoice still saves even if sync fails
try:
    sync_result = InvoiceStockSyncService.sync_invoice_to_stock(db, invoice_id, shop_id)
except Exception as e:
    logger.error(f"Sync failed: {e}")
    # Invoice is saved, can retry sync later
```

**Duplicate Items**:
- Same product_name + batch_number → Updates existing quantity
- Different batch_number → Creates new StockItem

**Stock Reversal Failure**:
```python
# Deletion continues even if reversal fails
try:
    # Reverse stock quantities
except Exception as e:
    logger.error(f"Reversal failed: {e}")
    # Invoice still deleted
```

### Benefits of Integration

1. **Automatic Stock Updates**: No manual data entry for stock
2. **Single Source of Truth**: Invoice is the source for stock data
3. **Audit Trail**: source_invoice_id links stock to invoice
4. **Batch Tracking**: Separate stock items per batch
5. **Expiry Management**: Expiry dates tracked from invoice
6. **Price Tracking**: Unit prices and MRP from invoice
7. **Quantity Accuracy**: Software quantities match invoice quantities

## Authentication

All endpoints require staff authentication:
```python
def get_current_user(user_dict: dict, db: Session) -> tuple[Staff, int]:
    # Validates staff token
    # Resolves shop_id from shop_code
    # Returns (staff, shop_id)
```

**Token Requirements**:
- `user_type`: "staff"
- `shop_code`: Valid shop code
- `organization_id`: Matches staff's organization

## Configuration

### Environment Variables
```bash
GEMINI_API_KEY=your_gemini_api_key  # Required for AI extraction
GOOGLE_API_KEY=your_google_api_key  # Alternative to GEMINI_API_KEY
```

### Upload Directory
```python
UPLOAD_DIR = "uploads/invoices"
```

## Error Handling

### Duplicate Detection
```python
# Checks invoice_number before saving
if existing_invoice:
    raise HTTPException(status_code=409, detail="Duplicate invoice detected!")
```

### AI Fallback
```python
# Automatically falls back to regex if AI fails
if self.model:
    return self._ai_extract(text)
else:
    return self._fallback_extract(text)
```

### Stock Reversal Safety
```python
# Continues with deletion even if stock reversal fails
try:
    # Reverse stock quantities
except Exception as e:
    logger.error(f"Failed to reverse stock: {e}")
    # Continue with invoice deletion
```

## Date Handling

### Invoice Dates
- Format: DD/MM/YYYY
- Parsed to Python date object
- Stored as DATE in database

### Expiry Dates
- Input: MM/YYYY or DD/MM/YYYY
- Processing: Prepends "01/" if MM/YYYY
- Storage: DATE (always 1st of month for MM/YYYY)
- Display: Shows as MM/YYYY if day is 1st

```python
# Parsing
if len(parts) == 2:  # MM/YYYY
    expiry_date = datetime.strptime(f"01/{expiry_str}", "%d/%m/%Y").date()
elif len(parts) == 3:  # DD/MM/YYYY
    expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y").date()
```

## Logging

```python
logger.info("📤 Upload request received")
logger.info("💾 Saving file to: {file_path}")
logger.info("🔍 Starting PDF extraction...")
logger.info("✅ PDF extraction completed - Found {count} items")
logger.info("🤖 Using Gemini AI for invoice extraction...")
logger.info("✅ AI extraction successful")
logger.error("❌ PDF extraction failed: {error}")
```

## Usage Example

```python
# Upload invoice
files = {'file': open('invoice.pdf', 'rb')}
response = requests.post(
    'http://api/invoice-analyzer/upload',
    files=files,
    headers={'Authorization': f'Bearer {token}'}
)
invoice = response.json()

# Verify and update
update_data = {
    "invoice_number": invoice["invoice_number"],
    "invoice_date": invoice["invoice_date"],
    "supplier_name": invoice["supplier_name"],
    "gross_amount": 14000.00,
    "net_amount": 15120.00,
    "items": invoice["items"]
}
response = requests.put(
    f'http://api/invoice-analyzer/{invoice["id"]}',
    json=update_data,
    headers={'Authorization': f'Bearer {token}'}
)

# Stock is now automatically synced
```

## Best Practices

1. **Always verify AI-extracted data** before syncing to stock
2. **Use PUT endpoint** to mark invoice as verified
3. **Check duplicate warnings** before re-uploading
4. **Monitor AI extraction logs** for accuracy
5. **Keep PDF files** for audit trail (stored in uploads/invoices/)

## Troubleshooting

### AI extraction fails
- Check GEMINI_API_KEY is set
- Verify google-generativeai is installed
- System automatically falls back to regex

### Duplicate invoice error
- Check if invoice_number already exists
- Delete old invoice if needed
- Ensure invoice numbers are unique

### Stock sync fails
- Check stock_audit module is available
- Verify InvoiceStockSyncService is working
- Invoice still saves, sync can be retried

### Date parsing errors
- Ensure dates are in DD/MM/YYYY format
- For expiry: MM/YYYY or DD/MM/YYYY
- System handles both formats automatically
