# GMTR0003 Excel Format Documentation

## Overview
The **GMTR0003 business record** is an employee update sheet used to track daily pharmacy business operations. This document details the exact Excel structure, formulas, and data mapping used by the system.

---

## File Structure

### Sheet Name
- **Sheet1** (default)

### Document Header
- **Row 1**: Color-coded fill cells (E1, G1, H1, J1, K1, N1)
- **Row 2**: Title spanning A2:Q2
  - `GMTR0003 business record - employee update sheet`

---

## Column Layout

### Row 3-5: Header Section (Merged Cells)

| Column | Header | Sub-header | Description |
|--------|--------|------------|-------------|
| **A** | Date | - | Transaction date (YYYY-MM-DD) |
| **B** | Day | - | Day of week (Monday-Sunday) |
| **C** | Cash balance | - | Opening cash balance for the day |
| **D** | Average bill | - | Calculated: Total sales ÷ No. of bills |
| **E** | No. of bills | - | Total number of bills issued |
| **F** | Cash | Total Cash | Sum of Actual Cash + Cash Reserve + Column Q |
| **G** | ↳ | Actual Cash | Bills deposited in bank (₹500, ₹200, ₹100 denominations) |
| **H** | Online | - | Online payment sales |
| **I** | Total sales | - | Actual Cash + Online sales |
| **J** | Sales | Unbilled | Items sold without billing (due to stock errors) |
| **K** | ↳ | Software fig. | Total sales value recorded in software |
| **L** | ↳ | Recorded sales | Software sales + Unbilled amount |
| **M** | Difference | - | Total sales - Recorded sales |
| **N** | Cash Reserve | - | Reserved cash amount |
| **O** | Reserve balance | - | Running balance of cash reserves |
| **P** | Expense record | Comments | Text notes for expenses (e.g., "Check settlement", "UNCLE") |
| **Q** | ↳ | Amount | Expense amount in rupees |

---

## Excel Formulas

### Row 6 onwards (Data Rows)

| Column | Formula | Description |
|--------|---------|-------------|
| **D** | `=L6/E6` | Average bill = Recorded sales ÷ No. of bills |
| **F** | `=SUM(G6+N6+Q6)` | Total Cash = Actual Cash + Cash Reserve + Q column |
| **I** | `=H6+F6` | Total sales = Online + Total Cash |
| **L** | `=J6+K6` | Recorded sales = Unbilled + Software figure |
| **M** | `=I6-L6` | Difference = Total sales - Recorded sales |

**Formula Pattern**: Replace `6` with the respective row number (7, 8, 9, etc.)

---

## Data Entry Columns (User Input Required)

Employees must manually enter data in these columns:

1. **A - Date**: Auto-filled with sequential dates
2. **B - Day**: Auto-filled based on date
3. **C - Cash balance**: Opening balance (typically ₹1000)
4. **E - No. of bills**: Count of bills issued
5. **G - Actual Cash**: Cash deposited to bank
6. **H - Online**: Online payment amount
7. **J - Unbilled**: Sales without bills
8. **K - Software fig.**: Software-recorded sales
9. **N - Cash Reserve**: Reserved cash amount
10. **O - Reserve balance**: Running reserve balance
11. **P - Expense Comments**: Optional text notes
12. **Q - Expense Amount**: Expense value

**Calculated Columns** (D, F, I, L, M): Auto-calculated via formulas

---

## Sample Data (Row 6-7)

### Row 6 (2026-02-02, Monday)
```
Date: 2026-02-02
Day: Monday
Cash balance: ₹1000
No. of bills: 5
Actual Cash: ₹150
Online: ₹30
Unbilled: ₹50
Software fig.: ₹150
Cash Reserve: ₹15

CALCULATED:
Average bill: ₹40 (200÷5)
Total Cash: ₹165 (150+15+0)
Total sales: ₹195 (30+165)
Recorded sales: ₹200 (50+150)
Difference: -₹5 (195-200)
```

### Row 7 (2026-02-03, Tuesday)
```
Date: 2026-02-03
Day: Tuesday
Cash balance: ₹1000
No. of bills: 7
Actual Cash: ₹150
Online: ₹263
Unbilled: ₹31
Software fig.: ₹386
Cash Reserve: ₹3

CALCULATED:
Average bill: ₹59.57 (417÷7)
Total Cash: ₹153 (150+3+0)
Total sales: ₹416 (263+153)
Recorded sales: ₹417 (31+386)
Difference: -₹1 (416-417)
```

---

## Legend Section (Rows 40-50)

Located at the bottom of the sheet for reference:

| Term | Formula/Definition |
|------|-------------------|
| **Average bill** | Total sales / No. of bills |
| **No of bills** | No. of bills sold |
| **Total Cash** | Amount equal to difference of recorded sales and online amount |
| **Actual Cash** | Bills of denomination ₹500, ₹200, ₹100 deposited in bank |
| **Online** | Actual cash from recorded sales |
| **Total sales** | Actual cash and online sales |
| **Unbilled** | Items sold without billing due to stock errors |
| **Software fig** | Total sales value on software |
| **Recorded sales** | Software sales and unbilled amount |

---

## API Mapping

### Database Field → Excel Column

| Database Field | Excel Column | Type | Formula |
|---------------|--------------|------|---------|
| `date` | A | Date | Input |
| `cash_balance` | C | Decimal | Input |
| `no_of_bills` | E | Integer | Input |
| `actual_cash` | G | Decimal | Input |
| `online_sales` | H | Decimal | Input |
| `unbilled_sales` | J | Decimal | Input |
| `software_sales` | K | Decimal | Input |
| `cash_reserve` | N | Decimal | Input |
| `total_cash` | F | Decimal | `=G+N+Q` |
| `total_sales` | I | Decimal | `=H+F` |
| `recorded_sales` | L | Decimal | `=J+K` |
| `sales_difference` | M | Decimal | `=I-L` |
| `average_bill` | D | Decimal | `=L/E` |
| `reserve_balance` | O | Decimal | Input |
| `expense_comments` | P | String | Input (Optional) |
| `expense_amount` | Q | Decimal | Input (Optional) |

---

## Import/Export Behavior

### Import from Excel (`POST /api/daily-records/import/excel`)
- Reads columns A-Q starting from Row 6
- Validates date format and numeric fields
- Auto-calculates formula fields if missing
- Skips empty rows
- Returns count of imported records

### Export to Excel (`GET /api/daily-records/export/excel/{year}/{month}`)
- Generates GMTR0003 format with headers
- Populates Rows 6+ with database records
- Includes Excel formulas in calculated columns
- Applies merged cell formatting
- Returns `.xlsx` file download

---

## Validation Rules

1. **Date**: Must be valid date, sequential preferred
2. **Cash balance**: Positive decimal, typically ₹1000
3. **No. of bills**: Positive integer, required for average calculation
4. **Actual Cash**: Non-negative decimal
5. **Online**: Non-negative decimal
6. **Unbilled**: Non-negative decimal
7. **Software fig.**: Non-negative decimal
8. **Cash Reserve**: Non-negative decimal
9. **Difference**: Alert if exceeds threshold (e.g., ±₹100)
10. **Reserve balance**: Non-negative decimal
11. **Expense Comments**: Optional text (max 255 chars)
12. **Expense Amount**: Non-negative decimal, optional

---

## Business Logic

### Cash Difference Alert
- **Trigger**: When `|sales_difference| > CASH_DIFFERENCE_LIMIT`
- **Action**: Send WhatsApp notification to management
- **Purpose**: Detect cash handling discrepancies

### Average Bill Calculation
- **Formula**: `recorded_sales / no_of_bills`
- **Use Case**: Track transaction size trends
- **Alert**: Unusually high/low averages may indicate data entry errors

### Total Cash Reconciliation
- **Expected**: `total_cash = actual_cash + cash_reserve + column_q`
- **Verification**: Should match physical cash count
- **Discrepancy**: Investigate if formula doesn't balance

---

## Color Coding (Row 1)

The Excel file uses color fills in Row 1 for visual organization:
- **E1**: Marks "No. of bills" section
- **G1**: Marks "Actual Cash" section
- **H1**: Marks "Online" section
- **J1**: Marks "Unbilled" section
- **K1**: Marks "Software fig." section
- **N1**: Marks "Cash Reserve" section

---

## Merged Cell Ranges

The template uses extensive cell merging for headers:
- **A2:Q2**: Title row
- **A3:A5, B3:B5, C3:C5**: Single column headers
- **F3:G3**: "Cash" header spans Total Cash + Actual Cash
- **H3:H5**: "Online" header
- **J3:L3**: "Sales" header spans Unbilled + Software + Recorded
- **M3:M5**: "Difference" header
- **N3:N5**: "Cash Reserve" header

---

## Usage Notes

1. **Daily Entry**: Employees fill one row per day starting from Row 6
2. **Month Boundary**: Continue to next month (e.g., Row 33 shows 2026-03-01)
3. **Formula Protection**: Lock formula cells to prevent accidental edits
4. **Backup**: Export to database daily via API import endpoint
5. **Audit Trail**: System tracks all modifications with timestamps

---

## Related Files

- **models.py**: DailyRecord SQLAlchemy model
- **schemas.py**: Pydantic validation schemas
- **service.py**: Excel import/export logic
- **routes.py**: API endpoints for Excel operations
- **DAILY_RECORDS_README.md**: Complete module documentation

---

## API Endpoints for Excel

```python
# Import Excel file
POST /api/daily-records/import/excel
Content-Type: multipart/form-data
Body: file=<GMTR0003.xlsx>

# Export to Excel
GET /api/daily-records/export/excel/{year}/{month}
Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

---

## Troubleshooting

### Common Import Errors

1. **"Invalid date format"**: Ensure Column A has YYYY-MM-DD dates
2. **"Missing required field"**: Check E, G, H, J, K, N columns have values
3. **"Formula mismatch"**: System recalculates D, F, I, L, M automatically
4. **"Duplicate date"**: Each date can only appear once per import

### Export Issues

1. **Empty file**: No records found for specified year/month
2. **Formula errors**: Check database has valid numeric values
3. **Encoding issues**: Excel file uses UTF-8 encoding

---

**Last Updated**: Based on `sample business record GMTR0003.xlsx`  
**Format Version**: GMTR0003  
**Compatible With**: Excel 2016+, LibreOffice Calc, Google Sheets
