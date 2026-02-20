from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'pharmacy',
    broker=settings.redis_url,
    backend=settings.redis_url,  # Use Redis as result backend
    include=['app.services.whatsapp_service', 'app.services.reminder_service']
)

# Celery configuration for high-load scenarios and
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker configuration for handling multiple users
    worker_prefetch_multiplier=4,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Redis broker settings
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
)

# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-reminders-daily': {
        'task': 'app.services.reminder_service.check_pending_reminders',
        'schedule': 86400.0,  # Run daily (24 hours)
    },
    'cleanup-expired-sessions': {
        'task': 'app.services.redis_service.cleanup_expired_data',
        'schedule': 3600.0,  # Run hourly
    },
}

if __name__ == '__main__':
    celery_app.start()