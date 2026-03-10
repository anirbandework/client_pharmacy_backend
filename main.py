from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

from modules.customer_tracking.routes import router as customer_router
from modules.invoice_analyzer.routes import router as invoice_router
from modules.invoice_analyzer.template_routes import router as invoice_template_router
from modules.invoice_analyzer.admin_analytics_routes import router as invoice_admin_analytics_router
from modules.invoice_analyzer.admin_routes import router as invoice_admin_router
from modules.invoice_analyzer.public_routes import router as invoice_public_router
from modules.invoice_analyzer.autocomplete_routes import router as invoice_autocomplete_router
from modules.invoice_analyzer.margin_playground_routes import router as invoice_analytics_router
from modules.invoice_analyzer.pricing_routes import router as invoice_pricing_router
from modules.stock_audit.routes import router as stock_router
from modules.profit_analysis.routes import router as profit_router
from modules.auth.routes import router as auth_router
from modules.auth.distributor.routes import router as distributor_router
from modules.distributor_invoice.routes import router as distributor_invoice_router
from modules.auth.salary_management.routes import router as salary_router
from modules.auth.attendance.routes import router as attendance_router
from modules.auth.rbac.routes import router as rbac_router
from modules.notifications.routes import router as notifications_router
from modules.feedback.routes import router as feedback_router
from modules.billing.routes import router as billing_router
from modules.billing.daily_records_routes import router as billing_daily_records_router
from modules.billing.analytics_routes import router as billing_analytics_router
from modules.billing.shop_config_routes import router as shop_config_router
from modules.billing.admin_config_routes import router as admin_config_router
from modules.billing.admin_analytics_routes import router as billing_admin_analytics_router
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
from modules.distributor_invoice.models import DistributorInvoice, DistributorInvoiceItem
from modules.feedback.models import Feedback
from modules.auth.rbac.models import Module, OrganizationModulePermission

# Create all tables
Base.metadata.create_all(bind=engine)

# Seed SuperAdmins on startup (production only)
import os
import sys
import importlib.util

if os.getenv('ENVIRONMENT') == 'production':
    try:
        # Load seed_superadmins module dynamically
        seed_path = os.path.join(os.path.dirname(__file__), 'super-admin', 'seed_superadmins.py')
        spec = importlib.util.spec_from_file_location("seed_superadmins", seed_path)
        seed_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(seed_module)
        seed_module.seed_superadmins()
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

# Custom validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to user-friendly messages"""
    errors = exc.errors()
    
    # Extract the first error for simplicity
    if errors:
        error = errors[0]
        field = error.get('loc', [])[-1] if error.get('loc') else 'field'
        msg = error.get('msg', 'Validation error')
        
        # Clean up the error message
        if 'Value error,' in msg:
            msg = msg.replace('Value error, ', '')
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": msg,
                "field": field,
                "message": msg  # For backward compatibility
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "message": "Invalid input data"}
    )

# CORS Configuration
allowed_origins = [
    "http://localhost:5173",  # Local Vite dev
    "http://localhost:3000",  # Alternative local
    "https://client-pharmacy-frontend.vercel.app",  # Old Vercel
    "https://xyz.com",  # Production domain
    "https://www.xyz.com",  # Production domain with www
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
app.include_router(distributor_router, prefix="/api/auth/distributors", tags=["Distributors"])
app.include_router(distributor_invoice_router, tags=["Distributor Invoices"])
app.include_router(rbac_router, prefix="/api/rbac", tags=["RBAC"])
app.include_router(salary_router, prefix="/api/salary", tags=["Salary Management"])
app.include_router(attendance_router, prefix="/api/attendance", tags=["Attendance System"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(feedback_router, prefix="/api/feedback", tags=["Feedback System"])
app.include_router(customer_router, prefix="/api/customer-tracking", tags=["Customer Tracking"])
app.include_router(invoice_public_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice - Public"])
app.include_router(invoice_template_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Analyzer"])
app.include_router(invoice_admin_analytics_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Analytics - Admin"])
app.include_router(invoice_admin_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice - Admin Verification"])
app.include_router(invoice_autocomplete_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Autocomplete"])
app.include_router(invoice_pricing_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Pricing"])
app.include_router(invoice_analytics_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Analytics"])
app.include_router(invoice_router, prefix="/api/purchase-invoices", tags=["Purchase Invoice Analyzer"])
app.include_router(stock_router, prefix="/api/stock-audit", tags=["Stock Audit"])
app.include_router(billing_router, prefix="/api/billing", tags=["Billing System"])
app.include_router(billing_daily_records_router, prefix="/api/billing", tags=["Daily Records"])
app.include_router(billing_analytics_router, prefix="/api/billing", tags=["Analytics"])
app.include_router(shop_config_router, prefix="/api/billing", tags=["Shop Config"])
app.include_router(admin_config_router, prefix="/api/billing", tags=["Admin Config"])
app.include_router(billing_admin_analytics_router, prefix="/api/billing", tags=["Admin Analytics"])
app.include_router(profit_router, prefix="/api/profit", tags=["Profit Analysis"])

# Start attendance scheduler for stale session detection
start_scheduler()

# Mount static files for uploads
os.makedirs("uploads/qr_codes", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("shutdown")
def shutdown_event():
    shutdown_scheduler()

@app.get("/")
async def root():
    return {"message": "Pharmacy Management System - Modular API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "modules": ["auth", "rbac", "salary_management", "attendance", "notifications", "feedback", "customer_tracking", "purchase_invoice_analyzer", "stock_audit", "billing", "profit_analysis"]}

@app.get("/modules")
async def list_modules():
    return {
        "modules": {
            "auth": "Multi-tenant authentication with admin/shop/staff hierarchy",
            "rbac": "Role-based access control with dynamic module permissions per organization",
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