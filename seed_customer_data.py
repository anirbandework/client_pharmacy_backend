"""Seed dummy data for customer tracking module"""

from app.database.database import SessionLocal
from modules.customer_tracking.models import *
from datetime import datetime, timedelta, date
import random

def seed_data():
    db = SessionLocal()
    
    try:
        print("🌱 Seeding customer tracking data...")
        
        # 1. Create Staff Members
        staff_data = [
            {"staff_code": "STAFF001", "name": "Rajesh Kumar", "phone": "9876543210", "max_contacts_per_day": 25},
            {"staff_code": "STAFF002", "name": "Priya Sharma", "phone": "9876543211", "max_contacts_per_day": 20},
            {"staff_code": "STAFF003", "name": "Amit Patel", "phone": "9876543212", "max_contacts_per_day": 30},
        ]
        
        for staff in staff_data:
            existing = db.query(StaffMember).filter(StaffMember.staff_code == staff["staff_code"]).first()
            if not existing:
                db.add(StaffMember(**staff))
        db.commit()
        print("✅ Created 3 staff members")
        
        # 2. Create Contact Records
        contact_data = [
            {"phone": "9123456780", "name": "Suresh Reddy", "whatsapp_status": "active"},
            {"phone": "9123456781", "name": "Lakshmi Iyer", "whatsapp_status": "active"},
            {"phone": "9123456782", "name": "Vijay Singh", "whatsapp_status": "inactive"},
            {"phone": "9123456783", "name": "Meera Nair", "whatsapp_status": "active"},
            {"phone": "9123456784", "name": "Karthik Rao", "whatsapp_status": "active"},
            {"phone": "9123456785", "name": "Divya Menon", "whatsapp_status": "inactive"},
            {"phone": "9123456786", "name": "Ravi Krishnan", "whatsapp_status": "active"},
            {"phone": "9123456787", "name": "Anjali Desai", "whatsapp_status": "active"},
        ]
        
        statuses = ["pending", "contacted", "converted", "yellow"]
        for i, contact in enumerate(contact_data):
            existing = db.query(ContactRecord).filter(ContactRecord.phone == contact["phone"]).first()
            if not existing:
                record = ContactRecord(
                    phone=contact["phone"],
                    name=contact["name"],
                    whatsapp_status=contact["whatsapp_status"],
                    contact_status=statuses[i % len(statuses)],
                    source_file="contacts_jan_2024.xlsx",
                    uploaded_by="admin",
                    upload_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                    assigned_staff_code=f"STAFF00{(i % 3) + 1}",
                    assigned_date=datetime.now() - timedelta(days=random.randint(1, 20)),
                    contact_attempts=random.randint(0, 5)
                )
                db.add(record)
        db.commit()
        print("✅ Created 8 contact records")
        
        # 3. Create Customer Profiles
        customer_data = [
            {"phone": "9383169659", "name": "Anirban De", "category": "first_time_prescription", "age": 28, "gender": "Male"},
            {"phone": "9876543220", "name": "Ramesh Gupta", "category": "regular_branded", "age": 45, "gender": "Male"},
            {"phone": "9876543221", "name": "Sita Devi", "category": "generic_informed", "age": 52, "gender": "Female"},
            {"phone": "9123456780", "name": "Suresh Reddy", "category": "contact_sheet", "age": 38, "gender": "Male"},
            {"phone": "9876543223", "name": "Arjun Menon", "category": "first_time_prescription", "age": 32, "gender": "Male"},
        ]
        
        for cust in customer_data:
            existing = db.query(CustomerProfile).filter(CustomerProfile.phone == cust["phone"]).first()
            if not existing:
                # Link to contact record if exists
                contact_record = db.query(ContactRecord).filter(ContactRecord.phone == cust["phone"]).first()
                
                profile = CustomerProfile(
                    phone=cust["phone"],
                    name=cust["name"],
                    category=cust["category"],
                    age=cust["age"],
                    gender=cust["gender"],
                    address=f"{random.randint(1, 999)} MG Road, Bangalore",
                    chronic_conditions="Diabetes" if random.random() > 0.5 else None,
                    allergies="Penicillin" if random.random() > 0.7 else None,
                    contact_record_id=contact_record.id if contact_record else None,
                    first_visit_date=datetime.now() - timedelta(days=random.randint(30, 180)),
                    total_visits=random.randint(1, 10),
                    total_purchases=random.uniform(500, 5000),
                    prefers_generic=cust["category"] == "generic_informed"
                )
                db.add(profile)
        db.commit()
        print("✅ Created 5 customer profiles")
        
        # 4. Create Purchases with Refill Reminders
        medicines = [
            {"name": "Metformin", "brand": "Glucophage", "generic": "Metformin HCl", "price": 5.0, "duration": 30},
            {"name": "Amlodipine", "brand": "Norvasc", "generic": "Amlodipine Besylate", "price": 3.5, "duration": 30},
            {"name": "Atorvastatin", "brand": "Lipitor", "generic": "Atorvastatin Calcium", "price": 8.0, "duration": 30},
            {"name": "Paracetamol", "brand": "Crocin", "generic": "Paracetamol", "price": 2.0, "duration": 5},
            {"name": "Omeprazole", "brand": "Prilosec", "generic": "Omeprazole", "price": 4.5, "duration": 15},
        ]
        
        customers = db.query(CustomerProfile).all()
        for customer in customers:
            # Create 1-3 purchases per customer
            for _ in range(random.randint(1, 3)):
                med = random.choice(medicines)
                qty = random.randint(10, 60)
                
                purchase = CustomerPurchase(
                    customer_id=customer.id,
                    medicine_name=med["name"],
                    brand_name=med["brand"],
                    generic_name=med["generic"],
                    quantity=qty,
                    unit_price=med["price"],
                    total_amount=qty * med["price"],
                    is_generic=random.random() > 0.5,
                    is_prescription=True,
                    duration_days=med["duration"],
                    purchase_date=datetime.now() - timedelta(days=random.randint(1, 25))
                )
                db.add(purchase)
                db.flush()
                
                # Create refill reminder
                reminder_date = (purchase.purchase_date + timedelta(days=med["duration"] - 3)).date()
                reminder = RefillReminder(
                    purchase_id=purchase.id,
                    customer_id=customer.id,
                    medicine_name=med["name"],
                    reminder_date=reminder_date,
                    notification_sent=reminder_date < date.today()
                )
                db.add(reminder)
        
        db.commit()
        print("✅ Created purchases and refill reminders")
        
        # 5. Create Contact Interactions
        contacts = db.query(ContactRecord).all()
        for contact in contacts[:5]:  # Add interactions for first 5 contacts
            for _ in range(random.randint(1, 3)):
                interaction = ContactInteraction(
                    contact_id=contact.id,
                    staff_code=contact.assigned_staff_code or "STAFF001",
                    interaction_date=datetime.now() - timedelta(days=random.randint(1, 15)),
                    interaction_type=random.choice(["call", "whatsapp", "visit"]),
                    notes=random.choice([
                        "Customer interested in diabetes medicines",
                        "Will visit tomorrow",
                        "Asked about generic alternatives",
                        "Requested home delivery"
                    ]),
                    call_successful=random.random() > 0.3,
                    call_duration=random.randint(60, 300) if random.random() > 0.5 else None
                )
                db.add(interaction)
        db.commit()
        print("✅ Created contact interactions")
        
        # 6. Create Contact Reminders
        for contact in contacts[:3]:
            reminder = ContactReminder(
                contact_id=contact.id,
                staff_code=contact.assigned_staff_code or "STAFF001",
                reminder_date=datetime.now() + timedelta(days=random.randint(1, 7)),
                reminder_type=random.choice(["follow_up", "callback", "visit_expected"]),
                message="Follow up on medicine inquiry",
                completed=False
            )
            db.add(reminder)
        db.commit()
        print("✅ Created contact reminders")
        
        # 7. Create Customer Visits
        for customer in customers:
            for _ in range(random.randint(1, 3)):
                visit = CustomerVisit(
                    customer_id=customer.id,
                    staff_code=random.choice(["STAFF001", "STAFF002", "STAFF003"]),
                    visit_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                    visit_purpose=random.choice(["prescription", "consultation", "purchase"]),
                    prescription_brought=random.random() > 0.5,
                    purchase_made=random.random() > 0.3,
                    purchase_amount=random.uniform(100, 1000) if random.random() > 0.3 else None,
                    staff_notes="Regular customer, prefers branded medicines"
                )
                db.add(visit)
        db.commit()
        print("✅ Created customer visits")
        
        print("\n🎉 Dummy data seeded successfully!")
        print("\n📊 Summary:")
        print(f"   - Staff Members: {db.query(StaffMember).count()}")
        print(f"   - Contact Records: {db.query(ContactRecord).count()}")
        print(f"   - Customer Profiles: {db.query(CustomerProfile).count()}")
        print(f"   - Purchases: {db.query(CustomerPurchase).count()}")
        print(f"   - Refill Reminders: {db.query(RefillReminder).count()}")
        print(f"   - Contact Interactions: {db.query(ContactInteraction).count()}")
        print(f"   - Contact Reminders: {db.query(ContactReminder).count()}")
        print(f"   - Customer Visits: {db.query(CustomerVisit).count()}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
