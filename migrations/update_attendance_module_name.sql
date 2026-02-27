-- Update attendance_admin module name from "Attendance Management" to "Attendance Handling"
UPDATE modules 
SET module_name = 'Attendance Handling' 
WHERE module_key = 'attendance_admin';
