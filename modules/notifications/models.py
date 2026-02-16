from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base
import enum

class NotificationType(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    ANNOUNCEMENT = "announcement"

class NotificationTargetType(str, enum.Enum):
    SHOP = "shop"  # All staff in shop
    STAFF = "staff"  # Specific staff members

class Notification(Base):
    """Notifications sent by admins"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Sender info
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False)
    admin_name = Column(String, nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), default=NotificationType.INFO)
    
    # Target
    target_type = Column(SQLEnum(NotificationTargetType), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiry
    
    # Relationships
    admin = relationship("Admin", foreign_keys=[admin_id])
    shop_targets = relationship("NotificationShopTarget", back_populates="notification", cascade="all, delete-orphan")
    staff_targets = relationship("NotificationStaffTarget", back_populates="notification", cascade="all, delete-orphan")
    reads = relationship("NotificationRead", back_populates="notification", cascade="all, delete-orphan")

class NotificationShopTarget(Base):
    """Shops targeted by notification"""
    __tablename__ = "notification_shop_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    
    notification = relationship("Notification", back_populates="shop_targets")
    shop = relationship("Shop")

class NotificationStaffTarget(Base):
    """Staff members targeted by notification"""
    __tablename__ = "notification_staff_targets"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    
    notification = relationship("Notification", back_populates="staff_targets")
    staff = relationship("Staff")

class NotificationRead(Base):
    """Track which staff have read notifications"""
    __tablename__ = "notification_reads"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    read_at = Column(DateTime, default=datetime.utcnow)
    
    notification = relationship("Notification", back_populates="reads")
    staff = relationship("Staff")
