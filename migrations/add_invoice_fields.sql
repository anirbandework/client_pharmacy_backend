-- Add new fields to purchase_invoice_items table
-- Run this migration to add all the new fields

ALTER TABLE purchase_invoice_items 
ADD COLUMN IF NOT EXISTS composition VARCHAR,
ADD COLUMN IF NOT EXISTS unit VARCHAR,
ADD COLUMN IF NOT EXISTS manufacturing_date DATE,
ADD COLUMN IF NOT EXISTS selling_price FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS profit_margin FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS discount_on_purchase FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS discount_on_sales FLOAT DEFAULT 0.0,
ADD COLUMN IF NOT EXISTS before_discount FLOAT DEFAULT 0.0;

-- Make product_name nullable (for cases where extraction fails)
ALTER TABLE purchase_invoice_items 
ALTER COLUMN product_name DROP NOT NULL;

-- Add comment
COMMENT ON TABLE purchase_invoice_items IS 'Purchase invoice line items with comprehensive fields for pharmaceutical invoices';
