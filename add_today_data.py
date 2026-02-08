"""Add today's activity data"""

from app.database.database import SessionLocal
from modules.customer_tracking.models import *
from datetime import datetime, date
import random

def add_today_data():
    db = SessionLocal()
    
    try:
        print("📅 Adding today's activity data...")
        
        today_start = datetime.combine(date.today(), datetime.min.time())
        
        # 1. Add contacts uploaded today
        for i in range(3):
            contact = ContactRecord(
                phone=f"912345678{90+i}",
                name=f"Today Customer {i+1}",
                whatsapp_status="active",
                contact_status="pending",
                source_file="contacts_today.xlsx",
                uploaded_by="admin",
                upload_date=today_start,
                contact_attempts=0
            )
            db.add(contact)
        db.commit()
        print("✅ Added 3 contacts uploaded today")
        
        # 2. Add interactions today
        contacts = db.query(ContactRecord).limit(5).all()
        for contact in contacts:
            interaction = ContactInteraction(
                contact_id=contact.id,
                staff_code="STAFF001",
                interaction_date=datetime.now(),
                interaction_type="call",
                notes="Called today - customer interested",
                call_successful=True,
                call_duration=180
            )
            db.add(interaction)
        db.commit()
        print("✅ Added 5 interactions today")
        
        # 3. Add conversions today
        contacts_to_convert = db.query(ContactRecord).filter(
            ContactRecord.contact_status == "contacted"
        ).limit(2).all()
        
        for contact in contacts_to_convert:
            contact.contact_status = "converted"
            contact.converted_date = datetime.now()
            contact.conversion_value = random.uniform(500, 2000)
        db.commit()
        print("✅ Added 2 conversions today")
        
        # 4. Add customer visits today
        customers = db.query(CustomerProfile).limit(3).all()
        for customer in customers:
            visit = CustomerVisit(
                customer_id=customer.id,
                staff_code="STAFF001",
                visit_date=datetime.now(),
                visit_purpose="purchase",
                prescription_brought=True,
                purchase_made=True,
                purchase_amount=random.uniform(200, 1500),
                staff_notes="Regular visit"
            )
            db.add(visit)
        db.commit()
        print("✅ Added 3 customer visits today")
        
        # 5. Add purchases today
        for customer in customers:
            purchase = CustomerPurchase(
                customer_id=customer.id,
                medicine_name="Paracetamol",
                brand_name="Crocin",
                generic_name="Paracetamol",
                quantity=20,
                unit_price=2.5,
                total_amount=50.0,
                is_generic=False,
                is_prescription=False,
                duration_days=5,
                purchase_date=datetime.now()
            )
            db.add(purchase)
        db.commit()
        print("✅ Added 3 purchases today")
        
        print("\n🎉 Today's data added successfully!")
        
        # Show summary
        today_contacts = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= today_start
        ).count()
        
        today_interactions = db.query(ContactInteraction).filter(
            ContactInteraction.interaction_date >= today_start
        ).count()
        
        today_conversions = db.query(ContactRecord).filter(
            ContactRecord.converted_date >= today_start
        ).count()
        
        today_visits = db.query(CustomerVisit).filter(
            CustomerVisit.visit_date >= today_start
        ).count()
        
        today_revenue = db.query(func.sum(CustomerPurchase.total_amount)).filter(
            CustomerPurchase.purchase_date >= today_start
        ).scalar() or 0
        
        print(f"\n📊 Today's Summary:")
        print(f"   - Contacts processed: {today_contacts}")
        print(f"   - Interactions: {today_interactions}")
        print(f"   - Conversions: {today_conversions}")
        print(f"   - Customer visits: {today_visits}")
        print(f"   - Revenue: ₹{today_revenue:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_today_data()
