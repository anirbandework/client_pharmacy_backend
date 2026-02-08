"""Create all database tables"""

from app.database.database import engine, Base
from modules.auth.models import Admin, Shop, Staff
from modules.customer_tracking.models import *
from modules.daily_records.models import DailyRecord, RecordModification
from modules.stock_audit.models import *

print("Creating all database tables...")
Base.metadata.create_all(bind=engine)
print("✓ All tables created successfully!")
