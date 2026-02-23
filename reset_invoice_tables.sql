-- Drop existing purchase invoice tables
DROP TABLE IF EXISTS purchase_invoice_items CASCADE;
DROP TABLE IF EXISTS purchase_invoices CASCADE;

-- Create purchase_invoices table
CREATE TABLE purchase_invoices (
    id SERIAL PRIMARY KEY,
    shop_id INTEGER REFERENCES shops(id) ON DELETE CASCADE,
    staff_id INTEGER REFERENCES staff(id),
    staff_name VARCHAR,
    invoice_number VARCHAR NOT NULL,
    invoice_date DATE,
    due_date DATE,
    supplier_name VARCHAR,
    supplier_address TEXT,
    supplier_gstin VARCHAR(15),
    supplier_dl_numbers TEXT,
    supplier_phone VARCHAR(15),
    gross_amount DOUBLE PRECISION DEFAULT 0,
    discount_amount DOUBLE PRECISION DEFAULT 0,
    taxable_amount DOUBLE PRECISION DEFAULT 0,
    cgst_amount DOUBLE PRECISION DEFAULT 0,
    sgst_amount DOUBLE PRECISION DEFAULT 0,
    igst_amount DOUBLE PRECISION DEFAULT 0,
    total_gst DOUBLE PRECISION DEFAULT 0,
    round_off DOUBLE PRECISION DEFAULT 0,
    net_amount DOUBLE PRECISION DEFAULT 0,
    pdf_filename VARCHAR,
    pdf_path VARCHAR,
    raw_extracted_data JSONB,
    custom_fields JSONB,
    is_verified BOOLEAN DEFAULT FALSE,
    verified_by INTEGER REFERENCES staff(id),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create purchase_invoice_items table
CREATE TABLE purchase_invoice_items (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES purchase_invoices(id) ON DELETE CASCADE,
    hsn_code VARCHAR(8),
    product_name VARCHAR NOT NULL,
    batch_number VARCHAR,
    expiry_date VARCHAR,
    quantity DOUBLE PRECISION DEFAULT 0,
    free_quantity DOUBLE PRECISION DEFAULT 0,
    unit_price DOUBLE PRECISION DEFAULT 0,
    discount_percent DOUBLE PRECISION DEFAULT 0,
    discount_amount DOUBLE PRECISION DEFAULT 0,
    taxable_amount DOUBLE PRECISION DEFAULT 0,
    cgst_percent DOUBLE PRECISION DEFAULT 0,
    cgst_amount DOUBLE PRECISION DEFAULT 0,
    sgst_percent DOUBLE PRECISION DEFAULT 0,
    sgst_amount DOUBLE PRECISION DEFAULT 0,
    igst_percent DOUBLE PRECISION DEFAULT 0,
    igst_amount DOUBLE PRECISION DEFAULT 0,
    total_amount DOUBLE PRECISION DEFAULT 0,
    custom_fields JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_purchase_invoices_shop_id ON purchase_invoices(shop_id);
CREATE INDEX idx_purchase_invoices_invoice_number ON purchase_invoices(invoice_number);
CREATE INDEX idx_purchase_invoices_invoice_date ON purchase_invoices(invoice_date);
CREATE INDEX idx_purchase_invoice_items_invoice_id ON purchase_invoice_items(invoice_id);
CREATE INDEX idx_purchase_invoice_items_hsn_code ON purchase_invoice_items(hsn_code);
