# Customer Tracking System - Implementation Guide

## Overview
Complete customer tracking system for pharmacy with contact record management, customer categorization, and automated refill reminders.

## Features Implemented

### 1. Contact Record Management
- **Upload Contact Sheets**: Excel/CSV file upload with phone numbers
- **WhatsApp Detection**: Automatic detection of WhatsApp status (active/inactive)
- **Staff Assignment**: Distribute contacts evenly among staff members
- **Contact Status Tracking**: pending → contacted → converted/yellow
- **Interaction Logging**: Record calls, WhatsApp messages, visits with notes
- **Reminders**: Set follow-up reminders for staff

### 2. Customer Categorization (4 Categories)
- **contact_sheet**: Customers from uploaded contact records
- **first_time_prescription**: Walk-in customers with prescriptions
- **regular_branded**: Regular customers using branded medicines
- **generic_informed**: Customers informed about generic medicines

### 3. Customer Tracking
- Personal details (age, gender, address, email)
- Medical information (chronic conditions, allergies, primary doctor)
- Purchase history and visit tracking
- Generic medicine preference tracking
- Special notes for personalized care

### 4. Refill Reminder System
- Automatic reminder creation based on medicine duration
- Reminder date: 5 days before medicine exhausts
- WhatsApp and call reminder tracking
- Customer response tracking

### 5. Billing Integration
- Added fields to Bill model:
  - `customer_category`: Track customer type
  - `was_contacted_before`: Mark if customer was contacted from contact sheet
  - `visited_but_no_purchase`: Mark as "yellow" status
- Automatic customer creation/update on bill creation
- Contact conversion tracking

## Database Schema

### Tables Created
1. **contact_records**: Uploaded contact data with WhatsApp status
2. **contact_interactions**: Staff interactions with contacts
3. **contact_reminders**: Follow-up reminders for staff
4. **customers**: Customer profiles with categorization
5. **customer_purchases**: Purchase history with duration tracking
6. **refill_reminders**: Automated refill reminders

## API Endpoints

### Contact Records
- `POST /api/customer-tracking/contacts/upload` - Upload Excel/CSV contact file
- `GET /api/customer-tracking/contacts` - List contacts with filters
- `POST /api/customer-tracking/contacts/assign` - Assign contacts to staff
- `PUT /api/customer-tracking/contacts/{id}` - Update contact
- `POST /api/customer-tracking/contacts/{id}/interactions` - Add interaction
- `POST /api/customer-tracking/contacts/{id}/reminders` - Add reminder
- `POST /api/customer-tracking/contacts/{id}/mark-yellow` - Mark as yellow

### Customers
- `POST /api/customer-tracking/customers` - Create customer
- `GET /api/customer-tracking/customers` - List customers
- `GET /api/customer-tracking/customers/phone/{phone}` - Get by phone
- `PUT /api/customer-tracking/customers/{id}` - Update customer

### Refill Reminders
- `GET /api/customer-tracking/refill-reminders` - Get due reminders
- `POST /api/customer-tracking/refill-reminders/{id}/mark-sent` - Mark as sent

### Reports
- `GET /api/customer-tracking/reports/conversion` - Conversion report

## Workflow

### Contact Sheet Processing
1. Staff uploads Excel/CSV file with phone numbers
2. System normalizes phone numbers (+91XXXXXXXXXX)
3. System detects WhatsApp status (placeholder for API integration)
4. Contacts marked as "pending"
5. Manager assigns contacts to staff members
6. Staff calls and logs interactions
7. System tracks conversion when customer makes purchase

### Customer Visit Flow
1. Customer walks in
2. Staff asks: "Have you been contacted by our store before?"
3. If YES:
   - Mark `was_contacted_before = true`
   - Select category: `contact_sheet`
   - System auto-converts contact record on purchase
4. If NO:
   - Select appropriate category:
     - `first_time_prescription` (with prescription)
     - `regular_branded` (regular customer)
     - `generic_informed` (educated about generics)
5. Create bill with customer details
6. If customer visits but doesn't buy:
   - Mark contact as "yellow" status

### Refill Reminder Flow
1. During billing, staff enters medicine duration (e.g., 30 days)
2. System calculates reminder date (duration - 5 days)
3. System creates refill reminder
4. On reminder date:
   - WhatsApp message sent automatically
   - Staff gets list of customers to call
5. Staff marks reminder as sent
6. Track customer response and purchase

## Migration

Run Alembic migration:
```bash
alembic upgrade head
```

This creates all customer tracking tables and adds fields to bills table.

## Integration Points

### Billing System
- Bill creation automatically creates/updates customer
- Contact conversion tracking on first purchase
- Customer category selection in bill form

### Staff Management
- Contact assignment based on staff_id
- Interaction tracking per staff member
- Workload distribution

### WhatsApp Integration (TODO)
- Integrate WhatsApp Business API for status detection
- Automated message sending to WhatsApp-active contacts
- Refill reminder WhatsApp messages

## Frontend Requirements

### Contact Management UI
- File upload component for Excel/CSV
- Contact list with filters (status, WhatsApp, assigned staff)
- Contact detail view with interaction history
- Add interaction form (call notes, customer response)
- Reminder creation form

### Billing UI Updates
- Add customer category dropdown
- Add "Was contacted before?" checkbox
- Add "Mark as yellow" button for no-purchase visits

### Customer Profile UI
- Customer search by phone
- Customer detail view with purchase history
- Edit customer information
- View refill reminders

### Refill Reminder UI
- Daily reminder list
- Mark as sent (WhatsApp/Call)
- Track customer response

## Staff Training Points

1. **Always ask**: "Have you been contacted by our store before?"
2. **Categorize correctly**: Choose appropriate customer category
3. **Log interactions**: Record all calls and visits with notes
4. **Set reminders**: Use reminder system for follow-ups
5. **Mark yellow**: If customer visits but doesn't buy
6. **Duration tracking**: Always ask medicine duration for refill reminders
7. **Personalized care**: Use customer notes for better service

## Reports Available

### Conversion Report
- Total contacts uploaded
- Conversion rate (%)
- Yellow status count
- Total conversion value
- Average conversion value
- Pending/Contacted/Converted breakdown

## Security & Privacy
- All data scoped to shop_id
- Staff can only access their shop's data
- Cascade delete on shop deletion
- Phone numbers normalized and indexed

## Next Steps

1. **WhatsApp API Integration**: Implement actual WhatsApp detection and messaging
2. **SMS Integration**: Add SMS reminders as backup
3. **Analytics Dashboard**: Visual reports for conversion tracking
4. **AI Insights**: Predict customer behavior and optimal contact times
5. **Automated Workflows**: Auto-assign contacts, auto-send reminders
