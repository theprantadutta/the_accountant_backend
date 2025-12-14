"""Add transaction special types for Cashew parity

Revision ID: 003
Revises: 002
Create Date: 2024-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add special transaction type columns to transactions table
    # These enable Cashew-like functionality: upcoming, subscription, credit, debt

    # special_type: 0=none, 1=upcoming, 2=subscription, 3=repetitive, 4=credit, 5=debt
    op.add_column('transactions', sa.Column('special_type', sa.Integer(), nullable=True, server_default='0'))

    # is_paid: Whether the transaction has been paid/settled
    op.add_column('transactions', sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='true'))

    # original_due_date: Original due date before being marked as paid
    op.add_column('transactions', sa.Column('original_due_date', sa.DateTime(), nullable=True))

    # skip_paid: For skipping a recurring unpaid transaction
    op.add_column('transactions', sa.Column('skip_paid', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('transactions', 'skip_paid')
    op.drop_column('transactions', 'original_due_date')
    op.drop_column('transactions', 'is_paid')
    op.drop_column('transactions', 'special_type')
