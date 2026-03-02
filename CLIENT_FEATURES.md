# System Features Documentation







## Section 1: User Management & Authentication

### 1.1 User Types

#### Admin Users
- **Multi-Admin Organization**: Multiple admins can manage the same organization using a shared organization ID
- **Phone-Based Authentication**: Login using phone number and OTP verification
- **Secure Signup Process**: 
  - Admin account created by system administrator
  - Set password on first login
  - OTP verification for secure access
- **Profile Management**: Update name, email, phone number, and account status
- **Organization-Wide Access**: All admins with the same organization ID can access and manage all shops and staff

#### Staff Users
- **Individual Staff Accounts**: Each staff member has a unique account with staff code
- **Phone-Based Login**: Secure OTP-based authentication using registered phone number
- **Role-Based Access**: Different permission levels (staff, shop manager)
- **Shop Assignment**: Each staff member is assigned to a specific shop
- **Permissions Control**:
  - Manage staff (for shop managers)
  - View analytics
  - Manage inventory
  - Manage customers
- **Salary Information**: Monthly salary, joining date, and eligibility tracking
- **Device Registration**: Automatic device registration for attendance tracking

### 1.2 Shop Management

#### Shop Creation & Configuration
- **Unique Shop Codes**: Each shop has a unique code within the organization
- **Complete Shop Details**:
  - Shop name and address
  - Contact information (phone, email)
  - Business license number
  - GST number
  - Custom bill configuration
- **Multi-Shop Support**: Organizations can manage multiple shops
- **Shop Status**: Active/inactive status control
- **Audit Trail**: Track who created and last updated shop information

#### Shop Operations
- **Centralized Management**: All admins in organization can manage all shops
- **Staff Assignment**: Assign and manage staff for each shop
- **Shop-Specific Settings**: Individual attendance and operational settings per shop
- **Shop Analytics**: View performance metrics for each shop

### 1.3 Organization Structure

#### Hierarchical Organization
```
Organization (Shared ID)
├── Multiple Admins (shared access)
├── Multiple Shops
│   ├── Shop 1
│   │   ├── Staff Members
│   │   ├── WiFi Configuration
│   │   └── Attendance Settings
│   └── Shop 2
│       ├── Staff Members
│       ├── WiFi Configuration
│       └── Attendance Settings
```

#### Organization Features
- **Shared Organization ID**: Multiple admins collaborate under one organization
- **Unified Management**: All admins can manage all shops and staff
- **Data Isolation**: Each organization's data is completely isolated
- **Scalability**: Add unlimited shops and staff members

### 1.4 Data Privacy & Security

#### Authentication Security
- **OTP-Based Login**: Secure 6-digit OTP sent via SMS
- **Password Encryption**: Industry-standard bcrypt hashing (72-byte limit)
- **JWT Tokens**: Secure token-based session management
- **Token Expiry**: 24-hour token validity for security
- **Phone Number Validation**: Strict Indian phone number format (+91XXXXXXXXXX)

#### Data Protection
- **Role-Based Access Control**: Users can only access data they're authorized for
- **Shop-Level Isolation**: Staff can only access their assigned shop's data
- **Organization-Level Isolation**: Complete data separation between organizations
- **Secure Password Storage**: Never store plain text passwords
- **Password Requirements**: Minimum 6 characters, maximum 72 bytes

#### Privacy Features
- **Audit Trails**: Track who created and modified records
- **Timestamps**: All records include creation and update timestamps
- **User Activity Tracking**: Last login tracking for staff members
- **Data Integrity**: Unique constraints prevent duplicate entries

### 1.5 OTP Authentication System

#### OTP Features
- **Fast Delivery**: OTP sent via SMS within seconds
- **5-Minute Validity**: OTPs expire after 5 minutes for security
- **Resend Protection**: 30-second cooldown between OTP requests
- **One-Time Use**: OTPs are marked as used after verification
- **Automatic Cleanup**: Old OTPs are invalidated when new ones are requested

#### OTP Workflow
1. **Signup Flow** (First Time):
   - User sets password
   - OTP sent automatically
   - Verify OTP to complete signup
   
2. **Login Flow** (Subsequent):
   - Enter phone number and password
   - Request OTP
   - Verify OTP to login
   - Receive access token

#### Supported User Types
- **Admin OTP Login**: Secure access for organization admins
- **Staff OTP Login**: Secure access for shop staff members

---







## Section 2: Attendance Management System

### 2.1 WiFi-Based Automatic Attendance

#### Automatic Check-In/Out
- **WiFi Heartbeat System**: Staff app sends heartbeat every 30-60 seconds when connected to shop WiFi
- **Auto Check-In**: First heartbeat of the day automatically checks in staff
- **Auto Check-Out**: Automatically checks out when:
  - WiFi disconnects
  - No heartbeat received for 5 minutes
  - End of day (configurable time)
- **Real-Time Tracking**: Live monitoring of who is currently in the shop

#### Location Validation (Geofencing)
- **GPS Verification**: Every heartbeat includes GPS coordinates
- **Geofence Radius**: Configurable radius around shop (default 100 meters)
- **Distance Calculation**: Precise distance calculation using Haversine formula
- **Location Enforcement**: Staff must be within geofence to check in
- **Error Feedback**: Real-time feedback if outside allowed area

### 2.2 Attendance Features

#### Daily Attendance Tracking
- **Check-In Time**: Automatic timestamp when staff arrives
- **Check-Out Time**: Automatic timestamp when staff leaves
- **Total Work Hours**: Automatic calculation of hours worked
- **Break Time Tracking**: 
  - Gaps >30 minutes between heartbeats counted as breaks
  - Cumulative break time throughout the day
- **Late Arrival Detection**:
  - Configurable work start time and grace period
  - Automatic flagging of late arrivals
  - Exact minutes late calculation

#### Attendance Status
- **Present**: Staff checked in and working
- **Late**: Checked in after grace period
- **Half Day**: Partial day attendance
- **Absent**: No check-in for the day
- **On Leave**: Approved leave application

### 2.3 Shop WiFi Configuration

#### WiFi Setup (Admin Only)
- **Network Configuration**:
  - WiFi SSID (network name)
  - WiFi password (optional, for staff reference)
  - Shop GPS coordinates (latitude/longitude)
  - Geofence radius in meters
- **Multiple Networks**: Support for multiple WiFi networks per shop
- **Active/Inactive Status**: Enable or disable WiFi networks

#### Device Management
- **Automatic Registration**: Staff devices auto-register on first heartbeat
- **MAC Address Tracking**: Unique device identification
- **Device Information**: Track device name and last seen time
- **Multi-Device Support**: Staff can use multiple devices

### 2.4 Attendance Settings

#### Work Timings Configuration
- **Work Start Time**: Default 09:00 AM (configurable)
- **Work End Time**: Default 06:00 PM (configurable)
- **Grace Period**: Default 15 minutes late allowance (configurable)
- **Auto Checkout Time**: Default 07:00 PM (configurable)

#### Working Days Configuration
- **Individual Day Control**: Enable/disable each day of the week
- **Default Schedule**: Monday-Saturday working, Sunday off
- **Flexible Scheduling**: Customize for each shop

#### WiFi Enforcement
- **Module Access Control**: Restrict certain modules to WiFi-connected staff
- **Emergency Toggle**: `allow_any_network` - Admin can temporarily disable WiFi requirement
- **Protected Modules**: Stock audit, billing, profit analysis, customer tracking, purchase invoices
- **Exempt Modules**: Authentication, attendance, notifications, feedback

### 2.5 Leave Management

#### Leave Request System (Staff)
- **Leave Types**:
  - Sick Leave
  - Casual Leave
  - Earned Leave
- **Leave Application**:
  - Select date range (from date to date)
  - Automatic calculation of total days
  - Optional reason/description
- **Request Status Tracking**: View all submitted leave requests
- **Status Updates**: Pending, Approved, or Rejected

#### Leave Approval System (Admin)
- **Pending Requests**: View all pending leave applications
- **Filtered Views**: Filter by staff member or status
- **Approval Actions**:
  - Approve leave requests
  - Reject with reason
  - Track who approved/rejected
- **Leave Calendar**: View approved leaves affecting attendance

### 2.6 Attendance Reports & Analytics

#### Daily Reports
- **Today's Attendance**: Real-time view of all staff attendance
- **Connected Staff**: Live list of currently connected staff
- **Attendance Summary**:
  - Total staff count
  - Present today
  - Absent today
  - Late today
  - On leave today
  - Pending leave requests

#### Monthly Reports
- **Per-Staff Analytics**:
  - Total working days in month
  - Present days
  - Absent days
  - Late days
  - Leave days
  - Attendance percentage
  - Average check-in time
  - Total work hours

### 2.7 Real-Time Monitorings
  - Leave days
  - Attendance percentage
  - Average check-in time
  - Total work hours
- **Export Capability**: Generate reports for payroll processing

#### Attendance History
- **Date Range Filtering**: View attendance for any date range
- **Staff Filtering**: View specific staff member's attendance
- **Detailed Records**: Complete check-in/out times, breaks, and notes
- **Status Indicators**: Visual indicators for late, absent, on leave

### 2.7 Real-Time Monitoring

#### Admin Dashboard
- **Live Connection Status**: See who is currently in the shop
- **Last Seen Timestamps**: When each staff member last sent heartbeat
- **Duration Tracking**: How long each staff has been working today
- **Connection Alerts**: Identify staff with connection issues

#### Staff View
- **Personal Status**: Check own attendance status
- **Module Access Status**: See if connected to shop WiFi
- **Location Feedback**: Real-time feedback on geofence status
- **Error Messages**: Clear messages if outside allowed area

### 2.8 Automated Features

#### Background Processes
- **Stale Session Cleanup**: Runs every minute
  - Auto checks out sessions with no heartbeat for 5+ minutes
  - Adds explanatory notes
- **End-of-Day Checkout**: Scheduled daily
  - Auto checks out all staff at configured time
  - Calculates total work hours

#### Smart Break Detection
- **Automatic Break Tracking**: Gaps >30 minutes between heartbeats
- **Cumulative Calculation**: Total break time for the day
- **Resume Detection**: Automatically resumes session after breaks

### 2.9 Security & Compliance

#### Attendance Data Security
- **Shop-Level Isolation**: Staff can only view own attendance
- **Admin Access Control**: Admins can view all staff in their shops
- **Audit Trail**: Track all attendance modifications
- **Tamper-Proof**: Automatic timestamps prevent manual manipulation

#### Location Privacy
- **Purpose-Limited**: GPS only used for geofence validation
- **No Tracking**: Location not stored, only distance calculated
- **Transparent**: Staff knows when location is being checked
- **Error Reporting**: Clear feedback on location issues

---

## Key Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Leave Management**: Streamlined approval workflow  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  

---








## Section 3: Salary Management System

### 3.1 Staff Salary Configuration

#### Salary Setup
- **Monthly Salary**: Set fixed monthly salary for each staff member
- **Joining Date**: Track when staff member joined
- **Eligibility Tracking**: Automatic eligibility based on joining date
- **Flexible Configuration**: Update salary amounts anytime

#### Payment Information (Staff Managed)
- **UPI Details**:
  - UPI ID for instant payments
  - QR code upload for easy scanning
- **Bank Account Details**:
  - Account number
  - IFSC code
  - Account holder name
- **Preferred Payment Method**: Choose between UPI or bank transfer
- **Self-Service**: Staff can update their own payment information

### 3.2 Salary Record Management

#### Automatic Record Generation
- **Monthly Auto-Generation**: Create salary records for all eligible staff
- **Bulk Processing**: Generate records for entire month with one click
- **Smart Eligibility**: Only creates records for staff with salary configured
- **Duplicate Prevention**: Prevents creating duplicate records for same month

#### Manual Record Creation
- **Individual Records**: Create salary record for specific staff member
- **Custom Amounts**: Override default salary if needed
- **Due Date Setting**: Set custom payment due dates
- **Notes**: Add notes or special instructions

#### Salary Record Details
- **Month & Year**: Track which month the salary is for
- **Salary Amount**: Amount to be paid
- **Due Date**: Payment deadline (default: 5th of next month)
- **Payment Status**: Pending, Paid, or Overdue
- **Payment Date**: When salary was actually paid
- **Paid By**: Track which admin processed the payment
- **Notes**: Additional information or instructions

### 3.3 Payment Processing

#### Payment Workflow
1. **View Pending Payments**: See all unpaid salaries
2. **Access Payment Info**: View staff's UPI/bank details
3. **Make Payment**: Transfer via UPI or bank
4. **Mark as Paid**: Update record with payment confirmation
5. **Automatic Tracking**: System records payment date and admin name

#### Payment Methods
- **UPI Payment**:
  - Scan staff QR code
  - Or use UPI ID directly
  - Instant transfer confirmation
- **Bank Transfer**:
  - Use provided bank details
  - NEFT/RTGS/IMPS
  - Add transaction reference in notes

#### Payment Status Tracking
- **Pending**: Salary not yet paid
- **Paid**: Payment completed and confirmed
- **Overdue**: Payment past due date (automatic status update)

### 3.4 Salary Dashboard & Analytics

#### Admin Dashboard
- **Overview Metrics**:
  - Total staff count
  - Pending payments count
  - Overdue payments count
  - Upcoming payments (due in next 5 days)
  - Total pending amount
  - Total overdue amount
- **Active Alerts**: Real-time notifications for due/overdue salaries
- **Quick Actions**: Fast access to payment processing

#### Monthly Summary
- **Month-wise Breakdown**:
  - Total staff for the month
  - Paid count
  - Pending count
  - Overdue count
  - Total salary amount
  - Paid amount
  - Pending amount
- **Payment Progress**: Visual indicators of payment completion

### 3.5 Staff Salary Profile

#### Complete Salary View (Admin)
- **Staff Information**:
  - Name, staff code, contact details
  - Monthly salary amount
  - Joining date and eligibility status
- **Payment Information**:
  - UPI ID and QR code
  - Bank account details
  - Preferred payment method
- **Salary Statistics**:
  - Pending months count
  - Paid months count
  - Overdue months count
  - Last payment date
- **Quick Actions**: Direct access to payment processing

#### Staff Self-Service Portal
- **View Own Salary**: Check monthly salary amount
- **Payment History**: See all past payments
- **Pending Salaries**: View unpaid months
- **Update Payment Info**: Manage UPI/bank details
- **Upload QR Code**: Add/update payment QR code
- **Total Earnings**: Track total paid and pending amounts

### 3.6 Salary History & Reports

#### Individual Salary History
- **Complete Payment Record**: All salary records for a staff member
- **Chronological View**: Sorted by year and month
- **Payment Details**: Date paid, amount, paid by whom
- **Summary Statistics**:
  - Total amount paid (lifetime)
  - Total amount pending
  - Number of months paid
  - Number of months pending
- **Export Capability**: Download for personal records

#### Filtered Reports
- **Filter by Staff**: View specific staff member's records
- **Filter by Month/Year**: View specific time period
- **Filter by Status**: Pending, paid, or overdue only
- **Combined Filters**: Multiple filters for precise reports

### 3.7 Alerts & Notifications

#### Automatic Alerts
- **Upcoming Payment Alerts**: 5 days before due date
- **Overdue Alerts**: Immediate alert when payment becomes overdue
- **Alert Dashboard**: Centralized view of all active alerts
- **Dismissible Alerts**: Mark alerts as acknowledged

#### Alert Information
- **Staff Details**: Who needs to be paid
- **Amount**: How much is due
- **Due Date**: When payment is/was due
- **Alert Type**: Upcoming or overdue
- **Priority Sorting**: Overdue alerts shown first

### 3.8 Automated Features

#### Status Management
- **Auto-Overdue Detection**: Automatically marks pending payments as overdue after due date
- **Status Updates**: Real-time status changes based on dates
- **Alert Generation**: Automatic creation of alerts for new records
- **Alert Cleanup**: Auto-dismiss alerts when salary is paid

#### Bulk Operations
- **Monthly Generation**: Create all salary records for a month
- **Eligibility Check**: Only process eligible staff members
- **Duplicate Prevention**: Skip staff who already have records
- **Batch Summary**: Report of created and skipped records

### 3.9 Security & Access Control

#### Admin Access
- **Full Visibility**: View all staff salary information
- **Payment Processing**: Mark salaries as paid
- **Record Management**: Create, view, and update salary records
- **Report Access**: Generate and view all reports
- **Payment Info Access**: View staff payment details for processing

#### Staff Access
- **Own Data Only**: Staff can only view their own salary information
- **Payment Info Management**: Update own UPI/bank details
- **History Access**: View own payment history
- **No Admin Functions**: Cannot create records or mark as paid
- **Privacy Protected**: Cannot see other staff members' data

### 3.10 Data Privacy & Audit

#### Sensitive Data Protection
- **Payment Information**: Encrypted storage of UPI/bank details
- **Access Logging**: Track who accessed payment information
- **Role-Based Access**: Strict separation between admin and staff access
- **Secure File Storage**: QR codes stored securely with unique identifiers

#### Audit Trail
- **Payment Tracking**: Record who paid and when
- **Modification History**: Track all changes to salary records
- **Timestamps**: Creation and update times for all records
- **Admin Attribution**: Know which admin performed each action

---

## Enhanced Key Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Streamlined Payments**: Easy salary processing with payment info  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  
✅ **Payment Alerts**: Never miss a salary due date  
✅ **Audit Trail**: Complete record of all payments  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance and salary history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  
✅ **Payment Control**: Manage own payment information  
✅ **Salary Visibility**: Track pending and paid salaries  
✅ **Self-Service**: Update payment details without admin help  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  
✅ **Transparent**: Clear salary records and payment tracking  
✅ **Automated**: Reduce manual salary management work  

---







## Section 4: Notification & Communication System

### 4.1 Notification Types

#### Message Categories
- **Info**: General information and updates
- **Warning**: Important warnings that need attention
- **Urgent**: Critical messages requiring immediate action
- **Announcement**: Company-wide announcements and news

#### Visual Indicators
- **Color Coding**: Different colors for each notification type
- **Priority Badges**: Visual indicators for urgent messages
- **Unread Count**: Red badge showing number of unread notifications
- **Timestamp**: When notification was sent

### 4.2 Sending Notifications (Admin)

#### Target Options
- **Shop-Level Notifications**:
  - Send to all staff in selected shops
  - Select multiple shops at once
  - Reaches all active staff in those shops
- **Direct Staff Notifications**:
  - Send to specific staff members
  - Select individual staff from list
  - Targeted communication for specific people

#### Notification Creation
- **Title**: Short, clear subject line (max 200 characters)
- **Message**: Detailed message content
- **Type Selection**: Choose info, warning, urgent, or announcement
- **Target Selection**: Choose shops or specific staff
- **Optional Expiry**: Set expiration date for time-sensitive messages
- **Organization Scope**: Can only send to own organization's shops/staff

#### Validation & Security
- **Access Control**: Admins can only notify their organization
- **Shop Validation**: System verifies admin has access to selected shops
- **Staff Validation**: System verifies admin has access to selected staff
- **Input Validation**: Title and message cannot be empty

### 4.3 Receiving Notifications (Staff)

#### Notification Inbox
- **Notification List**: All notifications targeted to staff
- **Unread First**: Unread notifications shown at top
- **Read History**: Access to previously read notifications
- **Filtering Options**: Show only unread or include read messages
- **Pagination**: Load more notifications as needed

#### Notification Sources
- **Shop Notifications**: Messages sent to entire shop
- **Direct Notifications**: Messages sent specifically to the staff member
- **Automatic Filtering**: Only see relevant notifications
- **Expired Hidden**: Expired notifications automatically hidden

#### Reading Notifications
- **One-Click Read**: Mark as read with single tap
- **Auto-Update**: Unread count updates automatically
- **Read Timestamp**: Track when notification was read
- **Persistent History**: Access read notifications anytime

### 4.4 Real-Time Features

#### Notification Bell
- **Navbar Integration**: Bell icon in top navigation bar
- **Unread Badge**: Red badge with count of unread notifications
- **Quick Access**: Click to view notifications
- **Auto-Update**: Refreshes every 30 seconds
- **Staff Only**: Only visible to staff users

#### Live Updates
- **Automatic Polling**: Checks for new notifications every 30 seconds
- **Background Refresh**: Updates without page reload
- **Instant Notifications**: New messages appear immediately
- **Count Updates**: Unread count updates in real-time

### 4.5 Notification Statistics (Admin)

#### Engagement Metrics
- **Total Recipients**: How many staff received the notification
- **Total Read**: How many staff have read it
- **Read Percentage**: Percentage of recipients who read
- **Read Tracking**: See which staff have read the message

#### Sent Notifications View
- **History**: View all previously sent notifications
- **Chronological Order**: Most recent first
- **Detailed Stats**: Click to see read statistics
- **Audit Trail**: Track notification delivery and reads

### 4.6 Expiry Management

#### Time-Sensitive Messages
- **Optional Expiry**: Set expiration date/time for notifications
- **Automatic Hiding**: Expired notifications hidden from staff view
- **Permanent Messages**: Leave expiry blank for permanent notifications
- **Flexible Timing**: Set any future date/time for expiry

#### Use Cases
- **Event Reminders**: Expire after event date
- **Temporary Announcements**: Auto-hide after deadline
- **Urgent Alerts**: Expire once situation resolved
- **Permanent Policies**: No expiry for ongoing information

### 4.7 Audit Trail & Tracking

#### Read Tracking
- **Staff Name**: Record who read the notification
- **Shop ID**: Track which shop the staff belongs to
- **Read Timestamp**: Exact time notification was read
- **Audit History**: Complete record of all reads

#### Admin Tracking
- **Sender Information**: Track which admin sent notification
- **Admin Name**: Display sender's name with notification
- **Creation Time**: When notification was created
- **Target Details**: Record of who was targeted

### 4.8 User Interface

#### Admin Interface
- **Send Notification Form**:
  - Easy-to-use form with all options
  - Shop/staff selection dropdowns
  - Type selector with visual indicators
  - Optional expiry date picker
- **Sent Notifications List**:
  - View all sent notifications
  - Click to see statistics
  - Filter and search options
  - Chronological display

#### Staff Interface
- **Notification Bell**:
  - Always visible in navbar
  - Unread count badge
  - Quick access to inbox
- **Notification Inbox**:
  - Clean, organized list
  - Unread highlighted
  - One-click mark as read
  - Show/hide read messages toggle
  - Responsive mobile design

### 4.9 Communication Workflows

#### Scenario 1: Shop-Wide Announcement
1. Admin creates announcement notification
2. Selects target shops (e.g., Shop 1, Shop 2)
3. All staff in selected shops receive notification
4. Staff see notification in their inbox
5. Staff mark as read after viewing
6. Admin can track read statistics

#### Scenario 2: Urgent Alert to Specific Staff
1. Admin creates urgent notification
2. Selects specific staff members
3. Only selected staff receive notification
4. Urgent badge highlights importance
5. Staff receive immediate notification
6. Admin tracks who has read the alert

#### Scenario 3: Time-Sensitive Update
1. Admin creates notification with expiry date
2. Notification visible until expiry
3. Staff see notification in inbox
4. After expiry, notification auto-hides
5. Read statistics remain available to admin

### 4.10 Best Practices

#### For Admins
- **Clear Titles**: Use descriptive, concise titles
- **Appropriate Type**: Choose correct notification type
- **Right Audience**: Target only relevant staff/shops
- **Set Expiry**: Use expiry for time-sensitive messages
- **Check Stats**: Monitor read rates to ensure engagement
- **Urgent Sparingly**: Reserve urgent type for critical messages

#### For Staff
- **Check Regularly**: Review notifications daily
- **Mark as Read**: Mark notifications after reading
- **Urgent First**: Prioritize urgent notifications
- **Keep Inbox Clean**: Review and clear old notifications

### 4.11 Security & Privacy

#### Access Control
- **Organization Scoped**: Admins can only notify their organization
- **Shop Validation**: System verifies shop access before sending
- **Staff Validation**: System verifies staff access before sending
- **Authentication Required**: All endpoints require valid JWT tokens
- **Read-Only Staff**: Staff can only read and mark as read

#### Data Protection
- **Secure Storage**: Notifications stored securely in database
- **Audit Trail**: Complete tracking of all actions
- **Privacy Respected**: Staff only see their own notifications
- **No Unauthorized Access**: Strict role-based access control

### 4.12 Performance & Reliability

#### Optimization
- **Efficient Queries**: Fast database queries with proper indexes
- **Pagination**: Load notifications in batches
- **Smart Filtering**: Exclude expired and irrelevant notifications
- **Cascade Deletes**: Automatic cleanup of related records
- **Indexed Columns**: Fast lookups on key fields

#### Reliability
- **Real-Time Updates**: 30-second polling ensures fresh data
- **Error Handling**: Graceful handling of network issues
- **Automatic Retry**: Failed requests automatically retried
- **Persistent Storage**: Notifications stored permanently

---

## Enhanced Key Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Streamlined Payments**: Easy salary processing with payment info  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  
✅ **Payment Alerts**: Never miss a salary due date  
✅ **Audit Trail**: Complete record of all payments  
✅ **Instant Communication**: Send notifications to all staff instantly  
✅ **Engagement Tracking**: Monitor who reads your messages  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance and salary history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  
✅ **Payment Control**: Manage own payment information  
✅ **Salary Visibility**: Track pending and paid salaries  
✅ **Self-Service**: Update payment details without admin help  
✅ **Stay Informed**: Receive important updates instantly  
✅ **Never Miss Updates**: Notification bell keeps you informed  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  
✅ **Transparent**: Clear salary records and payment tracking  
✅ **Automated**: Reduce manual salary management work  
✅ **Connected**: Keep entire organization informed  
✅ **Trackable**: Monitor communication effectiveness  

---








## Section 5: Purchase Invoice Management & AI Processing

### 5.1 AI-Powered Invoice Processing

#### Automatic Data Extraction
- **AI Technology**: Powered by Google Gemini 2.5 Flash AI
- **PDF Upload**: Simply upload purchase invoice PDF
- **Instant Processing**: Automatic extraction of all invoice data
- **Structured Output**: Organized data ready for review
- **Fallback System**: Regex parser activates if AI unavailable

#### Extracted Information
- **Invoice Details**:
  - Invoice number
  - Invoice date and due date
  - Gross amount, discounts, taxes
  - Net amount
- **Supplier Information**:
  - Supplier name and address
  - GSTIN (GST Identification Number)
  - Drug License (DL) numbers
  - Contact phone number
- **Product Line Items**:
  - Manufacturer name (4-letter code)
  - HSN code (8-digit tax code)
  - Product name
  - Batch number
  - Quantity and free quantity
  - Package information (e.g., "10 X 6")
  - Expiry date (MM/YYYY or DD/MM/YYYY)
  - MRP (Maximum Retail Price)
  - Unit price
  - Tax breakdown (CGST, SGST, IGST)
  - Discount amounts
  - Total amount per item

#### Smart Data Processing
- **Format Recognition**: Handles various invoice formats
- **Date Parsing**: Supports multiple date formats
- **Tax Calculation**: Automatic GST breakdown
- **Package Extraction**: Identifies pack sizes
- **MRP Formatting**: Preserves price format (e.g., "69.00/STRIP")
- **Auto-Correction**: Fixes common OCR errors

### 5.2 Invoice Upload & Management

#### Upload Process
1. **Select PDF File**: Choose purchase invoice PDF
2. **Automatic Upload**: File saved securely to server
3. **AI Extraction**: System processes PDF automatically
4. **Data Review**: View extracted data in organized format
5. **Verification**: Review and edit if needed
6. **Confirmation**: Save verified invoice

#### File Storage
- **Secure Storage**: PDFs stored in organized folders
- **Naming Convention**: `{shop_id}_{timestamp}_{filename}.pdf`
- **Permanent Archive**: Files retained for audit trail
- **Easy Access**: Download original PDF anytime

#### Duplicate Detection
- **Automatic Check**: System checks for duplicate invoice numbers
- **Warning Alert**: Notifies if invoice already exists
- **Prevention**: Stops duplicate uploads automatically
- **Data Integrity**: Ensures unique invoice records

### 5.3 Invoice Verification & Editing

#### Review Interface
- **Organized Display**: All extracted data shown clearly
- **Item-by-Item View**: Each product listed separately
- **Financial Summary**: Totals and tax breakdown
- **Edit Capability**: Modify any field if needed

#### Verification Process
1. **Review Extracted Data**: Check all fields for accuracy
2. **Edit if Needed**: Correct any extraction errors
3. **Verify Items**: Confirm product details, quantities, prices
4. **Check Totals**: Ensure amounts match invoice
5. **Mark as Verified**: Confirm invoice is accurate
6. **Auto-Sync**: System syncs to stock automatically

#### Editable Fields
- **Invoice Information**: Number, dates, amounts
- **Supplier Details**: Name, address, GSTIN, DL numbers
- **Product Items**: All product fields editable
- **Quantities**: Adjust quantities and free quantities
- **Pricing**: Update unit prices and MRP
- **Tax Details**: Modify tax percentages and amounts

### 5.4 Stock Integration

#### Automatic Stock Sync
- **Triggered on Verification**: When invoice is verified and saved
- **Instant Update**: Stock quantities updated immediately
- **New Products**: Creates new stock items automatically
- **Existing Products**: Updates quantities for existing items
- **Batch Tracking**: Separate stock entries per batch number

#### Stock Item Creation
- **Product Information**: Manufacturer, HSN, product name
- **Batch Details**: Batch number and expiry date
- **Quantities**: Software quantity from invoice
- **Pricing**: Unit price and MRP
- **Package Info**: Pack size information
- **Source Tracking**: Links to source invoice
- **Unassigned Status**: Items await section assignment

#### Stock Update Logic
- **Match by Product + Batch**: Finds existing stock items
- **If Exists**: Adds quantity to existing stock
- **If New**: Creates new stock item
- **Quantity Tracking**: Maintains accurate software quantities
- **Audit Trail**: Tracks source invoice for each item

### 5.5 Invoice List & Search

#### Invoice List View
- **All Invoices**: View all uploaded invoices
- **Key Information**:
  - Invoice number and date
  - Supplier name
  - Net amount
  - Total items count
  - Verification status
  - Uploaded by (staff name)
  - Upload date/time
- **Pagination**: Load invoices in batches
- **Sorting**: Most recent first

#### Search & Filters
- **By Supplier**: Filter by supplier name (partial match)
- **By Date Range**: Filter by invoice date
  - Start date
  - End date
- **By Status**: Verified or unverified
- **Combined Filters**: Use multiple filters together
- **Quick Search**: Find invoices quickly

#### Invoice Details View
- **Complete Information**: All invoice and supplier details
- **Full Item List**: All products with complete details
- **Financial Breakdown**: Detailed tax and amount calculations
- **PDF Access**: Download original PDF
- **Edit Option**: Modify invoice if needed
- **Delete Option**: Remove invoice with stock reversal

### 5.6 Product Item Search

#### Search Capabilities
- **By Product Name**: Search for specific products
- **By Batch Number**: Find specific batches
- **Across Invoices**: Search all invoices at once
- **Partial Match**: Finds similar product names
- **Quick Results**: Fast search with pagination

#### Search Results
- **Product Details**: Full product information
- **Invoice Reference**: Which invoice contains the item
- **Quantities**: Quantity and free quantity
- **Pricing**: Unit price and MRP
- **Expiry Date**: When product expires
- **Tax Details**: Complete tax breakdown

### 5.7 Invoice Statistics & Analytics

#### Summary Statistics
- **Total Invoices**: Count of all invoices
- **Total Amount**: Sum of all invoice amounts
- **Total Items**: Count of all product items
- **Average Invoice Amount**: Mean invoice value
- **Date Range**: Statistics for selected period

#### Top Suppliers
- **Supplier Ranking**: Sorted by total purchase amount
- **Purchase Totals**: Amount spent per supplier
- **Invoice Count**: Number of invoices per supplier
- **Trend Analysis**: Track supplier relationships

#### Financial Insights
- **Purchase Trends**: Track spending over time
- **Tax Analysis**: GST amounts and breakdowns
- **Discount Tracking**: Total discounts received
- **Supplier Comparison**: Compare supplier pricing

### 5.8 Invoice Deletion & Stock Reversal

#### Deletion Process
1. **Select Invoice**: Choose invoice to delete
2. **Confirmation**: System asks for confirmation
3. **Stock Reversal**: Automatically reverses stock quantities
4. **PDF Removal**: Deletes PDF file from storage
5. **Database Cleanup**: Removes invoice and items
6. **Completion**: Confirms successful deletion

#### Stock Reversal Logic
- **Find Matching Items**: Locates stock items by product + batch
- **Subtract Quantities**: Removes invoice quantities from stock
- **Delete if Zero**: Removes stock items if quantity becomes zero
- **Source Check**: Only deletes items from this invoice
- **Safe Operation**: Continues even if reversal fails

#### Deletion Safety
- **Confirmation Required**: Prevents accidental deletion
- **Audit Trail**: Logs deletion action
- **Stock Protection**: Carefully reverses quantities
- **Error Handling**: Graceful handling of issues

### 5.9 Workflow Integration

#### Complete Workflow
1. **Upload Invoice PDF**
   - Staff uploads purchase invoice
   - AI extracts all data automatically
   - Invoice created in system

2. **Review & Verify**
   - Staff reviews extracted data
   - Edits any incorrect information
   - Marks invoice as verified

3. **Automatic Stock Sync**
   - System syncs to stock management
   - Creates/updates stock items
   - Items marked as unassigned

4. **Section Assignment**
   - Staff assigns items to rack sections
   - Items now organized in warehouse
   - Ready for physical audit

5. **Stock Management**
   - Items appear in stock lists
   - Available for sales
   - Tracked in inventory

#### Integration Points
- **Stock Audit System**: Automatic sync on verification
- **Inventory Management**: Real-time quantity updates
- **Batch Tracking**: Separate entries per batch
- **Expiry Management**: Tracks expiry dates
- **Pricing System**: Updates unit prices and MRP

### 5.10 Data Accuracy & Validation

#### AI Extraction Accuracy
- **High Accuracy**: Gemini 2.5 Flash provides excellent results
- **Format Handling**: Works with various invoice layouts
- **Error Correction**: Auto-fixes common OCR errors
- **Fallback System**: Regex parser as backup
- **Manual Review**: Staff verifies before saving

#### Validation Checks
- **Required Fields**: Ensures critical data present
- **Date Validation**: Checks date formats
- **Amount Validation**: Verifies calculations
- **Duplicate Check**: Prevents duplicate invoices
- **Tax Validation**: Ensures GST calculations correct

#### Data Quality
- **Structured Format**: Consistent data structure
- **Complete Information**: All fields captured
- **Accurate Calculations**: Correct totals and taxes
- **Clean Data**: Properly formatted and organized
- **Audit Trail**: Complete history maintained

### 5.11 Security & Access Control

#### Staff Access
- **Authentication Required**: Valid staff token needed
- **Shop-Level Access**: Staff can only access own shop's invoices
- **Organization Scope**: Limited to organization's data
- **Secure Upload**: Encrypted file transfer
- **Protected Storage**: Secure file storage

#### Data Protection
- **Encrypted Storage**: Sensitive data encrypted
- **Access Logging**: Track who accessed what
- **Audit Trail**: Complete action history
- **Secure PDFs**: Protected file storage
- **Privacy Maintained**: Shop-level data isolation

### 5.12 Benefits & Advantages

#### Time Savings
- **No Manual Entry**: AI extracts all data automatically
- **Instant Processing**: Upload and extract in seconds
- **Bulk Upload**: Process multiple invoices quickly
- **Auto-Sync**: Stock updates automatically
- **Reduced Errors**: Eliminates manual typing errors

#### Accuracy Improvements
- **AI Precision**: High accuracy extraction
- **Validation Checks**: Multiple validation layers
- **Error Detection**: Identifies potential issues
- **Duplicate Prevention**: Stops duplicate entries
- **Consistent Format**: Standardized data structure

#### Inventory Benefits
- **Real-Time Updates**: Stock always current
- **Batch Tracking**: Separate tracking per batch
- **Expiry Management**: Tracks product expiry
- **Source Tracking**: Links stock to invoices
- **Accurate Quantities**: Precise inventory counts

#### Business Insights
- **Purchase Analytics**: Track spending patterns
- **Supplier Analysis**: Compare supplier performance
- **Trend Identification**: Spot purchasing trends
- **Cost Tracking**: Monitor purchase costs
- **Financial Reports**: Detailed purchase reports

---

## Complete System Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Streamlined Payments**: Easy salary processing with payment info  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  
✅ **Payment Alerts**: Never miss a salary due date  
✅ **Audit Trail**: Complete record of all payments  
✅ **Instant Communication**: Send notifications to all staff instantly  
✅ **Engagement Tracking**: Monitor who reads your messages  
✅ **Purchase Insights**: Track spending and supplier performance  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance and salary history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  
✅ **Payment Control**: Manage own payment information  
✅ **Salary Visibility**: Track pending and paid salaries  
✅ **Self-Service**: Update payment details without admin help  
✅ **Stay Informed**: Receive important updates instantly  
✅ **Never Miss Updates**: Notification bell keeps you informed  
✅ **AI-Powered Tools**: Upload invoices with automatic data extraction  
✅ **Inventory Management**: Easy stock updates from invoices  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  
✅ **Transparent**: Clear salary records and payment tracking  
✅ **Automated**: Reduce manual salary management work  
✅ **Connected**: Keep entire organization informed  
✅ **Trackable**: Monitor communication effectiveness  
✅ **AI-Enhanced**: Leverage AI for invoice processing  
✅ **Integrated**: Seamless flow from invoice to inventory  

---









## Section 6: Inventory Management & Stock Audit System

### 6.1 Warehouse Organization

#### Rack Management
- **Physical Racks**: Create and manage storage racks
- **Rack Numbering**: Unique identifiers (e.g., R1, R2, R3)
- **Location Tracking**: Record physical location in shop
- **Description**: Add notes about rack contents
- **Flexible Structure**: Add unlimited racks as needed

#### Section Management
- **Rack Sections**: Divide racks into organized sections
- **Section Codes**: Unique codes (e.g., R1-S1, R1-S2)
- **Category Organization**: Group similar products
  - Antibiotics
  - Pain Relief
  - Vitamins
  - Cold & Flu
  - Diabetes Care
- **Easy Navigation**: Find products quickly by section

#### Organization Benefits
- **Structured Storage**: Organized warehouse layout
- **Quick Location**: Find products by rack and section
- **Efficient Audits**: Audit one section at a time
- **Staff Training**: Easy to teach new staff
- **Scalable**: Expand as inventory grows

### 6.2 Stock Item Management

#### Product Information
- **Complete Details**:
  - Manufacturer (4-letter code)
  - HSN code (8-digit tax code)
  - Product name
  - Batch number
  - Package size (e.g., "10 X 6")
  - Expiry date
  - MRP (Maximum Retail Price)
  - Unit price
- **Location**: Assigned rack and section
- **Source Tracking**: Links to purchase invoice

#### Quantity Tracking
- **Software Quantity**: Calculated from transactions
  - Starts from invoice quantity
  - Increases with purchases
  - Decreases with sales
  - Adjusts with manual corrections
- **Physical Quantity**: From physical audits
  - Set during physical count
  - Compared to software quantity
  - Identifies discrepancies

#### Stock Operations
- **Add Items**: Manually add new stock items
- **View Items**: List all stock with filters
- **Update Items**: Modify product details
- **Delete Items**: Remove discontinued products
- **Search**: Find items by name or batch
- **Filter**: By section, expiry, quantity

### 6.3 Purchase Management

#### Recording Purchases
- **Purchase Details**:
  - Purchase date
  - Supplier name
  - Invoice number
  - Total amount
- **Purchase Items**:
  - Select stock item
  - Enter batch number
  - Specify quantity
  - Unit cost and total cost
- **Automatic Stock Update**: Quantities increase automatically

#### Purchase Workflow
1. **Create Purchase Record**: Enter supplier and date
2. **Add Items**: Select products and quantities
3. **Automatic Update**: System adds to stock quantities
4. **Confirmation**: Purchase saved with updated stock

#### Purchase History
- **View All Purchases**: Complete purchase history
- **Filter by Date**: Select date range
- **Filter by Supplier**: View specific supplier purchases
- **Purchase Details**: See all items in each purchase
- **Edit/Delete**: Modify or remove purchases

### 6.4 Sales Management

#### Recording Sales
- **Sale Details**:
  - Sale date
  - Customer phone (optional)
  - Bill number
  - Total amount
- **Sale Items**:
  - Select stock item
  - Enter batch number
  - Specify quantity
  - Unit price and total price
- **Stock Validation**: Checks availability before sale
- **Automatic Stock Update**: Quantities decrease automatically

#### Sale Workflow
1. **Create Sale Record**: Enter customer and date
2. **Add Items**: Select products and quantities
3. **Availability Check**: System validates stock
4. **Automatic Update**: System deducts from stock
5. **Confirmation**: Sale saved with updated stock

#### Sales History
- **View All Sales**: Complete sales history
- **Filter by Date**: Select date range
- **Filter by Customer**: View specific customer sales
- **Sale Details**: See all items in each sale
- **Edit/Delete**: Modify or remove sales

### 6.5 Physical Audit System

#### Random Section Audit
- **Smart Selection**: System picks section for audit
- **Avoids Recent Audits**: Skips recently audited sections
- **Fair Distribution**: Ensures all sections audited regularly
- **Item List**: Shows all items to count in section

#### Audit Process
1. **Start Audit Session**: Begin audit tracking
2. **Get Random Section**: System selects section
3. **Physical Count**: Staff counts actual stock
4. **Record Results**: Enter physical quantity for each item
5. **Automatic Comparison**: System calculates discrepancies
6. **Complete Session**: Finish audit with summary

#### Audit Recording
- **Physical Quantity**: Actual counted amount
- **Software Quantity**: System calculated amount
- **Discrepancy**: Difference between physical and software
- **Notes**: Add observations or explanations
- **Timestamp**: When audit was conducted
- **Staff Tracking**: Who performed the audit

### 6.6 Discrepancy Management

#### Discrepancy Detection
- **Automatic Calculation**: System finds differences
- **Threshold Filtering**: Show only significant discrepancies
- **Section Grouping**: View by rack and section
- **Priority Sorting**: Largest discrepancies first

#### Discrepancy Information
- **Item Details**: Product name, batch, section
- **Software Quantity**: Expected amount
- **Physical Quantity**: Counted amount
- **Difference**: How much is missing or extra
- **Value Impact**: Financial impact of discrepancy
- **Last Audit**: When last counted

#### Resolution Process
1. **Identify Discrepancy**: Review audit results
2. **Investigate Cause**: Check for reasons
  - Theft or loss
  - Damaged items
  - Counting errors
  - System errors
  - Unreported sales
3. **Take Action**: Correct the issue
4. **Create Adjustment**: Update stock if needed
5. **Mark Resolved**: Close discrepancy with notes

### 6.7 Stock Adjustments

#### Adjustment Types
- **Damage**: Items damaged or expired
- **Return**: Customer returns
- **Correction**: Fix counting errors
- **Found**: Discovered missing items
- **Lost**: Confirmed missing items

#### Creating Adjustments
- **Select Item**: Choose stock item
- **Adjustment Type**: Select reason
- **Quantity Change**: Positive or negative
- **Reason**: Explain adjustment
- **Notes**: Additional details
- **Automatic Update**: Stock quantity adjusts

#### Adjustment Tracking
- **Complete History**: All adjustments recorded
- **Staff Attribution**: Who made adjustment
- **Timestamp**: When adjustment made
- **Audit Trail**: Full transparency
- **Filter Options**: By type, item, date

### 6.8 Stock Calculations

#### Automatic Calculations
- **Software Quantity Formula**:
  ```
  Software Qty = Invoice Qty + Purchases - Sales + Adjustments
  ```
- **Real-Time Updates**: Quantities update instantly
- **Transaction Tracking**: All changes recorded
- **Recalculation**: Can recalculate all items if needed

#### Stock Verification
- **View Calculation**: See detailed breakdown
- **Transaction History**: All purchases and sales
- **Adjustment History**: All manual changes
- **Verify Accuracy**: Compare to physical count

### 6.9 Reports & Analytics

#### Low Stock Report
- **Threshold Setting**: Define minimum quantity
- **Alert List**: Items below threshold
- **Reorder Suggestions**: What to purchase
- **Priority Items**: Critical low stock

#### Expiry Report
- **Days Ahead**: Set warning period (e.g., 30 days)
- **Expiring Items**: Products nearing expiry
- **Batch Details**: Which batches to clear
- **Value at Risk**: Financial impact

#### Stock Movement Report
- **Date Range**: Select period
- **Purchase Summary**: Total purchases and value
- **Sales Summary**: Total sales and value
- **Net Movement**: Overall stock change
- **Trend Analysis**: Track patterns

#### Audit Summary
- **Total Items**: Complete inventory count
- **Total Sections**: Number of sections
- **Items with Discrepancies**: Problem items
- **Audit Completion Rate**: % of items audited
- **Last Audit Date**: Most recent audit
- **Pending Audits**: Items not yet audited

### 6.10 AI-Powered Analytics

#### Comprehensive Analysis
- **AI Technology**: Powered by Google Gemini 2.0 Flash
- **Data Analysis**: Examines audit history and patterns
- **Intelligent Insights**: AI-generated recommendations
- **Trend Identification**: Spots patterns humans might miss

#### AI Insights Include
- **Key Findings**: 3-5 bullet points summarizing status
- **Risk Areas**: Sections or items needing attention
- **Recommendations**: 3-5 actionable steps to improve
- **Predictions**: Potential issues if trends continue
- **Staff Performance**: Audit quality by staff member

#### Analytics Charts
- **Discrepancy Trend**: Track over time
- **Section Analysis**: Problem areas by location
- **Staff Performance**: Audits vs discrepancies
- **Completion Rate**: Audit progress tracking

### 6.11 Unassigned Items Management

#### From Invoice Integration
- **Automatic Creation**: Items from verified invoices
- **Unassigned Status**: No section assigned yet
- **Pending Organization**: Awaits physical placement

#### Assignment Workflow
1. **View Unassigned**: List all items without sections
2. **Physical Placement**: Staff places items in racks
3. **Assign Section**: Update item with section
4. **Now Available**: Item appears in section views
5. **Ready for Audit**: Can be included in audits

#### Benefits
- **Organized Workflow**: Clear process for new stock
- **Prevents Errors**: Staff assigns based on physical location
- **Tracking**: Know what needs to be organized
- **Flexibility**: Assign when convenient

### 6.12 Excel Export

#### Export Options
- **Stock Items**: Complete inventory list
  - All product details
  - Quantities and values
  - Section assignments
  - Expiry dates
- **Audit Records**: Audit history
  - All audits conducted
  - Discrepancies found
  - Resolution status
- **Adjustments**: Manual changes
  - All adjustment types
  - Reasons and notes
  - Staff attribution

#### Export Features
- **Excel Format**: .xlsx files
- **Styled Headers**: Professional formatting
- **Auto-Sized Columns**: Easy to read
- **Complete Data**: All relevant information
- **Date Filtering**: Export specific periods

### 6.13 Integration with Invoice System

#### Seamless Connection
- **Automatic Sync**: Verified invoices create stock items
- **Batch Tracking**: Separate items per batch
- **Quantity Updates**: Stock increases from invoices
- **Price Tracking**: Unit prices and MRP from invoices
- **Source Linking**: Each item links to source invoice

#### Integration Benefits
- **Zero Manual Entry**: No typing product details
- **Accuracy**: Data directly from invoices
- **Time Savings**: Instant stock updates
- **Audit Trail**: Complete traceability
- **Consistency**: Standardized data format

### 6.14 Security & Access Control

#### Staff Access
- **Authentication Required**: Valid staff token
- **Shop-Level Access**: Only own shop's inventory
- **Action Tracking**: All changes logged
- **Staff Attribution**: Know who did what

#### Data Protection
- **Secure Storage**: Encrypted database
- **Audit Trail**: Complete history
- **Privacy**: Shop-level isolation
- **Backup**: Regular data backups

### 6.15 Best Practices

#### For Effective Inventory Management
- **Regular Audits**: Conduct physical counts regularly
- **Assign Sections**: Keep unassigned items list empty
- **Record Sales**: Always record sales to update stock
- **Use Adjustments**: Document damages and losses
- **Review Discrepancies**: Investigate and resolve issues
- **Check Expiry**: Monitor expiring items
- **Monitor Low Stock**: Reorder before stockouts
- **Use AI Insights**: Act on recommendations

#### For Accurate Stock Tracking
- **Verify Invoices**: Ensure invoice data is correct
- **Count Carefully**: Take time during physical audits
- **Document Issues**: Add notes to discrepancies
- **Resolve Quickly**: Address problems promptly
- **Train Staff**: Ensure everyone follows procedures
- **Review Reports**: Check analytics regularly

---

## Complete System Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Streamlined Payments**: Easy salary processing with payment info  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  
✅ **Payment Alerts**: Never miss a salary due date  
✅ **Audit Trail**: Complete record of all payments  
✅ **Instant Communication**: Send notifications to all staff instantly  
✅ **Engagement Tracking**: Monitor who reads your messages  
✅ **Purchase Insights**: Track spending and supplier performance  
✅ **Inventory Control**: Complete stock visibility and management  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance and salary history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  
✅ **Payment Control**: Manage own payment information  
✅ **Salary Visibility**: Track pending and paid salaries  
✅ **Self-Service**: Update payment details without admin help  
✅ **Stay Informed**: Receive important updates instantly  
✅ **Never Miss Updates**: Notification bell keeps you informed  
✅ **AI-Powered Tools**: Upload invoices with automatic data extraction  
✅ **Inventory Management**: Easy stock updates from invoices  
✅ **Organized Workflow**: Clear processes for stock management  
✅ **Audit Support**: Guided physical audit process  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  
✅ **Transparent**: Clear salary records and payment tracking  
✅ **Automated**: Reduce manual salary management work  
✅ **Connected**: Keep entire organization informed  
✅ **Trackable**: Monitor communication effectiveness  
✅ **AI-Enhanced**: Leverage AI for invoice and inventory insights  
✅ **Integrated**: Seamless flow from invoice to inventory to sales  
✅ **Accurate**: Real-time stock tracking with discrepancy detection  
✅ **Profitable**: Reduce losses through better inventory control  

---










## Section 7: Billing & Sales Management System

### 7.1 Point of Sale (POS) Billing

#### Quick Billing Interface
- **Medicine Search**: Fast search by product name
- **Batch Selection**: Choose specific batch if multiple available
- **Quantity Entry**: Specify quantity to sell
- **Automatic Pricing**: MRP and unit price auto-filled
- **Discount Application**: Apply item-level or bill-level discounts
- **Tax Calculation**: Automatic GST calculation (SGST + CGST)
- **Real-Time Total**: Running total updates as items added

#### Bill Creation Process
1. **Search Medicine**: Find product in inventory
2. **Add to Cart**: Select quantity and add to bill
3. **Apply Discounts**: Optional discounts per item or total
4. **Customer Details**: Enter customer information (optional)
5. **Payment Method**: Select cash, card, online, or split
6. **Generate Bill**: Create bill with unique bill number
7. **Stock Update**: Inventory automatically reduced

#### Customer Information
- **Customer Name**: Optional customer name
- **Phone Number**: For customer tracking and follow-up
- **Email**: For digital receipts (optional)
- **Doctor Name**: Prescribing doctor (if applicable)
- **Customer Category**: New, regular, VIP, etc.
- **Contact History**: Track if contacted before

### 7.2 Payment Methods

#### Split Payment Support
- **Cash Payment**: Traditional cash transactions
- **Card Payment**: Credit/debit card payments
- **Online Payment**: UPI, digital wallets, net banking
- **Split Payment**: Combine multiple payment methods
  - Example: ₹500 cash + ₹300 card
  - Flexible combinations
  - Separate tracking for each method

#### Payment Recording
- **Cash Amount**: Amount paid in cash
- **Card Amount**: Amount paid by card
- **Online Amount**: Amount paid online
- **Payment Reference**: Transaction ID for card/online
- **Change Calculation**: Automatic change returned
- **Total Validation**: Ensures payment covers bill amount

### 7.3 Bill Items & Pricing

#### Item Details
- **Product Information**:
  - Product name
  - Batch number
  - Rack and section location
  - Manufacturer
  - HSN code
- **Pricing Details**:
  - MRP (Maximum Retail Price)
  - Unit price (actual selling price)
  - Quantity
  - Discount percentage
  - Discount amount
- **Tax Breakdown**:
  - Tax percentage (typically 5% for medicines)
  - SGST (State GST) - 2.5%
  - CGST (Central GST) - 2.5%
  - Total tax amount
- **Total Price**: Final price after discount and tax

#### Automatic Calculations
- **Subtotal**: Sum of all item prices
- **Discount**: Item-level and bill-level discounts
- **Tax**: Automatic GST calculation
- **Total Amount**: Final payable amount
- **Change**: Amount to return to customer

### 7.4 Stock Integration

#### Automatic Stock Deduction
- **Real-Time Update**: Stock reduces immediately on bill creation
- **Batch Tracking**: Deducts from specific batch
- **Availability Check**: Validates stock before billing
- **Insufficient Stock Alert**: Warns if quantity not available
- **Multi-Batch Support**: Can sell from different batches

#### Stock Validation
- **Pre-Bill Check**: Verifies stock availability
- **Quantity Verification**: Ensures sufficient quantity
- **Batch Verification**: Confirms batch exists
- **Error Prevention**: Stops billing if stock insufficient

### 7.5 Bill Management

#### Bill List View
- **All Bills**: Complete billing history
- **Key Information**:
  - Bill number
  - Date and time
  - Customer name and phone
  - Total amount
  - Payment method
  - Staff who created bill
- **Search & Filter**:
  - By date range
  - By customer phone
  - By bill number
  - By payment method
  - By staff member

#### Bill Details
- **Complete Information**: All bill and customer details
- **Item Breakdown**: All products with pricing
- **Payment Details**: Split payment information
- **Tax Summary**: GST breakdown
- **Staff Attribution**: Who created the bill
- **Timestamp**: Exact date and time

#### Bill Operations
- **View Bill**: See complete bill details
- **Print Bill**: Generate printable receipt
- **Email Bill**: Send digital copy to customer
- **Search Bills**: Find specific bills quickly
- **Export Bills**: Download bill data

### 7.6 Medicine Search

#### Smart Search Features
- **Product Name Search**: Find by medicine name
- **Partial Match**: Works with incomplete names
- **Batch Filter**: Filter by specific batch
- **Availability Filter**: Show only in-stock items
- **Quick Results**: Fast search with autocomplete

#### Search Results Display
- **Product Name**: Full medicine name
- **Batch Number**: Specific batch
- **Available Quantity**: Current stock
- **MRP**: Maximum retail price
- **Unit Price**: Selling price
- **Location**: Rack and section
- **Expiry Date**: When product expires
- **Manufacturer**: Company name
- **Package**: Pack size information

### 7.7 Daily Records Management

#### Daily Sales Summary
- **Automatic Calculation**:
  - Number of bills
  - Total software sales (from bills)
  - Cash sales amount
  - Card sales amount
  - Online sales amount
- **Date-Based**: One record per day per shop
- **Real-Time Updates**: Updates as bills created

#### Manual Entries
- **Unbilled Amount**: Sales without formal bills
  - Emergency sales
  - Quick sales
  - Notes explaining unbilled items
- **Cash Management**:
  - Actual cash deposited (large notes)
  - Cash reserve (small notes and coins)
  - Denomination tracking

#### Daily Expenses
- **Expense Categories**:
  - Rent
  - Utilities (electricity, water)
  - Salaries
  - Supplies
  - Maintenance
  - Transportation
  - Miscellaneous
- **Expense Details**:
  - Category
  - Amount
  - Description
  - Staff who recorded
  - Timestamp
- **Total Expenses**: Sum of all daily expenses

### 7.8 Sales Analytics

#### Daily Analytics
- **Sales Summary**:
  - Total bills count
  - Total revenue
  - Cash vs card vs online breakdown
  - Average bill value
  - Peak hours analysis
- **Payment Method Distribution**:
  - Cash percentage
  - Card percentage
  - Online percentage
  - Split payment count

#### Period Analytics
- **Date Range Reports**: Select any period
- **Trend Analysis**: Track sales over time
- **Comparison**: Compare periods
- **Growth Metrics**: Calculate growth rates
- **Top Products**: Best-selling medicines
- **Customer Insights**: Repeat customers, new customers

#### Financial Reports
- **Revenue Reports**: Total sales by period
- **Expense Reports**: Total expenses by category
- **Profit Analysis**: Revenue minus expenses
- **Payment Method Reports**: Breakdown by payment type
- **Staff Performance**: Sales by staff member

### 7.9 Customer Tracking

#### Customer Database
- **Customer Records**: All customers with phone numbers
- **Purchase History**: All bills for each customer
- **Contact Tracking**: Mark if contacted before
- **Visit Tracking**: Track visits without purchases
- **Category Assignment**: Classify customers

#### Customer Categories
- **New Customer**: First-time buyer
- **Regular Customer**: Frequent buyer
- **VIP Customer**: High-value customer
- **Contacted Before**: Previously reached out
- **Visited No Purchase**: Browsed but didn't buy

#### Customer Insights
- **Total Purchases**: Lifetime purchase value
- **Last Purchase**: Most recent transaction
- **Purchase Frequency**: How often they buy
- **Preferred Products**: What they usually buy
- **Contact History**: Communication record

### 7.10 Bill Configuration

#### Shop-Specific Settings
- **Bill Format**: Customize bill layout
- **Shop Details**: Name, address, contact
- **License Numbers**: Drug license, GST number
- **Logo**: Shop logo on bills
- **Terms & Conditions**: Custom T&C text
- **Footer Text**: Additional information

#### Tax Configuration
- **Default Tax Rate**: Standard GST percentage
- **Tax Breakdown**: SGST and CGST split
- **Tax-Free Items**: Exempted products
- **Tax Calculation**: Automatic or manual

### 7.11 Prescription Management

#### Prescription Tracking
- **Prescription Required**: Mark if prescription needed
- **Doctor Name**: Prescribing doctor
- **Prescription Notes**: Additional information
- **Compliance**: Track prescription requirements

#### Prescription Validation
- **Alert System**: Warn for prescription-only medicines
- **Doctor Tracking**: Record prescribing doctors
- **Audit Trail**: Complete prescription history

### 7.12 Cash Management

#### Daily Cash Reconciliation
- **Expected Cash**: From cash bills
- **Actual Cash**: Physical cash counted
- **Cash Deposited**: Large denomination notes
- **Cash Reserve**: Small notes and coins for change
- **Variance**: Difference between expected and actual

#### Denomination Tracking
- **Large Notes**: ₹500, ₹200, ₹100 (deposited)
- **Small Notes**: ₹50, ₹20, ₹10 (reserve)
- **Coins**: ₹5, ₹2, ₹1 (reserve)
- **Change Management**: Maintain adequate change

### 7.13 Security & Access Control

#### Staff Access
- **Authentication Required**: Valid staff token
- **Shop-Level Access**: Only own shop's bills
- **Action Tracking**: All bills logged with staff name
- **Audit Trail**: Complete transaction history

#### Data Protection
- **Secure Storage**: Encrypted database
- **Customer Privacy**: Protected personal information
- **Transaction Security**: Secure payment processing
- **Backup**: Regular data backups

### 7.14 Integration Benefits

#### Inventory Integration
- **Real-Time Stock**: Always current inventory
- **Automatic Deduction**: No manual stock updates
- **Batch Tracking**: Precise batch-level tracking
- **Expiry Management**: Tracks product expiry

#### Financial Integration
- **Daily Records**: Automatic sales summary
- **Expense Tracking**: Complete expense management
- **Profit Calculation**: Revenue minus expenses
- **Tax Reports**: GST calculation and reporting

#### Customer Integration
- **Customer Database**: Build customer relationships
- **Purchase History**: Track customer behavior
- **Marketing Insights**: Identify opportunities
- **Loyalty Programs**: Support repeat business

### 7.15 Best Practices

#### For Efficient Billing
- **Verify Stock**: Check availability before billing
- **Accurate Entry**: Double-check quantities and prices
- **Customer Details**: Collect phone numbers for tracking
- **Payment Verification**: Confirm payment before finalizing
- **Print Bills**: Provide receipts to customers
- **Daily Reconciliation**: Match cash at end of day

#### For Accurate Records
- **Record Unbilled**: Don't forget unbilled sales
- **Track Expenses**: Record all daily expenses
- **Deposit Cash**: Separate large notes for deposit
- **Maintain Reserve**: Keep adequate change
- **Review Daily**: Check daily records for accuracy
- **Resolve Discrepancies**: Address cash variances promptly

---

## Complete System Benefits

### For Admins
✅ **Automated Attendance**: No manual entry required  
✅ **Real-Time Visibility**: Know who's working at any moment  
✅ **Accurate Payroll**: Precise work hours for salary calculation  
✅ **Streamlined Payments**: Easy salary processing with payment info  
✅ **Comprehensive Reports**: Monthly analytics for decision making  
✅ **Multi-Shop Management**: Manage all locations from one account  
✅ **Payment Alerts**: Never miss a salary due date  
✅ **Audit Trail**: Complete record of all payments  
✅ **Instant Communication**: Send notifications to all staff instantly  
✅ **Engagement Tracking**: Monitor who reads your messages  
✅ **Purchase Insights**: Track spending and supplier performance  
✅ **Inventory Control**: Complete stock visibility and management  
✅ **Sales Analytics**: Detailed revenue and profit reports  

### For Staff
✅ **Hassle-Free**: Automatic check-in when arriving at shop  
✅ **Transparent**: View own attendance and salary history anytime  
✅ **Easy Leave Requests**: Apply for leave through the app  
✅ **Fair Tracking**: Accurate work hours and break time  
✅ **Secure Access**: OTP-based authentication  
✅ **Payment Control**: Manage own payment information  
✅ **Salary Visibility**: Track pending and paid salaries  
✅ **Self-Service**: Update payment details without admin help  
✅ **Stay Informed**: Receive important updates instantly  
✅ **Never Miss Updates**: Notification bell keeps you informed  
✅ **AI-Powered Tools**: Upload invoices with automatic data extraction  
✅ **Inventory Management**: Easy stock updates from invoices  
✅ **Organized Workflow**: Clear processes for stock management  
✅ **Audit Support**: Guided physical audit process  
✅ **Fast Billing**: Quick POS system for customer service  
✅ **Automatic Calculations**: No manual math required  

### For Organization
✅ **Scalable**: Add unlimited shops and staff  
✅ **Secure**: Industry-standard encryption and authentication  
✅ **Compliant**: Complete audit trails and data privacy  
✅ **Efficient**: Reduce administrative overhead  
✅ **Reliable**: Automatic backups and data integrity  
✅ **Transparent**: Clear salary records and payment tracking  
✅ **Automated**: Reduce manual salary management work  
✅ **Connected**: Keep entire organization informed  
✅ **Trackable**: Monitor communication effectiveness  
✅ **AI-Enhanced**: Leverage AI for invoice and inventory insights  
✅ **Integrated**: Seamless flow from invoice to inventory to sales  
✅ **Accurate**: Real-time stock tracking with discrepancy detection  
✅ **Profitable**: Reduce losses through better inventory control  
✅ **Customer-Focused**: Build relationships and track preferences  
✅ **Financial Control**: Complete visibility into revenue and expenses  

---









## Section 8: Feedback & Support System

### 8.1 Share Your Feedback

#### Easy Feedback Submission
- **Quick Access**: Feedback option available in app
- **Simple Form**: Easy-to-use feedback form
- **Express Yourself**: Share thoughts, ideas, and concerns
- **Track Status**: See updates on your feedback

#### Feedback Types
- **🚀 Feature Request**: Suggest new features you'd like
- **🐛 Bug Report**: Report issues or problems
- **💡 Improvement**: Suggest how to make things better
- **😞 Complaint**: Share concerns or frustrations
- **💖 Appreciation**: Say thanks or share positive feedback
- **📌 Other**: Anything else you want to share

### 8.2 How to Submit Feedback

#### Simple Process
1. **Select Type**: Choose what kind of feedback
2. **Share Your Mood**: How are you feeling?
   - 😄 Excited
   - 😊 Happy
   - 😐 Neutral
   - 😤 Frustrated
   - 😡 Angry
3. **Write Title**: Give it a short title
4. **Describe Details**: Explain your feedback
5. **Rate Satisfaction**: Give 1-5 star rating (optional)
6. **Would Recommend**: Would you recommend the system?
7. **Submit**: Send your feedback

### 8.3 Feedback Status

#### Track Your Feedback
- **Pending**: Feedback received, awaiting review
- **Reviewed**: Team has reviewed your feedback
- **In Progress**: Working on your suggestion/issue
- **Resolved**: Issue fixed or feature implemented
- **Closed**: Feedback addressed and closed

#### View Your History
- **My Feedback**: See all your submitted feedback
- **Status Updates**: Track progress on each item
- **Responses**: Read replies from support team
- **Timeline**: See when feedback was submitted and updated

### 8.4 What Happens Next

#### After Submission
- **Confirmation**: You'll see a success message
- **Review**: Support team reviews your feedback
- **Priority Assignment**: Urgent issues get priority
- **Response**: You'll receive updates and responses
- **Resolution**: Issues are addressed and resolved

#### Response Time
- **Urgent Issues**: Addressed quickly
- **Bug Reports**: Reviewed and fixed promptly
- **Feature Requests**: Considered for future updates
- **Appreciation**: Always appreciated and acknowledged

### 8.5 Benefits

#### For You
✅ **Voice Heard**: Your opinions matter
✅ **Direct Communication**: Reach support team easily
✅ **Track Progress**: See status of your feedback
✅ **Improve System**: Help make the system better
✅ **Quick Resolution**: Issues addressed promptly

#### For Everyone
✅ **Better Features**: New features based on feedback
✅ **Fewer Bugs**: Issues reported and fixed
✅ **Improved Experience**: System gets better over time
✅ **User-Focused**: Built based on real user needs

---

## Final System Overview

This comprehensive pharmacy management system provides:

### Complete Management
1. **User Management** - Multi-admin organizations, staff, secure authentication
2. **Attendance Tracking** - Automatic WiFi-based check-in/out with geofencing
3. **Salary Management** - Payment processing, alerts, complete tracking
4. **Communication** - Real-time notifications and messaging
5. **Invoice Processing** - AI-powered PDF extraction and stock sync
6. **Inventory Control** - Complete stock management with audits
7. **Billing System** - Fast POS with split payments and analytics
8. **Feedback System** - Easy way to share thoughts and get support

### Key Advantages
✅ **Fully Integrated**: All modules work together seamlessly
✅ **AI-Powered**: Intelligent automation reduces manual work
✅ **Real-Time**: Instant updates across all features
✅ **User-Friendly**: Easy to learn and use
✅ **Secure**: Industry-standard security and privacy
✅ **Scalable**: Grows with your business
✅ **Mobile-Ready**: Access from anywhere
✅ **Support**: Feedback system for continuous improvement

---

## Technical Specifications

### Supported Platforms
- **Web Dashboard**: Complete management interface


### System Requirements
- **Internet Connection**: Required for OTP, data sync, and AI processing
- **GPS**: Required for location-based attendance
- **WiFi**: Required for automatic attendance tracking

### Data Storage
- **Database**: Secure cloud database with encryption
- **Backups**: Automatic daily backups
- **Retention**: Unlimited history storage for all modules
- **Timezone**: All times stored in UTC, displayed in local time
- **File Storage**: Secure cloud storage for invoice PDFs and documents

### Performance
- **Heartbeat Frequency**: 30-60 seconds
- **OTP Delivery**: Within 5 seconds
- **Real-Time Updates**: Sub-second latency
- **Concurrent Users**: Supports unlimited users

---

*This system provides a complete, automated solution for pharmacy management—from staff attendance and payroll to AI-powered invoice processing, inventory control, and sales—with minimal manual intervention while maintaining high security and accuracy standards.*
