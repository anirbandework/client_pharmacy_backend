"""add_mrp_to_stock_items

Revision ID: 0b46f8997a58
Revises: f972558b78b6
Create Date: 2026-02-19 22:41:31.562834

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b46f8997a58'
down_revision: Union[str, Sequence[str], None] = 'f972558b78b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stock_items_audit', sa.Column('mrp', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('stock_items_audit', 'mrp')
