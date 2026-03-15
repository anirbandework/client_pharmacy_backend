-- SQL Migration Script to Fix Production Database Schema
-- Run this on PRODUCTION database to match LOCAL schema

-- ============================================================================
-- 1. Fix distributor_invoice_items table
-- ============================================================================

-- Change DOUBLE PRECISION to REAL for discount and pricing columns
ALTER TABLE distributor_invoice_items 
    ALTER COLUMN discount_on_sales TYPE REAL,
    ALTER COLUMN before_discount TYPE REAL,
    ALTER COLUMN discount_on_purchase TYPE REAL;

-- ============================================================================
-- 2. Fix distributors table
-- ============================================================================

-- Change VARCHAR to VARCHAR with specific lengths
ALTER TABLE distributors 
    ALTER COLUMN company_name TYPE VARCHAR(255),
    ALTER COLUMN password_hash TYPE VARCHAR(255),
    ALTER COLUMN created_by_super_admin TYPE VARCHAR(255),
    ALTER COLUMN contact_person TYPE VARCHAR(255),
    ALTER COLUMN updated_by_super_admin TYPE VARCHAR(255),
    ALTER COLUMN distributor_code TYPE VARCHAR(100),
    ALTER COLUMN email TYPE VARCHAR(255),
    ALTER COLUMN pincode TYPE VARCHAR(10),
    ALTER COLUMN state TYPE VARCHAR(100),
    ALTER COLUMN dl_number TYPE VARCHAR(50),
    ALTER COLUMN city TYPE VARCHAR(100),
    ALTER COLUMN gstin TYPE VARCHAR(15);

-- Change DOUBLE PRECISION to NUMERIC(12, 2) for credit_limit
ALTER TABLE distributors 
    ALTER COLUMN credit_limit TYPE NUMERIC(12, 2);

-- ============================================================================
-- 3. Fix purchase_invoice_items table
-- ============================================================================

-- Change VARCHAR to VARCHAR(255) for product_name
ALTER TABLE purchase_invoice_items 
    ALTER COLUMN product_name TYPE VARCHAR(255);

-- Change JSONB to JSON for custom_fields
ALTER TABLE purchase_invoice_items 
    ALTER COLUMN custom_fields TYPE JSON USING custom_fields::json;

-- ============================================================================
-- 4. Fix purchase_invoices table
-- ============================================================================

-- Add missing columns
ALTER TABLE purchase_invoices 
    ADD COLUMN IF NOT EXISTS admin_rejected_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS admin_rejected_by INTEGER REFERENCES admins(id);

-- Change VARCHAR to VARCHAR with specific lengths
ALTER TABLE purchase_invoices 
    ALTER COLUMN invoice_number TYPE VARCHAR(100),
    ALTER COLUMN supplier_name TYPE VARCHAR(255),
    ALTER COLUMN supplier_gstin TYPE VARCHAR(50),
    ALTER COLUMN pdf_filename TYPE VARCHAR(255),
    ALTER COLUMN pdf_path TYPE VARCHAR(500),
    ALTER COLUMN staff_name TYPE VARCHAR(100),
    ALTER COLUMN supplier_phone TYPE VARCHAR(50);

-- Change JSONB to JSON and TEXT for data columns
ALTER TABLE purchase_invoices 
    ALTER COLUMN raw_extracted_data TYPE TEXT USING raw_extracted_data::text,
    ALTER COLUMN custom_fields TYPE JSON USING custom_fields::json;

-- ============================================================================
-- 5. Fix stock_items_audit table
-- ============================================================================

-- Add missing columns
ALTER TABLE stock_items_audit 
    ADD COLUMN IF NOT EXISTS composition VARCHAR(500),
    ADD COLUMN IF NOT EXISTS manufacturing_date DATE,
    ADD COLUMN IF NOT EXISTS profit_margin NUMERIC(5, 2),
    ADD COLUMN IF NOT EXISTS selling_price NUMERIC(10, 2),
    ADD COLUMN IF NOT EXISTS unit VARCHAR(50);

-- ============================================================================
-- VERIFICATION QUERIES (Run these after migration to verify)
-- ============================================================================

-- Check distributor_invoice_items columns
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'distributor_invoice_items' 
-- AND column_name IN ('discount_on_sales', 'before_discount', 'discount_on_purchase');

-- Check distributors columns
-- SELECT column_name, data_type, character_maximum_length 
-- FROM information_schema.columns 
-- WHERE table_name = 'distributors' 
-- AND column_name IN ('company_name', 'password_hash', 'credit_limit');

-- Check purchase_invoices columns
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'purchase_invoices' 
-- AND column_name IN ('admin_rejected_at', 'admin_rejected_by', 'raw_extracted_data', 'custom_fields');

-- Check stock_items_audit columns
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'stock_items_audit' 
-- AND column_name IN ('composition', 'manufacturing_date', 'profit_margin', 'selling_price', 'unit');
