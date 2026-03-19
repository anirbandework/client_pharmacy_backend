-- Rollback Migration: Remove password reset fields from all user tables
-- Date: 2024
-- Description: Removes reset_token and reset_token_expires fields

-- Drop indexes first
DROP INDEX IF EXISTS idx_super_admins_reset_token;
DROP INDEX IF EXISTS idx_admins_reset_token;
DROP INDEX IF EXISTS idx_staff_reset_token;
DROP INDEX IF EXISTS idx_distributors_reset_token;

-- Remove reset fields from super_admins table
ALTER TABLE super_admins 
DROP COLUMN IF EXISTS reset_token,
DROP COLUMN IF EXISTS reset_token_expires;

-- Remove reset fields from admins table
ALTER TABLE admins 
DROP COLUMN IF EXISTS reset_token,
DROP COLUMN IF EXISTS reset_token_expires;

-- Remove reset fields from staff table
ALTER TABLE staff 
DROP COLUMN IF EXISTS reset_token,
DROP COLUMN IF EXISTS reset_token_expires;

-- Remove reset fields from distributors table
ALTER TABLE distributors 
DROP COLUMN IF EXISTS reset_token,
DROP COLUMN IF EXISTS reset_token_expires;

-- Verify rollback
SELECT 'Rollback completed successfully!' as status;
