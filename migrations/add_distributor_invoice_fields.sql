-- Add new fields to distributor_invoices table to match purchase_invoices structure
ALTER TABLE distributor_invoices ADD COLUMN IF NOT EXISTS due_date DATE;
ALTER TABLE distributor_invoices ADD COLUMN IF NOT EXISTS custom_fields JSON;

-- Add new fields to distributor_invoice_items table to match purchase_invoice_items structure
ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS discount_on_purchase REAL DEFAULT 0.0;
ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS discount_on_sales REAL DEFAULT 0.0;
ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS before_discount REAL DEFAULT 0.0;
ALTER TABLE distributor_invoice_items ADD COLUMN IF NOT EXISTS custom_fields JSON;

-- Make shop_id nullable in distributor_invoice_items for external shops
-- Note: This may require data migration if there are existing records with shop_id constraints
