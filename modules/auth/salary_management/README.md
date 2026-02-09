# Salary Management System

Complete salary management system for staff with payment tracking, QR codes, and automated alerts.

## Features

### Admin Features
- **Salary Dashboard**: Overview of all staff salaries, pending payments, and alerts
- **Payment Tracking**: Mark salaries as paid with admin audit trail
- **Staff Management**: Set monthly salaries when creating/updating staff
- **Payment Info Access**: View staff UPI IDs, QR codes, and bank details
- **Automated Alerts**: Get notified 5 days before salary due dates
- **Monthly Reports**: Comprehensive salary summaries by month/year
- **Overdue Tracking**: Automatic status updates for overdue payments

### Staff Features
- **Personal Profile**: View salary details, payment history, and pending amounts
- **Payment Info Management**: Update UPI ID, bank details, and upload QR codes
- **Salary History**: Complete payment history with status tracking
- **Payment Status**: See paid/pending/overdue months clearly

## API Endpoints

### Admin Routes (`/api/salary/`)

#### Dashboard & Overview
- `GET /dashboard` - Salary management dashboard
- `GET /alerts` - Active salary alerts
- `PUT /alerts/{alert_id}/dismiss` - Dismiss alert

#### Salary Records Management
- `POST /records` - Create salary record for staff
- `GET /records` - Get salary records (with filters)
- `PUT /records/{record_id}/pay` - Mark salary as paid

#### Staff Management
- `GET /staff/{staff_id}/profile` - Staff salary profile
- `GET /staff/{staff_id}/history` - Staff salary history
- `GET /staff/{staff_id}/payment-info` - Staff payment info
- `GET /staff/{staff_id}/qr-code` - Download staff QR code

#### Reports
- `GET /monthly-summary/{year}/{month}` - Monthly salary summary

### Staff Routes (`/api/salary/`)

#### Personal Management
- `GET /my-profile` - Current staff salary profile
- `GET /my-history` - Current staff salary history
- `GET /my-payment-info` - Current staff payment info
- `PUT /my-payment-info` - Update payment information
- `POST /my-qr-code` - Upload QR code image

## Database Schema

### Tables Created
1. **salary_records** - Individual salary records with payment status
2. **staff_payment_info** - UPI IDs, QR codes, bank details
3. **salary_alerts** - Automated alerts for upcoming/overdue payments

### Staff Table Updates
- Added `monthly_salary` field
- Renamed `full_name` to `name`
- Added `staff_code` field (auto-generated)

## Payment Status Flow

1. **PENDING** - Salary record created, payment due
2. **OVERDUE** - Payment past due date (auto-updated)
3. **PAID** - Payment completed by admin

## Alert System

### Automatic Alerts
- **Upcoming**: Created 5 days before due date
- **Overdue**: Created when payment becomes overdue

### Alert Management
- Admins can dismiss alerts
- Alerts auto-dismiss when salary is paid
- Dashboard shows active alerts count

## File Upload

### QR Code Management
- Staff can upload payment QR codes
- Files stored in `uploads/qr_codes/`
- Unique filenames prevent conflicts
- Admin can download QR codes for payments

## Usage Examples

### Creating Salary Record
```python
# Admin creates monthly salary for staff
POST /api/salary/records
{
    "staff_id": 1,
    "month": 12,
    "year": 2024,
    "salary_amount": 25000.0,
    "due_date": "2024-12-31"
}
```

### Staff Updates Payment Info
```python
# Staff updates their UPI ID
PUT /api/salary/my-payment-info
{
    "upi_id": "staff@paytm",
    "preferred_payment_method": "upi"
}
```

### Admin Pays Salary
```python
# Admin marks salary as paid
PUT /api/salary/records/123/pay
{
    "paid_by_admin": "Admin Name",
    "notes": "Paid via UPI"
}
```

## Integration

### Authentication
- Uses existing admin/staff authentication
- Admin routes require admin token
- Staff routes require staff token

### Database Migration
Run migration to set up tables:
```bash
python3 modules/auth/salary_management/migrate_salary_system.py
```

### Frontend Integration
- Dashboard widgets for admin overview
- Staff profile pages with salary info
- Payment forms with QR code display
- Alert notifications system

## Security Features

- Admin audit trail for all payments
- Staff can only access their own data
- File upload validation for QR codes
- Secure file storage with unique names