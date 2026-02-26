-- Migration: Add shop_id to salary management tables
-- Run this on both LOCAL and PRODUCTION databases

-- Step 1: Add shop_id column to salary_records (nullable first)
ALTER TABLE salary_records ADD COLUMN shop_id INTEGER;

-- Step 2: Add shop_id column to staff_payment_info (nullable first)
ALTER TABLE staff_payment_info ADD COLUMN shop_id INTEGER;

-- Step 3: Add shop_id column to salary_alerts (nullable first)
ALTER TABLE salary_alerts ADD COLUMN shop_id INTEGER;

-- Step 4: Populate shop_id from staff table for salary_records
UPDATE salary_records sr
SET shop_id = s.shop_id
FROM staff s
WHERE sr.staff_id = s.id;

-- Step 5: Populate shop_id from staff table for staff_payment_info
UPDATE staff_payment_info spi
SET shop_id = s.shop_id
FROM staff s
WHERE spi.staff_id = s.id;

-- Step 6: Populate shop_id from staff table for salary_alerts
UPDATE salary_alerts sa
SET shop_id = s.shop_id
FROM staff s
WHERE sa.staff_id = s.id;

-- Step 7: Make shop_id NOT NULL and add foreign key constraints
ALTER TABLE salary_records ALTER COLUMN shop_id SET NOT NULL;
ALTER TABLE salary_records ADD CONSTRAINT fk_salary_records_shop FOREIGN KEY (shop_id) REFERENCES shops(id);
CREATE INDEX idx_salary_records_shop_id ON salary_records(shop_id);

ALTER TABLE staff_payment_info ALTER COLUMN shop_id SET NOT NULL;
ALTER TABLE staff_payment_info ADD CONSTRAINT fk_staff_payment_info_shop FOREIGN KEY (shop_id) REFERENCES shops(id);
CREATE INDEX idx_staff_payment_info_shop_id ON staff_payment_info(shop_id);

ALTER TABLE salary_alerts ALTER COLUMN shop_id SET NOT NULL;
ALTER TABLE salary_alerts ADD CONSTRAINT fk_salary_alerts_shop FOREIGN KEY (shop_id) REFERENCES shops(id);
CREATE INDEX idx_salary_alerts_shop_id ON salary_alerts(shop_id);

-- Verification queries (run these to check)
-- SELECT COUNT(*) FROM salary_records WHERE shop_id IS NULL;
-- SELECT COUNT(*) FROM staff_payment_info WHERE shop_id IS NULL;
-- SELECT COUNT(*) FROM salary_alerts WHERE shop_id IS NULL;
