#!/usr/bin/env python3
"""
Enhanced Customer Tracking Sample Data Generator
Creates realistic customer profiles with prescriptions, medical conditions, and call scripts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.database import get_db, engine
from modules.customer_tracking.models import *
from datetime import datetime, date, timedelta
import random

# Try to import CallScriptService, but continue without it if pandas is missing
try:
    from modules.customer_tracking.services import CallScriptService
    CALL_SCRIPT_AVAILABLE = True
except ImportError:
    CALL_SCRIPT_AVAILABLE = False
    print("⚠️  CallScriptService not available (pandas missing). Skipping call script generation.")

# Sample data with minimal dependencies
CUSTOMERS = [
    {
        "name": "Rajesh Kumar",
        "phone": "+919876543210",
        "age": 55,
        "gender": "Male",
        "category": "regular_branded",
        "primary_doctor": "Dr. Sharma",
        "doctor_phone": "+919876543211"
    },
    {
        "name": "Priya Patel",
        "phone": "+919876543220",
        "age": 32,
        "gender": "Female",
        "category": "generic_informed",
        "primary_doctor": "Dr. Mehta",
        "doctor_phone": "+919876543221"
    }
]

def create_sample_data():
    """Create comprehensive sample data for enhanced customer tracking"""
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    db = next(get_db())
    
    try:
        print("🏥 Creating Enhanced Customer Tracking Sample Data...")
        
        for customer_data in CUSTOMERS:
            print(f"\n👤 Creating customer: {customer_data['name']}")
            
            # Create customer profile (without shop_id to avoid foreign key issues)
            customer = CustomerProfile(
                phone=customer_data["phone"],
                name=customer_data["name"],
                age=customer_data["age"],
                gender=customer_data["gender"],
                category=customer_data["category"],
                primary_doctor=customer_data["primary_doctor"],
                doctor_phone=customer_data["doctor_phone"],
                total_visits=random.randint(2, 8),
                total_purchases=random.uniform(500, 5000),
                prefers_generic=customer_data["category"] == "generic_informed"
            )
            db.add(customer)
            db.flush()
            
            # Add a sample medical condition
            condition = CustomerMedicalCondition(
                customer_id=customer.id,
                condition_name="Hypertension" if customer.age > 40 else "Vitamin Deficiency",
                condition_type="chronic" if customer.age > 40 else "acute",
                severity="mild",
                requires_monitoring=True,
                monitoring_frequency="monthly",
                primary_medicine="Amlodipine" if customer.age > 40 else "Multivitamin",
                diagnosed_date=date.today() - timedelta(days=random.randint(30, 365)),
                next_checkup_date=date.today() + timedelta(days=random.randint(7, 30))
            )
            db.add(condition)
            
            # Add a sample prescription
            prescription = CustomerPrescription(
                customer_id=customer.id,
                prescription_date=date.today() - timedelta(days=random.randint(1, 15)),
                doctor_name=customer_data["primary_doctor"],
                condition_name=condition.condition_name,
                is_chronic=condition.condition_type == "chronic",
                next_followup_date=date.today() + timedelta(days=random.randint(15, 45)),
                followup_type="doctor_visit"
            )
            db.add(prescription)
            db.flush()
            
            # Add prescription medicine
            medicine = PrescriptionMedicine(
                prescription_id=prescription.id,
                medicine_name=condition.primary_medicine,
                dosage="5mg" if "Amlodipine" in condition.primary_medicine else "1 tablet",
                frequency="Once daily",
                duration_days=30,
                total_quantity_prescribed=30,
                start_date=prescription.prescription_date,
                end_date=prescription.prescription_date + timedelta(days=30)
            )
            db.add(medicine)
            
            # Add purchase history
            purchase = CustomerPurchase(
                customer_id=customer.id,
                purchase_date=datetime.now() - timedelta(days=random.randint(1, 15)),
                medicine_name=condition.primary_medicine,
                quantity=30,
                unit_price=random.uniform(10, 100),
                total_amount=random.uniform(300, 1000),
                is_generic=customer.prefers_generic,
                duration_days=30
            )
            db.add(purchase)
            db.flush()
            
            # Add refill reminder
            reminder = RefillReminder(
                purchase_id=purchase.id,
                customer_id=customer.id,
                medicine_name=purchase.medicine_name,
                reminder_date=purchase.purchase_date.date() + timedelta(days=27)
            )
            db.add(reminder)
        
        db.commit()
        print("\n✅ Sample data created successfully!")
        
        # Generate call scripts if available
        if CALL_SCRIPT_AVAILABLE:
            print("\n📞 Generating call scripts...")
            customers = db.query(CustomerProfile).all()
            
            for customer in customers:
                call_type = random.choice(["refill_reminder", "follow_up", "general"])
                script = CallScriptService.generate_call_script(db, customer.id, call_type)
                if script:
                    print(f"   ✓ Generated {call_type} script for {customer.name}")
            
            print("\n🎯 Call scripts generated successfully!")
        else:
            print("\n⚠️  Skipping call script generation (pandas not installed)")
        
        # Display summary
        print("\n" + "="*60)
        print("📊 SAMPLE DATA SUMMARY")
        print("="*60)
        
        total_customers = db.query(CustomerProfile).count()
        total_conditions = db.query(CustomerMedicalCondition).count()
        total_prescriptions = db.query(CustomerPrescription).count()
        total_medicines = db.query(PrescriptionMedicine).count()
        total_scripts = db.query(CallScript).count() if CALL_SCRIPT_AVAILABLE else 0
        total_reminders = db.query(RefillReminder).count()
        
        print(f"👥 Customers: {total_customers}")
        print(f"🏥 Medical Conditions: {total_conditions}")
        print(f"📋 Prescriptions: {total_prescriptions}")
        print(f"💊 Medicines: {total_medicines}")
        print(f"📞 Call Scripts: {total_scripts}")
        print(f"⏰ Refill Reminders: {total_reminders}")
        
        print("\n" + "="*60)
        print("🚀 Enhanced Customer Tracking System Ready!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()