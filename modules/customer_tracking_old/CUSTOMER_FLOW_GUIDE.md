# Customer Tracking System - Complete Flow Guide

## Overview
This system tracks the complete customer journey from initial contact through conversion to repeat customer, with automated reminders and personalized care.

---

## Customer Flow Categories

### 1. Contact Sheet Customers (Category: `contact_sheet`)
**Flow:**
1. Upload contact records (PDF/Excel) → `/api/customers/upload-contacts`
2. System segregates by WhatsApp status
3. Auto-send WhatsApp materials to active numbers
4. Staff assigned to call non-WhatsApp numbers
5. Staff logs interactions and sets reminders
6. When customer visits → Mark as converted
7. If visited but didn't buy → Mark as "yellow"

### 2. First Time Prescription (Category: `first_time_prescription`)
**Flow:**
1. Walk-in customer with prescription
2. Staff enters details via quick purchase → `/api/customers/quick-purchase`
3. System creates customer profile
4. Records purchase with medicine duration
5. Auto-schedules refill reminder

### 3. Regular Branded Customers (Category: `regular_branded`)
**Flow:**
1. Repeat customer using branded medicines
2. Staff enters purchase details
3. System tracks purchase history
4. Identifies opportunity for generic education

### 4. Generic Informed (Category: `generic_informed`)
**Flow:**
1. Customer educated about generic alternatives
2. System tracks generic preference
3. Special retention tracking
4. Personalized follow-up

---

## Key API Endpoints

### Quick Purchase Entry (Main Endpoint for Walk-ins)
```http
POST /api/customers/quick-purchase
```

**Request Body:**
```json
{
  "phone": "9876543210",
  "name": "John Doe",
  "category": "first_time_prescription",
  "age": 45,
  "gender": "Male",
  "address": "123 Main St",
  "chronic_conditions": "Diabetes, Hypertension",
  "allergies": "Penicillin",
  "items": [
    {
      "medicine_name": "Metformin",
      "brand_name": "Glucophage",
      "generic_name": "Metformin HCl",
      "quantity": 30,
      "unit_price": 5.0,
      "total_amount": 150.0,
      "is_generic": false,
      "is_prescription": true,
      "duration_days": 30
    }
  ]
}
```

**Response:**
```json
{
  "customer_id": 123,
  "is_new_customer": true,
  "is_repeat_customer": false,
  "total_amount": 150.0,
  "refill_reminders_scheduled": 1,
  "message": "Purchase recorded successfully"
}
```

**Features:**
- ✅ Auto-creates customer if new
- ✅ Updates existing customer if repeat
- ✅ Detects if customer came from contact sheet
- ✅ Auto-schedules refill reminders
- ✅ Tracks generic preference
- ✅ Records all medical information

---

### Customer Lookup by Phone
```http
GET /api/customers/phone/{phone}
```

**Use Case:** Before entering purchase, check if customer exists

---

### Refill Reminders

#### Get Pending Reminders
```http
GET /api/customers/reminders/pending?days_ahead=3
```

**Response:**
```json
[
  {
    "id": 1,
    "customer_id": 123,
    "medicine_name": "Metformin",
    "reminder_date": "2024-01-15",
    "notification_sent": false,
    "customer_purchased": false
  }
]
```

#### Send Reminder Notification
```http
POST /api/customers/reminders/{reminder_id}/notify
```

---

### Contact Management

#### Upload Contact Records
```http
POST /api/customers/upload-contacts
```
- Accepts PDF or Excel files
- Auto-segregates by WhatsApp status
- Detects duplicates

#### Get Contacts with Filters
```http
GET /api/customers/contacts?status=pending&whatsapp_status=active
```

#### Add Interaction
```http
POST /api/customers/contacts/{contact_id}/interact
```

**Request Body:**
```json
{
  "contact_id": 1,
  "staff_code": "STAFF001",
  "interaction_type": "call",
  "notes": "Customer interested in diabetes medicines",
  "customer_response": "Will visit tomorrow",
  "next_action": "Follow up if doesn't visit",
  "call_duration": 180,
  "call_successful": true
}
```

#### Update Contact Status
```http
PUT /api/customers/contacts/{contact_id}/status?status=yellow
```

**Status Options:**
- `pending` - Not yet contacted
- `contacted` - Called/messaged
- `converted` - Made a purchase
- `yellow` - Visited but didn't buy
- `inactive` - Not interested

---

### Staff Management

#### Create Staff Member
```http
POST /api/customers/staff
```

```json
{
  "staff_code": "STAFF001",
  "name": "Jane Smith",
  "phone": "9876543210",
  "max_contacts_per_day": 20
}
```

#### Auto-Assign Contacts to Staff
```http
POST /api/customers/assign-contacts
```

#### Get Staff Daily Tasks
```http
GET /api/customers/staff/{staff_code}/tasks
```

---

### Analytics

#### Conversion Report
```http
GET /api/customers/analytics/conversion-report?start_date=2024-01-01&end_date=2024-01-31
```

#### Customer Analytics
```http
GET /api/customers/analytics/customer-analytics
```

**Returns:**
- Total customers by category
- Conversion metrics
- Top medicines
- Generic adoption rate

#### Daily Summary
```http
GET /api/customers/analytics/daily-summary?target_date=2024-01-15
```

---

## Staff Workflow

### Morning Routine
1. Check daily tasks: `GET /api/customers/staff/{staff_code}/tasks`
2. Review pending contacts and reminders
3. Check refill reminders: `GET /api/customers/reminders/pending`

### During Customer Visit
1. Ask: "Have you been contacted by our store before?"
2. Get customer by phone: `GET /api/customers/phone/{phone}`
3. Enter purchase: `POST /api/customers/quick-purchase`
4. System auto-detects if from contact sheet

### After Calls
1. Log interaction: `POST /api/customers/contacts/{contact_id}/interact`
2. Set reminder if needed: `POST /api/customers/contacts/{contact_id}/reminder`
3. Update status if visited but didn't buy: `PUT /api/customers/contacts/{contact_id}/status?status=yellow`

---

## Automated Features

### 1. WhatsApp Auto-Send
- When contacts uploaded with WhatsApp status = active
- Sends store materials automatically
- Tracks sent status

### 2. Refill Reminders
- Auto-scheduled when purchase has duration_days
- Reminder sent 3 days before medicine runs out
- WhatsApp notification with personalized message

### 3. Conversion Tracking
- Auto-detects when contact sheet customer makes purchase
- Updates contact status to "converted"
- Tracks conversion value
- Updates staff performance metrics

### 4. Task Assignment
- Auto-distributes contacts to staff
- Respects max_contacts_per_day limit
- Prevents overlap

---

## Database Schema

### Customer Categories
```python
CONTACT_SHEET = "contact_sheet"           # From uploaded contacts
FIRST_TIME_PRESCRIPTION = "first_time_prescription"  # Walk-in with prescription
REGULAR_BRANDED = "regular_branded"       # Regular using branded
GENERIC_INFORMED = "generic_informed"     # Educated about generics
```

### Contact Status
```python
PENDING = "pending"       # Not contacted yet
CONTACTED = "contacted"   # Called/messaged
CONVERTED = "converted"   # Made purchase
YELLOW = "yellow"         # Visited but didn't buy
INACTIVE = "inactive"     # Not interested
```

---

## Best Practices

### For Staff
1. **Always ask** if customer was contacted before
2. **Record everything** - allergies, conditions, preferences
3. **Set reminders** for follow-ups
4. **Update status** immediately after interactions
5. **Log detailed notes** for personalized care

### For Management
1. Review conversion reports weekly
2. Monitor staff performance metrics
3. Check pending reminders daily
4. Analyze customer analytics monthly
5. Train staff on generic medicine education

---

## Example: Complete Customer Journey

### Scenario: Contact Sheet to Repeat Customer

**Day 1: Contact Upload**
```bash
POST /api/customers/upload-contacts
# Upload Excel with 100 contacts
# System finds 60 have WhatsApp
# Auto-sends materials to 60 numbers
```

**Day 2: Staff Calling**
```bash
# Staff STAFF001 gets daily tasks
GET /api/customers/staff/STAFF001/tasks

# Calls contact, logs interaction
POST /api/customers/contacts/1/interact
{
  "staff_code": "STAFF001",
  "interaction_type": "call",
  "notes": "Interested in diabetes medicines",
  "customer_response": "Will visit tomorrow"
}
```

**Day 3: Customer Visits**
```bash
# Customer walks in, staff checks phone
GET /api/customers/phone/9876543210

# Records purchase
POST /api/customers/quick-purchase
{
  "phone": "9876543210",
  "name": "John Doe",
  "category": "contact_sheet",
  "items": [{
    "medicine_name": "Metformin",
    "duration_days": 30,
    ...
  }]
}

# System auto:
# - Marks contact as converted
# - Schedules refill reminder for Day 30
# - Updates staff conversion rate
```

**Day 30: Refill Reminder**
```bash
# System auto-sends WhatsApp reminder
# Customer visits again - now a repeat customer!
```

---

## Integration with Other Modules

- **Daily Records**: Purchase amounts sync with daily sales
- **Stock Audit**: Medicine purchases update stock levels
- **Profit Analysis**: Customer purchases feed into profit calculations
- **Invoice Analyzer**: Customer invoices tracked monthly

---

## Support

For questions or issues, refer to the main README.md or contact system administrator.
