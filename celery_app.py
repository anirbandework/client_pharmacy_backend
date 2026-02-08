from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'pharmacy',
    broker=settings.redis_url,
    include=['app.services.whatsapp_service', 'app.services.reminder_service']
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-reminders-daily': {
        'task': 'app.services.reminder_service.check_pending_reminders',
        'schedule': 86400.0,  # Run daily (24 hours)
    },
}

celery_app.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery_app.start()