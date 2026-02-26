from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from datetime import datetime

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
from modules.auth.attendance.wifi_middleware import WiFiEnforcementMiddleware
from modules.auth.attendance.scheduler import start_scheduler, shutdown_scheduler
from app.middleware.rate_limit import RateLimitMiddleware
from app.core.config import settings
from app.database.database import engine, Base
from modules.customer_tracking.models import (
    ContactRecord, ContactInteraction, ContactReminder,
    Customer, CustomerPurchase, RefillReminder
)
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
from modules.invoice_analyzer.models import PurchaseInvoice, PurchaseInvoiceItem
from modules.feedback.models import Feedback

# Create all tables
Base.metadata.create_all(bind=engine)

# Seed SuperAdmins on startup (production only)
import os
if os.getenv('ENVIRONMENT') == 'production':
    from seed_superadmins import seed_superadmins
    try:
        seed_superadmins()
    except Exception as e:
        print(f"Warning: Could not seed SuperAdmins: {e}")

# Custom JSON encoder to append 'Z' to datetime strings
class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return super().render(
            jsonable_encoder(
                content,
                custom_encoder={
                    datetime: lambda v: v.isoformat() + 'Z' if v else None
                }
            )
        )

app = FastAPI(
    title="Pharmacy Management System",
    description="Modular microservice for pharmacy operations",
    version="2.0.0",
    default_response_class=CustomJSONResponse
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

# WiFi enforcement middleware (must be after auth middleware)
app.add_middleware(WiFiEnforcementMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Module routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(salary_router, prefix="/api/salary", tags=["Salary Management"])
app.include_router(attendance_router, prefix="/api/attendance", tags=["Attendance System"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback System"])
app.include_router(customer_router, prefix="/api/customer-tracking", tags=["Customer Tracking"])
app.include_router(invoice_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Analyzer"])
app.include_router(stock_router, prefix="/api/stock-audit", tags=["Stock Audit"])
app.include_router(billing_router, prefix="/api/billing", tags=["Billing System"])
app.include_router(billing_daily_records_router, prefix="/api/billing", tags=["Daily Records"])
app.include_router(billing_analytics_router, prefix="/api/billing", tags=["Analytics"])
app.include_router(profit_router, prefix="/api/profit", tags=["Profit Analysis"])

# Start attendance scheduler for stale session detection
start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()

@app.get("/")
async def root():
    return {"message": "Pharmacy Management System - Modular API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "modules": ["auth", "salary_management", "attendance", "notifications", "feedback", "customer_tracking", "purchase_invoice_analyzer", "stock_audit", "billing", "profit_analysis"]}

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
            "invoice_analyzer": "PDF-based purchase invoice analyzer with automatic data extraction, supplier tracking, and item-wise GST details",
            "stock_audit": "Random section auditing with discrepancy tracking",
            "billing": "Customer billing system with medicine search, stock integration, payment tracking (cash/online), and daily business records",
            "profit_analysis": "Bill-wise profit margin calculation"
        }
    }