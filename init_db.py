from app.database.database import engine, Base
from modules.customer_tracking.models import *
from modules.daily_records.models import *
from modules.stock_audit.models import *

Base.metadata.create_all(bind=engine)
print("✅ Database tables created successfully!")
