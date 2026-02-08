# Daily Records API Documentation

Complete API reference for the Daily Records module with all endpoints, request/response examples, and business logic.

## Base URL
```
http://localhost:8000/api/daily-records
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Create a new daily record |
| GET | `/` | Get all records with filters |
| GET | `/{record_id}` | Get specific record by ID |
| GET | `/date/{record_date}` | Get record by date |
| PUT | `/{record_id}` | Update a record |
| DELETE | `/{record_id}` | Delete a record |
| GET | `/{record_id}/modifications` | Get modification history |
| POST | `/bulk` | Create multiple records |
| GET | `/analytics/monthly/{year}/{month}` | Monthly analytics |
| GET | `/analytics/variances` | Variance report |
| GET | `/analytics/dashboard` | Dashboard summary |
| POST | `/import/excel` | Import from Excel |
| GET | `/export/excel/{year}/{month}` | Export to Excel |

---

## 1. Create Daily Record

**Endpoint:** `POST /api/daily-records/`

**Description:** Create a new daily record with automatic field calculations.

**Request Body:**
```json
{
  "date": "2024-02-15",
  "day": "Thursday",
  "cash_balance": 1000,
  "no_of_bills": 25,
  "actual_cash": 5000,
  "online_sales": 2000,
  "unbilled_sales": 100,
  "software_figure": 6900,
  "cash_reserve": 200,
  "reserve_comments": "Small change for daily operations",
  "expense_amount": 150,
  "notes": "Normal business day",
  "created_by": "admin"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "date": "2024-02-15",
  "day": "Thursday",
  "cash_balance": 1000,
  "no_of_bills": 25,
  "actual_cash": 5000,
  "online_sales": 2000,
  "unbilled_sales": 100,
  "software_figure": 6900,
  "cash_reserve": 200,
  "expense_amount": 150,
  "notes": "Normal business day",
  "total_cash": 5350,
  "total_sales": 7000,
  "recorded_sales": 7000,
  "sales_difference": 0,
  "average_bill": 280,
  "created_at": "2024-02-15T10:30:00",
  "modified_at": "2024-02-15T10:30:00",
  "created_by": "admin"
}
```

**Automatic Calculations:**
- `total_cash` = actual_cash + cash_reserve + expense_amount
- `total_sales` = actual_cash + online_sales
- `recorded_sales` = unbilled_sales + software_figure
- `sales_difference` = total_sales - recorded_sales
- `average_bill` = recorded_sales / no_of_bills

**Error Responses:**
- `400 Bad Request` - Record already exists for this date
- `422 Unprocessable Entity` - Invalid data format

---

## 2. Get All Records

**Endpoint:** `GET /api/daily-records/`

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum records to return (default: 100)
- `start_date` (date, optional): Filter from this date
- `end_date` (date, optional): Filter until this date

**Example Request:**
```
GET /api/daily-records/?start_date=2024-02-01&end_date=2024-02-29&limit=50
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "date": "2024-02-15",
    "day": "Thursday",
    "total_sales": 7000,
    "sales_difference": 0,
    ...
  },
  {
    "id": 2,
    "date": "2024-02-14",
    "day": "Wednesday",
    "total_sales": 6500,
    "sales_difference": -50,
    ...
  }
]
```

---

## 3. Get Record by ID

**Endpoint:** `GET /api/daily-records/{record_id}`

**Example Request:**
```
GET /api/daily-records/1
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "date": "2024-02-15",
  "day": "Thursday",
  "cash_balance": 1000,
  "total_sales": 7000,
  "sales_difference": 0,
  ...
}
```

**Error Responses:**
- `404 Not Found` - Record does not exist

---

## 4. Get Record by Date

**Endpoint:** `GET /api/daily-records/date/{record_date}`

**Example Request:**
```
GET /api/daily-records/date/2024-02-15
```

**Response:** `200 OK` (same as Get by ID)

**Error Responses:**
- `404 Not Found` - No record found for this date

---

## 5. Update Record

**Endpoint:** `PUT /api/daily-records/{record_id}`

**Query Parameters:**
- `modified_by` (string, optional): User who made the modification

**Request Body:** (all fields optional)
```json
{
  "actual_cash": 5100,
  "notes": "Updated after recount",
  "cash_reserve": 250
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "date": "2024-02-15",
  "actual_cash": 5100,
  "cash_reserve": 250,
  "notes": "Updated after recount",
  "total_cash": 5500,
  "total_sales": 7100,
  "sales_difference": 100,
  "modified_at": "2024-02-15T15:45:00",
  ...
}
```

**Features:**
- Tracks all modifications in modification history
- Recalculates all derived fields automatically
- Triggers WhatsApp alert if variance exceeds threshold

**Error Responses:**
- `404 Not Found` - Record does not exist

---

## 6. Delete Record

**Endpoint:** `DELETE /api/daily-records/{record_id}`

**Response:** `200 OK`
```json
{
  "message": "Record deleted successfully",
  "id": 1
}
```

**Error Responses:**
- `404 Not Found` - Record does not exist

---

## 7. Get Modification History

**Endpoint:** `GET /api/daily-records/{record_id}/modifications`

**Description:** Get complete audit trail of all changes made to a record.

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "daily_record_id": 1,
    "field_name": "actual_cash",
    "old_value": "5000",
    "new_value": "5100",
    "modified_at": "2024-02-15T15:45:00",
    "modified_by": "admin"
  },
  {
    "id": 2,
    "daily_record_id": 1,
    "field_name": "notes",
    "old_value": "Normal business day",
    "new_value": "Updated after recount",
    "modified_at": "2024-02-15T15:45:00",
    "modified_by": "admin"
  }
]
```

---

## 8. Bulk Create Records

**Endpoint:** `POST /api/daily-records/bulk`

**Description:** Create multiple records in a single request.

**Request Body:**
```json
[
  {
    "date": "2024-02-15",
    "day": "Thursday",
    "cash_balance": 1000,
    "actual_cash": 5000,
    "online_sales": 2000,
    ...
  },
  {
    "date": "2024-02-16",
    "day": "Friday",
    "cash_balance": 1000,
    "actual_cash": 5500,
    "online_sales": 2200,
    ...
  }
]
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "date": "2024-02-15",
    ...
  },
  {
    "id": 2,
    "date": "2024-02-16",
    ...
  }
]
```

**Note:** Skips records that already exist for a given date.

---

## 9. Monthly Analytics

**Endpoint:** `GET /api/daily-records/analytics/monthly/{year}/{month}`

**Example Request:**
```
GET /api/daily-records/analytics/monthly/2024/2
```

**Response:** `200 OK`
```json
{
  "year": 2024,
  "month": 2,
  "total_days": 29,
  "total_sales": 203500.50,
  "total_cash": 145000.00,
  "total_online": 58500.50,
  "total_unbilled": 2900.00,
  "total_expenses": 4350.00,
  "total_cash_reserve": 5800.00,
  "average_bill_value": 285.50,
  "total_bills": 725,
  "cash_percentage": 71.25,
  "online_percentage": 28.75,
  "variance_days": 3,
  "variance_details": [
    {
      "date": "2024-02-15",
      "difference": 100.00
    },
    {
      "date": "2024-02-20",
      "difference": -75.50
    },
    {
      "date": "2024-02-25",
      "difference": 150.00
    }
  ]
}
```

**Error Responses:**
- `404 Not Found` - No records found for this month

---

## 10. Variance Report

**Endpoint:** `GET /api/daily-records/analytics/variances`

**Query Parameters:**
- `start_date` (date, optional): Filter from this date
- `end_date` (date, optional): Filter until this date
- `threshold` (float, optional): Minimum variance amount (default: 50.0)

**Example Request:**
```
GET /api/daily-records/analytics/variances?threshold=100&start_date=2024-02-01
```

**Response:** `200 OK`
```json
{
  "threshold": 100.0,
  "total_variances": 5,
  "variances": [
    {
      "id": 15,
      "date": "2024-02-25",
      "day": "Sunday",
      "total_sales": 8500.00,
      "recorded_sales": 8350.00,
      "difference": 150.00,
      "percentage": 1.80,
      "notes": "Extra cash found"
    },
    {
      "id": 10,
      "date": "2024-02-20",
      "day": "Tuesday",
      "total_sales": 7200.00,
      "recorded_sales": 7325.00,
      "difference": -125.00,
      "percentage": -1.71,
      "notes": "Cash shortage investigated"
    }
  ]
}
```

**Note:** Results sorted by absolute difference (highest first).

---

## 11. Dashboard Summary

**Endpoint:** `GET /api/daily-records/analytics/dashboard`

**Description:** Get quick summary of last 7 days for dashboard display.

**Response:** `200 OK`
```json
{
  "latest_record": {
    "date": "2024-02-15",
    "total_sales": 7000.00,
    "difference": 0.00
  },
  "last_7_days": {
    "total_sales": 49500.00,
    "average_daily_sales": 7071.43,
    "days_with_variance": 2,
    "total_records": 7
  },
  "recent_records": [
    {
      "date": "2024-02-15",
      "day": "Thursday",
      "total_sales": 7000.00,
      "difference": 0.00
    },
    {
      "date": "2024-02-14",
      "day": "Wednesday",
      "total_sales": 6500.00,
      "difference": -50.00
    }
  ]
}
```

---

## 12. Import from Excel

**Endpoint:** `POST /api/daily-records/import/excel`

**Description:** Import records from Excel file in GMTR0003 format.

**Request:** `multipart/form-data`
- `file`: Excel file (.xlsx or .xls)

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/api/daily-records/import/excel" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_business_record_GMTR0003.xlsx"
```

**Response:** `200 OK`
```json
{
  "success": true,
  "records_imported": 28,
  "errors": [],
  "message": "Successfully imported 28 records"
}
```

**Error Response:**
```json
{
  "success": false,
  "records_imported": 0,
  "errors": ["Invalid file format", "Row 10: Invalid date"],
  "message": "Failed to import Excel file"
}
```

**Notes:**
- Skips records that already exist
- Validates all data before import
- Calculates all derived fields automatically
- Supports GMTR0003 Excel format

---

## 13. Export to Excel

**Endpoint:** `GET /api/daily-records/export/excel/{year}/{month}`

**Description:** Export monthly records to Excel in GMTR0003 format.

**Example Request:**
```
GET /api/daily-records/export/excel/2024/2
```

**Response:** Excel file download
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Filename:** `daily_records_2024_2.xlsx`

**Example (cURL):**
```bash
curl -X GET "http://localhost:8000/api/daily-records/export/excel/2024/2" \
  -o daily_records_feb_2024.xlsx
```

**Error Responses:**
- `404 Not Found` - No records found for this month

---

## Business Logic & Calculations

### Automatic Field Calculations

All calculated fields are automatically computed on create and update:

```
Total Cash = Actual Cash + Cash Reserve + Expense Amount
Total Sales = Actual Cash + Online Sales
Recorded Sales = Unbilled Sales + Software Figure
Sales Difference = Total Sales - Recorded Sales
Average Bill = Recorded Sales / Number of Bills
```

### Cash Variance Alerts

When `sales_difference` exceeds the configured threshold (default: ₹100):
- WhatsApp alert is sent automatically
- Alert includes date, difference amount, and total sales
- Configurable in settings: `CASH_DIFFERENCE_THRESHOLD`

### Modification Tracking

Every field update is tracked:
- Old value and new value stored
- Timestamp of modification
- User who made the change
- Complete audit trail maintained

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (duplicate record, invalid data) |
| 404 | Not Found (record doesn't exist) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

---

## Data Validation Rules

1. **Date**: Must be unique, cannot have duplicate records for same date
2. **Cash Balance**: Must be positive number
3. **No. of Bills**: Must be positive integer or null
4. **All Amount Fields**: Must be numeric (can be null)
5. **Day**: String (Monday-Sunday)
6. **Notes/Comments**: Text fields (optional)

---

## Best Practices

1. **Daily Entry**: Create records at end of each business day
2. **Immediate Updates**: Update records immediately when discrepancies found
3. **Use Modification Tracking**: Always provide `modified_by` parameter
4. **Monitor Variances**: Check variance report regularly
5. **Monthly Export**: Export data monthly for backup
6. **Bulk Import**: Use Excel import for historical data migration

---

## Integration Examples

### Python Client
```python
import requests

# Create record
response = requests.post(
    "http://localhost:8000/api/daily-records/",
    json={
        "date": "2024-02-15",
        "day": "Thursday",
        "cash_balance": 1000,
        "actual_cash": 5000,
        "online_sales": 2000,
        "unbilled_sales": 100,
        "software_figure": 6900,
        "no_of_bills": 25
    }
)
print(response.json())

# Get monthly analytics
response = requests.get(
    "http://localhost:8000/api/daily-records/analytics/monthly/2024/2"
)
print(response.json())
```

### JavaScript/Fetch
```javascript
// Create record
const createRecord = async () => {
  const response = await fetch('http://localhost:8000/api/daily-records/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      date: '2024-02-15',
      day: 'Thursday',
      cash_balance: 1000,
      actual_cash: 5000,
      online_sales: 2000,
      unbilled_sales: 100,
      software_figure: 6900,
      no_of_bills: 25
    })
  });
  return await response.json();
};

// Update record
const updateRecord = async (id) => {
  const response = await fetch(
    `http://localhost:8000/api/daily-records/${id}?modified_by=admin`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actual_cash: 5100,
        notes: 'Updated after recount'
      })
    }
  );
  return await response.json();
};
```

---

## Testing

Access interactive API documentation at:
```
http://localhost:8000/docs
```

All endpoints can be tested directly from the Swagger UI.

---

## Support

For issues or questions:
- Check modification history for audit trail
- Review variance reports for discrepancies
- Monitor WhatsApp alerts for real-time notifications
- Export data regularly for backup and analysis
