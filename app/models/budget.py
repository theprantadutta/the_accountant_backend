"""Budget model for tracking spending limits"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Date, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base
from app.utils.time_utils import utc_now


class BudgetPeriod(str, enum.Enum):
    """Budget period enum"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Budget(Base):
    """Budget for tracking spending limits by category/wallet"""

    __tablename__ = "budgets"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Budget details
    name = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)

    # Period settings
    period = Column(
        Enum(BudgetPeriod),
        default=BudgetPeriod.MONTHLY,
        nullable=False
    )
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Required for custom period

    # Filters - which wallets and categories to include
    wallet_ids = Column(JSON, nullable=True)  # Array of wallet UUIDs, null = all wallets
    category_ids = Column(JSON, nullable=True)  # Array of category UUIDs, null = all categories

    # Budget type - track income or expenses
    is_income = Column(Boolean, default=False, nullable=False)

    # Display settings
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="budgets")

    @property
    def is_deleted(self) -> bool:
        """Check if budget is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self):
        return f"<Budget(id={self.id}, name={self.name}, amount={self.amount}, period={self.period})>"
