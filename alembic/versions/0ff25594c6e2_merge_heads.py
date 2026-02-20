"""merge_heads

Revision ID: 0ff25594c6e2
Revises: a1b2c3d4e5f6, a56951bb5a63
Create Date: 2026-02-20 16:46:03.981105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ff25594c6e2'
down_revision: Union[str, Sequence[str], None] = ('a1b2c3d4e5f6', 'a56951bb5a63')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
