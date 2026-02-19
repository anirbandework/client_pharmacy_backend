"""add_unique_constraint_daily_records

Revision ID: a56951bb5a63
Revises: 403a2731ea8b
Create Date: 2026-02-20 01:06:49.691140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a56951bb5a63'
down_revision: Union[str, Sequence[str], None] = '403a2731ea8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint('uq_daily_records_shop_date', 'daily_records', ['shop_id', 'record_date'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_daily_records_shop_date', 'daily_records', type_='unique')
