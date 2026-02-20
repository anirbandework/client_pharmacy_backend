"""add_customer_tracking_tables

Revision ID: a1b2c3d4e5f6
Revises: 7f9a0b1c4567
Create Date: 2026-02-19 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '7f9a0b1c4567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add customer tracking fields to bills table
    op.add_column('bills', sa.Column('customer_category', sa.String(), nullable=True))
    op.add_column('bills', sa.Column('was_contacted_before', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('bills', sa.Column('visited_but_no_purchase', sa.Boolean(), nullable=True, server_default='false'))
    
    # Create contact_records table
    op.create_table('contact_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('whatsapp_status', sa.String(), nullable=True),
        sa.Column('contact_status', sa.String(), nullable=True),
        sa.Column('source_file', sa.String(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('uploaded_by_staff_id', sa.Integer(), nullable=True),
        sa.Column('assigned_staff_id', sa.Integer(), nullable=True),
        sa.Column('assigned_date', sa.DateTime(), nullable=True),
        sa.Column('first_contact_date', sa.DateTime(), nullable=True),
        sa.Column('last_contact_date', sa.DateTime(), nullable=True),
        sa.Column('contact_attempts', sa.Integer(), nullable=True),
        sa.Column('whatsapp_sent', sa.Boolean(), nullable=True),
        sa.Column('whatsapp_sent_date', sa.DateTime(), nullable=True),
        sa.Column('converted_date', sa.DateTime(), nullable=True),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_staff_id'], ['staff.id']),
        sa.ForeignKeyConstraint(['assigned_staff_id'], ['staff.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contact_records_id', 'contact_records', ['id'])
    op.create_index('ix_contact_records_shop_id', 'contact_records', ['shop_id'])
    op.create_index('ix_contact_records_phone', 'contact_records', ['phone'])
    op.create_index('ix_contact_records_contact_status', 'contact_records', ['contact_status'])
    
    # Create contact_interactions table
    op.create_table('contact_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('staff_id', sa.Integer(), nullable=False),
        sa.Column('interaction_date', sa.DateTime(), nullable=True),
        sa.Column('interaction_type', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('customer_response', sa.Text(), nullable=True),
        sa.Column('next_action', sa.String(), nullable=True),
        sa.Column('call_duration', sa.Integer(), nullable=True),
        sa.Column('call_successful', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contact_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contact_interactions_id', 'contact_interactions', ['id'])
    op.create_index('ix_contact_interactions_shop_id', 'contact_interactions', ['shop_id'])
    op.create_index('ix_contact_interactions_interaction_date', 'contact_interactions', ['interaction_date'])
    
    # Create contact_reminders table
    op.create_table('contact_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('contact_id', sa.Integer(), nullable=False),
        sa.Column('staff_id', sa.Integer(), nullable=False),
        sa.Column('reminder_date', sa.DateTime(), nullable=False),
        sa.Column('reminder_type', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('completed_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_id'], ['contact_records.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contact_reminders_id', 'contact_reminders', ['id'])
    op.create_index('ix_contact_reminders_shop_id', 'contact_reminders', ['shop_id'])
    op.create_index('ix_contact_reminders_reminder_date', 'contact_reminders', ['reminder_date'])
    
    # Create customers table
    op.create_table('customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('contact_record_id', sa.Integer(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('chronic_conditions', sa.Text(), nullable=True),
        sa.Column('allergies', sa.Text(), nullable=True),
        sa.Column('primary_doctor', sa.String(), nullable=True),
        sa.Column('first_visit_date', sa.DateTime(), nullable=True),
        sa.Column('last_visit_date', sa.DateTime(), nullable=True),
        sa.Column('total_visits', sa.Integer(), nullable=True),
        sa.Column('total_purchases', sa.Float(), nullable=True),
        sa.Column('prefers_generic', sa.Boolean(), nullable=True),
        sa.Column('generic_education_given', sa.Boolean(), nullable=True),
        sa.Column('special_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['contact_record_id'], ['contact_records.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customers_id', 'customers', ['id'])
    op.create_index('ix_customers_shop_id', 'customers', ['shop_id'])
    op.create_index('ix_customers_phone', 'customers', ['phone'])
    op.create_index('ix_customers_category', 'customers', ['category'])
    
    # Create customer_purchases table
    op.create_table('customer_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('bill_id', sa.Integer(), nullable=True),
        sa.Column('purchase_date', sa.DateTime(), nullable=True),
        sa.Column('medicine_name', sa.String(), nullable=False),
        sa.Column('generic_name', sa.String(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('is_generic', sa.Boolean(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('refill_reminder_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bill_id'], ['bills.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_customer_purchases_id', 'customer_purchases', ['id'])
    op.create_index('ix_customer_purchases_shop_id', 'customer_purchases', ['shop_id'])
    op.create_index('ix_customer_purchases_purchase_date', 'customer_purchases', ['purchase_date'])
    op.create_index('ix_customer_purchases_refill_reminder_date', 'customer_purchases', ['refill_reminder_date'])
    
    # Create refill_reminders table
    op.create_table('refill_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('shop_id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=True),
        sa.Column('medicine_name', sa.String(), nullable=False),
        sa.Column('reminder_date', sa.Date(), nullable=False),
        sa.Column('whatsapp_sent', sa.Boolean(), nullable=True),
        sa.Column('whatsapp_sent_date', sa.DateTime(), nullable=True),
        sa.Column('call_reminder_sent', sa.Boolean(), nullable=True),
        sa.Column('call_reminder_date', sa.DateTime(), nullable=True),
        sa.Column('customer_responded', sa.Boolean(), nullable=True),
        sa.Column('customer_purchased', sa.Boolean(), nullable=True),
        sa.Column('response_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['shop_id'], ['shops.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_id'], ['customer_purchases.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_refill_reminders_id', 'refill_reminders', ['id'])
    op.create_index('ix_refill_reminders_shop_id', 'refill_reminders', ['shop_id'])
    op.create_index('ix_refill_reminders_reminder_date', 'refill_reminders', ['reminder_date'])

def downgrade() -> None:
    op.drop_table('refill_reminders')
    op.drop_table('customer_purchases')
    op.drop_table('customers')
    op.drop_table('contact_reminders')
    op.drop_table('contact_interactions')
    op.drop_table('contact_records')
    
    op.drop_column('bills', 'visited_but_no_purchase')
    op.drop_column('bills', 'was_contacted_before')
    op.drop_column('bills', 'customer_category')
