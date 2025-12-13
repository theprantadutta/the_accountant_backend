"""User model"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class User(Base):
    """User account model with Firebase Auth support"""

    __tablename__ = "users"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for Google-only users

    # Firebase/Google Authentication
    firebase_uid = Column(String(255), unique=True, nullable=True, index=True)
    auth_provider = Column(String(50), default="email", nullable=False)  # 'email', 'google', 'firebase'
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Profile
    created_at = Column(DateTime, default=utc_now, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Future: Premium subscription fields
    subscription_tier = Column(String(50), default="free", nullable=False)
    subscription_expires_at = Column(DateTime, nullable=True)

    # Valid paid subscription tiers
    PAID_TIERS = ["basic", "premium", "pro"]

    @property
    def is_premium(self) -> bool:
        """Check if user has any active paid subscription"""
        if self.subscription_tier == "free":
            return False

        # Check if user has a valid paid tier
        if self.subscription_tier in self.PAID_TIERS:
            # If no expiration date set, treat as expired
            if self.subscription_expires_at is None:
                return False
            # Check if subscription hasn't expired
            return utc_now() < self.subscription_expires_at

        return False

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"
