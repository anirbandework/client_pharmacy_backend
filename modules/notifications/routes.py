from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.database import get_db
from typing import List, Optional
from modules.auth.dependencies import get_current_admin, get_current_staff
from modules.auth.models import Admin, Staff
from app.utils.cache import dashboard_cache
from . import schemas
from .service import NotificationService

router = APIRouter()

# ADMIN ENDPOINTS

@router.post("/admin/send", response_model=schemas.NotificationResponse)
def send_notification(
    notification_data: schemas.NotificationCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin sends notification to shops or staff"""
    try:
        notification = NotificationService.create_notification(db, admin, notification_data)
        return schemas.NotificationResponse(
            id=notification.id,
            admin_id=notification.admin_id,
            admin_name=notification.admin_name,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            target_type=notification.target_type,
            created_at=notification.created_at,
            expires_at=notification.expires_at,
            is_read=False
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.get("/admin/sent", response_model=List[schemas.NotificationResponse])
def get_sent_notifications(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    shop_code: Optional[str] = Query(None),
    limit: int = 50
):
    """Get notifications sent by admin, optionally filtered by shop"""
    notifications = NotificationService.get_admin_notifications(db, admin, shop_code, limit)
    return [
        schemas.NotificationResponse(
            id=n.id,
            admin_id=n.admin_id,
            admin_name=n.admin_name,
            title=n.title,
            message=n.message,
            type=n.type,
            target_type=n.target_type,
            created_at=n.created_at,
            expires_at=n.expires_at,
            is_read=False
        )
        for n in notifications
    ]

@router.get("/admin/stats/{notification_id}", response_model=schemas.NotificationStats)
def get_notification_stats(
    notification_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get read statistics for notification (cached)"""
    cache_key = f"notif_stats:{notification_id}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=60)
    if cached:
        return cached
    
    stats = NotificationService.get_notification_stats(db, notification_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    result = schemas.NotificationStats(
        total_sent=1,
        total_recipients=stats["total_recipients"],
        total_read=stats["total_read"],
        read_percentage=stats["read_percentage"]
    )
    dashboard_cache.set(cache_key, result)
    return result

# STAFF ENDPOINTS

@router.get("/staff/list", response_model=schemas.NotificationListResponse)
def get_staff_notifications(
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
    include_read: bool = False,
    limit: int = 20,
    offset: int = 0
):
    """Get notifications for staff with pagination"""
    notifications_data = NotificationService.get_staff_notifications(
        db, staff, include_read, limit
    )
    
    notifications = [
        schemas.NotificationResponse(
            id=item["notification"].id,
            admin_id=item["notification"].admin_id,
            admin_name=item["notification"].admin_name,
            title=item["notification"].title,
            message=item["notification"].message,
            type=item["notification"].type,
            target_type=item["notification"].target_type,
            created_at=item["notification"].created_at,
            expires_at=item["notification"].expires_at,
            is_read=item["is_read"],
            read_at=item["read_at"]
        )
        for item in notifications_data
    ]
    
    unread_count = sum(1 for n in notifications if not n.is_read)
    
    return schemas.NotificationListResponse(
        notifications=notifications,
        unread_count=unread_count,
        total_count=len(notifications)
    )

@router.post("/staff/read/{notification_id}")
def mark_notification_read(
    notification_id: int,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    NotificationService.mark_as_read(db, notification_id, staff)
    return {"message": "Notification marked as read"}

@router.get("/staff/unread-count")
def get_unread_count(
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications (cached)"""
    cache_key = f"unread_count:{staff.id}"
    cached = dashboard_cache.get(cache_key, ttl_seconds=30)
    if cached is not None:
        return {"unread_count": cached}

    count = NotificationService.get_unread_count_optimized(db, staff)
    dashboard_cache.set(cache_key, count)
    return {"unread_count": count}


# ── STAFF REQUEST ENDPOINTS ───────────────────────────────────────────────────

@router.post("/staff/request", response_model=schemas.StaffRequestResponse)
def send_staff_request(
    data: schemas.StaffRequestCreate,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    """Staff sends a request/message to their shop admin"""
    req = NotificationService.create_staff_request(db, staff, data)
    return req


@router.get("/staff/my-requests", response_model=List[schemas.StaffRequestResponse])
def get_my_requests(
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Staff views their own sent requests"""
    return NotificationService.get_staff_own_requests(db, staff, limit)


@router.get("/admin/requests", response_model=List[schemas.StaffRequestResponse])
def get_staff_requests(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
    shop_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = 100
):
    """Admin views staff requests, optionally filtered by shop"""
    return NotificationService.get_admin_staff_requests(db, admin, shop_code, status, limit)


@router.put("/admin/requests/{request_id}/acknowledge", response_model=schemas.StaffRequestResponse)
def acknowledge_request(
    request_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin acknowledges a staff request"""
    req = NotificationService.acknowledge_staff_request(db, request_id, admin, dismiss=False)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req


@router.put("/admin/requests/{request_id}/dismiss", response_model=schemas.StaffRequestResponse)
def dismiss_request(
    request_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin dismisses a staff request"""
    req = NotificationService.acknowledge_staff_request(db, request_id, admin, dismiss=True)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req
