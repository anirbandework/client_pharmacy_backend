from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import ContactRecord, ContactInteraction, ContactReminder, Customer, CustomerPurchase, RefillReminder
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import re

class CustomerTrackingService:
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """Normalize phone number to +91XXXXXXXXXX format"""
        phone = re.sub(r'[^\d+]', '', phone)
        phone = phone.replace('+', '')
        if phone.startswith('91'):
            phone = phone[2:]
        if len(phone) == 10:
            return f"+91{phone}"
        return None
    
    @staticmethod
    def detect_whatsapp_status(phone: str) -> str:
        """Detect if phone has WhatsApp (placeholder - needs actual API integration)"""
        # TODO: Integrate with WhatsApp Business API
        return "unknown"
    
    @staticmethod
    def process_contact_file(
        db: Session,
        shop_id: int,
        file_content: bytes,
        filename: str,
        staff_id: int
    ) -> Dict[str, int]:
        """Process uploaded Excel/PDF contact file"""
        
        # Parse file based on extension
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file_content)
        elif filename.endswith('.csv'):
            df = pd.read_csv(file_content)
        else:
            raise ValueError("Unsupported file format. Use Excel or CSV")
        
        # Expected columns: phone, name (optional)
        if 'phone' not in df.columns:
            raise ValueError("File must contain 'phone' column")
        
        stats = {
            'total_contacts': len(df),
            'whatsapp_active': 0,
            'whatsapp_inactive': 0,
            'duplicates_skipped': 0,
            'contacts_added': 0
        }
        
        for _, row in df.iterrows():
            phone = CustomerTrackingService.normalize_phone(str(row['phone']))
            if not phone:
                continue
            
            # Check for duplicates
            existing = db.query(ContactRecord).filter(
                ContactRecord.shop_id == shop_id,
                ContactRecord.phone == phone
            ).first()
            
            if existing:
                stats['duplicates_skipped'] += 1
                continue
            
            # Detect WhatsApp status
            whatsapp_status = CustomerTrackingService.detect_whatsapp_status(phone)
            if whatsapp_status == "active":
                stats['whatsapp_active'] += 1
            elif whatsapp_status == "inactive":
                stats['whatsapp_inactive'] += 1
            
            # Create contact record
            contact = ContactRecord(
                shop_id=shop_id,
                phone=phone,
                name=row.get('name'),
                whatsapp_status=whatsapp_status,
                source_file=filename,
                uploaded_by_staff_id=staff_id
            )
            db.add(contact)
            stats['contacts_added'] += 1
        
        db.commit()
        return stats
    
    @staticmethod
    def assign_contacts_to_staff(
        db: Session,
        shop_id: int,
        staff_ids: List[int],
        contact_status: str = "pending"
    ):
        """Distribute pending contacts evenly among staff"""
        
        contacts = db.query(ContactRecord).filter(
            ContactRecord.shop_id == shop_id,
            ContactRecord.contact_status == contact_status,
            ContactRecord.assigned_staff_id == None
        ).all()
        
        if not contacts or not staff_ids:
            return
        
        # Round-robin assignment
        for i, contact in enumerate(contacts):
            staff_id = staff_ids[i % len(staff_ids)]
            contact.assigned_staff_id = staff_id
            contact.assigned_date = datetime.utcnow()
        
        db.commit()
    
    @staticmethod
    def add_interaction(
        db: Session,
        shop_id: int,
        contact_id: int,
        staff_id: int,
        interaction_data: dict
    ) -> ContactInteraction:
        """Add interaction to contact record"""
        
        interaction = ContactInteraction(
            shop_id=shop_id,
            contact_id=contact_id,
            staff_id=staff_id,
            **interaction_data
        )
        db.add(interaction)
        
        # Update contact record
        contact = db.query(ContactRecord).filter(ContactRecord.id == contact_id).first()
        if contact:
            contact.contact_attempts += 1
            contact.last_contact_date = datetime.utcnow()
            if not contact.first_contact_date:
                contact.first_contact_date = datetime.utcnow()
            if contact.contact_status == "pending":
                contact.contact_status = "contacted"
        
        db.commit()
        db.refresh(interaction)
        return interaction
    
    @staticmethod
    def mark_contact_converted(
        db: Session,
        phone: str,
        shop_id: int,
        conversion_value: float
    ):
        """Mark contact as converted when they make first purchase"""
        
        contact = db.query(ContactRecord).filter(
            ContactRecord.shop_id == shop_id,
            ContactRecord.phone == phone
        ).first()
        
        if contact and contact.contact_status != "converted":
            contact.contact_status = "converted"
            contact.converted_date = datetime.utcnow()
            contact.conversion_value = conversion_value
            db.commit()
    
    @staticmethod
    def mark_contact_yellow(
        db: Session,
        phone: str,
        shop_id: int
    ):
        """Mark contact as yellow (visited but didn't buy)"""
        
        contact = db.query(ContactRecord).filter(
            ContactRecord.shop_id == shop_id,
            ContactRecord.phone == phone
        ).first()
        
        if contact:
            contact.contact_status = "yellow"
            db.commit()
    
    @staticmethod
    def get_or_create_customer(
        db: Session,
        shop_id: int,
        phone: str,
        name: Optional[str],
        category: str,
        contact_record_id: Optional[int] = None
    ) -> Customer:
        """Get existing customer or create new one"""
        
        customer = db.query(Customer).filter(
            Customer.shop_id == shop_id,
            Customer.phone == phone
        ).first()
        
        if not customer:
            customer = Customer(
                shop_id=shop_id,
                phone=phone,
                name=name,
                category=category,
                contact_record_id=contact_record_id
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
        
        return customer
    
    @staticmethod
    def record_purchase(
        db: Session,
        customer_id: int,
        shop_id: int,
        purchase_data: dict,
        bill_id: Optional[int] = None
    ) -> CustomerPurchase:
        """Record customer purchase and create refill reminder if duration provided"""
        
        purchase = CustomerPurchase(
            shop_id=shop_id,
            customer_id=customer_id,
            bill_id=bill_id,
            **purchase_data
        )
        db.add(purchase)
        
        # Update customer stats
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer:
            customer.total_visits += 1
            customer.total_purchases += purchase_data['total_amount']
            customer.last_visit_date = datetime.utcnow()
        
        # Create refill reminder if duration provided
        if purchase_data.get('duration_days'):
            reminder_date = date.today() + timedelta(days=purchase_data['duration_days'] - 5)
            purchase.refill_reminder_date = reminder_date
            
            reminder = RefillReminder(
                shop_id=shop_id,
                customer_id=customer_id,
                medicine_name=purchase_data['medicine_name'],
                reminder_date=reminder_date
            )
            db.add(reminder)
        
        db.commit()
        db.refresh(purchase)
        return purchase
    
    @staticmethod
    def get_due_refill_reminders(
        db: Session,
        shop_id: int,
        days_ahead: int = 0
    ) -> List[RefillReminder]:
        """Get refill reminders due today or in next N days"""
        
        target_date = date.today() + timedelta(days=days_ahead)
        
        return db.query(RefillReminder).filter(
            RefillReminder.shop_id == shop_id,
            RefillReminder.reminder_date <= target_date,
            RefillReminder.customer_purchased == False
        ).all()
    
    @staticmethod
    def get_contact_conversion_report(
        db: Session,
        shop_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Generate contact conversion report"""
        
        query = db.query(ContactRecord).filter(ContactRecord.shop_id == shop_id)
        
        if start_date:
            query = query.filter(ContactRecord.upload_date >= start_date)
        if end_date:
            query = query.filter(ContactRecord.upload_date <= end_date)
        
        contacts = query.all()
        
        total = len(contacts)
        converted = sum(1 for c in contacts if c.contact_status == "converted")
        yellow = sum(1 for c in contacts if c.contact_status == "yellow")
        contacted = sum(1 for c in contacts if c.contact_status == "contacted")
        pending = sum(1 for c in contacts if c.contact_status == "pending")
        
        total_conversion_value = sum(c.conversion_value or 0 for c in contacts if c.contact_status == "converted")
        
        return {
            "total_contacts": total,
            "converted": converted,
            "yellow": yellow,
            "contacted": contacted,
            "pending": pending,
            "conversion_rate": (converted / total * 100) if total > 0 else 0,
            "total_conversion_value": total_conversion_value,
            "avg_conversion_value": (total_conversion_value / converted) if converted > 0 else 0
        }
