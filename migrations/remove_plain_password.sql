-- Migration: Remove plain_password columns from admins and staff tables
-- This improves security by removing plain text password storage

-- Remove plain_password from admins table
ALTER TABLE admins DROP COLUMN IF EXISTS plain_password;

-- Remove plain_password from staff table
ALTER TABLE staff DROP COLUMN IF EXISTS plain_password;
