from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from modules.customer_tracking.routes import router as customer_router
from modules.invoice_analyzer.routes import router as invoice_router
from modules.stock_audit.routes import router as stock_router
from modules.profit_analysis.routes import router as profit_router
from modules.auth.routes import router as auth_router
from modules.auth.salary_management.routes import router as salary_router
from modules.auth.attendance.routes import router as attendance_router
from modules.notifications.routes import router as notifications_router
from modules.feedback.routes import router as feedback_router
from modules.billing.routes import router as billing_router
from modules.billing.daily_records_routes import router as billing_daily_records_router
from modules.billing.analytics_routes import router as billing_analytics_router
from modules.auth.middleware import ShopContextMiddleware
from app.core.config import settings
from app.database.database import engine, Base
from modules.customer_tracking.models import *
from modules.stock_audit.models import *
from modules.billing.models import Bill, BillItem
from modules.billing.daily_records_models import DailyRecord as BillingDailyRecord, DailyExpense
from modules.auth.models import Admin, Shop, Staff
from modules.auth.otp.models import OTPVerification
from modules.auth.salary_management.models import SalaryRecord, StaffPaymentInfo, SalaryAlert
from modules.auth.attendance.models import (
    ShopWiFi, StaffDevice, AttendanceRecord, 
    AttendanceSettings, LeaveRequest
)
from modules.notifications.models import (
    Notification, NotificationShopTarget, NotificationStaffTarget, NotificationRead
)
from modules.invoice_analyzer.models import (
    PurchaseInvoice, PurchaseInvoiceItem, ItemSale, 
    ExpiryAlert, MonthlyInvoiceSummary
)
from modules.feedback.models import Feedback

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pharmacy Management System",
    description="Modular microservice for pharmacy operations",
    version="2.0.0"
)

# CORS Configuration
allowed_origins = [
    "http://localhost:5173",  # Local Vite dev
    "http://localhost:3000",  # Alternative local
    "https://client-pharmacy-frontend.vercel.app",  # Production Vercel
]

# Allow all Vercel preview deployments
allow_origin_regex = r"https://.*\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shop context middleware
app.add_middleware(ShopContextMiddleware)

# Module routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(salary_router, prefix="/api/salary", tags=["Salary Management"])
app.include_router(attendance_router, prefix="/api/attendance", tags=["Attendance System"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback System"])
app.include_router(customer_router, prefix="/api/customers", tags=["Customer Tracking"])
app.include_router(invoice_router, prefix="/api/invoices", tags=["Purchase Invoice Analyzer"])
app.include_router(stock_router, prefix="/api/stock-audit", tags=["Stock Audit"])
app.include_router(billing_router, prefix="/api/billing", tags=["Billing System"])
app.include_router(billing_daily_records_router, prefix="/api/billing", tags=["Daily Records"])
app.include_router(billing_analytics_router, prefix="/api/billing", tags=["Analytics"])
app.include_router(profit_router, prefix="/api/profit", tags=["Profit Analysis"])

@app.get("/")
async def root():
    return {"message": "Pharmacy Management System - Modular API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "modules": ["auth", "salary_management", "attendance", "notifications", "feedback", "customer_tracking", "invoice_analyzer", "stock_audit", "billing", "profit_analysis"]}

@app.get("/modules")
async def list_modules():
    return {
        "modules": {
            "auth": "Multi-tenant authentication with admin/shop/staff hierarchy",
            "salary_management": "Staff salary management with payment tracking, QR codes, and automated alerts",
            "attendance": "WiFi-based automatic attendance tracking with real-time monitoring and leave management",
            "notifications": "Admin-to-staff notification system with shop-level and direct messaging",
            "feedback": "Engaging feedback system with mood tracking, ratings, and priority management for admins and staff",
            "customer_tracking": "Regular customer tracking with reminders",
            "invoice_analyzer": "Purchase invoice tracking with AI-powered movement analysis, expiry alerts, and color-coded status monitoring",
            "stock_audit": "Random section auditing with discrepancy tracking",
            "billing": "Customer billing system with medicine search, stock integration, payment tracking (cash/online), and daily business records",
            "profit_analysis": "Bill-wise profit margin calculation"
        }
    }