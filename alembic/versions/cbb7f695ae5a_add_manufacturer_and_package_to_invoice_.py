"""add_manufacturer_and_package_to_invoice_items

Revision ID: cbb7f695ae5a
Revises: eefe43ffc9ab
Create Date: 2026-02-24 16:18:54.575086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbb7f695ae5a'
down_revision: Union[str, Sequence[str], None] = 'eefe43ffc9ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add manufacturer and package columns to purchase_invoice_items
    op.add_column('purchase_invoice_items', sa.Column('manufacturer', sa.String(), nullable=True))
    op.add_column('purchase_invoice_items', sa.Column('package', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove manufacturer and package columns
    op.drop_column('purchase_invoice_items', 'package')
    op.drop_column('purchase_invoice_items', 'manufacturer')
