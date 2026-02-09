#!/usr/bin/env python3
"""
Simple test for enhanced customer tracking system
Manually creates a customer and tests the new endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/customers"

def test_enhanced_customer_system():
    """Test the enhanced customer tracking system"""
    
    print("🧪 Testing Enhanced Customer Tracking System")
    print("=" * 50)
    
    # Test 1: Create a customer
    print("\n1. Creating a customer...")
    customer_data = {
        "phone": "+919876543210",
        "name": "Test Customer",
        "category": "regular_branded",
        "age": 45,
        "gender": "Male",
        "primary_doctor": "Dr. Test",
        "doctor_phone": "+919876543211"
    }
    
    try:
        response = requests.post(f"{BASE_URL}", json=customer_data)
        if response.status_code == 200:
            customer = response.json()
            customer_id = customer["id"]
            print(f"✅ Customer created successfully: ID {customer_id}")
        else:
            print(f"❌ Failed to create customer: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error creating customer: {str(e)}")
        return
    
    # Test 2: Add medical condition
    print("\n2. Adding medical condition...")
    condition_data = {
        "customer_id": customer_id,
        "condition_name": "Hypertension",
        "condition_type": "chronic",
        "severity": "moderate",
        "requires_monitoring": True,
        "monitoring_frequency": "monthly",
        "primary_medicine": "Amlodipine"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/{customer_id}/medical-conditions", json=condition_data)
        if response.status_code == 200:
            print("✅ Medical condition added successfully")
        else:
            print(f"❌ Failed to add medical condition: {response.text}")
    except Exception as e:
        print(f"❌ Error adding medical condition: {str(e)}")
    
    # Test 3: Add prescription
    print("\n3. Adding prescription...")
    prescription_data = {
        "customer_id": customer_id,
        "prescription_date": "2024-01-15",
        "doctor_name": "Dr. Test",
        "condition_name": "Hypertension",
        "is_chronic": True,
        "next_followup_date": "2024-02-15",
        "medicines": [
            {
                "medicine_name": "Amlodipine",
                "dosage": "5mg",
                "frequency": "Once daily",
                "duration_days": 30,
                "total_quantity_prescribed": 30,
                "start_date": "2024-01-15",
                "end_date": "2024-02-14"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/{customer_id}/prescriptions", json=prescription_data)
        if response.status_code == 200:
            print("✅ Prescription added successfully")
        else:
            print(f"❌ Failed to add prescription: {response.text}")
    except Exception as e:
        print(f"❌ Error adding prescription: {str(e)}")
    
    # Test 4: Generate call script
    print("\n4. Generating call script...")
    try:
        response = requests.post(f"{BASE_URL}/{customer_id}/call-script?call_type=follow_up")
        if response.status_code == 200:
            script = response.json()
            print("✅ Call script generated successfully")
            print(f"   Priority: {script['priority']}")
            print(f"   Customer Summary: {script['customer_summary'][:100]}...")
        else:
            print(f"❌ Failed to generate call script: {response.text}")
    except Exception as e:
        print(f"❌ Error generating call script: {str(e)}")
    
    # Test 5: Get call details
    print("\n5. Getting comprehensive call details...")
    try:
        response = requests.get(f"{BASE_URL}/{customer_id}/call-details")
        if response.status_code == 200:
            call_details = response.json()
            print("✅ Call details retrieved successfully")
            print(f"   Customer: {call_details['name']}")
            print(f"   Active Conditions: {len(call_details['active_conditions'])}")
            print(f"   Current Prescriptions: {len(call_details['current_prescriptions'])}")
            if call_details['suggested_script']:
                print(f"   Script Available: Yes ({call_details['suggested_script']['call_type']})")
        else:
            print(f"❌ Failed to get call details: {response.text}")
    except Exception as e:
        print(f"❌ Error getting call details: {str(e)}")
    
    # Test 6: Analytics
    print("\n6. Testing analytics endpoints...")
    
    # Prescription compliance
    try:
        response = requests.get(f"{BASE_URL}/../analytics/prescription-compliance")
        if response.status_code == 200:
            analytics = response.json()
            print("✅ Prescription compliance analytics retrieved")
            print(f"   Total Prescriptions: {analytics['total_prescriptions']}")
            print(f"   Compliance Rate: {analytics['compliance_rate']:.1f}%")
        else:
            print(f"❌ Failed to get prescription analytics: {response.text}")
    except Exception as e:
        print(f"❌ Error getting prescription analytics: {str(e)}")
    
    # Call effectiveness
    try:
        response = requests.get(f"{BASE_URL}/../analytics/call-effectiveness")
        if response.status_code == 200:
            analytics = response.json()
            print("✅ Call effectiveness analytics retrieved")
            print(f"   Total Scripts Generated: {analytics['total_scripts_generated']}")
            print(f"   Usage Rate: {analytics['usage_rate']:.1f}%")
        else:
            print(f"❌ Failed to get call analytics: {response.text}")
    except Exception as e:
        print(f"❌ Error getting call analytics: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Enhanced Customer Tracking System Test Complete!")
    print("\nKey Features Tested:")
    print("✓ Customer profile with doctor details")
    print("✓ Medical condition tracking")
    print("✓ Prescription management with medicines")
    print("✓ Intelligent call script generation")
    print("✓ Comprehensive call details for staff")
    print("✓ Prescription compliance analytics")
    print("✓ Call effectiveness metrics")

if __name__ == "__main__":
    test_enhanced_customer_system()