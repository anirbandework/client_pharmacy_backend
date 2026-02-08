import requests
from app.core.config import settings

def send_whatsapp_alert(message: str, phone_number: str = None):
    """Send WhatsApp alert using WhatsApp Business API"""
    if not settings.whatsapp_api_url or not settings.whatsapp_token:
        print(f"WhatsApp not configured. Message: {message}")
        return
    
    headers = {
        'Authorization': f'Bearer {settings.whatsapp_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'messaging_product': 'whatsapp',
        'to': phone_number or 'owner_phone_number',
        'type': 'text',
        'text': {'body': message}
    }
    
    try:
        response = requests.post(settings.whatsapp_api_url, headers=headers, json=data)
        return response.json()
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
        return None

def send_customer_reminder(customer_phone: str, medicine_name: str):
    """Send medicine reminder to customer"""
    message = f"Reminder: Your {medicine_name} will run out in 5 days. Please visit our store to refill."
    return send_whatsapp_alert(message, customer_phone)