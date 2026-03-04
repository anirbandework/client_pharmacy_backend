"""
Migration: Add two-step verification to purchase invoices
Run this SQL in your PostgreSQL database
"""

-- Add new columns for two-step verification
ALTER TABLE purchase_invoices 
ADD COLUMN IF NOT EXISTS is_staff_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS staff_verified_by INTEGER REFERENCES staff(id),
ADD COLUMN IF NOT EXISTS staff_verified_at TIMESTAMP;

-- Migrate existing data: if is_verified=true, set both staff and admin verified
UPDATE purchase_invoices 
SET is_staff_verified = TRUE,
    staff_verified_by = verified_by,
    staff_verified_at = verified_at
WHERE is_verified = TRUE;

-- Update foreign key for verified_by to reference admins table
-- First, backup the old verified_by values to staff_verified_by if not already done
UPDATE purchase_invoices 
SET staff_verified_by = verified_by,
    staff_verified_at = verified_at
WHERE is_verified = FALSE AND verified_by IS NOT NULL;

-- Now clear verified_by for non-admin-verified invoices
UPDATE purchase_invoices 
SET verified_by = NULL,
    verified_at = NULL
WHERE is_verified = FALSE;

-- Note: The foreign key constraint change from staff.id to admins.id
-- will be handled by SQLAlchemy when the model is updated
