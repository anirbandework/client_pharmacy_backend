"""
Background scheduler for attendance tasks
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database.database import SessionLocal
from .wifi_heartbeat_service import WiFiHeartbeatService
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def check_stale_sessions_job():
    """Job to check and auto-checkout stale sessions"""
    db = SessionLocal()
    try:
        result = WiFiHeartbeatService.check_stale_sessions(db, stale_minutes=5)
        if result['checked_out_count'] > 0:
            logger.info(f"Auto checked-out {result['checked_out_count']} stale sessions")
    except Exception as e:
        logger.error(f"Error checking stale sessions: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    # Check stale sessions every minute
    scheduler.add_job(
        check_stale_sessions_job,
        trigger=IntervalTrigger(minutes=1),
        id='check_stale_sessions',
        name='Check and auto-checkout stale WiFi sessions',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Attendance scheduler started - checking stale sessions every minute")

def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()
    logger.info("Attendance scheduler stopped")
