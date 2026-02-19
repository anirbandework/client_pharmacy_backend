"""fix_organization_shared_access_v2

Revision ID: 9b2c3d4e5f67
Revises: 6e8f9a0b3456
Create Date: 2026-02-19 03:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b2c3d4e5f67'
down_revision: Union[str, Sequence[str], None] = '6e8f9a0b3456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create all missing auth and stock tables with organization-based shops
    op.create_table('super_admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('phone', sa.String(length=15), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_super_admins_email'), 'super_admins', ['email'], unique=True)
    op.create_index(op.f('ix_super_admins_id'), 'super_admins', ['id'], unique=False)
    op.create_index(op.f('ix_super_admins_phone'), 'super_admins', ['phone'], unique=True)

    op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('organization_id', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('password_hash', sa.String(), nullable=True),
    sa.Column('plain_password', sa.String(), nullable=True),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('phone', sa.String(length=15), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_password_set', sa.Boolean(), nullable=True),
    sa.Column('created_by_super_admin', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True)
    op.create_index(op.f('ix_admins_id'), 'admins', ['id'], unique=False)
    op.create_index(op.f('ix_admins_organization_id'), 'admins', ['organization_id'], unique=False)
    op.create_index(op.f('ix_admins_phone'), 'admins', ['phone'], unique=True)

    op.create_table('otp_verifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(length=15), nullable=False),
    sa.Column('otp_code', sa.String(length=6), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otp_verifications_id'), 'otp_verifications', ['id'], unique=False)
    op.create_index(op.f('ix_otp_verifications_phone'), 'otp_verifications', ['phone'], unique=False)

    # Create shops with organization_id (not admin_id)
    op.create_table('shops',
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
    op.create_index(op.f('ix_shops_id'), 'shops', ['id'], unique=False)
    op.create_index(op.f('ix_shops_shop_code'), 'shops', ['shop_code'], unique=False)
    op.create_index(op.f('ix_shops_organization_id'), 'shops', ['organization_id'], unique=False)

    op.create_table('staff',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('staff_code', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=True),
    sa.Column('plain_password', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('role', sa.String(), nullable=True),
    sa.Column('monthly_salary', sa.Float(), nullable=True),
    sa.Column('joining_date', sa.Date(), nullable=True),
    sa.Column('salary_eligibility_days', sa.Integer(), nullable=True),
    sa.Column('can_manage_staff', sa.Boolean(), nullable=True),
    sa.Column('can_view_analytics', sa.Boolean(), nullable=True),
    sa.Column('can_manage_inventory', sa.Boolean(), nullable=True),
    sa.Column('can_manage_customers', sa.Boolean(), nullable=True),
    sa.Column('is_password_set', sa.Boolean(), nullable=True),
    sa.Column('created_by_admin', sa.String(), nullable=False),
    sa.Column('updated_by_admin', sa.String(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_staff_id'), 'staff', ['id'], unique=False)
    op.create_index(op.f('ix_staff_phone'), 'staff', ['phone'], unique=True)
    op.create_index(op.f('ix_staff_staff_code'), 'staff', ['staff_code'], unique=True)
    op.create_index(op.f('ix_staff_uuid'), 'staff', ['uuid'], unique=True)

    # Create stock audit tables
    op.create_table('stock_racks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.Column('rack_number', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_racks_id'), 'stock_racks', ['id'], unique=False)
    op.create_index(op.f('ix_stock_racks_rack_number'), 'stock_racks', ['rack_number'], unique=True)
    op.create_index(op.f('ix_stock_racks_shop_id'), 'stock_racks', ['shop_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_stock_racks_shop_id'), table_name='stock_racks')
    op.drop_index(op.f('ix_stock_racks_rack_number'), table_name='stock_racks')
    op.drop_index(op.f('ix_stock_racks_id'), table_name='stock_racks')
    op.drop_table('stock_racks')
    op.drop_index(op.f('ix_staff_uuid'), table_name='staff')
    op.drop_index(op.f('ix_staff_staff_code'), table_name='staff')
    op.drop_index(op.f('ix_staff_phone'), table_name='staff')
    op.drop_index(op.f('ix_staff_id'), table_name='staff')
    op.drop_table('staff')
    op.drop_index(op.f('ix_shops_organization_id'), table_name='shops')
    op.drop_index(op.f('ix_shops_shop_code'), table_name='shops')
    op.drop_index(op.f('ix_shops_id'), table_name='shops')
    op.drop_table('shops')
    op.drop_index(op.f('ix_otp_verifications_phone'), table_name='otp_verifications')
    op.drop_index(op.f('ix_otp_verifications_id'), table_name='otp_verifications')
    op.drop_table('otp_verifications')
    op.drop_index(op.f('ix_admins_phone'), table_name='admins')
    op.drop_index(op.f('ix_admins_organization_id'), table_name='admins')
    op.drop_index(op.f('ix_admins_id'), table_name='admins')
    op.drop_index(op.f('ix_admins_email'), table_name='admins')
    op.drop_table('admins')
    op.drop_index(op.f('ix_super_admins_phone'), table_name='super_admins')
    op.drop_index(op.f('ix_super_admins_id'), table_name='super_admins')
    op.drop_index(op.f('ix_super_admins_email'), table_name='super_admins')
    op.drop_table('super_admins')