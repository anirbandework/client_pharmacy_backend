from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FeedbackCreate(BaseModel):
    feedback_type: str  # feature_request, bug_report, improvement, complaint, appreciation, other
    mood: str  # excited, happy, neutral, frustrated, angry
    title: str
    message: str
    would_recommend: bool = True
    satisfaction_rating: Optional[int] = None  # 1-5

class FeedbackResponse(BaseModel):
    id: int
    user_type: str
    user_id: int
    user_name: str
    user_phone: Optional[str]
    user_email: Optional[str]
    shop_id: Optional[int]
    shop_name: Optional[str]
    shop_location: Optional[str]
    organization_id: Optional[str]
    admin_name: Optional[str]
    admin_phone: Optional[str]
    feedback_type: str
    mood: str
    title: str
    message: str
    would_recommend: bool
    satisfaction_rating: Optional[int]
    priority: str
    status: str
    admin_response: Optional[str]
    responded_by: Optional[str]
    responded_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FeedbackUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    admin_response: Optional[str] = None
