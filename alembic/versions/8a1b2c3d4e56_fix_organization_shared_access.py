"""fix_organization_shared_access

Revision ID: 8a1b2c3d4e56
Revises: 7f9a0b1c4567
Create Date: 2026-02-19 03:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a1b2c3d4e56'
down_revision: Union[str, Sequence[str], None] = '7f9a0b1c4567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create new shops table with organization_id instead of admin_id
    op.create_table('shops_new',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.String(), nullable=False),
    sa.Column('shop_name', sa.String(), nullable=False),
    sa.Column('shop_code', sa.String(), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('license_number', sa.String(), nullable=True),
    sa.Column('gst_number', sa.String(), nullable=True),
    sa.Column('created_by_admin', sa.String(), nullable=False),
    sa.Column('updated_by_admin', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('shop_code', 'organization_id', name='unique_shop_code_per_organization')
    )
    op.create_index('ix_shops_new_id', 'shops_new', ['id'], unique=False)
    op.create_index('ix_shops_new_shop_code', 'shops_new', ['shop_code'], unique=False)
    op.create_index('ix_shops_new_organization_id', 'shops_new', ['organization_id'], unique=False)
    
    # Migrate data: get organization_id from admin_id
    op.execute('''
        INSERT INTO shops_new (id, organization_id, shop_name, shop_code, address, phone, email, 
                              license_number, gst_number, created_by_admin, updated_by_admin, 
                              updated_at, is_active, created_at)
        SELECT s.id, a.organization_id, s.shop_name, s.shop_code, s.address, s.phone, s.email,
               s.license_number, s.gst_number, s.created_by_admin, s.updated_by_admin,
               s.updated_at, s.is_active, s.created_at
        FROM shops s
        JOIN admins a ON s.admin_id = a.id
    ''')
    
    # Drop old shops table and rename new one
    op.drop_table('shops')
    op.rename_table('shops_new', 'shops')


def downgrade() -> None:
    """Downgrade schema."""
    
    # Create old shops table with admin_id
    op.create_table('shops_old',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=False),
    sa.Column('shop_name', sa.String(), nullable=False),
    sa.Column('shop_code', sa.String(), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('license_number', sa.String(), nullable=True),
    sa.Column('gst_number', sa.String(), nullable=True),
    sa.Column('created_by_admin', sa.String(), nullable=False),
    sa.Column('updated_by_admin', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('shop_code', 'admin_id', name='unique_shop_code_per_admin')
    )
    
    # Migrate data back: use first admin with matching organization_id
    op.execute('''
        INSERT INTO shops_old (id, admin_id, shop_name, shop_code, address, phone, email,
                              license_number, gst_number, created_by_admin, updated_by_admin,
                              updated_at, is_active, created_at)
        SELECT s.id, 
               (SELECT MIN(a.id) FROM admins a WHERE a.organization_id = s.organization_id) as admin_id,
               s.shop_name, s.shop_code, s.address, s.phone, s.email,
               s.license_number, s.gst_number, s.created_by_admin, s.updated_by_admin,
               s.updated_at, s.is_active, s.created_at
        FROM shops s
    ''')
    
    op.drop_table('shops')
    op.rename_table('shops_old', 'shops')
    op.create_index(op.f('ix_shops_id'), 'shops', ['id'], unique=False)
    op.create_index(op.f('ix_shops_shop_code'), 'shops', ['shop_code'], unique=False)