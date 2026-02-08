# Daily Business Records - GMTR0003 Format

## Overview

This document describes the daily business record tracking system used for pharmacy operations. The Excel template (GMTR0003) provides a comprehensive monthly view of daily sales, cash management, and expense tracking with automated calculations and variance detection.

## Sheet Structure

### Main Sheet: Employee Update Sheet

A monthly calendar-based tracking sheet (31+ days) with the following columns:

## Column Definitions

### A-B: Date Information
- **Date**: Daily date entry (YYYY-MM-DD format)
- **Day**: Day of the week (Monday-Sunday)

### C: Cash Management
- **Cash Balance**: Starting cash balance for the day (typically fixed, e.g., 1000)

### D-E: Bill Metrics
- **Average Bill**: Calculated as `Total Sales / No. of Bills`
- **No. of Bills**: Count of bills sold during the day

### F-G: Cash Tracking
- **Total Cash**: Sum of `Actual Cash + Cash Reserve + Expense Amount`
  - Formula: `=SUM(G + N + Q)`
- **Actual Cash**: Physical cash deposited in bank (bills of 500, 200, 100 denominations)

### H: Online Payments
- **Online**: Digital payment transactions (UPI, cards, etc.)

### I: Sales Total
- **Total Sales**: Combined cash and online sales
  - Formula: `=Actual Cash + Online`

### J-L: Sales Reconciliation
- **Unbilled**: Items sold without billing due to stock errors or other reasons
- **Software Fig.**: Total sales value recorded in pharmacy software
- **Recorded Sales**: Sum of software sales and unbilled amount
  - Formula: `=Unbilled + Software Fig.`

### M: Variance Detection
- **Difference**: Cash variance between total sales and recorded sales
  - Formula: `=Total Sales - Recorded Sales`
  - Used to identify discrepancies and cash handling issues

### N-O: Cash Reserve Management
- **Cash Reserve**: Small denomination notes (10, 20, 50 rupees) and coins kept for daily change
- **Reserve Balance**: Aggregate sum of all daily cash reserves
  - Formula: `=SUM(N6:N36)` (monthly total)

### P: Comments
- **Comments**: Notes about specific transactions or events (e.g., "5 candles", "1 pen")

### Q: Expenses
- **Expense Record**: Daily operational expenses
- **Amount**: Expense amount in rupees

## Sample Data

### Example Entry (Feb 2, 2026):
```
Date: 2026-02-02 (Monday)
Cash Balance: 1000
No. of Bills: 5
Actual Cash: 150
Online: 30
Unbilled: 50
Software Fig.: 150
Cash Reserve: 15
Comments: "5 candles"
Expense: 5

Calculated Values:
- Total Cash: 170 (150 + 15 + 5)
- Total Sales: 180 (150 + 30)
- Recorded Sales: 200 (50 + 150)
- Difference: -20 (180 - 200)
- Average Bill: 40 (200 / 5)
```

## Key Features

### 1. Automated Calculations
- Average bill value per transaction
- Total cash reconciliation
- Sales variance detection
- Monthly cash reserve aggregation

### 2. Cash Variance Tracking
The **Difference** column automatically flags discrepancies between:
- Physical cash collected (Total Sales)
- System-recorded sales (Recorded Sales)

Positive difference = Excess cash
Negative difference = Cash shortage

### 3. Multi-Payment Support
- Cash transactions
- Online/digital payments
- Unbilled sales tracking

### 4. Expense Integration
- Daily expense recording
- Integrated into cash flow calculations
- Comments field for expense details

### 5. Cash Reserve Management
- Tracks small denomination currency
- Monthly aggregation for reserve planning
- Ensures adequate change availability

## Business Logic

### Cash Flow Formula
```
Total Cash = Actual Cash + Cash Reserve + Expenses
Total Sales = Actual Cash + Online
Recorded Sales = Unbilled + Software Fig.
Difference = Total Sales - Recorded Sales
```

### Reconciliation Process
1. Count physical cash (Actual Cash)
2. Record online payments
3. Check software sales figure
4. Add unbilled items
5. Calculate difference
6. Investigate variances
7. Document in comments

## Use Cases

### Daily Operations
- Record all sales transactions
- Track cash vs. digital payments
- Monitor unbilled items
- Log daily expenses
- Maintain change reserve

### Monthly Analysis
- Identify cash handling patterns
- Detect recurring discrepancies
- Analyze average bill values
- Review expense trends
- Audit cash reserve requirements

### Compliance & Auditing
- Complete transaction trail
- Variance documentation
- Modification tracking (via backend system)
- Historical record maintenance

## Integration with Backend System

The backend API (`/api/daily-records/`) supports:

### Create Record
```json
POST /api/daily-records/
{
  "date": "2026-02-02",
  "day": "Monday",
  "cash_balance": 1000,
  "no_of_bills": 5,
  "actual_cash": 150,
  "online": 30,
  "unbilled": 50,
  "software_fig": 150,
  "cash_reserve": 15,
  "comments": "5 candles",
  "expense_amount": 5
}
```

### Update Record (with modification tracking)
```json
PUT /api/daily-records/{id}
{
  "actual_cash": 160,
  "comments": "Updated after recount"
}
```

### View Modifications
```json
GET /api/daily-records/{id}/modifications
```

## Legend Summary

| Field | Description |
|-------|-------------|
| Average Bill | Total sales / No. of bills |
| No. of Bills | Number of bills sold |
| Total Cash | Amount equal to difference of recorded sales and online amount |
| Actual Cash | Bills of denominations 500, 200, 100 deposited in bank |
| Online | Actual cash from recorded sales |
| Total Sales | Actual cash and online sales |
| Unbilled | Items sold without billing due to stock errors |
| Software Fig. | Total sales value on software |
| Recorded Sales | Software sales and unbilled amount |
| Difference | Recorded sales from total sales - needed to check cash variance |
| Cash Reserve | 10-20-50 rupees notes and coins for daily change |
| Reserve Balance | Aggregate amount of cash reserve |
| Expense Record | Daily expense records |

## Best Practices

1. **Daily Entry**: Update records at end of each business day
2. **Immediate Reconciliation**: Investigate differences > ±50 rupees immediately
3. **Comment Documentation**: Always document unusual transactions
4. **Cash Reserve**: Maintain minimum 200-300 rupees in small denominations
5. **Backup**: Keep digital and physical copies of monthly records
6. **Audit Trail**: Use backend modification tracking for all changes
7. **Monthly Review**: Analyze trends and patterns at month-end

## Alerts & Notifications

The backend system triggers WhatsApp notifications when:
- Cash difference exceeds threshold (configurable)
- Multiple consecutive days show variances
- Unbilled items exceed normal range

## File Location

Template: `/modules/daily_records/sample business record GMTR0003.xlsx`

## Related Documentation

- Main README: `/README.md`
- API Documentation: `http://localhost:8000/docs`
- Daily Records API: `/api/daily-records/`
