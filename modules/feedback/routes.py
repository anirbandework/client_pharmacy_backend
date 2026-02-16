from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from typing import List, Optional
from datetime import datetime
from . import schemas, models
from modules.auth.dependencies import get_current_user as get_user_dict, get_current_admin, get_current_staff, get_current_super_admin
from modules.auth.models import Staff, Admin, SuperAdmin, Shop

router = APIRouter()

# STAFF FEEDBACK
@router.post("/staff/feedback", response_model=schemas.FeedbackResponse)
def submit_staff_feedback(
    feedback: schemas.FeedbackCreate,
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Staff submits feedback"""
    if user_dict["token_data"].user_type != "staff":
        raise HTTPException(status_code=403, detail="Staff access required")
    
    staff = user_dict["user"]
    shop = staff.shop
    
    # Get admin info
    admin = db.query(Admin).filter(Admin.id == shop.admin_id).first()
    
    db_feedback = models.Feedback(
        user_type="staff",
        user_id=staff.id,
        user_name=staff.name,
        user_phone=staff.phone,
        user_email=staff.email,
        shop_id=shop.id,
        shop_name=shop.shop_name,
        shop_location=shop.address,
        organization_id=admin.organization_id if admin else None,
        admin_name=admin.full_name if admin else None,
        admin_phone=admin.phone if admin else None,
        **feedback.model_dump()
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

# ADMIN FEEDBACK
@router.post("/admin/feedback", response_model=schemas.FeedbackResponse)
def submit_admin_feedback(
    feedback: schemas.FeedbackCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Admin submits feedback"""
    db_feedback = models.Feedback(
        user_type="admin",
        user_id=admin.id,
        user_name=admin.full_name,
        user_phone=admin.phone,
        user_email=admin.email,
        organization_id=admin.organization_id,
        **feedback.model_dump()
    )
    
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

# GET USER'S OWN FEEDBACK
@router.get("/my-feedback", response_model=List[schemas.FeedbackResponse])
def get_my_feedback(
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get current user's feedback history"""
    user_type = user_dict["token_data"].user_type
    user_id = user_dict["user"].id
    
    return db.query(models.Feedback).filter(
        models.Feedback.user_type == user_type,
        models.Feedback.user_id == user_id
    ).order_by(models.Feedback.created_at.desc()).all()

# GET UNREAD RESPONSES COUNT
@router.get("/my-feedback/unread-count")
def get_unread_responses_count(
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Get count of feedback with new responses from SuperAdmin"""
    user_type = user_dict["token_data"].user_type
    user_id = user_dict["user"].id
    
    # Count feedback that has admin_response but status is not 'closed'
    unread = db.query(models.Feedback).filter(
        models.Feedback.user_type == user_type,
        models.Feedback.user_id == user_id,
        models.Feedback.admin_response.isnot(None),
        models.Feedback.status != "closed"
    ).count()
    
    return {"unread_responses": unread}

# MARK FEEDBACK AS READ
@router.put("/my-feedback/{feedback_id}/mark-read")
def mark_feedback_as_read(
    feedback_id: int,
    db: Session = Depends(get_db),
    user_dict: dict = Depends(get_user_dict)
):
    """Mark feedback as read/closed after viewing response"""
    user_type = user_dict["token_data"].user_type
    user_id = user_dict["user"].id
    
    feedback = db.query(models.Feedback).filter(
        models.Feedback.id == feedback_id,
        models.Feedback.user_type == user_type,
        models.Feedback.user_id == user_id
    ).first()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.status = "closed"
    feedback.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Feedback marked as read"}

# SUPERADMIN - VIEW ALL FEEDBACK
@router.get("/super-admin/all-feedback", response_model=List[schemas.FeedbackResponse])
def get_all_feedback(
    status: Optional[str] = None,
    feedback_type: Optional[str] = None,
    user_type: Optional[str] = None,
    organization_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin views all feedback with filters"""
    query = db.query(models.Feedback)
    
    if status:
        query = query.filter(models.Feedback.status == status)
    if feedback_type:
        query = query.filter(models.Feedback.feedback_type == feedback_type)
    if user_type:
        query = query.filter(models.Feedback.user_type == user_type)
    if organization_id:
        query = query.filter(models.Feedback.organization_id == organization_id)
    
    return query.order_by(models.Feedback.created_at.desc()).offset(skip).limit(limit).all()

# SUPERADMIN - RESPOND TO FEEDBACK
@router.put("/super-admin/feedback/{feedback_id}", response_model=schemas.FeedbackResponse)
def respond_to_feedback(
    feedback_id: int,
    update: schemas.FeedbackUpdate,
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """SuperAdmin responds to feedback"""
    feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    if update.status:
        feedback.status = update.status
    if update.priority:
        feedback.priority = update.priority
    if update.admin_response:
        feedback.admin_response = update.admin_response
        feedback.responded_by = super_admin.full_name
        feedback.responded_at = datetime.utcnow()
    
    feedback.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(feedback)
    return feedback

# SUPERADMIN - FEEDBACK STATS
@router.get("/super-admin/feedback-stats")
def get_feedback_stats(
    super_admin: SuperAdmin = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Get feedback statistics"""
    total = db.query(models.Feedback).count()
    pending = db.query(models.Feedback).filter(models.Feedback.status == "pending").count()
    resolved = db.query(models.Feedback).filter(models.Feedback.status == "resolved").count()
    
    by_type = {}
    for ftype in ["feature_request", "bug_report", "improvement", "complaint", "appreciation", "other"]:
        by_type[ftype] = db.query(models.Feedback).filter(models.Feedback.feedback_type == ftype).count()
    
    by_mood = {}
    for mood in ["excited", "happy", "neutral", "frustrated", "angry"]:
        by_mood[mood] = db.query(models.Feedback).filter(models.Feedback.mood == mood).count()
    
    avg_rating = db.query(func.avg(models.Feedback.satisfaction_rating)).filter(
        models.Feedback.satisfaction_rating.isnot(None)
    ).scalar() or 0
    
    return {
        "total_feedback": total,
        "pending": pending,
        "resolved": resolved,
        "by_type": by_type,
        "by_mood": by_mood,
        "average_satisfaction": round(float(avg_rating), 2),
        "recommendation_rate": round(
            (db.query(models.Feedback).filter(models.Feedback.would_recommend == True).count() / total * 100) if total > 0 else 0,
            2
        )
    }
