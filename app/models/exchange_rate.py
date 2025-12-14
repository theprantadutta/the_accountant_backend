"""Exchange rate model for storing user's currency conversion rates"""
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class ExchangeRate(Base):
    """Exchange rate model for per-user currency conversion rates"""

    __tablename__ = "exchange_rates"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Currency pair (ISO 4217 codes)
    from_currency = Column(String(3), nullable=False)  # e.g., "USD"
    to_currency = Column(String(3), nullable=False)    # e.g., "EUR"

    # Rates (using Numeric for precision with currency)
    api_rate = Column(Numeric(20, 10), nullable=True)      # Rate fetched from API
    custom_rate = Column(Numeric(20, 10), nullable=True)   # User-defined override rate
    use_custom_rate = Column(Boolean, default=False, nullable=False)

    # API rate metadata
    api_rate_fetched_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Sync tracking
    version = Column(Numeric, default=1, nullable=False)

    # Relationship
    user = relationship("User", backref="exchange_rates")

    # Unique constraint: one rate per currency pair per user
    __table_args__ = (
        UniqueConstraint('user_id', 'from_currency', 'to_currency', name='uq_exchange_rates_user_currency_pair'),
    )

    def __repr__(self):
        rate = self.custom_rate if self.use_custom_rate else self.api_rate
        return f"<ExchangeRate({self.from_currency}/{self.to_currency}={rate})>"
