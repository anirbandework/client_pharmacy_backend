"""add_staff_to_daily_expenses

Revision ID: 403a2731ea8b
Revises: ca35a185490c
Create Date: 2026-02-20 00:50:24.619649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '403a2731ea8b'
down_revision: Union[str, Sequence[str], None] = 'ca35a185490c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('daily_expenses', sa.Column('staff_id', sa.Integer(), nullable=True))
    op.add_column('daily_expenses', sa.Column('staff_name', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('daily_expenses', 'staff_name')
    op.drop_column('daily_expenses', 'staff_id')
