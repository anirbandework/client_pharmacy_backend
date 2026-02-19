"""create_missing_tables_with_cascade

Revision ID: 7f9a0b1c4567
Revises: 6e8f9a0b3456
Create Date: 2026-02-19 03:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9a0b1c4567'
down_revision: Union[str, Sequence[str], None] = '6e8f9a0b3456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    
    # Create auth tables with CASCADE delete
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

    op.create_table('shops',
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
    op.create_index(op.f('ix_shops_id'), 'shops', ['id'], unique=False)
    op.create_index(op.f('ix_shops_shop_code'), 'shops', ['shop_code'], unique=False)

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

    # Create stock audit tables with CASCADE delete
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

    op.create_table('stock_sections_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.Column('rack_id', sa.Integer(), nullable=True),
    sa.Column('section_name', sa.String(), nullable=False),
    sa.Column('section_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['rack_id'], ['stock_racks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_sections_audit_id'), 'stock_sections_audit', ['id'], unique=False)
    op.create_index(op.f('ix_stock_sections_audit_section_code'), 'stock_sections_audit', ['section_code'], unique=True)
    op.create_index(op.f('ix_stock_sections_audit_shop_id'), 'stock_sections_audit', ['shop_id'], unique=False)

    op.create_table('purchases_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.Column('staff_id', sa.Integer(), nullable=True),
    sa.Column('staff_name', sa.String(), nullable=True),
    sa.Column('purchase_date', sa.Date(), nullable=False),
    sa.Column('supplier_name', sa.String(), nullable=False),
    sa.Column('invoice_number', sa.String(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_purchases_audit_id'), 'purchases_audit', ['id'], unique=False)
    op.create_index(op.f('ix_purchases_audit_shop_id'), 'purchases_audit', ['shop_id'], unique=False)
    op.create_index(op.f('ix_purchases_audit_staff_id'), 'purchases_audit', ['staff_id'], unique=False)

    op.create_table('sales_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.Column('staff_id', sa.Integer(), nullable=True),
    sa.Column('staff_name', sa.String(), nullable=True),
    sa.Column('sale_date', sa.Date(), nullable=False),
    sa.Column('customer_phone', sa.String(), nullable=True),
    sa.Column('bill_number', sa.String(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sales_audit_id'), 'sales_audit', ['id'], unique=False)
    op.create_index(op.f('ix_sales_audit_shop_id'), 'sales_audit', ['shop_id'], unique=False)
    op.create_index(op.f('ix_sales_audit_staff_id'), 'sales_audit', ['staff_id'], unique=False)

    op.create_table('stock_items_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=True),
    sa.Column('section_id', sa.Integer(), nullable=True),
    sa.Column('item_name', sa.String(), nullable=False),
    sa.Column('generic_name', sa.String(), nullable=True),
    sa.Column('brand_name', sa.String(), nullable=True),
    sa.Column('batch_number', sa.String(), nullable=False),
    sa.Column('quantity_software', sa.Integer(), nullable=True),
    sa.Column('quantity_physical', sa.Integer(), nullable=True),
    sa.Column('unit_price', sa.Float(), nullable=True),
    sa.Column('expiry_date', sa.Date(), nullable=True),
    sa.Column('manufacturer', sa.String(), nullable=True),
    sa.Column('last_audit_date', sa.DateTime(), nullable=True),
    sa.Column('last_audit_by_staff_id', sa.Integer(), nullable=True),
    sa.Column('last_audit_by_staff_name', sa.String(), nullable=True),
    sa.Column('audit_discrepancy', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['last_audit_by_staff_id'], ['staff.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['section_id'], ['stock_sections_audit.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_stock_items_audit_batch_number'), 'stock_items_audit', ['batch_number'], unique=False)
    op.create_index(op.f('ix_stock_items_audit_id'), 'stock_items_audit', ['id'], unique=False)
    op.create_index(op.f('ix_stock_items_audit_item_name'), 'stock_items_audit', ['item_name'], unique=False)
    op.create_index(op.f('ix_stock_items_audit_shop_id'), 'stock_items_audit', ['shop_id'], unique=False)

    # Additional auth tables
    op.create_table('attendance_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('work_start_time', sa.Time(), nullable=True),
    sa.Column('work_end_time', sa.Time(), nullable=True),
    sa.Column('grace_period_minutes', sa.Integer(), nullable=True),
    sa.Column('auto_checkout_enabled', sa.Boolean(), nullable=True),
    sa.Column('auto_checkout_time', sa.Time(), nullable=True),
    sa.Column('monday', sa.Boolean(), nullable=True),
    sa.Column('tuesday', sa.Boolean(), nullable=True),
    sa.Column('wednesday', sa.Boolean(), nullable=True),
    sa.Column('thursday', sa.Boolean(), nullable=True),
    sa.Column('friday', sa.Boolean(), nullable=True),
    sa.Column('saturday', sa.Boolean(), nullable=True),
    sa.Column('sunday', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('shop_id')
    )
    op.create_index(op.f('ix_attendance_settings_id'), 'attendance_settings', ['id'], unique=False)

    op.create_table('shop_wifi',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('shop_id', sa.Integer(), nullable=False),
    sa.Column('wifi_ssid', sa.String(length=100), nullable=False),
    sa.Column('wifi_password', sa.String(length=255), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shop_wifi_id'), 'shop_wifi', ['id'], unique=False)

    op.create_table('salary_records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('staff_id', sa.Integer(), nullable=False),
    sa.Column('month', sa.Integer(), nullable=False),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('salary_amount', sa.Float(), nullable=False),
    sa.Column('payment_status', sa.String(length=20), nullable=True),
    sa.Column('payment_date', sa.DateTime(), nullable=True),
    sa.Column('paid_by_admin', sa.String(length=100), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['staff_id'], ['staff.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salary_records_id'), 'salary_records', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_salary_records_id'), table_name='salary_records')
    op.drop_table('salary_records')
    op.drop_index(op.f('ix_shop_wifi_id'), table_name='shop_wifi')
    op.drop_table('shop_wifi')
    op.drop_index(op.f('ix_attendance_settings_id'), table_name='attendance_settings')
    op.drop_table('attendance_settings')
    op.drop_index(op.f('ix_stock_items_audit_shop_id'), table_name='stock_items_audit')
    op.drop_index(op.f('ix_stock_items_audit_item_name'), table_name='stock_items_audit')
    op.drop_index(op.f('ix_stock_items_audit_id'), table_name='stock_items_audit')
    op.drop_index(op.f('ix_stock_items_audit_batch_number'), table_name='stock_items_audit')
    op.drop_table('stock_items_audit')
    op.drop_index(op.f('ix_sales_audit_staff_id'), table_name='sales_audit')
    op.drop_index(op.f('ix_sales_audit_shop_id'), table_name='sales_audit')
    op.drop_index(op.f('ix_sales_audit_id'), table_name='sales_audit')
    op.drop_table('sales_audit')
    op.drop_index(op.f('ix_purchases_audit_staff_id'), table_name='purchases_audit')
    op.drop_index(op.f('ix_purchases_audit_shop_id'), table_name='purchases_audit')
    op.drop_index(op.f('ix_purchases_audit_id'), table_name='purchases_audit')
    op.drop_table('purchases_audit')
    op.drop_index(op.f('ix_stock_sections_audit_shop_id'), table_name='stock_sections_audit')
    op.drop_index(op.f('ix_stock_sections_audit_section_code'), table_name='stock_sections_audit')
    op.drop_index(op.f('ix_stock_sections_audit_id'), table_name='stock_sections_audit')
    op.drop_table('stock_sections_audit')
    op.drop_index(op.f('ix_stock_racks_shop_id'), table_name='stock_racks')
    op.drop_index(op.f('ix_stock_racks_rack_number'), table_name='stock_racks')
    op.drop_index(op.f('ix_stock_racks_id'), table_name='stock_racks')
    op.drop_table('stock_racks')
    op.drop_index(op.f('ix_staff_uuid'), table_name='staff')
    op.drop_index(op.f('ix_staff_staff_code'), table_name='staff')
    op.drop_index(op.f('ix_staff_phone'), table_name='staff')
    op.drop_index(op.f('ix_staff_id'), table_name='staff')
    op.drop_table('staff')
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