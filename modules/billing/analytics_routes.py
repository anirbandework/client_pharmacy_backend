from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from datetime import date, timedelta
from typing import List, Dict, Any
from .daily_records_models import DailyRecord, DailyExpense
from .models import Bill
from modules.auth.dependencies import get_current_user as get_user_dict
from modules.auth.models import Staff, Shop

def get_current_user(user_dict: dict = Depends(get_user_dict), db: Session = Depends(get_db)) -> tuple[Staff, int]:
    """Extract staff user from auth dict and resolve shop_id"""
    staff = user_dict["user"]
    shop_code = user_dict["token_data"].shop_code
    shop = db.query(Shop).filter(
        Shop.shop_code == shop_code,
        Shop.organization_id == staff.shop.organization_id
    ).first()
    return staff, shop.id

router = APIRouter()

@router.get("/analytics/overview")
def get_analytics_overview(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Get comprehensive analytics overview"""
    staff, shop_id = current_user
    
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    # Get daily records
    records = db.query(DailyRecord).filter(
        DailyRecord.shop_id == shop_id,
        DailyRecord.record_date >= start_date,
        DailyRecord.record_date <= end_date
    ).order_by(DailyRecord.record_date).all()
    
    if not records:
        return {"message": "No data available", "data": {}}
    
    # Calculate metrics
    total_sales = sum(r.cash_sales + r.online_sales for r in records)
    total_bills = sum(r.no_of_bills for r in records)
    total_expenses = sum(r.total_expenses for r in records)
    avg_daily_sales = total_sales / len(records) if records else 0
    avg_bills_per_day = total_bills / len(records) if records else 0
    
    # Trends data
    daily_data = []
    for r in records:
        daily_data.append({
            "date": str(r.record_date),
            "day": r.record_date.strftime('%A'),
            "sales": float(r.cash_sales + r.online_sales),
            "bills": r.no_of_bills,
            "expenses": float(r.total_expenses),
            "cash_sales": float(r.cash_sales),
            "online_sales": float(r.online_sales),
            "average_bill": float(r.cash_sales + r.online_sales) / r.no_of_bills if r.no_of_bills > 0 else 0
        })
    
    # Day-wise analysis
    day_wise = {}
    for r in records:
        day = r.record_date.strftime('%A')
        if day not in day_wise:
            day_wise[day] = {"sales": 0, "bills": 0, "count": 0}
        day_wise[day]["sales"] += float(r.cash_sales + r.online_sales)
        day_wise[day]["bills"] += r.no_of_bills
        day_wise[day]["count"] += 1
    
    day_wise_avg = {
        day: {
            "avg_sales": data["sales"] / data["count"],
            "avg_bills": data["bills"] / data["count"]
        }
        for day, data in day_wise.items()
    }
    
    # Expense breakdown
    expenses = db.query(
        DailyExpense.expense_category,
        func.sum(DailyExpense.amount).label('total')
    ).join(DailyRecord).filter(
        DailyRecord.shop_id == shop_id,
        DailyRecord.record_date >= start_date,
        DailyRecord.record_date <= end_date
    ).group_by(DailyExpense.expense_category).all()
    
    expense_breakdown = [{"category": e[0], "amount": float(e[1])} for e in expenses]
    
    # Simple prediction (linear trend)
    if len(records) >= 7:
        recent_7_days = records[-7:]
        avg_recent = sum(r.cash_sales + r.online_sales for r in recent_7_days) / 7
        prediction_next_7_days = avg_recent * 7
    else:
        prediction_next_7_days = avg_daily_sales * 7
    
    return {
        "summary": {
            "period_days": days,
            "total_sales": round(total_sales, 2),
            "total_bills": total_bills,
            "total_expenses": round(total_expenses, 2),
            "net_revenue": round(total_sales - total_expenses, 2),
            "avg_daily_sales": round(avg_daily_sales, 2),
            "avg_bills_per_day": round(avg_bills_per_day, 2),
            "avg_bill_value": round(total_sales / total_bills, 2) if total_bills > 0 else 0
        },
        "daily_trends": daily_data,
        "day_wise_analysis": day_wise_avg,
        "expense_breakdown": expense_breakdown,
        "predictions": {
            "next_7_days_sales": round(prediction_next_7_days, 2),
            "avg_daily_prediction": round(prediction_next_7_days / 7, 2)
        }
    }

@router.get("/analytics/comparison")
def get_period_comparison(
    current_days: int = Query(30),
    db: Session = Depends(get_db),
    current_user: tuple = Depends(get_current_user)
):
    """Compare current period with previous period"""
    staff, shop_id = current_user
    
    end_date = date.today()
    current_start = end_date - timedelta(days=current_days)
    previous_start = current_start - timedelta(days=current_days)
    
    # Current period
    current_records = db.query(DailyRecord).filter(
        DailyRecord.shop_id == shop_id,
        DailyRecord.record_date >= current_start,
        DailyRecord.record_date <= end_date
    ).all()
    
    # Previous period
    previous_records = db.query(DailyRecord).filter(
        DailyRecord.shop_id == shop_id,
        DailyRecord.record_date >= previous_start,
        DailyRecord.record_date < current_start
    ).all()
    
    def calculate_metrics(records):
        if not records:
            return {"sales": 0, "bills": 0, "expenses": 0}
        return {
            "sales": sum(r.cash_sales + r.online_sales for r in records),
            "bills": sum(r.no_of_bills for r in records),
            "expenses": sum(r.total_expenses for r in records)
        }
    
    current = calculate_metrics(current_records)
    previous = calculate_metrics(previous_records)
    
    def calc_change(curr, prev):
        if prev == 0:
            return 100 if curr > 0 else 0
        return ((curr - prev) / prev) * 100
    
    return {
        "current_period": {
            "days": current_days,
            "sales": round(current["sales"], 2),
            "bills": current["bills"],
            "expenses": round(current["expenses"], 2)
        },
        "previous_period": {
            "days": current_days,
            "sales": round(previous["sales"], 2),
            "bills": previous["bills"],
            "expenses": round(previous["expenses"], 2)
        },
        "changes": {
            "sales_change": round(calc_change(current["sales"], previous["sales"]), 2),
            "bills_change": round(calc_change(current["bills"], previous["bills"]), 2),
            "expenses_change": round(calc_change(current["expenses"], previous["expenses"]), 2)
        }
    }
