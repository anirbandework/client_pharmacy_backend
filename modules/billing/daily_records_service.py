from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from .daily_records_models import DailyRecord, DailyExpense
from .models import Bill, PaymentMethod
from datetime import date, datetime
from typing import Optional, Dict, Any

class DailyRecordsService:
    
    @staticmethod
    def get_or_create_daily_record(
        db: Session,
        shop_id: int,
        record_date: date,
        staff_id: int,
        staff_name: str
    ) -> DailyRecord:
        """Get existing or create new daily record"""
        record = db.query(DailyRecord).filter(
            DailyRecord.shop_id == shop_id,
            DailyRecord.record_date == record_date
        ).first()
        
        if not record:
            record = DailyRecord(
                shop_id=shop_id,
                record_date=record_date,
                staff_id=staff_id,
                staff_name=staff_name
            )
            db.add(record)
            db.flush()
        
        return record
    
    @staticmethod
    def calculate_daily_figures(db: Session, shop_id: int, record_date: date) -> Dict[str, Any]:
        """Calculate daily figures from bills"""
        start_datetime = datetime.combine(record_date, datetime.min.time())
        end_datetime = datetime.combine(record_date, datetime.max.time())
        
        bills = db.query(Bill).filter(
            Bill.shop_id == shop_id,
            Bill.created_at >= start_datetime,
            Bill.created_at <= end_datetime
        ).all()
        
        no_of_bills = len(bills)
        software_sales = sum(b.total_amount for b in bills)
        cash_sales = sum(b.total_amount for b in bills if b.payment_method == PaymentMethod.CASH)
        online_sales = sum(b.total_amount for b in bills if b.payment_method == PaymentMethod.ONLINE)
        
        return {
            "no_of_bills": no_of_bills,
            "software_sales": float(software_sales),
            "cash_sales": float(cash_sales),
            "online_sales": float(online_sales)
        }
    
    @staticmethod
    def update_daily_record(
        db: Session,
        shop_id: int,
        record_date: date,
        staff_id: int,
        staff_name: str,
        data: dict
    ) -> DailyRecord:
        """Update daily record with manual entries"""
        record = DailyRecordsService.get_or_create_daily_record(
            db, shop_id, record_date, staff_id, staff_name
        )
        
        # Update auto-calculated figures
        figures = DailyRecordsService.calculate_daily_figures(db, shop_id, record_date)
        record.no_of_bills = figures["no_of_bills"]
        record.software_sales = figures["software_sales"]
        record.cash_sales = figures["cash_sales"]
        record.online_sales = figures["online_sales"]
        
        # Update manual entries
        if "unbilled_amount" in data:
            record.unbilled_amount = data["unbilled_amount"]
        if "unbilled_notes" in data:
            record.unbilled_notes = data["unbilled_notes"]
        if "actual_cash_deposited" in data:
            record.actual_cash_deposited = data["actual_cash_deposited"]
        if "cash_reserve" in data:
            record.cash_reserve = data["cash_reserve"]
        
        record.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
        
        return record
    
    @staticmethod
    def add_expense(
        db: Session,
        shop_id: int,
        daily_record_id: int,
        expense_data: dict,
        staff_id: int = None,
        staff_name: str = None
    ) -> DailyExpense:
        """Add expense to daily record"""
        expense = DailyExpense(
            shop_id=shop_id,
            daily_record_id=daily_record_id,
            staff_id=staff_id,
            staff_name=staff_name,
            **expense_data
        )
        db.add(expense)
        
        # Update total expenses in daily record
        record = db.query(DailyRecord).filter(DailyRecord.id == daily_record_id).first()
        if record:
            total = db.query(func.sum(DailyExpense.amount)).filter(
                DailyExpense.daily_record_id == daily_record_id
            ).scalar() or 0.0
            record.total_expenses = float(total)
        
        db.commit()
        db.refresh(expense)
        return expense
    
    @staticmethod
    def get_daily_record_with_calculations(db: Session, record: DailyRecord) -> Dict[str, Any]:
        """Get daily record with all calculated fields"""
        average_bill = record.software_sales / record.no_of_bills if record.no_of_bills > 0 else 0.0
        total_cash = record.cash_sales
        recorded_sales = record.software_sales + record.unbilled_amount
        total_sales = record.cash_sales + record.online_sales
        difference = recorded_sales - total_sales
        
        # Calculate depositable amount (rounded down to nearest 100)
        depositable_amount = float((int(record.cash_sales) // 100) * 100)
        small_denomination = float(record.cash_sales - depositable_amount)
        
        return {
            **record.__dict__,
            "average_bill": float(average_bill),
            "total_cash": float(total_cash),
            "recorded_sales": float(recorded_sales),
            "total_sales": float(total_sales),
            "difference": float(difference),
            "reserve_balance": float(record.cash_reserve),
            "depositable_amount": depositable_amount,
            "small_denomination": small_denomination,
            "expenses": record.expenses
        }
