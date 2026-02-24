-- Migration: Change MRP from Float to String in bill_items table
-- Date: 2025-02-24
-- Purpose: Sync billing system with stock audit system to store MRP as exact text (e.g., "69.00/STRIP")

-- Change mrp column from Float to VARCHAR in bill_items
ALTER TABLE bill_items 
ALTER COLUMN mrp TYPE VARCHAR USING mrp::VARCHAR;

-- Add comment to document the change
COMMENT ON COLUMN bill_items.mrp IS 'Maximum Retail Price stored as text (e.g., "69.00/STRIP", "299.00/BOTTLE")';
