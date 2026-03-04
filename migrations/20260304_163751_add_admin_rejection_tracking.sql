-- Add admin rejection tracking fields to purchase_invoices table
ALTER TABLE purchase_invoices 
ADD COLUMN admin_rejected_by INTEGER REFERENCES admins(id),
ADD COLUMN admin_rejected_at TIMESTAMP;
