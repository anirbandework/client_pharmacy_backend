-- Add allowed_ip_range column to shop_wifi table for IP-based network validation
ALTER TABLE shop_wifi ADD COLUMN IF NOT EXISTS allowed_ip_range VARCHAR(50);

-- Example: Set IP range for existing shops (admin can update via WiFi Setup)
-- UPDATE shop_wifi SET allowed_ip_range = '192.168.1' WHERE shop_id = 1;
