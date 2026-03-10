-- Create distributor_invoices table
CREATE TABLE IF NOT EXISTS distributor_invoices (
    id SERIAL PRIMARY KEY,
    distributor_id INTEGER NOT NULL REFERENCES distributors(id),
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    invoice_number VARCHAR NOT NULL,
    invoice_date DATE NOT NULL,
    gross_amount FLOAT DEFAULT 0.0,
    discount_amount FLOAT DEFAULT 0.0,
    taxable_amount FLOAT DEFAULT 0.0,
    cgst_amount FLOAT DEFAULT 0.0,
    sgst_amount FLOAT DEFAULT 0.0,
    igst_amount FLOAT DEFAULT 0.0,
    total_gst FLOAT DEFAULT 0.0,
    round_off FLOAT DEFAULT 0.0,
    net_amount FLOAT DEFAULT 0.0,
    is_staff_verified BOOLEAN DEFAULT FALSE,
    staff_verified_by INTEGER REFERENCES staff(id),
    staff_verified_at TIMESTAMP,
    is_admin_verified BOOLEAN DEFAULT FALSE,
    admin_verified_by INTEGER REFERENCES admins(id),
    admin_verified_at TIMESTAMP,
    is_rejected BOOLEAN DEFAULT FALSE,
    rejected_by INTEGER,
    rejected_at TIMESTAMP,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_distributor_invoices_distributor ON distributor_invoices(distributor_id);
CREATE INDEX idx_distributor_invoices_shop ON distributor_invoices(shop_id);
CREATE INDEX idx_distributor_invoices_number ON distributor_invoices(invoice_number);

-- Create distributor_invoice_items table
CREATE TABLE IF NOT EXISTS distributor_invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL REFERENCES distributor_invoices(id) ON DELETE CASCADE,
    shop_id INTEGER NOT NULL REFERENCES shops(id),
    composition VARCHAR NOT NULL,
    product_name VARCHAR NOT NULL,
    batch_number VARCHAR NOT NULL,
    quantity FLOAT NOT NULL,
    unit VARCHAR NOT NULL,
    manufacturing_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    unit_price FLOAT NOT NULL,
    selling_price FLOAT NOT NULL,
    manufacturer VARCHAR,
    hsn_code VARCHAR,
    free_quantity FLOAT DEFAULT 0.0,
    package VARCHAR,
    mrp VARCHAR,
    profit_margin FLOAT DEFAULT 0.0,
    discount_percent FLOAT DEFAULT 0.0,
    discount_amount FLOAT DEFAULT 0.0,
    taxable_amount FLOAT NOT NULL,
    cgst_percent FLOAT DEFAULT 0.0,
    cgst_amount FLOAT DEFAULT 0.0,
    sgst_percent FLOAT DEFAULT 0.0,
    sgst_amount FLOAT DEFAULT 0.0,
    igst_percent FLOAT DEFAULT 0.0,
    igst_amount FLOAT DEFAULT 0.0,
    total_amount FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_distributor_invoice_items_shop ON distributor_invoice_items(shop_id);
