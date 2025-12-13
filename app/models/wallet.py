"""Wallet model for managing multiple accounts/wallets"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class Wallet(Base):
    """Wallet/Account for organizing finances (personal, business, etc.)"""

    __tablename__ = "wallets"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Wallet details
    name = Column(String(100), nullable=False)
    icon_name = Column(String(50), nullable=False, default="wallet")
    color = Column(String(7), nullable=False, default="#6366F1")  # Hex color
    currency = Column(String(3), nullable=False, default="USD")  # ISO 4217 currency code

    # Balance (updated via transactions)
    balance = Column(Numeric(15, 2), default=0, nullable=False)

    # Settings
    is_default = Column(Boolean, default=False, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="wallets")

    @property
    def is_deleted(self) -> bool:
        """Check if wallet is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self):
        return f"<Wallet(id={self.id}, name={self.name}, balance={self.balance}, currency={self.currency})>"
