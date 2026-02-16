from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from typing import List
from modules.auth.dependencies import get_current_admin, get_current_staff
from modules.auth.models import Admin, Staff
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
    limit: int = 50
):
    """Get notifications sent by admin"""
    notifications = NotificationService.get_admin_notifications(db, admin, limit)
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
    """Get read statistics for notification"""
    stats = NotificationService.get_notification_stats(db, notification_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return schemas.NotificationStats(
        total_sent=1,
        total_recipients=stats["total_recipients"],
        total_read=stats["total_read"],
        read_percentage=stats["read_percentage"]
    )

# STAFF ENDPOINTS

@router.get("/staff/list", response_model=schemas.NotificationListResponse)
def get_staff_notifications(
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
    include_read: bool = False,
    limit: int = 50
):
    """Get notifications for staff"""
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
    """Get count of unread notifications"""
    notifications_data = NotificationService.get_staff_notifications(
        db, staff, include_read=False, limit=1000
    )
    return {"unread_count": len(notifications_data)}
