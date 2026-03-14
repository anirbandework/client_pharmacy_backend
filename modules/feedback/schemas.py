from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime

VALID_FEEDBACK_TYPES = {"feature_request", "bug_report", "improvement", "complaint", "appreciation", "other"}
VALID_MOODS = {"excited", "happy", "neutral", "frustrated", "angry"}

class FeedbackCreate(BaseModel):
    feedback_type: str
    mood: str
    title: str
    message: str
    would_recommend: bool = True
    satisfaction_rating: Optional[int] = None  # 1-5

    @field_validator("feedback_type")
    @classmethod
    def validate_feedback_type(cls, v):
        if v not in VALID_FEEDBACK_TYPES:
            raise ValueError(f"feedback_type must be one of: {', '.join(sorted(VALID_FEEDBACK_TYPES))}")
        return v

    @field_validator("mood")
    @classmethod
    def validate_mood(cls, v):
        if v not in VALID_MOODS:
            raise ValueError(f"mood must be one of: {', '.join(sorted(VALID_MOODS))}")
        return v

    @field_validator("satisfaction_rating")
    @classmethod
    def validate_rating(cls, v):
        if v is not None and v not in range(1, 6):
            raise ValueError("satisfaction_rating must be between 1 and 5")
        return v

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
