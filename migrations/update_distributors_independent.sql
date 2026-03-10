-- Migration: Update distributors table structure
-- Date: 2024-03-04
-- Description: Updates distributors to be independent entities with many-to-many shop relationships

-- Drop existing table if it exists
DROP TABLE IF EXISTS distributors CASCADE;

-- Create distributors table (independent entities)
CREATE TABLE distributors (
    id SERIAL PRIMARY KEY,
    
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
    
    -- Audit fields (created by SuperAdmin)
    created_by_super_admin VARCHAR(255) NOT NULL,
    updated_by_super_admin VARCHAR(255),
    updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Create distributor-shop association table
CREATE TABLE distributor_shops (
    distributor_id INTEGER REFERENCES distributors(id) ON DELETE CASCADE,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (distributor_id, shop_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_distributors_distributor_code ON distributors(distributor_code);
CREATE INDEX IF NOT EXISTS idx_distributors_phone ON distributors(phone);
CREATE INDEX IF NOT EXISTS idx_distributors_email ON distributors(email);
CREATE INDEX IF NOT EXISTS idx_distributors_active ON distributors(is_active);
CREATE INDEX IF NOT EXISTS idx_distributor_shops_distributor_id ON distributor_shops(distributor_id);
CREATE INDEX IF NOT EXISTS idx_distributor_shops_shop_id ON distributor_shops(shop_id);

-- Verify table creation
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('distributors', 'distributor_shops')
ORDER BY table_name, ordinal_position;