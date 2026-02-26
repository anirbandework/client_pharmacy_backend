-- Add WiFi enforcement fields to attendance_settings table

ALTER TABLE attendance_settings 
ADD COLUMN IF NOT EXISTS allow_any_network BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS require_wifi_for_modules BOOLEAN DEFAULT TRUE;

-- Update existing records
UPDATE attendance_settings 
SET allow_any_network = FALSE, 
    require_wifi_for_modules = TRUE 
WHERE allow_any_network IS NULL OR require_wifi_for_modules IS NULL;
