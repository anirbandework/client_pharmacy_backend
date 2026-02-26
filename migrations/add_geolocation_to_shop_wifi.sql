-- Replace IP-based validation with geolocation-based validation
ALTER TABLE shop_wifi DROP COLUMN IF EXISTS allowed_ip_range;
ALTER TABLE shop_wifi ADD COLUMN IF NOT EXISTS shop_latitude VARCHAR(20);
ALTER TABLE shop_wifi ADD COLUMN IF NOT EXISTS shop_longitude VARCHAR(20);
ALTER TABLE shop_wifi ADD COLUMN IF NOT EXISTS geofence_radius_meters INTEGER DEFAULT 100;
