"""Payment method model"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class PaymentMethod(Base):
    """Payment method for transactions (cash, credit card, debit card, etc.)"""

    __tablename__ = "payment_methods"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Payment method details
    name = Column(String(100), nullable=False)
    icon_name = Column(String(50), nullable=False, default="credit_card")

    # Settings
    is_default = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="payment_methods")

    @property
    def is_deleted(self) -> bool:
        """Check if payment method is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, name={self.name})>"
