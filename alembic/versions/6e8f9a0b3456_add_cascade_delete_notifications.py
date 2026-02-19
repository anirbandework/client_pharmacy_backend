"""add_cascade_delete_notifications

Revision ID: 6e8f9a0b3456
Revises: 5d7e8f9a2345
Create Date: 2026-02-19 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e8f9a0b3456'
down_revision: Union[str, Sequence[str], None] = '5d7e8f9a2345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Fix notification_shop_targets with CASCADE delete
    op.create_table('notification_shop_targets_new',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_shop_targets_new SELECT * FROM notification_shop_targets')
    op.drop_table('notification_shop_targets')
    op.rename_table('notification_shop_targets_new', 'notification_shop_targets')
    op.create_index(op.f('ix_notification_shop_targets_id'), 'notification_shop_targets', ['id'], unique=False)
    
    # Fix notification_reads with CASCADE delete
    op.create_table('notification_reads_new',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('staff_name', sa.String(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_reads_new SELECT * FROM notification_reads')
    op.drop_table('notification_reads')
    op.rename_table('notification_reads_new', 'notification_reads')
    op.create_index(op.f('ix_notification_reads_id'), 'notification_reads', ['id'], unique=False)
    op.create_index(op.f('ix_notification_reads_shop_id'), 'notification_reads', ['shop_id'], unique=False)
    op.create_index(op.f('ix_notification_reads_staff_id'), 'notification_reads', ['staff_id'], unique=False)
    
    # Fix notification_staff_targets with CASCADE delete
    op.create_table('notification_staff_targets_new',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_staff_targets_new SELECT * FROM notification_staff_targets')
    op.drop_table('notification_staff_targets')
    op.rename_table('notification_staff_targets_new', 'notification_staff_targets')
    op.create_index(op.f('ix_notification_staff_targets_id'), 'notification_staff_targets', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    
    # Revert notification_shop_targets
    op.create_table('notification_shop_targets_old',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_shop_targets_old SELECT * FROM notification_shop_targets')
    op.drop_table('notification_shop_targets')
    op.rename_table('notification_shop_targets_old', 'notification_shop_targets')
    op.create_index(op.f('ix_notification_shop_targets_id'), 'notification_shop_targets', ['id'], unique=False)
    
    # Revert notification_reads
    op.create_table('notification_reads_old',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('staff_name', sa.String(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_reads_old SELECT * FROM notification_reads')
    op.drop_table('notification_reads')
    op.rename_table('notification_reads_old', 'notification_reads')
    op.create_index(op.f('ix_notification_reads_id'), 'notification_reads', ['id'], unique=False)
    op.create_index(op.f('ix_notification_reads_shop_id'), 'notification_reads', ['shop_id'], unique=False)
    op.create_index(op.f('ix_notification_reads_staff_id'), 'notification_reads', ['staff_id'], unique=False)
    
    # Revert notification_staff_targets
    op.create_table('notification_staff_targets_old',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.execute('INSERT INTO notification_staff_targets_old SELECT * FROM notification_staff_targets')
    op.drop_table('notification_staff_targets')
    op.rename_table('notification_staff_targets_old', 'notification_staff_targets')
    op.create_index(op.f('ix_notification_staff_targets_id'), 'notification_staff_targets', ['id'], unique=False)