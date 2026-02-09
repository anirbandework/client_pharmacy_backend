# Enhanced Customer Tracking System

## Overview

The enhanced customer tracking system now captures comprehensive customer details including prescriptions, medical conditions, and generates intelligent call scripts to ensure staff have all necessary information for effective customer calls.

## Key Features

### 1. Comprehensive Customer Profiles
- **Basic Information**: Name, phone, age, gender, address
- **Medical History**: Chronic conditions, allergies, primary doctor details
- **Prescription Tracking**: Complete prescription history with follow-up dates
- **Purchase Behavior**: Medicine preferences, generic adoption, visit patterns

### 2. Prescription Management
- **Detailed Prescriptions**: Doctor details, condition, medicines with dosage/frequency
- **Follow-up Tracking**: Doctor visits, lab tests, medication reviews
- **Medicine Tracking**: Brand vs generic, refill schedules, compliance monitoring

### 3. Medical Condition Tracking
- **Condition Types**: Chronic, acute, preventive care
- **Monitoring Requirements**: Checkup schedules, severity tracking
- **Treatment History**: Primary medicines, treatment duration, progress notes

### 4. Intelligent Call Scripts
- **Auto-Generated**: Based on customer data, medical history, and pending needs
- **Personalized Content**: Customer summary, medical context, talking points
- **Priority-Based**: High priority for chronic conditions with pending refills
- **Outcome Tracking**: Call success rates, customer responses

## API Endpoints

### Customer Management
```
POST /api/customers/{customer_id}/prescriptions
POST /api/customers/{customer_id}/medical-conditions
GET /api/customers/{customer_id}/prescriptions
GET /api/customers/{customer_id}/medical-conditions
```

### Call Script Management
```
GET /api/customers/{customer_id}/call-details
POST /api/customers/{customer_id}/call-script
PUT /api/call-scripts/{script_id}/outcome
GET /api/call-scripts/priority/{priority}
```

### Enhanced Analytics
```
GET /api/analytics/prescription-compliance
GET /api/analytics/call-effectiveness
```

## Call Script Generation

### Automatic Script Creation
The system automatically generates call scripts containing:

1. **Customer Summary**
   - Visit history and relationship status
   - Medical condition overview
   - Recent purchase behavior

2. **Medical Context**
   - Active chronic conditions
   - Current medications and frequencies
   - Upcoming follow-up requirements

3. **Talking Points**
   - Personalized greeting approach
   - Health-focused conversation starters
   - Value proposition messaging
   - Generic medicine education opportunities

4. **Action Items**
   - Medicines due for refill
   - Follow-up appointments to schedule
   - Health monitoring reminders

### Priority System
- **High Priority**: Chronic conditions with pending refills
- **Medium Priority**: Overdue visits or pending refills
- **Low Priority**: General wellness checks

## Usage Workflow

### 1. Customer Registration
```python
# Add basic customer profile
customer = {
    "phone": "+919876543210",
    "name": "John Doe",
    "age": 45,
    "category": "regular_branded",
    "primary_doctor": "Dr. Smith",
    "doctor_phone": "+919876543211"
}
```

### 2. Add Prescription Details
```python
prescription = {
    "prescription_date": "2024-01-15",
    "doctor_name": "Dr. Smith",
    "condition_name": "Hypertension",
    "is_chronic": True,
    "next_followup_date": "2024-02-15",
    "medicines": [
        {
            "medicine_name": "Amlodipine",
            "dosage": "5mg",
            "frequency": "Once daily",
            "duration_days": 30,
            "total_quantity_prescribed": 30
        }
    ]
}
```

### 3. Add Medical Conditions
```python
condition = {
    "condition_name": "Type 2 Diabetes",
    "condition_type": "chronic",
    "severity": "moderate",
    "requires_monitoring": True,
    "monitoring_frequency": "monthly",
    "primary_medicine": "Metformin"
}
```

### 4. Generate Call Script
```python
# System automatically generates based on customer data
call_details = get_customer_call_details(customer_id)
# Returns comprehensive call information including script
```

## Call Script Example

### Generated Script Output
```
Customer Summary:
Repeat customer with 5 visits, total purchases: ₹2,500. Has 2 chronic condition(s) requiring ongoing care. Last visit 15 days ago.

Medical Summary:
Chronic conditions: Hypertension, Type 2 Diabetes. Current medications: Amlodipine (Once daily), Metformin (Twice daily).

Key Talking Points:
• Greet as valued customer - mention their 5 visits
• Remind about 2 medicine(s) due for refill
• Emphasize importance of continuous treatment
• Show concern for their chronic condition management
• Offer medication counseling and adherence support
• Mention competitive pricing and quality assurance
• Offer home delivery service if needed

Medicines to Discuss:
• Amlodipine - due 2024-02-15
• Metformin - due 2024-02-18

Follow-up Reminders:
• Doctor follow-up for Hypertension due in 5 days
• Health checkup for Type 2 Diabetes due in 12 days
• Schedule next call in 2-3 weeks if no immediate needs
```

## Benefits

### For Staff
- **Complete Context**: All customer information in one view
- **Conversation Guide**: Natural talking points and health focus
- **Relationship Building**: Personal details for rapport building
- **Efficiency**: Prioritized call lists with ready scripts

### For Customers
- **Personal Care**: Staff knows their medical history and needs
- **Timely Reminders**: Proactive refill and follow-up notifications
- **Health Focus**: Conversations centered on their wellbeing
- **Convenience**: Seamless pharmacy experience

### For Business
- **Customer Retention**: Personalized service increases loyalty
- **Revenue Growth**: Timely refill reminders prevent lost sales
- **Operational Efficiency**: Structured call processes
- **Health Outcomes**: Better medication compliance through follow-up

## Implementation Notes

1. **Data Privacy**: All medical information is encrypted and access-controlled
2. **Staff Training**: Train staff to use call scripts naturally, not robotically
3. **Regular Updates**: Scripts expire after 24 hours to ensure fresh information
4. **Outcome Tracking**: Monitor call success rates to improve script quality
5. **Integration**: Links with existing purchase and reminder systems

## Analytics and Reporting

### Prescription Compliance
- Track follow-up completion rates
- Monitor overdue appointments
- Analyze chronic condition management

### Call Effectiveness
- Script usage and success rates
- Priority-based performance metrics
- Staff performance tracking

This enhanced system ensures every customer call is informed, personal, and focused on their health needs while building strong pharmacy relationships.