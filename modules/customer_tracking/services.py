import pandas as pd
import PyPDF2
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from .models import *
from datetime import datetime, timedelta, date
import re
import requests
import os

class ContactProcessingService:
    
    @staticmethod
    def extract_contacts_from_excel(file_path: str) -> List[Dict[str, str]]:
        """Extract contacts from Excel file"""
        try:
            df = pd.read_excel(file_path)
            contacts = []
            
            # Try to find phone and name columns
            phone_cols = [col for col in df.columns if 'phone' in col.lower() or 'mobile' in col.lower() or 'number' in col.lower()]
            name_cols = [col for col in df.columns if 'name' in col.lower()]
            
            phone_col = phone_cols[0] if phone_cols else df.columns[0]
            name_col = name_cols[0] if name_cols else df.columns[1] if len(df.columns) > 1 else None
            
            for _, row in df.iterrows():
                phone = str(row[phone_col]).strip()
                name = str(row[name_col]).strip() if name_col else None
                
                # Clean phone number
                phone = re.sub(r'[^\d+]', '', phone)
                if phone and len(phone) >= 10:
                    contacts.append({
                        'phone': phone,
                        'name': name if name and name != 'nan' else None
                    })
            
            return contacts
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")
    
    @staticmethod
    def extract_contacts_from_pdf(file_path: str) -> List[Dict[str, str]]:
        """Extract contacts from PDF file"""
        try:
            contacts = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # Extract phone numbers using regex
            phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4,}'
            phones = re.findall(phone_pattern, text)
            
            # Extract names (assuming they appear before phone numbers)
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if re.search(phone_pattern, line):
                    phone = re.sub(r'[^\d+]', '', line)
                    if len(phone) >= 10:
                        # Try to find name in previous lines
                        name = None
                        for j in range(max(0, i-3), i):
                            if lines[j].strip() and not re.search(r'\d', lines[j]):
                                name = lines[j].strip()
                                break
                        
                        contacts.append({
                            'phone': phone,
                            'name': name
                        })
            
            return contacts
        except Exception as e:
            raise Exception(f"Error processing PDF file: {str(e)}")
    
    @staticmethod
    def check_whatsapp_status(phone: str) -> WhatsAppStatus:
        """Check if phone number has WhatsApp (mock implementation)"""
        # In real implementation, you would use WhatsApp Business API
        # For now, we'll use a simple heuristic
        
        # Mock logic: assume numbers ending in even digits have WhatsApp
        try:
            last_digit = int(phone[-1])
            return WhatsAppStatus.ACTIVE if last_digit % 2 == 0 else WhatsAppStatus.INACTIVE
        except:
            return WhatsAppStatus.UNKNOWN
    
    @staticmethod
    def process_contact_file(db: Session, file_path: str, filename: str, uploaded_by: str = None) -> Dict[str, Any]:
        """Process uploaded contact file and save to database"""
        
        # Create upload record
        upload_record = ContactUpload(
            filename=filename,
            file_type='excel' if filename.endswith(('.xlsx', '.xls')) else 'pdf',
            uploaded_by=uploaded_by
        )
        db.add(upload_record)
        db.commit()
        
        try:
            # Extract contacts based on file type
            if filename.endswith(('.xlsx', '.xls')):
                contacts = ContactProcessingService.extract_contacts_from_excel(file_path)
            else:
                contacts = ContactProcessingService.extract_contacts_from_pdf(file_path)
            
            # Process contacts
            whatsapp_count = 0
            non_whatsapp_count = 0
            duplicate_count = 0
            processed_count = 0
            
            for contact_data in contacts:
                phone = contact_data['phone']
                
                # Check for duplicates
                existing = db.query(ContactRecord).filter(ContactRecord.phone == phone).first()
                if existing:
                    duplicate_count += 1
                    continue
                
                # Check WhatsApp status
                whatsapp_status = ContactProcessingService.check_whatsapp_status(phone)
                
                # Create contact record
                contact_record = ContactRecord(
                    phone=phone,
                    name=contact_data['name'],
                    whatsapp_status=whatsapp_status,
                    source_file=filename,
                    uploaded_by=uploaded_by
                )
                
                db.add(contact_record)
                processed_count += 1
                
                if whatsapp_status == WhatsAppStatus.ACTIVE:
                    whatsapp_count += 1
                else:
                    non_whatsapp_count += 1
            
            # Update upload record
            upload_record.processed = True
            upload_record.processing_date = datetime.utcnow()
            upload_record.total_contacts = processed_count
            upload_record.whatsapp_contacts = whatsapp_count
            upload_record.non_whatsapp_contacts = non_whatsapp_count
            upload_record.duplicate_contacts = duplicate_count
            
            db.commit()
            
            return {
                'total_processed': processed_count,
                'whatsapp_contacts': whatsapp_count,
                'non_whatsapp_contacts': non_whatsapp_count,
                'duplicates_found': duplicate_count,
                'upload_id': upload_record.id
            }
            
        except Exception as e:
            upload_record.processing_errors = str(e)
            db.commit()
            raise e

class WhatsAppService:
    
    @staticmethod
    def send_store_materials(phone: str, message: str = None) -> bool:
        """Send store materials via WhatsApp"""
        try:
            from app.core.config import settings
            
            # Default message if none provided
            if not message:
                message = "🏥 Welcome to our Pharmacy!\n\nWe offer:\n✅ Quality medicines at best prices\n✅ Generic alternatives available\n✅ Expert consultation\n✅ Home delivery available\n\nVisit us today for all your healthcare needs!"
            
            # Check if WhatsApp API is configured
            if not settings.whatsapp_api_url or not settings.whatsapp_token:
                print(f"WhatsApp not configured. Message: {message}")
                return False
            
            # Format phone number
            formatted_phone = phone.replace('+', '').replace(' ', '')
            if not formatted_phone.startswith('91'):
                formatted_phone = '91' + formatted_phone
            
            # Detect provider type
            if 'twilio.com' in settings.whatsapp_api_url.lower():
                return WhatsAppService._send_via_twilio(formatted_phone, message, settings)
            else:
                return WhatsAppService._send_via_meta(formatted_phone, message, settings)
            
        except Exception as e:
            print(f"❌ WhatsApp error for {phone}: {str(e)}")
            return False
    
    @staticmethod
    def _send_via_twilio(phone: str, message: str, settings) -> bool:
        """Send via Twilio API"""
        import base64
        
        # Extract Account SID from URL
        account_sid = settings.whatsapp_api_url.split('/Accounts/')[1].split('/')[0]
        auth_token = settings.whatsapp_token
        from_number = settings.whatsapp_from_number if hasattr(settings, 'whatsapp_from_number') else '+14155238886'
        
        print(f"🔍 Twilio Debug - Account SID: {account_sid}")
        print(f"🔍 Twilio Debug - Auth Token: {auth_token[:8]}...")
        print(f"🔍 Twilio Debug - From: {from_number}")
        print(f"🔍 Twilio Debug - To: +{phone}")
        
        # Twilio uses Basic Auth
        auth_str = f"{account_sid}:{auth_token}"
        auth_bytes = auth_str.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'To': f'whatsapp:+{phone}',
            'From': f'whatsapp:{from_number}',
            'Body': message
        }
        
        response = requests.post(
            settings.whatsapp_api_url,
            headers=headers,
            data=data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            print(f"✅ WhatsApp sent to {phone} via Twilio")
            return True
        else:
            print(f"❌ Twilio failed: {response.text}")
            return False
    
    @staticmethod
    def _send_via_meta(phone: str, message: str, settings) -> bool:
        """Send via Meta WhatsApp Business API"""
        headers = {
            'Authorization': f'Bearer {settings.whatsapp_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': message}
        }
        
        response = requests.post(
            settings.whatsapp_api_url,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ WhatsApp sent to {phone} via Meta")
            return True
        else:
            print(f"❌ Meta failed: {response.text}")
            return False

class TaskAssignmentService:
    
    @staticmethod
    def assign_contacts_to_staff(db: Session) -> Dict[str, int]:
        """Automatically assign pending contacts to staff members"""
        
        # Get active staff members
        staff_members = db.query(StaffMember).filter(StaffMember.active == True).all()
        if not staff_members:
            return {}
        
        # Get unassigned contacts
        unassigned_contacts = db.query(ContactRecord).filter(
            ContactRecord.assigned_staff_code.is_(None),
            ContactRecord.contact_status == ContactStatus.PENDING.value
        ).all()
        
        if not unassigned_contacts:
            return {}
        
        # Distribute contacts evenly
        assignments = {}
        staff_index = 0
        
        for contact in unassigned_contacts:
            staff = staff_members[staff_index % len(staff_members)]
            
            # Check if staff member hasn't exceeded daily limit
            today_assignments = db.query(ContactRecord).filter(
                ContactRecord.assigned_staff_code == staff.staff_code,
                ContactRecord.assigned_date >= datetime.now().replace(hour=0, minute=0, second=0)
            ).count()
            
            if today_assignments < staff.max_contacts_per_day:
                contact.assigned_staff_code = staff.staff_code
                contact.assigned_date = datetime.utcnow()
                
                if staff.staff_code not in assignments:
                    assignments[staff.staff_code] = 0
                assignments[staff.staff_code] += 1
                
                staff.total_contacts_assigned += 1
            
            staff_index += 1
        
        db.commit()
        return assignments
    
    @staticmethod
    def get_daily_tasks(db: Session, staff_code: str) -> Dict[str, Any]:
        """Get daily task list for a staff member"""
        
        # Get assigned contacts that need calling
        pending_contacts = db.query(ContactRecord).filter(
            ContactRecord.assigned_staff_code == staff_code,
            ContactRecord.contact_status.in_([ContactStatus.PENDING.value, ContactStatus.CONTACTED.value])
        ).all()
        
        # Get pending reminders
        pending_reminders = db.query(ContactReminder).filter(
            ContactReminder.staff_code == staff_code,
            ContactReminder.completed == False,
            ContactReminder.reminder_date <= datetime.utcnow()
        ).all()
        
        return {
            'staff_code': staff_code,
            'pending_contacts': pending_contacts,
            'pending_reminders': pending_reminders,
            'total_tasks': len(pending_contacts) + len(pending_reminders)
        }

class ConversionTrackingService:
    
    @staticmethod
    def mark_conversion(db: Session, phone: str, purchase_amount: float = None) -> bool:
        """Mark a contact as converted when they make a purchase"""
        
        contact = db.query(ContactRecord).filter(ContactRecord.phone == phone).first()
        if contact:
            contact.contact_status = ContactStatus.CONVERTED.value
            contact.converted_date = datetime.utcnow()
            contact.conversion_value = purchase_amount
            
            # Update staff conversion rate
            if contact.assigned_staff_code:
                staff = db.query(StaffMember).filter(
                    StaffMember.staff_code == contact.assigned_staff_code
                ).first()
                if staff:
                    staff.total_conversions += 1
                    if staff.total_contacts_assigned > 0:
                        staff.conversion_rate = (staff.total_conversions / staff.total_contacts_assigned) * 100
            
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def generate_conversion_report(db: Session, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Generate conversion report"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # Get contacts in date range
        contacts = db.query(ContactRecord).filter(
            ContactRecord.upload_date >= start_date,
            ContactRecord.upload_date <= end_date
        ).all()
        
        total_contacts = len(contacts)
        contacted = len([c for c in contacts if c.contact_status in [ContactStatus.CONTACTED.value, ContactStatus.CONVERTED.value, ContactStatus.YELLOW.value]])
        converted = len([c for c in contacts if c.contact_status == ContactStatus.CONVERTED.value])
        yellow_status = len([c for c in contacts if c.contact_status == ContactStatus.YELLOW.value])
        
        conversion_rate = (converted / total_contacts * 100) if total_contacts > 0 else 0
        
        # Staff performance
        staff_performance = []
        staff_members = db.query(StaffMember).all()
        for staff in staff_members:
            staff_contacts = [c for c in contacts if c.assigned_staff_code == staff.staff_code]
            staff_conversions = [c for c in staff_contacts if c.contact_status == ContactStatus.CONVERTED.value]
            
            staff_performance.append({
                'staff_code': staff.staff_code,
                'name': staff.name,
                'assigned_contacts': len(staff_contacts),
                'conversions': len(staff_conversions),
                'conversion_rate': (len(staff_conversions) / len(staff_contacts) * 100) if staff_contacts else 0
            })
        
        return {
            'total_contacts': total_contacts,
            'contacted': contacted,
            'converted': converted,
            'yellow_status': yellow_status,
            'conversion_rate': conversion_rate,
            'staff_performance': staff_performance
        }

class ReminderService:
    
    @staticmethod
    def schedule_refill_reminder(db: Session, purchase_id: int, duration_days: int) -> RefillReminder:
        """Schedule refill reminder for a purchase"""
        
        purchase = db.query(CustomerPurchase).filter(CustomerPurchase.id == purchase_id).first()
        if not purchase:
            return None
        
        # Calculate reminder date (3 days before medicine runs out)
        reminder_date = (purchase.purchase_date + timedelta(days=duration_days - 3)).date()
        
        # Create reminder
        reminder = RefillReminder(
            purchase_id=purchase_id,
            customer_id=purchase.customer_id,
            medicine_name=purchase.medicine_name,
            reminder_date=reminder_date
        )
        
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        
        return reminder
    
    @staticmethod
    def get_pending_reminders(db: Session, days_ahead: int = 3) -> List[RefillReminder]:
        """Get pending refill reminders"""
        
        today = date.today()
        target_date = today + timedelta(days=days_ahead)
        
        reminders = db.query(RefillReminder).filter(
            RefillReminder.reminder_date <= target_date,
            RefillReminder.notification_sent == False
        ).all()
        
        return reminders
    
    @staticmethod
    def send_refill_notification(db: Session, reminder_id: int) -> bool:
        """Send refill reminder notification"""
        
        reminder = db.query(RefillReminder).filter(RefillReminder.id == reminder_id).first()
        if not reminder:
            return False
        
        # Get customer details
        customer = db.query(CustomerProfile).filter(CustomerProfile.id == reminder.customer_id).first()
        if not customer:
            return False
        
        # Send WhatsApp notification
        message = f"""Hello {customer.name or 'Customer'}! 👋

This is a friendly reminder that your medicine '{reminder.medicine_name}' is due for refill.

Visit us to refill your prescription and ensure uninterrupted treatment.

Thank you for choosing our pharmacy! 🏥"""
        
        success = WhatsAppService.send_store_materials(customer.phone, message)
        
        if success:
            reminder.notification_sent = True
            reminder.notification_sent_date = datetime.utcnow()
            reminder.notification_method = "whatsapp"
            db.commit()
        
        return success