"""Add exchange rates table and user onboarding fields

Revision ID: 004
Revises: 003
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create exchange_rates table
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_currency', sa.String(3), nullable=False),
        sa.Column('to_currency', sa.String(3), nullable=False),
        sa.Column('api_rate', sa.Numeric(20, 10), nullable=True),
        sa.Column('custom_rate', sa.Numeric(20, 10), nullable=True),
        sa.Column('use_custom_rate', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_rate_fetched_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('version', sa.Numeric(), nullable=False, server_default='1'),
    )

    # Create unique constraint for currency pair per user
    op.create_unique_constraint(
        'uq_exchange_rates_user_currency_pair',
        'exchange_rates',
        ['user_id', 'from_currency', 'to_currency']
    )

    # Add user onboarding and currency preference fields
    op.add_column('users', sa.Column('default_currency', sa.String(3), nullable=True, server_default='USD'))
    op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove user fields
    op.drop_column('users', 'onboarding_completed')
    op.drop_column('users', 'default_currency')

    # Drop exchange_rates table
    op.drop_constraint('uq_exchange_rates_user_currency_pair', 'exchange_rates', type_='unique')
    op.drop_table('exchange_rates')
