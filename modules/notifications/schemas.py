from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from .models import NotificationType, NotificationTargetType

class NotificationCreate(BaseModel):
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    target_type: NotificationTargetType
    shop_ids: Optional[List[int]] = []  # For shop targets
    staff_ids: Optional[List[int]] = []  # For staff targets
    expires_at: Optional[datetime] = None
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class NotificationResponse(BaseModel):
    id: int
    admin_id: int
    admin_name: str
    title: str
    message: str
    type: NotificationType
    target_type: NotificationTargetType
    created_at: datetime
    expires_at: Optional[datetime]
    is_read: bool = False
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class NotificationStats(BaseModel):
    total_sent: int
    total_recipients: int
    total_read: int
    read_percentage: float

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int
    total_count: int
