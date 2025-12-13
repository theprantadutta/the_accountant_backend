"""Initial user table

Revision ID: 001
Revises:
Create Date: 2024-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        # Identity
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=True),

        # Firebase/Google Authentication
        sa.Column('firebase_uid', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('auth_provider', sa.String(50), nullable=False, server_default='email'),
        sa.Column('google_id', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('photo_url', sa.Text(), nullable=True),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),

        # Profile
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        # Subscription
        sa.Column('subscription_tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('users')
