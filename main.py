from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from modules.customer_tracking.routes import router as customer_router
from modules.invoice_analyzer.routes import router as invoice_router
from modules.stock_audit.routes import router as stock_router
from modules.daily_records.routes import router as daily_records_router
from modules.profit_analysis.routes import router as profit_router
from modules.auth.routes import router as auth_router
from modules.auth.salary_management.routes import router as salary_router
from modules.auth.attendance.routes import router as attendance_router
from modules.notifications.routes import router as notifications_router
from modules.auth.middleware import ShopContextMiddleware
from app.core.config import settings
from app.database.database import engine, Base
from modules.daily_records.models import DailyRecord, RecordModification
from modules.customer_tracking.models import *
from modules.stock_audit.models import *
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
app.include_router(customer_router, prefix="/api/customers", tags=["Customer Tracking"])
app.include_router(invoice_router, prefix="/api/invoices", tags=["Purchase Invoice Analyzer"])
app.include_router(stock_router, prefix="/api/stock", tags=["Stock Audit"])
app.include_router(daily_records_router, prefix="/api/daily-records", tags=["Daily Records"])
app.include_router(profit_router, prefix="/api/profit", tags=["Profit Analysis"])

@app.get("/")
async def root():
    return {"message": "Pharmacy Management System - Modular API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "modules": ["auth", "salary_management", "attendance", "notifications", "customer_tracking", "invoice_analyzer", "stock_audit", "daily_records", "profit_analysis"]}

@app.get("/modules")
async def list_modules():
    return {
        "modules": {
            "auth": "Multi-tenant authentication with admin/shop/staff hierarchy",
            "salary_management": "Staff salary management with payment tracking, QR codes, and automated alerts",
            "attendance": "WiFi-based automatic attendance tracking with real-time monitoring and leave management",
            "notifications": "Admin-to-staff notification system with shop-level and direct messaging",
            "customer_tracking": "Regular customer tracking with reminders",
            "invoice_analyzer": "Purchase invoice tracking with AI-powered movement analysis, expiry alerts, and color-coded status monitoring",
            "stock_audit": "Random section auditing with discrepancy tracking",
            "daily_records": "Robust daily business recording with modification tracking",
            "profit_analysis": "Bill-wise profit margin calculation"
        }
    }