"""Add finance tables and update users

Revision ID: 002
Revises: 001
Create Date: 2024-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add IAP fields to users table
    op.add_column('users', sa.Column('iap_product_id', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('iap_purchase_token', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('iap_order_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('iap_platform', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('iap_purchased_at', sa.DateTime(), nullable=True))

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon_name', sa.String(50), nullable=False, server_default='category'),
        sa.Column('color', sa.String(7), nullable=False, server_default='#6366F1'),
        sa.Column('main_category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('is_income', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Create wallets table
    op.create_table(
        'wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon_name', sa.String(50), nullable=False, server_default='wallet'),
        sa.Column('color', sa.String(7), nullable=False, server_default='#6366F1'),
        sa.Column('currency', sa.String(3), nullable=False, server_default='USD'),
        sa.Column('balance', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Create payment_methods table
    op.create_table(
        'payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon_name', sa.String(50), nullable=False, server_default='credit_card'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Create recurring_configs table (before transactions since transactions reference it)
    op.create_table(
        'recurring_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        # base_transaction_id will be added after transactions table is created
        sa.Column('period_length', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('reoccurrence', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('next_occurrence', sa.Date(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wallets.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_methods.id', ondelete='SET NULL'), nullable=True),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=False, index=True),
        sa.Column('is_income', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('type', sa.String(30), nullable=False, server_default='regular'),
        sa.Column('paired_transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('recurring_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('recurring_configs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('receipt_image_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Add base_transaction_id to recurring_configs now that transactions exists
    op.add_column('recurring_configs',
        sa.Column('base_transaction_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=True)
    )

    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('period', sa.String(20), nullable=False, server_default='monthly'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('wallet_ids', postgresql.JSON(), nullable=True),
        sa.Column('category_ids', postgresql.JSON(), nullable=True),
        sa.Column('is_income', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Create objectives table
    op.create_table(
        'objectives',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wallets.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon_name', sa.String(50), nullable=False, server_default='flag'),
        sa.Column('color', sa.String(7), nullable=False, server_default='#6366F1'),
        sa.Column('target_amount', sa.Numeric(15, 2), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, server_default='goal'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    # Create objective_transactions junction table
    op.create_table(
        'objective_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('objective_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('objectives.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('transaction_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('transactions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create associated_titles table
    op.create_table(
        'associated_titles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False, index=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('is_exact_match', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create sync_logs table
    op.create_table(
        'sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('table_name', sa.String(50), nullable=False, index=True),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_server_version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('sync_logs')
    op.drop_table('associated_titles')
    op.drop_table('objective_transactions')
    op.drop_table('objectives')
    op.drop_table('budgets')
    op.drop_column('recurring_configs', 'base_transaction_id')
    op.drop_table('transactions')
    op.drop_table('recurring_configs')
    op.drop_table('payment_methods')
    op.drop_table('wallets')
    op.drop_table('categories')

    # Remove IAP columns from users
    op.drop_column('users', 'iap_purchased_at')
    op.drop_column('users', 'iap_platform')
    op.drop_column('users', 'iap_order_id')
    op.drop_column('users', 'iap_purchase_token')
    op.drop_column('users', 'iap_product_id')
