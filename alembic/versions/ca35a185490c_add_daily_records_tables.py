"""add_daily_records_tables

Revision ID: ca35a185490c
Revises: 0b46f8997a58
Create Date: 2026-02-19 23:01:52.160955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca35a185490c'
down_revision: Union[str, Sequence[str], None] = '0b46f8997a58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'daily_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('record_date', sa.Date(), nullable=False),
        sa.Column('no_of_bills', sa.Integer(), server_default='0'),
        sa.Column('software_sales', sa.Float(), server_default='0.0'),
        sa.Column('cash_sales', sa.Float(), server_default='0.0'),
        sa.Column('online_sales', sa.Float(), server_default='0.0'),
        sa.Column('unbilled_amount', sa.Float(), server_default='0.0'),
        sa.Column('unbilled_notes', sa.Text(), nullable=True),
        sa.Column('actual_cash_deposited', sa.Float(), server_default='0.0'),
        sa.Column('cash_reserve', sa.Float(), server_default='0.0'),
        sa.Column('total_expenses', sa.Float(), server_default='0.0'),
        sa.Column('staff_id', sa.Integer(), nullable=True),
        sa.Column('staff_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
        sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_records_record_date'), 'daily_records', ['record_date'], unique=False)
    op.create_index(op.f('ix_daily_records_shop_id'), 'daily_records', ['shop_id'], unique=False)
    
    op.create_table(
        'daily_expenses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('daily_record_id', sa.Integer(), nullable=False),
        sa.Column('expense_category', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['daily_record_id'], ['daily_records.id'], ),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_expenses_shop_id'), 'daily_expenses', ['shop_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_daily_expenses_shop_id'), table_name='daily_expenses')
    op.drop_table('daily_expenses')
    op.drop_index(op.f('ix_daily_records_shop_id'), table_name='daily_records')
    op.drop_index(op.f('ix_daily_records_record_date'), table_name='daily_records')
    op.drop_table('daily_records')
