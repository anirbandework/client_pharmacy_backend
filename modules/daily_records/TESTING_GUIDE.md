# Daily Records Module - Complete Testing Guide

## Quick Start

### 1. Start the Server
```bash
cd /Users/anirbande/Desktop/client\ backend
source venv/bin/activate
./start.sh
```

Or manually:
```bash
uvicorn main:app --reload
```

### 2. Access API Documentation
Open browser: `http://localhost:8000/docs`

---

## Testing Scenarios

### Scenario 1: Create Daily Record

**Request:**
```bash
curl -X POST "http://localhost:8000/api/daily-records/" \
  -H "Content-Type: application/json" \
  -d '{
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
    "created_by": "admin"
  }'
```

**Expected Result:**
- Status: 200 OK
- Returns record with calculated fields:
  - `total_cash`: 5350
  - `total_sales`: 7000
  - `recorded_sales`: 7000
  - `sales_difference`: 0
  - `average_bill`: 280

---

### Scenario 2: Update Record with Variance

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/daily-records/1?modified_by=admin" \
  -H "Content-Type: application/json" \
  -d '{
    "actual_cash": 5200,
    "notes": "Found extra cash in drawer"
  }'
```

**Expected Result:**
- Status: 200 OK
- Recalculated fields updated
- Modification tracked in history
- WhatsApp alert sent if difference > threshold

---

### Scenario 3: Get Monthly Analytics

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/analytics/monthly/2024/2"
```

**Expected Result:**
```json
{
  "year": 2024,
  "month": 2,
  "total_days": 29,
  "total_sales": 203500.50,
  "total_cash": 145000.00,
  "total_online": 58500.50,
  "average_bill_value": 285.50,
  "cash_percentage": 71.25,
  "online_percentage": 28.75,
  "variance_days": 3
}
```

---

### Scenario 4: Import Excel File

**Request:**
```bash
curl -X POST "http://localhost:8000/api/daily-records/import/excel" \
  -F "file=@modules/daily_records/sample business record GMTR0003.xlsx"
```

**Expected Result:**
- Status: 200 OK
- Records imported count
- List of any errors
- Skips duplicate dates

---

### Scenario 5: Export to Excel

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/export/excel/2024/2" \
  -o february_2024.xlsx
```

**Expected Result:**
- Excel file downloaded
- GMTR0003 format maintained
- All records for February 2024

---

### Scenario 6: Get Variance Report

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/analytics/variances?threshold=100&start_date=2024-02-01"
```

**Expected Result:**
- List of days with variance > ₹100
- Sorted by absolute difference
- Includes percentage variance

---

### Scenario 7: View Modification History

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/1/modifications"
```

**Expected Result:**
```json
[
  {
    "id": 1,
    "field_name": "actual_cash",
    "old_value": "5000",
    "new_value": "5200",
    "modified_at": "2024-02-15T15:45:00",
    "modified_by": "admin"
  }
]
```

---

### Scenario 8: Dashboard Summary

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/analytics/dashboard"
```

**Expected Result:**
- Latest record details
- Last 7 days summary
- Recent 5 records
- Variance count

---

### Scenario 9: Bulk Create Records

**Request:**
```bash
curl -X POST "http://localhost:8000/api/daily-records/bulk" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "date": "2024-02-16",
      "day": "Friday",
      "cash_balance": 1000,
      "actual_cash": 5500,
      "online_sales": 2200,
      "unbilled_sales": 120,
      "software_figure": 7580,
      "no_of_bills": 28
    },
    {
      "date": "2024-02-17",
      "day": "Saturday",
      "cash_balance": 1000,
      "actual_cash": 6000,
      "online_sales": 2500,
      "unbilled_sales": 150,
      "software_figure": 8350,
      "no_of_bills": 32
    }
  ]'
```

**Expected Result:**
- Multiple records created
- All calculations performed
- Skips existing dates

---

### Scenario 10: Get Record by Date

**Request:**
```bash
curl -X GET "http://localhost:8000/api/daily-records/date/2024-02-15"
```

**Expected Result:**
- Single record for that date
- 404 if date not found

---

## Python Testing Script

Create `test_daily_records.py`:

```python
import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000/api/daily-records"

def test_create_record():
    """Test creating a daily record"""
    data = {
        "date": str(date.today()),
        "day": "Thursday",
        "cash_balance": 1000,
        "no_of_bills": 25,
        "actual_cash": 5000,
        "online_sales": 2000,
        "unbilled_sales": 100,
        "software_figure": 6900,
        "cash_reserve": 200,
        "expense_amount": 150,
        "notes": "Test record",
        "created_by": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/", json=data)
    print(f"Create Record: {response.status_code}")
    print(response.json())
    return response.json()["id"]

def test_get_record(record_id):
    """Test getting a record"""
    response = requests.get(f"{BASE_URL}/{record_id}")
    print(f"\nGet Record: {response.status_code}")
    print(response.json())

def test_update_record(record_id):
    """Test updating a record"""
    data = {
        "actual_cash": 5200,
        "notes": "Updated in test"
    }
    
    response = requests.put(
        f"{BASE_URL}/{record_id}?modified_by=test_user",
        json=data
    )
    print(f"\nUpdate Record: {response.status_code}")
    print(response.json())

def test_get_modifications(record_id):
    """Test getting modification history"""
    response = requests.get(f"{BASE_URL}/{record_id}/modifications")
    print(f"\nModifications: {response.status_code}")
    print(response.json())

def test_monthly_analytics():
    """Test monthly analytics"""
    today = date.today()
    response = requests.get(
        f"{BASE_URL}/analytics/monthly/{today.year}/{today.month}"
    )
    print(f"\nMonthly Analytics: {response.status_code}")
    print(response.json())

def test_dashboard():
    """Test dashboard summary"""
    response = requests.get(f"{BASE_URL}/analytics/dashboard")
    print(f"\nDashboard: {response.status_code}")
    print(response.json())

def test_variance_report():
    """Test variance report"""
    response = requests.get(
        f"{BASE_URL}/analytics/variances?threshold=50"
    )
    print(f"\nVariance Report: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    print("=== Testing Daily Records API ===\n")
    
    # Run tests
    record_id = test_create_record()
    test_get_record(record_id)
    test_update_record(record_id)
    test_get_modifications(record_id)
    test_monthly_analytics()
    test_dashboard()
    test_variance_report()
    
    print("\n=== All Tests Complete ===")
```

Run tests:
```bash
python test_daily_records.py
```

---

## Frontend Integration Examples

### React Component Example

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const DailyRecordsManager = () => {
  const [records, setRecords] = useState([]);
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    day: '',
    cash_balance: 1000,
    actual_cash: 0,
    online_sales: 0,
    unbilled_sales: 0,
    software_figure: 0,
    no_of_bills: 0,
    cash_reserve: 0,
    expense_amount: 0,
    notes: ''
  });

  const API_URL = 'http://localhost:8000/api/daily-records';

  // Fetch records
  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      const response = await axios.get(`${API_URL}/`);
      setRecords(response.data);
    } catch (error) {
      console.error('Error fetching records:', error);
    }
  };

  // Create record
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/`, formData);
      alert('Record created successfully!');
      fetchRecords();
    } catch (error) {
      alert('Error creating record: ' + error.response?.data?.detail);
    }
  };

  // Get monthly analytics
  const getMonthlyAnalytics = async () => {
    const today = new Date();
    try {
      const response = await axios.get(
        `${API_URL}/analytics/monthly/${today.getFullYear()}/${today.getMonth() + 1}`
      );
      console.log('Monthly Analytics:', response.data);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div>
      <h1>Daily Records Manager</h1>
      
      <form onSubmit={handleSubmit}>
        <input
          type="date"
          value={formData.date}
          onChange={(e) => setFormData({...formData, date: e.target.value})}
        />
        <input
          type="number"
          placeholder="Actual Cash"
          value={formData.actual_cash}
          onChange={(e) => setFormData({...formData, actual_cash: parseFloat(e.target.value)})}
        />
        <input
          type="number"
          placeholder="Online Sales"
          value={formData.online_sales}
          onChange={(e) => setFormData({...formData, online_sales: parseFloat(e.target.value)})}
        />
        <button type="submit">Create Record</button>
      </form>

      <button onClick={getMonthlyAnalytics}>Get Monthly Analytics</button>

      <div>
        <h2>Recent Records</h2>
        {records.map(record => (
          <div key={record.id}>
            <p>{record.date} - Total Sales: ₹{record.total_sales}</p>
            <p>Difference: ₹{record.sales_difference}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DailyRecordsManager;
```

---

## Common Issues & Solutions

### Issue 1: Record Already Exists
**Error:** `400 Bad Request - Record already exists for {date}`

**Solution:** Use PUT to update existing record or check date before creating

### Issue 2: WhatsApp Alerts Not Sending
**Check:**
1. `WHATSAPP_API_URL` in `.env`
2. `WHATSAPP_TOKEN` in `.env`
3. `CASH_DIFFERENCE_THRESHOLD` setting

### Issue 3: Excel Import Fails
**Check:**
1. File format is .xlsx or .xls
2. File follows GMTR0003 structure
3. Dates are in correct format
4. No duplicate dates in file

### Issue 4: Calculations Incorrect
**Verify:**
- All input fields have correct values
- No null values where numbers expected
- Formula logic matches business requirements

---

## Performance Tips

1. **Batch Operations:** Use bulk create for multiple records
2. **Date Range Filters:** Always use date filters for large datasets
3. **Pagination:** Use skip/limit parameters for large result sets
4. **Caching:** Cache monthly analytics results
5. **Indexing:** Database indexes on date field for faster queries

---

## Security Considerations

1. **Authentication:** Add JWT authentication to routes
2. **Authorization:** Implement role-based access control
3. **Input Validation:** All inputs validated by Pydantic schemas
4. **SQL Injection:** Protected by SQLAlchemy ORM
5. **Audit Trail:** Complete modification history maintained

---

## Monitoring & Alerts

### Key Metrics to Monitor
- Daily variance count
- Average sales per day
- Cash vs online ratio
- Modification frequency
- Import/export success rate

### Alert Thresholds
- Cash difference > ₹100 (configurable)
- Multiple consecutive days with variance
- Unbilled sales > 5% of total
- No record created for current day

---

## Backup & Recovery

### Daily Backup
```bash
# Export current month
curl -X GET "http://localhost:8000/api/daily-records/export/excel/2024/2" \
  -o backup_$(date +%Y%m%d).xlsx
```

### Database Backup
```bash
# SQLite backup
cp pharmacy.db pharmacy_backup_$(date +%Y%m%d).db
```

### Recovery
```bash
# Import from Excel backup
curl -X POST "http://localhost:8000/api/daily-records/import/excel" \
  -F "file=@backup_20240215.xlsx"
```

---

## Next Steps

1. ✅ Test all API endpoints
2. ✅ Import sample Excel data
3. ✅ Verify calculations
4. ✅ Test WhatsApp alerts
5. ✅ Create frontend integration
6. ✅ Set up monitoring
7. ✅ Configure backups
8. ✅ Deploy to production

---

## Support & Documentation

- **API Docs:** http://localhost:8000/docs
- **Main README:** `/README.md`
- **API Reference:** `/modules/daily_records/API_DOCUMENTATION.md`
- **Business Logic:** `/modules/daily_records/DAILY_RECORDS_README.md`
