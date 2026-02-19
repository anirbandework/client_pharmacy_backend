"""Merge heads

Revision ID: a68c04c716c2
Revises: 8a1b2c3d4e56, 9b2c3d4e5f67
Create Date: 2026-02-19 21:37:23.093250

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a68c04c716c2'
down_revision: Union[str, Sequence[str], None] = ('8a1b2c3d4e56', '9b2c3d4e5f67')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
