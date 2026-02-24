"""add_mrp_to_invoice_items

Revision ID: 9268d03504c9
Revises: 98ab276c6166
Create Date: 2026-02-24 17:05:43.137942

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9268d03504c9'
down_revision: Union[str, Sequence[str], None] = '98ab276c6166'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('purchase_invoice_items', sa.Column('mrp', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('purchase_invoice_items', 'mrp')
