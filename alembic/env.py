from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.database.database import Base
import os

# Import all models
from modules.auth.models import SuperAdmin, Admin, Shop, Staff
from modules.auth.otp.models import OTPVerification
from modules.auth.salary_management.models import SalaryRecord, StaffPaymentInfo, SalaryAlert
from modules.auth.attendance.models import ShopWiFi, StaffDevice, AttendanceRecord, AttendanceSettings, LeaveRequest
from modules.notifications.models import Notification, NotificationShopTarget, NotificationStaffTarget, NotificationRead
from modules.stock_audit.models import StockRack, StockSection, StockItem, Purchase, PurchaseItem, Sale, SaleItem, StockAuditRecord, StockAuditSession, StockAdjustment
from modules.billing.models import Bill, BillItem
from modules.billing.daily_records_models import DailyRecord as BillingDailyRecord, DailyExpense

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with DATABASE_URL from environment (for Railway)
if os.getenv("DATABASE_URL"):
    database_url = os.getenv("DATABASE_URL")
    # Fix Railway's postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
