-- Migration: Add password reset fields to all user tables
-- Date: 2024
-- Description: Adds reset_token and reset_token_expires fields for password reset functionality

-- Add reset fields to super_admins table
ALTER TABLE super_admins 
ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Add reset fields to admins table
ALTER TABLE admins 
ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Add reset fields to staff table
ALTER TABLE staff 
ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Add reset fields to distributors table
ALTER TABLE distributors 
ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255),
ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Create indexes for faster token lookups
CREATE INDEX IF NOT EXISTS idx_super_admins_reset_token ON super_admins(reset_token);
CREATE INDEX IF NOT EXISTS idx_admins_reset_token ON admins(reset_token);
CREATE INDEX IF NOT EXISTS idx_staff_reset_token ON staff(reset_token);
CREATE INDEX IF NOT EXISTS idx_distributors_reset_token ON distributors(reset_token);

-- Verify migration
SELECT 'Migration completed successfully!' as status;
