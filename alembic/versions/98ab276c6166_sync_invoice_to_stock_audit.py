"""sync_invoice_to_stock_audit

Revision ID: 98ab276c6166
Revises: cbb7f695ae5a
Create Date: 2026-02-24 16:40:54.238239

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98ab276c6166'
down_revision: Union[str, Sequence[str], None] = 'cbb7f695ae5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename item_name to product_name
    op.alter_column('stock_items_audit', 'item_name', new_column_name='product_name')
    
    # Drop old columns
    op.drop_column('stock_items_audit', 'generic_name')
    op.drop_column('stock_items_audit', 'brand_name')
    
    # Add new columns
    op.add_column('stock_items_audit', sa.Column('hsn_code', sa.String(), nullable=True))
    op.add_column('stock_items_audit', sa.Column('package', sa.String(), nullable=True))
    op.add_column('stock_items_audit', sa.Column('source_invoice_id', sa.Integer(), nullable=True))
    
    # Make section_id nullable
    op.alter_column('stock_items_audit', 'section_id', nullable=True)
    
    # Add foreign key for source_invoice_id
    op.create_foreign_key('fk_stock_items_source_invoice', 'stock_items_audit', 'purchase_invoices', ['source_invoice_id'], ['id'])
    
    # Create index on hsn_code
    op.create_index('ix_stock_items_audit_hsn_code', 'stock_items_audit', ['hsn_code'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop index
    op.drop_index('ix_stock_items_audit_hsn_code', 'stock_items_audit')
    
    # Drop foreign key
    op.drop_constraint('fk_stock_items_source_invoice', 'stock_items_audit', type_='foreignkey')
    
    # Remove new columns
    op.drop_column('stock_items_audit', 'source_invoice_id')
    op.drop_column('stock_items_audit', 'package')
    op.drop_column('stock_items_audit', 'hsn_code')
    
    # Make section_id not nullable
    op.alter_column('stock_items_audit', 'section_id', nullable=False)
    
    # Add back old columns
    op.add_column('stock_items_audit', sa.Column('brand_name', sa.String(), nullable=True))
    op.add_column('stock_items_audit', sa.Column('generic_name', sa.String(), nullable=True))
    
    # Rename product_name back to item_name
    op.alter_column('stock_items_audit', 'product_name', new_column_name='item_name')
