"""add_cascade_delete_daily_records

Revision ID: 5d7e8f9a2345
Revises: 4c8d9e5f1234
Create Date: 2026-02-19 03:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d7e8f9a2345'
down_revision: Union[str, Sequence[str], None] = '4c8d9e5f1234'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop dependent table first
    op.drop_table('record_modifications')
    
    # Drop and recreate daily_records with CASCADE
    op.drop_table('daily_records')
    
    # Create daily_records table with CASCADE delete
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
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_records_date'), 'daily_records', ['date'], unique=False)
    op.create_index(op.f('ix_daily_records_id'), 'daily_records', ['id'], unique=False)
    op.create_index(op.f('ix_daily_records_shop_id'), 'daily_records', ['shop_id'], unique=False)
    
    # Create record_modifications table with CASCADE delete
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
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_record_modifications_daily_record_id'), 'record_modifications', ['daily_record_id'], unique=False)
    op.create_index(op.f('ix_record_modifications_id'), 'record_modifications', ['id'], unique=False)
    op.create_index(op.f('ix_record_modifications_shop_id'), 'record_modifications', ['shop_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate tables without CASCADE delete (revert to NO ACTION)
    
    # Create old daily_records table without CASCADE
    op.create_table('daily_records_old',
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
    
    op.execute('INSERT INTO daily_records_old SELECT * FROM daily_records')
    op.drop_table('daily_records')
    op.rename_table('daily_records_old', 'daily_records')
    
    op.create_index(op.f('ix_daily_records_date'), 'daily_records', ['date'], unique=False)
    op.create_index(op.f('ix_daily_records_id'), 'daily_records', ['id'], unique=False)
    op.create_index(op.f('ix_daily_records_shop_id'), 'daily_records', ['shop_id'], unique=False)
    
    # Create old record_modifications table
    op.create_table('record_modifications_old',
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
    
    op.execute('INSERT INTO record_modifications_old SELECT * FROM record_modifications')
    op.drop_table('record_modifications')
    op.rename_table('record_modifications_old', 'record_modifications')
    
    op.create_index(op.f('ix_record_modifications_daily_record_id'), 'record_modifications', ['daily_record_id'], unique=False)
    op.create_index(op.f('ix_record_modifications_id'), 'record_modifications', ['id'], unique=False)
    op.create_index(op.f('ix_record_modifications_shop_id'), 'record_modifications', ['shop_id'], unique=False)