#!/usr/bin/env python3
"""Quick test for customer purchase endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000"

# Test data
test_purchase = {
    "phone": "9383169659",
    "name": "Test Customer",
    "category": "first_time_prescription",
    "age": 35,
    "gender": "Male",
    "address": "123 Test Street",
    "chronic_conditions": "None",
    "allergies": "None",
    "items": [
        {
            "medicine_name": "Paracetamol",
            "brand_name": "Crocin",
            "generic_name": "Paracetamol",
            "quantity": 10,
            "unit_price": 5.0,
            "total_amount": 50.0,
            "is_generic": False,
            "is_prescription": False,
            "duration_days": 10
        }
    ]
}

print("🧪 Testing Quick Purchase Endpoint")
print("=" * 50)

try:
    response = requests.post(
        f"{BASE_URL}/api/customers/quick-purchase",
        json=test_purchase,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        print("\n✅ Test PASSED!")
    else:
        print("\n❌ Test FAILED!")
        
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
