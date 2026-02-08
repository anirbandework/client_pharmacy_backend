import os
from app.database.database import engine, Base
from modules.customer_tracking.models import *
from modules.daily_records.models import *
from modules.stock_audit.models import *

db_path = "pharmacy.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Removed: {db_path}")

Base.metadata.create_all(bind=engine)
print("✅ Database reset complete!")
