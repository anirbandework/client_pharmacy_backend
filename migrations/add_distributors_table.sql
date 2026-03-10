-- Migration: Add distributors table
-- Date: 2024-03-04
-- Description: Creates distributors table for medicine distributors who sell to shops

CREATE TABLE IF NOT EXISTS distributors (
    id SERIAL PRIMARY KEY,
    organization_id VARCHAR(255) NOT NULL,
    
    -- Basic info
    company_name VARCHAR(255) NOT NULL,
    distributor_code VARCHAR(100) UNIQUE NOT NULL,
    contact_person VARCHAR(255) NOT NULL,
    
    -- Authentication
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    is_password_set BOOLEAN DEFAULT FALSE,
    
    -- Business details
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    gstin VARCHAR(15),
    dl_number VARCHAR(50),
    
    -- Financial
    credit_limit NUMERIC(12, 2) DEFAULT 0.0,
    credit_days INTEGER DEFAULT 30,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Audit fields
    created_by_admin VARCHAR(255) NOT NULL,
    updated_by_admin VARCHAR(255),
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_distributors_organization_id ON distributors(organization_id);
CREATE INDEX IF NOT EXISTS idx_distributors_distributor_code ON distributors(distributor_code);
CREATE INDEX IF NOT EXISTS idx_distributors_phone ON distributors(phone);
CREATE INDEX IF NOT EXISTS idx_distributors_email ON distributors(email);
CREATE INDEX IF NOT EXISTS idx_distributors_active ON distributors(is_active);

-- Verify table creation
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'distributors'
ORDER BY ordinal_position;