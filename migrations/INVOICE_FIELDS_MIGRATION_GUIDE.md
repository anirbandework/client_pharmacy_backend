# Invoice Analyzer - New Fields Migration Guide

## Changes Made

### 1. **Database Schema (models.py)**
Added new fields to `PurchaseInvoiceItem`:
- `composition` - Generic/salt name
- `unit` - Unit type (Box, Strip, Bottle, etc.)
- `manufacturing_date` - Manufacturing date
- `selling_price` - Selling price per unit
- `profit_margin` - Profit margin percentage
- `discount_on_purchase` - Purchase discount %
- `discount_on_sales` - Sales discount %
- `before_discount` - Amount before discount
- `product_name` - Changed to nullable (to handle extraction failures)

### 2. **API Schemas (schemas.py)**
Updated Pydantic models to include all new fields with proper Optional types.

### 3. **Extractors**
- **AI Extractor (ai_extractor.py)** - Updated Gemini prompt to extract all 29 fields
- **Excel Extractor (excel_extractor.py)** - Already updated with all fields
- **Fallback Parser** - Updated to include new fields (set to None/0 if not found)

### 4. **Routes (routes.py)**
Updated upload and update endpoints to handle all new fields.

### 5. **Template (template_routes.py)**
Updated Excel template to include all 25 fields with 3 sheets (Invoice, Instructions, Field Reference).

## Migration Steps

### Step 1: Run Database Migration
```bash
cd /Users/anirbande/Desktop/client\ backend
psql -U your_username -d your_database -f migrations/add_invoice_fields.sql
```

Or manually run:
```sql
ALTER TABLE purchase_invoice_items 
ADD COLUMN IF NOT EXISTS composition VARCHAR,
ADD COLUMN IF NOT EXISTS unit VARCHAR,
ADD COLUMN IF NOT EXISTS manufacturing_date DATE,
ADD COLUMN IF NOT EXISTS selling_price FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS profit_margin FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS discount_on_purchase FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS discount_on_sales FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS before_discount FLOAT DEFAULT 0.0;

ALTER TABLE purchase_invoice_items 
ALTER COLUMN product_name DROP NOT NULL;
```

### Step 2: Restart Backend Server
```bash
# Stop current server (Ctrl+C)
# Start again
python main.py
# or
uvicorn main:app --reload
```

### Step 3: Test
1. Download new template: `GET /api/purchase-invoices/download-template`
2. Upload Excel with new fields
3. Upload PDF (AI will extract new fields)
4. Verify all fields are saved correctly

## Field Compatibility

| Field | Excel | PDF AI | PDF Fallback | Database |
|-------|-------|--------|--------------|----------|
| composition | ✅ | ✅ | ⚪ (null) | ✅ |
| unit | ✅ | ✅ | ⚪ (null) | ✅ |
| manufacturing_date | ✅ | ✅ | ⚪ (null) | ✅ |
| selling_price | ✅ | ✅ | ⚪ (0) | ✅ |
| profit_margin | ✅ | ✅ | ⚪ (0) | ✅ |
| discount_on_purchase | ✅ | ✅ | ⚪ (0) | ✅ |
| discount_on_sales | ✅ | ✅ | ⚪ (0) | ✅ |
| before_discount | ✅ | ✅ | ⚪ (0) | ✅ |

## Error Fixed

**Original Error:**
```
'product_name': Input should be a valid string, input: None
```

**Solution:**
- Changed `product_name` column to nullable in database
- Changed schema to `Optional[str]`
- Added fallback: `product_name or "Unknown Product"`

## Backward Compatibility

✅ Old invoices without new fields will work fine (fields will be NULL/0)
✅ Old Excel templates will still work (missing fields auto-filled)
✅ Old PDFs will still extract (new fields set to NULL/0)

## Next Steps

1. Run migration SQL
2. Restart server
3. Test with new template
4. Update frontend to display new fields (optional)
