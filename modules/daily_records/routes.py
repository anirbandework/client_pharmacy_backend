from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from app.database.database import get_db
from datetime import date, datetime, timedelta
from typing import Optional, List
from . import schemas, models, service
from .ai_analytics import DailyRecordsAIAnalytics
from app.core.config import settings
from modules.auth.dependencies import get_current_admin, get_current_staff, get_current_user
import io
import os

def get_shop_context(current_user = Depends(get_current_user)):
    """Get shop context from current user"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        return user.shop_id
    elif token_data.user_type == "admin":
        return None  # Admin can access all shops
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")

router = APIRouter()

# CREATE
@router.post("/", response_model=schemas.DailyRecord)
def create_daily_record(
    record: schemas.DailyRecordCreate, 
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new daily record with automatic calculations"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    # Determine which shop to use
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    # Check if record already exists for this date and shop
    existing = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.date == record.date,
            models.DailyRecord.shop_id == target_shop_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Record already exists for {record.date} in this shop")
    
    record_dict = record.model_dump()
    record_dict['shop_id'] = target_shop_id
    calculated = service.calculate_fields(record_dict)
    record_dict.update(calculated)
    
    db_record = models.DailyRecord(**record_dict)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # Check for cash difference alerts
    if db_record.sales_difference:
        service.check_cash_difference_alert(
            db_record.sales_difference,
            db_record.date,
            db_record.total_sales or 0
        )
    
    return db_record

# READ - Single
@router.get("/{record_id}", response_model=schemas.DailyRecord)
def get_daily_record(
    record_id: int, 
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific daily record by ID"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    record = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.id == record_id,
            models.DailyRecord.shop_id == target_shop_id
        )
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

# READ - By Date
@router.get("/date/{record_date}", response_model=schemas.DailyRecord)
def get_record_by_date(
    record_date: date, 
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get daily record by specific date"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    record = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.date == record_date,
            models.DailyRecord.shop_id == target_shop_id
        )
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"No record found for {record_date} in this shop")
    return record

# READ - List with filters
@router.get("/", response_model=List[schemas.DailyRecord])
def get_daily_records(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all daily records with optional date range filtering"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    query = db.query(models.DailyRecord).filter(models.DailyRecord.shop_id == target_shop_id)
    
    if start_date:
        query = query.filter(models.DailyRecord.date >= start_date)
    if end_date:
        query = query.filter(models.DailyRecord.date <= end_date)
    
    records = query.order_by(models.DailyRecord.date.desc()).offset(skip).limit(limit).all()
    return records

# UPDATE
@router.put("/{record_id}", response_model=schemas.DailyRecord)
def update_daily_record(
    record_id: int,
    record_update: schemas.DailyRecordUpdate,
    modified_by: Optional[str] = Query(None, description="Username of person making the update"),
    db: Session = Depends(get_db)
):
    """Update a daily record with modification tracking"""
    db_record = db.query(models.DailyRecord).filter(models.DailyRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    update_data = record_update.model_dump(exclude_unset=True)
    
    # Track modifications
    service.track_modifications(db, db_record, update_data, record_id, modified_by)
    
    # Update fields
    for field, value in update_data.items():
        setattr(db_record, field, value)
    
    # Recalculate derived fields
    record_dict = {
        'actual_cash': db_record.actual_cash,
        'online_sales': db_record.online_sales,
        'unbilled_sales': db_record.unbilled_sales,
        'software_figure': db_record.software_figure,
        'cash_reserve': db_record.cash_reserve,
        'no_of_bills': db_record.no_of_bills
    }
    calculated = service.calculate_fields(record_dict)
    for field, value in calculated.items():
        setattr(db_record, field, value)
    
    db_record.modified_at = datetime.utcnow()
    db_record.modified_by = modified_by
    db.commit()
    db.refresh(db_record)
    
    # Check for alerts
    if db_record.sales_difference:
        service.check_cash_difference_alert(
            db_record.sales_difference,
            db_record.date,
            db_record.total_sales or 0
        )
    
    return db_record

# DELETE
@router.delete("/{record_id}")
def delete_daily_record(record_id: int, db: Session = Depends(get_db)):
    """Delete a daily record"""
    db_record = db.query(models.DailyRecord).filter(models.DailyRecord.id == record_id).first()
    if not db_record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    db.delete(db_record)
    db.commit()
    return {"message": "Record deleted successfully", "id": record_id}

# MODIFICATIONS
@router.get("/{record_id}/modifications", response_model=List[schemas.RecordModification])
def get_record_modifications(record_id: int, db: Session = Depends(get_db)):
    """Get all modifications for a specific record"""
    record = db.query(models.DailyRecord).filter(models.DailyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    modifications = db.query(models.RecordModification).filter(
        models.RecordModification.daily_record_id == record_id
    ).order_by(models.RecordModification.modified_at.desc()).all()
    
    return modifications

# MONTHLY ANALYTICS
@router.get("/analytics/monthly/{year}/{month}")
def get_monthly_analytics(
    year: int, 
    month: int, 
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive monthly analytics"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    records = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.shop_id == target_shop_id,
            extract('year', models.DailyRecord.date) == year,
            extract('month', models.DailyRecord.date) == month
        )
    ).all()
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for {year}-{month}")
    
    total_sales = sum(r.total_sales or 0 for r in records)
    total_cash = sum(r.actual_cash or 0 for r in records)
    total_online = sum(r.online_sales or 0 for r in records)
    total_unbilled = sum(r.unbilled_sales or 0 for r in records)
    total_expenses = sum(r.expense_amount or 0 for r in records)
    total_reserve = sum(r.cash_reserve or 0 for r in records)
    avg_bill = sum(r.average_bill or 0 for r in records if r.average_bill) / len([r for r in records if r.average_bill]) if records else 0
    total_bills = sum(r.no_of_bills or 0 for r in records)
    
    # Variance analysis
    variances = [r for r in records if r.sales_difference and abs(r.sales_difference) > 50]
    
    return {
        "year": year,
        "month": month,
        "total_days": len(records),
        "total_sales": round(total_sales, 2),
        "total_cash": round(total_cash, 2),
        "total_online": round(total_online, 2),
        "total_unbilled": round(total_unbilled, 2),
        "total_expenses": round(total_expenses, 2),
        "total_cash_reserve": round(total_reserve, 2),
        "average_bill_value": round(avg_bill, 2),
        "total_bills": total_bills,
        "cash_percentage": round((total_cash / total_sales * 100) if total_sales > 0 else 0, 2),
        "online_percentage": round((total_online / total_sales * 100) if total_sales > 0 else 0, 2),
        "variance_days": len(variances),
        "variance_details": [
            {"date": str(r.date), "difference": r.sales_difference}
            for r in variances
        ]
    }

# VARIANCE REPORT
@router.get("/analytics/variances")
def get_variance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    threshold: float = 50.0,
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get records with cash variances exceeding threshold"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    query = db.query(models.DailyRecord).filter(models.DailyRecord.shop_id == target_shop_id)
    
    if start_date:
        query = query.filter(models.DailyRecord.date >= start_date)
    if end_date:
        query = query.filter(models.DailyRecord.date <= end_date)
    
    records = query.all()
    variances = [
        {
            "id": r.id,
            "date": r.date,
            "day": r.day,
            "total_sales": r.total_sales,
            "recorded_sales": r.recorded_sales,
            "difference": r.sales_difference,
            "percentage": round((r.sales_difference / r.recorded_sales * 100) if r.recorded_sales else 0, 2),
            "notes": r.notes
        }
        for r in records
        if r.sales_difference and abs(r.sales_difference) > threshold
    ]
    
    return {
        "threshold": threshold,
        "total_variances": len(variances),
        "variances": sorted(variances, key=lambda x: abs(x['difference']), reverse=True)
    }

# EXCEL IMPORT
@router.post("/import/excel", response_model=schemas.ExcelImportResponse)
async def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import daily records from Excel file (GMTR0003 format)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    
    result = await service.import_excel_data(file, db)
    return result

# EXCEL EXPORT
@router.get("/export/excel/{year}/{month}")
def export_to_excel(
    year: int, 
    month: int, 
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export monthly records to Excel in GMTR0003 format"""
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    records = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.shop_id == target_shop_id,
            extract('year', models.DailyRecord.date) == year,
            extract('month', models.DailyRecord.date) == month
        )
    ).order_by(models.DailyRecord.date).all()
    
    if not records:
        raise HTTPException(status_code=404, detail=f"No records found for {year}-{month}")
    
    excel_file = service.export_to_excel(records, year, month)
    
    return StreamingResponse(
        io.BytesIO(excel_file),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=daily_records_{year}_{month}.xlsx"}
    )

# BULK CREATE
@router.post("/bulk", response_model=List[schemas.DailyRecord])
def bulk_create_records(
    records: List[schemas.DailyRecordCreate],
    db: Session = Depends(get_db)
):
    """Create multiple daily records at once"""
    created_records = []
    
    for record in records:
        existing = db.query(models.DailyRecord).filter(models.DailyRecord.date == record.date).first()
        if existing:
            continue
        
        record_dict = record.model_dump()
        calculated = service.calculate_fields(record_dict)
        record_dict.update(calculated)
        
        db_record = models.DailyRecord(**record_dict)
        db.add(db_record)
        created_records.append(db_record)
    
    db.commit()
    for record in created_records:
        db.refresh(record)
    
    return created_records

# DASHBOARD SUMMARY
@router.get("/analytics/dashboard")
def get_dashboard_summary(
    shop_id: Optional[int] = Query(None, description="Shop ID for admin users"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for last 7 days (shop-specific)"""
    
    token_data = current_user["token_data"]
    user = current_user["user"]
    
    # Determine which shop to query
    if token_data.user_type == "staff":
        target_shop_id = user.shop_id
    elif token_data.user_type == "admin":
        target_shop_id = shop_id
        if not target_shop_id:
            raise HTTPException(status_code=400, detail="Shop ID required for admin users")
    else:
        raise HTTPException(status_code=403, detail="Invalid user type")
    
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    records = db.query(models.DailyRecord).filter(
        and_(
            models.DailyRecord.shop_id == target_shop_id,
            models.DailyRecord.date >= start_date,
            models.DailyRecord.date <= end_date
        )
    ).order_by(models.DailyRecord.date.desc()).all()
    
    if not records:
        return {
            "message": "No recent records found for this shop",
            "shop_id": target_shop_id,
            "latest_record": {"date": None, "total_sales": 0, "difference": 0},
            "last_7_days": {
                "total_sales": 0,
                "average_daily_sales": 0,
                "days_with_variance": 0,
                "total_records": 0
            },
            "recent_records": []
        }
    
    latest = records[0] if records else None
    total_sales_week = sum(r.total_sales or 0 for r in records)
    avg_daily_sales = total_sales_week / len(records) if records else 0
    variances = [r for r in records if r.sales_difference and abs(r.sales_difference) > 50]
    
    return {
        "shop_id": target_shop_id,
        "latest_record": {
            "date": latest.date if latest else None,
            "total_sales": latest.total_sales if latest else 0,
            "difference": latest.sales_difference if latest else 0
        },
        "last_7_days": {
            "total_sales": round(total_sales_week, 2),
            "average_daily_sales": round(avg_daily_sales, 2),
            "days_with_variance": len(variances),
            "total_records": len(records)
        },
        "recent_records": [
            {
                "date": r.date,
                "day": r.day,
                "total_sales": r.total_sales,
                "difference": r.sales_difference
            }
            for r in records[:5]
        ]
    }

# AUDIT LOGS
@router.get("/audit/logs", response_model=schemas.AuditLogResponse)
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive audit logs of all record activities"""
    
    # Get all records with filters
    query = db.query(models.DailyRecord)
    if start_date:
        query = query.filter(models.DailyRecord.created_at >= start_date)
    if end_date:
        query = query.filter(models.DailyRecord.created_at <= end_date)
    
    records = query.order_by(models.DailyRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    logs = []
    for record in records:
        # Creation log
        logs.append(schemas.AuditLog(
            record_id=record.id,
            date=record.date,
            action="created",
            user=record.created_by,
            timestamp=record.created_at,
            changes=None
        ))
        
        # Modification logs
        modifications = db.query(models.RecordModification).filter(
            models.RecordModification.daily_record_id == record.id
        ).order_by(models.RecordModification.modified_at.desc()).all()
        
        for mod in modifications:
            if user and mod.modified_by != user:
                continue
            if action and mod.action != action:
                continue
                
            logs.append(schemas.AuditLog(
                record_id=record.id,
                date=record.date,
                action=mod.action,
                user=mod.modified_by,
                timestamp=mod.modified_at,
                changes=[{
                    "field": mod.field_name,
                    "old_value": mod.old_value,
                    "new_value": mod.new_value
                }]
            ))
    
    # Sort by timestamp
    logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    return schemas.AuditLogResponse(
        total_logs=len(logs),
        logs=logs
    )

@router.get("/audit/users")
def get_audit_users(db: Session = Depends(get_db)):
    """Get list of all users who created or modified records"""
    
    # Get unique creators
    creators = db.query(models.DailyRecord.created_by).distinct().all()
    creators = [c[0] for c in creators if c[0]]
    
    # Get unique modifiers
    modifiers = db.query(models.RecordModification.modified_by).distinct().all()
    modifiers = [m[0] for m in modifiers if m[0]]
    
    # Combine and get unique users
    all_users = list(set(creators + modifiers))
    
    # Get activity count per user
    user_activity = []
    for user in all_users:
        created_count = db.query(models.DailyRecord).filter(
            models.DailyRecord.created_by == user
        ).count()
        
        modified_count = db.query(models.RecordModification).filter(
            models.RecordModification.modified_by == user
        ).count()
        
        user_activity.append({
            "username": user,
            "records_created": created_count,
            "records_modified": modified_count,
            "total_actions": created_count + modified_count
        })
    
    # Sort by total actions
    user_activity.sort(key=lambda x: x["total_actions"], reverse=True)
    
    return {
        "total_users": len(user_activity),
        "users": user_activity
    }

@router.get("/audit/activity/{record_id}")
def get_record_activity(
    record_id: int,
    db: Session = Depends(get_db)
):
    """Get complete activity timeline for a specific record"""
    
    record = db.query(models.DailyRecord).filter(models.DailyRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Get all modifications
    modifications = db.query(models.RecordModification).filter(
        models.RecordModification.daily_record_id == record_id
    ).order_by(models.RecordModification.modified_at.desc()).all()
    
    timeline = []
    
    # Add creation event
    timeline.append({
        "action": "created",
        "user": record.created_by,
        "timestamp": record.created_at,
        "details": f"Record created for {record.date}"
    })
    
    # Add modification events
    for mod in modifications:
        timeline.append({
            "action": mod.action,
            "user": mod.modified_by,
            "timestamp": mod.modified_at,
            "field": mod.field_name,
            "old_value": mod.old_value,
            "new_value": mod.new_value,
            "details": f"Changed {mod.field_name} from {mod.old_value} to {mod.new_value}"
        })
    
    # Sort by timestamp (newest first)
    timeline.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "record_id": record_id,
        "date": record.date,
        "created_by": record.created_by,
        "created_at": record.created_at,
        "last_modified_by": record.modified_by,
        "last_modified_at": record.modified_at,
        "total_modifications": len(modifications),
        "timeline": timeline
    }

# AI ANALYTICS ENDPOINTS

@router.get("/ai-analytics/comprehensive")
async def get_comprehensive_ai_analysis(
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive AI-powered analysis of daily records"""
    from app.core.config import settings
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(settings.gemini_api_key)
    
    try:
        analysis = await ai_analytics.comprehensive_analysis(db, days)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

@router.get("/ai-analytics/trends")
def get_trends_analysis(
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get statistical trends and patterns analysis"""
    from app.core.config import settings
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(settings.gemini_api_key)
    
    try:
        df = ai_analytics.get_records_dataframe(db, days)
        trends = ai_analytics.calculate_trends(df)
        return {
            "analysis_period": f"Last {days} days",
            "data_points": len(df),
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trends analysis failed: {str(e)}")

@router.get("/ai-analytics/predictions")
def get_future_predictions(
    days: int = Query(90, description="Number of days of historical data to use"),
    forecast_days: int = Query(30, description="Number of days to predict ahead"),
    db: Session = Depends(get_db)
):
    """Get AI-powered future predictions"""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(gemini_api_key)
    
    try:
        df = ai_analytics.get_records_dataframe(db, days)
        predictions = ai_analytics.predict_future_trends(df, forecast_days)
        return {
            "historical_period": f"Last {days} days",
            "forecast_period": f"Next {forecast_days} days",
            "predictions": predictions,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Predictions failed: {str(e)}")

@router.get("/ai-analytics/chart-data")
def get_chart_data(
    days: int = Query(90, description="Number of days to include in charts"),
    db: Session = Depends(get_db)
):
    """Get data formatted for frontend charts and visualizations"""
    from app.core.config import settings
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(settings.gemini_api_key)
    
    try:
        df = ai_analytics.get_records_dataframe(db, days)
        chart_data = ai_analytics.generate_chart_data(df)
        return {
            "period": f"Last {days} days",
            "data_points": len(df),
            "charts": chart_data,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chart data generation failed: {str(e)}")

@router.get("/ai-analytics/insights")
async def get_ai_insights(
    days: int = Query(90, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get AI-generated business insights and recommendations"""
    from app.core.config import settings
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(settings.gemini_api_key)
    
    try:
        df = ai_analytics.get_records_dataframe(db, days)
        trends = ai_analytics.calculate_trends(df)
        predictions = ai_analytics.predict_future_trends(df)
        insights = await ai_analytics.generate_ai_insights(trends, predictions)
        
        return {
            "analysis_period": f"Last {days} days",
            "insights": insights,
            "data_quality": {
                "total_records": len(df),
                "completeness": (df.notna().sum().sum() / (len(df) * len(df.columns))) * 100 if not df.empty else 0,
                "date_range": {
                    "start": df['date'].min().isoformat() if not df.empty else None,
                    "end": df['date'].max().isoformat() if not df.empty else None
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI insights generation failed: {str(e)}")

@router.get("/ai-analytics/dashboard")
async def get_ai_dashboard(
    db: Session = Depends(get_db)
):
    """Get AI-powered dashboard with key metrics, trends, and insights"""
    from app.core.config import settings
    
    if not settings.gemini_api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    ai_analytics = DailyRecordsAIAnalytics(settings.gemini_api_key)
    
    try:
        # Get comprehensive analysis for dashboard
        analysis = await ai_analytics.comprehensive_analysis(db, 30)  # Last 30 days for dashboard
        
        # Extract key dashboard metrics
        dashboard_data = {
            "summary": analysis.get("analysis_summary", {}),
            "key_metrics": {
                "avg_daily_sales": analysis.get("trends", {}).get("sales_trend", {}).get("avg_daily_sales", 0),
                "sales_growth_rate": analysis.get("trends", {}).get("sales_trend", {}).get("sales_growth_rate", 0),
                "cash_accuracy_rate": analysis.get("trends", {}).get("cash_trend", {}).get("cash_accuracy_rate", 0),
                "avg_bill_value": analysis.get("trends", {}).get("bill_patterns", {}).get("avg_bill_value", 0)
            },
            "predictions": analysis.get("predictions", {}),
            "chart_data": analysis.get("chart_data", {}),
            "ai_insights": analysis.get("ai_insights", {}),
            "data_quality": analysis.get("data_quality", {}),
            "alerts": []
        }
        
        # Add alerts based on analysis
        trends = analysis.get("trends", {})
        if trends.get("cash_trend", {}).get("cash_accuracy_rate", 100) < 80:
            dashboard_data["alerts"].append({
                "type": "warning",
                "message": "Cash accuracy rate is below 80%",
                "priority": "high"
            })
        
        if trends.get("sales_trend", {}).get("sales_growth_rate", 0) < 0:
            dashboard_data["alerts"].append({
                "type": "danger",
                "message": "Negative sales growth trend detected",
                "priority": "critical"
            })
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI dashboard generation failed: {str(e)}")