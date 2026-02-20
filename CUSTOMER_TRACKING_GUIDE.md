# Customer Tracking Module - Complete User Guide

## Overview
The Customer Tracking module helps pharmacy staff manage customer relationships, track contact records, send refill reminders, and analyze conversion rates. It integrates seamlessly with the Billing module to automatically create customer profiles.

---

## Table of Contents
1. [Customer Categories](#customer-categories)
2. [Contact Records Workflow](#contact-records-workflow)
3. [Customer Management](#customer-management)
4. [Refill Reminders](#refill-reminders)
5. [Reports & Analytics](#reports--analytics)
6. [Integration with Billing](#integration-with-billing)

---

## Customer Categories

The system tracks 4 types of customers:

### 1. Contact Sheet (`contact_sheet`)
- **Source**: Uploaded from Excel/CSV files
- **Status**: Pending contact
- **Purpose**: Cold leads from contact lists
- **Workflow**: Upload → Contact → Convert to customer

### 2. First Time Prescription (`first_time_prescription`)
- **Source**: Walk-in customers with prescriptions
- **Status**: New customer
- **Purpose**: Track first-time visitors
- **Workflow**: Create bill → Mark category → Follow up

### 3. Regular Branded (`regular_branded`)
- **Source**: Repeat customers preferring branded medicines
- **Status**: Established customer
- **Purpose**: Track brand-loyal customers
- **Workflow**: Regular purchases → Refill reminders

### 4. Generic Informed (`generic_informed`)
- **Source**: Customers educated about generic alternatives
- **Status**: Cost-conscious customer
- **Purpose**: Track generic adoption
- **Workflow**: Education → Generic purchases → Savings tracking

---

## Contact Records Workflow

### Step 1: Upload Contacts
**Location**: Customer Tracking → Upload Contacts tab

**Supported Formats**: Excel (.xlsx, .xls) or CSV (.csv)

**Required Columns**:
- `phone` - Customer phone number (required)
- `name` - Customer name (optional)

**Process**:
1. Click "Choose File" and select your contact list
2. System automatically:
   - Normalizes phone numbers (removes spaces, dashes)
   - Detects WhatsApp availability (placeholder for future)
   - Assigns contacts to staff members
   - Sets status to "pending"

**Example CSV**:
```csv
phone,name
9876543210,John Doe
9876543211,Jane Smith
```

### Step 2: View & Filter Contacts
**Location**: Customer Tracking → Contact Records tab

**Filters**:
- Contact Status: pending, contacted, converted, yellow
- WhatsApp Status: available, not_available, unknown

**Actions per Contact**:
- **Call**: Mark as contacted, add interaction notes
- **WhatsApp**: Send message (future integration)
- **Convert**: Mark as converted when they make a purchase
- **Yellow Flag**: Mark as "visited but didn't purchase"

### Step 3: Contact Interaction
When clicking "Interact" on a contact:

**Interaction Types**:
- `call` - Phone call made
- `whatsapp` - WhatsApp message sent
- `visit` - Customer visited store
- `email` - Email sent

**Fields**:
- Notes: What was discussed
- Customer Response: Their feedback
- Next Action: Follow-up plan
- Call Duration: Minutes (for calls)
- Call Successful: Yes/No

**Status Changes**:
- `pending` → `contacted` (after first interaction)
- `contacted` → `converted` (when they purchase)
- `contacted` → `yellow` (if they visit but don't buy)

### Step 4: Conversion
**Automatic**: When a bill is created with "Was Contacted Before" checked
**Manual**: Click "Mark as Converted" in Contact List

**What Happens**:
- Contact status → `converted`
- Conversion date recorded
- Conversion value (bill amount) saved
- Customer profile auto-created
- Contact linked to customer record

---

## Customer Management

### Customer Profiles
**Location**: Customer Tracking → Customers tab

**Filter by Category**:
- All Customers
- Contact Sheet
- First Time Prescription
- Regular Branded
- Generic Informed

**Customer Information**:
- Basic: Name, phone, email, age, gender, address
- Medical: Chronic conditions, allergies, primary doctor
- Purchase History: Total visits, total purchases
- Preferences: Prefers generic, generic education given
- Special Notes: Any additional information

**Actions**:
- View full profile
- Edit customer details
- View purchase history
- Set refill reminders

### Purchase Tracking
Each customer purchase records:
- Medicine name (brand/generic)
- Quantity and amount
- Duration (days of medication)
- Refill reminder date (auto-calculated as duration - 5 days)

---

## Refill Reminders

### How Refill Reminders Work

**Automatic Creation**:
When a bill is created with medicine duration specified:
- System calculates: `refill_date = purchase_date + duration_days - 5`
- Creates reminder in database
- Links to customer and purchase

**Example**:
- Purchase Date: Feb 1
- Medicine Duration: 30 days
- Refill Reminder: Feb 26 (30 - 5 + 1 = Feb 26)

### Viewing Reminders
**Location**: Customer Tracking → Refill Reminders tab

**Filter Options**:
- Days Ahead: 0 (today), 7, 14, 30 days
- Shows all reminders due within selected timeframe

**Reminder Information**:
- Customer name and phone
- Medicine name
- Reminder date
- Days until due
- Contact status (WhatsApp sent, Call made)
- Customer response

**Actions**:
- Send WhatsApp reminder
- Make phone call
- Mark as responded
- Mark as purchased

### Reminder Workflow
1. **View Due Reminders**: Check daily for upcoming refills
2. **Contact Customer**: WhatsApp or call
3. **Track Response**: Mark if customer responded
4. **Record Purchase**: Mark as purchased when they buy
5. **New Reminder**: Auto-created for next refill

---

## Reports & Analytics

### Conversion Report
**Location**: Customer Tracking → Reports tab

**Metrics Displayed**:

1. **Total Contacts**: All uploaded contacts
2. **Contacted**: Contacts that have been reached
3. **Converted**: Contacts who made purchases
4. **Conversion Rate**: (Converted / Contacted) × 100%
5. **Total Conversion Value**: Sum of all converted sales
6. **Average Conversion Value**: Total value / Converted count

**Time Filters**:
- Last 7 days
- Last 30 days
- Last 90 days
- All time

**Use Cases**:
- Measure staff performance
- Track ROI on contact lists
- Identify best conversion sources
- Optimize follow-up strategies

---

## Integration with Billing

### Creating Bills with Customer Tracking

**Location**: Billing → Create Bill

**New Fields**:

1. **Customer Category** (Dropdown):
   - Contact Sheet
   - First Time Prescription
   - Regular Branded
   - Generic Informed

2. **Was Contacted Before** (Checkbox):
   - Check if customer came from contact list
   - Triggers automatic conversion tracking

3. **Visited But No Purchase** (Checkbox):
   - For walk-ins who didn't buy
   - Marks contact as "yellow" status

### Automatic Actions on Bill Creation

**When "Was Contacted Before" is checked**:
1. System searches for contact by phone number
2. If found:
   - Marks contact as `converted`
   - Records conversion date and value
   - Creates/updates customer profile
   - Links contact to customer
3. If not found:
   - Creates new customer profile
   - Records category and purchase

**Customer Profile Creation**:
- Phone number from bill
- Customer name from bill
- Category from dropdown
- First visit date = bill date
- Total visits = 1
- Total purchases = bill amount

**Refill Reminder Creation**:
- For each medicine with duration specified
- Calculates reminder date
- Links to customer and purchase
- Ready for follow-up

---

## Best Practices

### For Contact Management
1. **Upload Regularly**: Add new contact lists weekly
2. **Follow Up Quickly**: Contact within 24-48 hours
3. **Document Everything**: Add detailed interaction notes
4. **Track Yellow Flags**: Follow up with non-purchasers
5. **Measure Conversion**: Review reports monthly

### For Customer Relationships
1. **Categorize Accurately**: Helps with targeted marketing
2. **Update Profiles**: Keep medical info current
3. **Generic Education**: Offer savings to appropriate customers
4. **Special Notes**: Record preferences and concerns
5. **Consistent Service**: Build trust through reliability

### For Refill Reminders
1. **Check Daily**: Review reminders each morning
2. **Multi-Channel**: Use both WhatsApp and calls
3. **Personalize**: Reference previous purchases
4. **Offer Value**: Mention discounts or new products
5. **Track Results**: Mark responses and purchases

### For Staff Performance
1. **Assign Contacts**: Distribute fairly among staff
2. **Set Targets**: Conversion rate goals
3. **Review Reports**: Weekly performance meetings
4. **Share Best Practices**: Learn from top performers
5. **Incentivize**: Reward high conversion rates

---

## Common Workflows

### Workflow 1: New Contact List
```
1. Receive contact list from marketing
2. Upload via "Upload Contacts" tab
3. System assigns to staff members
4. Staff reviews assigned contacts
5. Staff makes calls/sends WhatsApp
6. Records interactions and responses
7. Converts successful contacts
8. Follows up with non-responders
```

### Workflow 2: Walk-in Customer
```
1. Customer enters with prescription
2. Staff creates bill in Billing module
3. Selects category: "First Time Prescription"
4. Enters medicine duration if applicable
5. Completes bill
6. System creates customer profile
7. System creates refill reminder
8. Staff follows up before refill date
```

### Workflow 3: Refill Reminder
```
1. Check "Refill Reminders" tab daily
2. Filter for today's reminders
3. Send WhatsApp or call customer
4. Mark as "WhatsApp Sent" or "Call Made"
5. Customer responds and visits
6. Create new bill
7. System creates next refill reminder
8. Cycle continues
```

### Workflow 4: Generic Education
```
1. Regular customer buys branded medicine
2. Staff suggests generic alternative
3. Explains cost savings
4. Customer agrees to try
5. Create bill with category "Generic Informed"
6. Mark "Generic Education Given" in profile
7. Follow up on next visit
8. Track savings and satisfaction
```

---

## Troubleshooting

### Contact Upload Issues
**Problem**: File upload fails
- **Solution**: Check file format (Excel/CSV only)
- **Solution**: Ensure "phone" column exists
- **Solution**: Remove special characters from phone numbers

### Conversion Not Working
**Problem**: Contact not marked as converted
- **Solution**: Ensure phone numbers match exactly
- **Solution**: Check "Was Contacted Before" box
- **Solution**: Verify contact exists in system

### Reminders Not Showing
**Problem**: No refill reminders appear
- **Solution**: Ensure medicine duration was entered in bill
- **Solution**: Check date filters (days ahead)
- **Solution**: Verify customer profile exists

### Reports Show Zero
**Problem**: Conversion report shows no data
- **Solution**: Ensure contacts have been converted
- **Solution**: Check date range filter
- **Solution**: Verify bills have customer category set

---

## Database Schema Reference

### Tables
- `contact_records` - Uploaded contact lists
- `contact_interactions` - Call/message history
- `contact_reminders` - Follow-up reminders
- `customers` - Customer profiles
- `customer_purchases` - Purchase history
- `refill_reminders` - Medication refill alerts

### Key Relationships
- Contact → Customer (via contact_record_id)
- Customer → Purchases (via customer_id)
- Purchase → Refill Reminder (via purchase_id)
- Bill → Customer (via phone number)

---

## Future Enhancements

### Planned Features
- WhatsApp API integration for automated messages
- SMS reminders via Twilio
- Email marketing campaigns
- Customer loyalty points
- Prescription image upload
- Medicine interaction warnings
- Inventory alerts for customer medicines
- Birthday/anniversary reminders
- Bulk WhatsApp messaging
- Advanced analytics dashboard

---

## Support

For technical issues or feature requests:
1. Check this guide first
2. Review error messages in browser console
3. Check Railway logs for backend errors
4. Contact system administrator

---

**Last Updated**: February 20, 2026
**Version**: 1.0
