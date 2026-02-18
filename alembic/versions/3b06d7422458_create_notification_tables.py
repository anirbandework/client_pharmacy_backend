"""create_notification_tables

Revision ID: 3b06d7422458
Revises: 5451be965254
Create Date: 2026-02-19 02:36:37.393302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b06d7422458'
down_revision: Union[str, Sequence[str], None] = 'e245981beea1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add missing columns to notification_reads table with default values
    op.add_column('notification_reads', sa.Column('staff_name', sa.String(), nullable=False, server_default=''))
    op.add_column('notification_reads', sa.Column('shop_id', sa.Integer(), nullable=False, server_default='0'))
    
    # Add foreign key constraint for shop_id
    op.create_foreign_key(None, 'notification_reads', 'shops', ['shop_id'], ['id'])
    
    # Add indexes for the new columns
    op.create_index(op.f('ix_notification_reads_shop_id'), 'notification_reads', ['shop_id'], unique=False)
    op.create_index(op.f('ix_notification_reads_staff_id'), 'notification_reads', ['staff_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes
    op.drop_index(op.f('ix_notification_reads_staff_id'), table_name='notification_reads')
    op.drop_index(op.f('ix_notification_reads_shop_id'), table_name='notification_reads')
    
    # Remove foreign key constraint
    op.drop_constraint(None, 'notification_reads', type_='foreignkey')
    
    # Remove columns
    op.drop_column('notification_reads', 'shop_id')
    op.drop_column('notification_reads', 'staff_name')
