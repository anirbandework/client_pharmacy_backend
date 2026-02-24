-- Migration: Change MRP column from Float to String
-- This allows storing exact MRP text like "69.00/STRIP", "299.00/STRIP", "422.20/BOTTLE"

-- Update purchase_invoice_items table
ALTER TABLE purchase_invoice_items 
ALTER COLUMN mrp TYPE VARCHAR USING CASE 
    WHEN mrp IS NULL THEN NULL 
    ELSE mrp::VARCHAR 
END;

-- Update stock_items_audit table
ALTER TABLE stock_items_audit 
ALTER COLUMN mrp TYPE VARCHAR USING CASE 
    WHEN mrp IS NULL THEN NULL 
    ELSE mrp::VARCHAR 
END;

-- Add comment to document the change
COMMENT ON COLUMN purchase_invoice_items.mrp IS 'MRP as exact text from invoice (e.g., 69.00/STRIP, 299.00/STRIP)';
COMMENT ON COLUMN stock_items_audit.mrp IS 'MRP as exact text from invoice (e.g., 69.00/STRIP, 299.00/STRIP)';
