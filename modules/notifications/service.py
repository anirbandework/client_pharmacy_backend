from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime
from .models import (
    Notification, NotificationShopTarget, NotificationStaffTarget, 
    NotificationRead, NotificationTargetType
)
from modules.auth.models import Admin, Staff, Shop
from . import schemas

class NotificationService:
    
    @staticmethod
    def create_notification(
        db: Session,
        admin: Admin,
        notification_data: schemas.NotificationCreate
    ) -> Notification:
        """Create notification and assign targets"""
        
        # Validate targets based on admin's organization
        if notification_data.target_type == NotificationTargetType.SHOP:
            # Validate shop access
            org_shop_ids = db.query(Shop.id).join(Admin).filter(
                Admin.organization_id == admin.organization_id
            ).all()
            org_shop_ids = [sid[0] for sid in org_shop_ids]
            
            invalid_shops = set(notification_data.shop_ids) - set(org_shop_ids)
            if invalid_shops:
                raise ValueError(f"No access to shops: {invalid_shops}")
        
        elif notification_data.target_type == NotificationTargetType.STAFF:
            # Validate staff access
            org_staff_ids = db.query(Staff.id).join(Shop).join(Admin).filter(
                Admin.organization_id == admin.organization_id
            ).all()
            org_staff_ids = [sid[0] for sid in org_staff_ids]
            
            invalid_staff = set(notification_data.staff_ids) - set(org_staff_ids)
            if invalid_staff:
                raise ValueError(f"No access to staff: {invalid_staff}")
        
        # Create notification
        notification = Notification(
            admin_id=admin.id,
            admin_name=admin.full_name,
            title=notification_data.title,
            message=notification_data.message,
            type=notification_data.type,
            target_type=notification_data.target_type,
            expires_at=notification_data.expires_at
        )
        db.add(notification)
        db.flush()
        
        # Add targets
        if notification_data.target_type == NotificationTargetType.SHOP:
            for shop_id in notification_data.shop_ids:
                target = NotificationShopTarget(
                    notification_id=notification.id,
                    shop_id=shop_id
                )
                db.add(target)
        
        elif notification_data.target_type == NotificationTargetType.STAFF:
            for staff_id in notification_data.staff_ids:
                target = NotificationStaffTarget(
                    notification_id=notification.id,
                    staff_id=staff_id
                )
                db.add(target)
        
        db.commit()
        db.refresh(notification)
        return notification
    
    @staticmethod
    def get_staff_notifications(
        db: Session,
        staff: Staff,
        include_read: bool = False,
        limit: int = 50
    ) -> List[dict]:
        """Get notifications for staff (shop-based + direct)"""
        
        # Query notifications targeted to staff's shop OR directly to staff
        query = db.query(Notification).filter(
            or_(
                # Shop notifications
                and_(
                    Notification.target_type == NotificationTargetType.SHOP,
                    Notification.id.in_(
                        db.query(NotificationShopTarget.notification_id).filter(
                            NotificationShopTarget.shop_id == staff.shop_id
                        )
                    )
                ),
                # Direct staff notifications
                and_(
                    Notification.target_type == NotificationTargetType.STAFF,
                    Notification.id.in_(
                        db.query(NotificationStaffTarget.notification_id).filter(
                            NotificationStaffTarget.staff_id == staff.id
                        )
                    )
                )
            )
        )
        
        # Filter expired
        query = query.filter(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        # Get read status
        read_notif_ids = db.query(NotificationRead.notification_id).filter(
            NotificationRead.staff_id == staff.id
        ).all()
        read_notif_ids = [nid[0] for nid in read_notif_ids]
        
        if not include_read:
            query = query.filter(~Notification.id.in_(read_notif_ids))
        
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        # Add read status
        result = []
        for notif in notifications:
            read_record = db.query(NotificationRead).filter(
                NotificationRead.notification_id == notif.id,
                NotificationRead.staff_id == staff.id
            ).first()
            
            result.append({
                "notification": notif,
                "is_read": read_record is not None,
                "read_at": read_record.read_at if read_record else None
            })
        
        return result
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int, staff: Staff):
        """Mark notification as read"""
        existing = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id,
            NotificationRead.staff_id == staff.id
        ).first()
        
        if not existing:
            read_record = NotificationRead(
                notification_id=notification_id,
                staff_id=staff.id,
                staff_name=staff.name,  # Audit trail
                shop_id=staff.shop_id  # Shop-level filtering
            )
            db.add(read_record)
            db.commit()
    
    @staticmethod
    def get_notification_stats(db: Session, notification_id: int) -> dict:
        """Get read statistics for notification"""
        notification = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return None
        
        # Count total recipients
        if notification.target_type == NotificationTargetType.SHOP:
            shop_ids = db.query(NotificationShopTarget.shop_id).filter(
                NotificationShopTarget.notification_id == notification_id
            ).all()
            shop_ids = [sid[0] for sid in shop_ids]
            total_recipients = db.query(Staff).filter(
                Staff.shop_id.in_(shop_ids),
                Staff.is_active == True
            ).count()
        else:
            total_recipients = db.query(NotificationStaffTarget).filter(
                NotificationStaffTarget.notification_id == notification_id
            ).count()
        
        # Count reads
        total_read = db.query(NotificationRead).filter(
            NotificationRead.notification_id == notification_id
        ).count()
        
        read_percentage = (total_read / total_recipients * 100) if total_recipients > 0 else 0
        
        return {
            "total_recipients": total_recipients,
            "total_read": total_read,
            "read_percentage": round(read_percentage, 2)
        }
    
    @staticmethod
    def get_admin_notifications(
        db: Session,
        admin: Admin,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications sent by admin"""
        return db.query(Notification).filter(
            Notification.admin_id == admin.id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
