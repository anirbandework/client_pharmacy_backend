"""create_daily_records_tables

Revision ID: 4c8d9e5f1234
Revises: 3b06d7422458
Create Date: 2026-02-19 03:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c8d9e5f1234'
down_revision: Union[str, Sequence[str], None] = '3b06d7422458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create daily_records table
    op.create_table('daily_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('day', sa.String(), nullable=True),
    sa.Column('cash_balance', sa.Float(), nullable=True),
    sa.Column('average_bill', sa.Float(), nullable=True),
    sa.Column('no_of_bills', sa.Integer(), nullable=True),
    sa.Column('total_cash', sa.Float(), nullable=True),
    sa.Column('actual_cash', sa.Float(), nullable=True),
    sa.Column('online_sales', sa.Float(), nullable=True),
    sa.Column('total_sales', sa.Float(), nullable=True),
    sa.Column('unbilled_sales', sa.Float(), nullable=True),
    sa.Column('software_figure', sa.Float(), nullable=True),
    sa.Column('recorded_sales', sa.Float(), nullable=True),
    sa.Column('sales_difference', sa.Float(), nullable=True),
    sa.Column('cash_reserve', sa.Float(), nullable=True),
    sa.Column('reserve_comments', sa.Text(), nullable=True),
    sa.Column('expense_amount', sa.Float(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('modified_by', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_records_date'), 'daily_records', ['date'], unique=False)
    op.create_index(op.f('ix_daily_records_id'), 'daily_records', ['id'], unique=False)
    op.create_index(op.f('ix_daily_records_shop_id'), 'daily_records', ['shop_id'], unique=False)

    # Create record_modifications table
    op.create_table('record_modifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('daily_record_id', sa.Integer(), nullable=True),
    sa.Column('field_name', sa.String(), nullable=False),
    sa.Column('old_value', sa.String(), nullable=True),
    sa.Column('new_value', sa.String(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=False),
    sa.Column('modified_by', sa.String(), nullable=True),
    sa.Column('action', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_record_modifications_daily_record_id'), 'record_modifications', ['daily_record_id'], unique=False)
    op.create_index(op.f('ix_record_modifications_id'), 'record_modifications', ['id'], unique=False)
    op.create_index(op.f('ix_record_modifications_shop_id'), 'record_modifications', ['shop_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_record_modifications_shop_id'), table_name='record_modifications')
    op.drop_index(op.f('ix_record_modifications_id'), table_name='record_modifications')
    op.drop_index(op.f('ix_record_modifications_daily_record_id'), table_name='record_modifications')
    op.drop_table('record_modifications')
    op.drop_index(op.f('ix_daily_records_shop_id'), table_name='daily_records')
    op.drop_index(op.f('ix_daily_records_id'), table_name='daily_records')
    op.drop_index(op.f('ix_daily_records_date'), table_name='daily_records')
    op.drop_table('daily_records')