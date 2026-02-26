-- Add break tracking and enforce geolocation
ALTER TABLE attendance_records ADD COLUMN IF NOT EXISTS total_break_minutes INTEGER DEFAULT 0;

-- Make geolocation fields NOT NULL (after ensuring existing records have values)
UPDATE shop_wifi SET shop_latitude = '0', shop_longitude = '0' WHERE shop_latitude IS NULL;
ALTER TABLE shop_wifi ALTER COLUMN shop_latitude SET NOT NULL;
ALTER TABLE shop_wifi ALTER COLUMN shop_longitude SET NOT NULL;
ALTER TABLE shop_wifi ALTER COLUMN geofence_radius_meters SET NOT NULL;
ALTER TABLE shop_wifi ALTER COLUMN geofence_radius_meters SET DEFAULT 100;
