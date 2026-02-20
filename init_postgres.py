#!/usr/bin/env python3
"""Initialize PostgreSQL database with all tables"""

import os
os.environ["DATABASE_URL"] = "postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db"

from app.database.database import Base, engine
from modules.auth.models import SuperAdmin, Admin, Shop, Staff
from modules.auth.otp.models import OTPVerification
from modules.auth.salary_management.models import SalaryRecord, StaffPaymentInfo, SalaryAlert
from modules.auth.attendance.models import ShopWiFi, StaffDevice, AttendanceRecord, AttendanceSettings, LeaveRequest
from modules.notifications.models import Notification, NotificationShopTarget, NotificationStaffTarget, NotificationRead
from modules.stock_audit.models import StockRack, StockSection, StockItem, Purchase, PurchaseItem, Sale, SaleItem, StockAuditRecord, StockAuditSession, StockAdjustment
from modules.billing.models import Bill, BillItem
from modules.billing.daily_records_models import DailyRecord as BillingDailyRecord, DailyExpense
from modules.customer_tracking.models import *
from modules.invoice_analyzer.models import *
from modules.feedback.models import Feedback

print("🔧 Creating all tables in PostgreSQL...")
Base.metadata.create_all(bind=engine)
print("✅ All tables created successfully!")
print("\n📊 Database ready at: postgresql://pharmacy_user:pharmacy_pass@localhost:5432/pharmacy_db")
