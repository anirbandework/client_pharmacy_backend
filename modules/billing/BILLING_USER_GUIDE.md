# Billing System User Guide

## Overview
The Billing System is a comprehensive point-of-sale solution designed for pharmacies and medical stores. It integrates with the Stock Audit system to provide real-time inventory management, customer tracking, and detailed financial reporting.

## Key Features
- **Real-time Stock Integration**: Automatically updates inventory when bills are created
- **Multi-payment Support**: Cash, Card, and Online payments in a single transaction
- **Customer Tracking**: Track customer categories and purchase history
- **Daily Records Management**: Comprehensive daily sales and expense tracking
- **Tax Compliance**: GST calculation with SGST/CGST breakdown
- **Analytics & Reports**: Detailed insights and Excel exports
- **Bill Configuration**: Customizable store details and bill format

---

## 1. Creating Bills

### Medicine Search
- **Search by**: Product name, batch number, or manufacturer
- **Real-time Results**: Shows available stock, location (rack/section), and pricing
- **Stock Validation**: Only shows items with available quantity

### Customer Information (Optional)
- **Basic Details**: Name, phone, email, doctor name
- **Customer Categories**:
  - First Time with Prescription
  - Regular (Branded Medicines)
  - Generic Informed
  - From Contact Sheet
- **Contact Tracking**: Mark if customer was contacted before

### Adding Items to Bill
1. Search for medicine using the search bar
2. Click on desired item from search results
3. Adjust quantity (cannot exceed available stock)
4. Modify unit price if needed
5. Remove items using trash icon

### Payment Processing
- **Split Payments**: Combine cash, card, and online payments
- **Payment Reference**: Add transaction ID for card/online payments
- **Change Calculation**: Automatic change calculation for overpayments
- **Validation**: Ensures total payment covers bill amount

### Tax & Discounts
- **Tax Rate**: Configurable GST percentage (default 5%)
- **Bill-level Discount**: Percentage-based discount on subtotal
- **GST Breakdown**: Automatic SGST/CGST split (equal distribution)

---

## 2. Bill Management

### Viewing Bills
- **Bill History**: View all bills with search and filter options
- **Search by Phone**: Find customer's previous purchases
- **Bill Details**: Complete bill information with item breakdown
- **Print Function**: Professional tax invoice format

### Bill Information Includes
- **Bill Number**: Auto-generated unique identifier
- **Customer Details**: Name, phone, doctor information
- **Item Details**: Product name, batch, quantity, pricing, tax breakdown
- **Payment Details**: Cash/card/online amounts, change returned
- **Location Info**: Rack and section for each item
- **Staff Information**: Who created the bill

### Bill Deletion (Manager Only)
- **Stock Restoration**: Automatically restores inventory quantities
- **Audit Trail**: Updates stock discrepancy calculations
- **Permission Required**: Only staff with management privileges

---

## 3. Daily Records Management

### Automatic Calculations
- **Sales Figures**: Auto-calculated from bills created
- **Bill Count**: Number of transactions per day
- **Payment Breakdown**: Cash vs online sales separation
- **Average Bill Value**: Total sales divided by bill count

### Manual Entries
- **Unbilled Amount**: Cash sales without formal billing
- **Cash Management**:
  - **Depositable Amount**: ₹500, ₹200, ₹100 notes for bank deposit
  - **Cash Reserve**: ₹10, ₹20, ₹50 notes and coins for daily operations
- **Notes**: Additional information about unbilled sales

### Expense Tracking
- **Categories**: Rent, utilities, salary, supplies, etc.
- **Amount & Description**: Detailed expense information
- **Staff Attribution**: Tracks who added each expense
- **Real-time Totals**: Automatic expense sum calculation

### Key Metrics
- **Total Sales**: Software sales + unbilled amount
- **Recorded Sales**: All documented revenue
- **Difference**: Variance between expected and actual figures
- **Reserve Balance**: Available cash for operations

---

## 4. Analytics & Reports

### Dashboard Overview
- **Total Bills**: Count of transactions
- **Total Revenue**: Sum of all sales
- **Payment Method Breakdown**: Cash vs card vs online
- **Average Bill Value**: Revenue per transaction

### Advanced Analytics
- **Period Comparison**: Current vs previous period analysis
- **Daily Trends**: Sales patterns over time
- **Day-wise Analysis**: Performance by day of week
- **Expense Breakdown**: Category-wise expense analysis
- **Sales Predictions**: Trend-based forecasting

### Top Selling Items
- **Quantity Sold**: Most popular products by volume
- **Revenue Generated**: Highest earning products
- **Transaction Count**: Frequency of sales

### Customer Analytics
- **Purchase History**: Individual customer transaction records
- **Total Spent**: Customer lifetime value
- **Visit Frequency**: Customer engagement metrics

---

## 5. Configuration Management

### Store Information
- **Basic Details**: Store name, address, contact information
- **Legal Information**: 
  - D.L Numbers (Drug License 20 & 21)
  - F.L Number (Food License)
  - GST IN (GST Identification Number)
- **Logo**: Store logo for bill printing

### Bill Format Settings
- **Header Information**: Store details and legal numbers
- **Tax Invoice Format**: Professional layout with all required fields
- **Footer Details**: GST information and totals
- **Print Optimization**: Formatted for standard receipt printers

---

## 6. Integration Features

### Stock Audit Integration
- **Real-time Updates**: Stock quantities updated immediately upon billing
- **Location Tracking**: Items show rack and section information
- **Discrepancy Calculation**: Automatic physical vs software stock variance
- **Availability Check**: Prevents overselling with stock validation

### Customer Tracking Integration
- **Customer Database**: Automatic customer record creation
- **Contact Conversion**: Track success of marketing outreach
- **Category Management**: Segment customers by behavior
- **Purchase History**: Complete transaction timeline

---

## 7. Export & Reporting

### Excel Exports
- **Bills Export**: Complete transaction data with filters
- **Daily Records Export**: Comprehensive daily performance data
- **Date Range Selection**: Flexible reporting periods
- **Multiple Sheets**: Separate tabs for different data types

### Report Contents
- **Bill Reports**: Transaction details, customer info, payment methods
- **Daily Reports**: Sales figures, expenses, cash management
- **Expense Reports**: Category-wise expense breakdown with staff attribution

---

## 8. User Permissions

### Staff Roles
- **Regular Staff**: Create bills, view records, add expenses
- **Managers**: All staff permissions plus bill deletion, configuration access
- **Admin**: Full system access including analytics and configuration

### Security Features
- **Geofence Validation**: Location-based access control
- **Rate Limiting**: Protection against system abuse
- **Audit Trail**: Complete activity logging

---

## 9. Best Practices

### Daily Operations
1. **Start of Day**: Review previous day's records and cash position
2. **During Sales**: Use proper customer categorization for tracking
3. **End of Day**: Complete daily record with actual cash counts
4. **Regular Exports**: Download reports for backup and analysis

### Inventory Management
- **Stock Monitoring**: Regular checks on low-stock items
- **Location Updates**: Ensure rack/section information is current
- **Batch Tracking**: Monitor expiry dates through batch numbers

### Customer Service
- **Information Capture**: Collect customer details for follow-up
- **Payment Flexibility**: Offer multiple payment options
- **Receipt Printing**: Always provide printed receipts

### Financial Management
- **Daily Reconciliation**: Match cash counts with system records
- **Expense Documentation**: Record all business expenses promptly
- **Regular Analysis**: Review analytics for business insights

---

## 10. Troubleshooting

### Common Issues
- **Stock Unavailable**: Check stock audit system for inventory updates
- **Payment Errors**: Verify total payment covers bill amount
- **Print Issues**: Ensure printer is connected and has paper
- **Search Problems**: Try different search terms or check spelling

### Error Messages
- **"Insufficient Stock"**: Item quantity exceeds available inventory
- **"Insufficient Payment"**: Total paid is less than bill amount
- **"Permission Denied"**: User lacks required access level
- **"Bill Not Found"**: Invalid bill number or access restriction

### Support Actions
- **Refresh Data**: Reload page to get latest information
- **Check Permissions**: Verify user role and access rights
- **Contact Admin**: For configuration or system issues
- **Export Backup**: Regular data exports for safety

---

## Technical Notes

### System Requirements
- **Internet Connection**: Required for real-time synchronization
- **Modern Browser**: Chrome, Firefox, Safari, or Edge
- **Printer Support**: For receipt printing functionality
- **Mobile Responsive**: Works on tablets and mobile devices

### Data Backup
- **Automatic Sync**: Real-time data synchronization
- **Export Options**: Manual Excel exports for backup
- **Audit Trail**: Complete transaction history preservation

### Performance
- **Caching**: Optimized for fast response times
- **Rate Limiting**: Prevents system overload
- **Offline Resilience**: Handles temporary connection issues

---

*This guide covers the complete billing system functionality. For additional support or feature requests, contact your system administrator.*