-- Migration: Add composition, unit, manufacturing_date, selling_price, and profit_margin to stock_items_audit
-- Date: 2024-03-04
-- Description: Adds missing fields to stock_items_audit table to support full invoice data sync

-- Add composition field (indexed for fast lookups)
ALTER TABLE stock_items_audit 
ADD COLUMN IF NOT EXISTS composition VARCHAR(500);

CREATE INDEX IF NOT EXISTS idx_stock_items_composition 
ON stock_items_audit(composition);

-- Add unit field (e.g., Strip, Box, Bottle)
ALTER TABLE stock_items_audit 
ADD COLUMN IF NOT EXISTS unit VARCHAR(50);

-- Add manufacturing_date field
ALTER TABLE stock_items_audit 
ADD COLUMN IF NOT EXISTS manufacturing_date DATE;

-- Add selling_price field (different from unit_price which is purchase price)
ALTER TABLE stock_items_audit 
ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2);

-- Add profit_margin field (percentage)
ALTER TABLE stock_items_audit 
ADD COLUMN IF NOT EXISTS profit_margin NUMERIC(5, 2);

-- Verify columns were added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'stock_items_audit'
AND column_name IN ('composition', 'unit', 'manufacturing_date', 'selling_price', 'profit_margin')
ORDER BY column_name;
