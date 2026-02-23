"""add_staff_id_to_purchase_invoices

Revision ID: eefe43ffc9ab
Revises: 9da7a87fed6e
Create Date: 2026-02-23 21:28:39.605996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eefe43ffc9ab'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7g8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add staff_id column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name='purchase_invoices' AND column_name='staff_id') THEN
                ALTER TABLE purchase_invoices ADD COLUMN staff_id INTEGER;
                ALTER TABLE purchase_invoices ADD CONSTRAINT purchase_invoices_staff_id_fkey 
                    FOREIGN KEY (staff_id) REFERENCES staff(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns 
                      WHERE table_name='purchase_invoices' AND column_name='staff_id') THEN
                ALTER TABLE purchase_invoices DROP CONSTRAINT IF EXISTS purchase_invoices_staff_id_fkey;
                ALTER TABLE purchase_invoices DROP COLUMN staff_id;
            END IF;
        END $$;
    """)
