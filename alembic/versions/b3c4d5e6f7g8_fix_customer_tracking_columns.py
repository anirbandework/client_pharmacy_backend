"""fix_customer_tracking_columns

Revision ID: b3c4d5e6f7g8
Revises: 0ff25594c6e2
Create Date: 2026-02-20 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b3c4d5e6f7g8'
down_revision: Union[str, Sequence[str], None] = '0ff25594c6e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add missing columns to contact_records
    op.execute("""
        ALTER TABLE contact_records 
        ADD COLUMN IF NOT EXISTS uploaded_by_staff_id INTEGER REFERENCES staff(id),
        ADD COLUMN IF NOT EXISTS assigned_staff_id INTEGER REFERENCES staff(id),
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
    """)
    
    # Add missing columns to refill_reminders
    op.execute("""
        ALTER TABLE refill_reminders 
        ADD COLUMN IF NOT EXISTS whatsapp_sent BOOLEAN DEFAULT false,
        ADD COLUMN IF NOT EXISTS whatsapp_sent_date TIMESTAMP WITHOUT TIME ZONE,
        ADD COLUMN IF NOT EXISTS call_reminder_sent BOOLEAN DEFAULT false,
        ADD COLUMN IF NOT EXISTS call_reminder_date TIMESTAMP WITHOUT TIME ZONE
    """)
    
    # Add missing columns to customer_purchases
    op.execute("""
        ALTER TABLE customer_purchases 
        ADD COLUMN IF NOT EXISTS bill_id INTEGER REFERENCES bills(id),
        ADD COLUMN IF NOT EXISTS refill_reminder_date DATE,
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
    """)
    
    # Add indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_refill_reminders_reminder_date ON refill_reminders(reminder_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_customer_purchases_purchase_date ON customer_purchases(purchase_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_customer_purchases_refill_reminder_date ON customer_purchases(refill_reminder_date)")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_customer_purchases_refill_reminder_date")
    op.execute("DROP INDEX IF EXISTS ix_customer_purchases_purchase_date")
    op.execute("DROP INDEX IF EXISTS ix_refill_reminders_reminder_date")
    
    op.drop_column('customer_purchases', 'created_at')
    op.drop_column('customer_purchases', 'refill_reminder_date')
    op.drop_column('customer_purchases', 'bill_id')
    
    op.drop_column('refill_reminders', 'call_reminder_date')
    op.drop_column('refill_reminders', 'call_reminder_sent')
    op.drop_column('refill_reminders', 'whatsapp_sent_date')
    op.drop_column('refill_reminders', 'whatsapp_sent')
    
    op.drop_column('contact_records', 'created_at')
    op.drop_column('contact_records', 'assigned_staff_id')
    op.drop_column('contact_records', 'uploaded_by_staff_id')
