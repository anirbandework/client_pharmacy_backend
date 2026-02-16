from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User info
    user_type = Column(String, nullable=False)  # admin or staff
    user_id = Column(Integer, nullable=False)
    user_name = Column(String, nullable=False)
    user_phone = Column(String, nullable=True)
    user_email = Column(String, nullable=True)
    
    # Shop/Organization info
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=True)
    shop_name = Column(String, nullable=True)
    shop_location = Column(String, nullable=True)
    organization_id = Column(String, nullable=True)
    admin_name = Column(String, nullable=True)
    admin_phone = Column(String, nullable=True)
    
    # Feedback content
    feedback_type = Column(String, nullable=False)  # feature_request, bug_report, improvement, complaint, appreciation, other
    mood = Column(String, nullable=False)  # excited, happy, neutral, frustrated, angry
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Engagement features
    would_recommend = Column(Boolean, default=True)
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 stars
    
    # Priority & Status
    priority = Column(String, default="medium")  # low, medium, high, urgent
    status = Column(String, default="pending")  # pending, reviewed, in_progress, resolved, closed
    
    # SuperAdmin response
    admin_response = Column(Text, nullable=True)
    responded_by = Column(String, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shop = relationship("Shop", foreign_keys=[shop_id])
