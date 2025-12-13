"""Objective model for goals and savings tracking"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Date, ForeignKey, Enum, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base
from app.utils.time_utils import utc_now


class ObjectiveType(str, enum.Enum):
    """Objective type enum"""
    GOAL = "goal"  # Saving up for something
    LOAN = "loan"  # Paying off debt


# Association table for objective-transaction many-to-many relationship
objective_transactions = Table(
    "objective_transactions",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("objective_id", UUID(as_uuid=True), ForeignKey("objectives.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("transaction_id", UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True),
    Column("created_at", DateTime, default=utc_now, nullable=False),
)


class Objective(Base):
    """Objective/Goal for savings tracking or debt payoff"""

    __tablename__ = "objectives"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Optional link to a specific wallet
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="SET NULL"), nullable=True)

    # Objective details
    name = Column(String(100), nullable=False)
    icon_name = Column(String(50), nullable=False, default="flag")
    color = Column(String(7), nullable=False, default="#6366F1")  # Hex color
    target_amount = Column(Numeric(15, 2), nullable=False)

    # Type - are we saving up or paying off?
    type = Column(
        Enum(ObjectiveType),
        default=ObjectiveType.GOAL,
        nullable=False
    )

    # Timeline
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Optional deadline

    # Display settings
    is_pinned = Column(Boolean, default=False, nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="objectives")
    wallet = relationship("Wallet", backref="objectives")
    transactions = relationship(
        "Transaction",
        secondary=objective_transactions,
        backref="objectives"
    )

    @property
    def is_deleted(self) -> bool:
        """Check if objective is soft deleted"""
        return self.deleted_at is not None

    @property
    def is_goal(self) -> bool:
        """Check if this is a savings goal"""
        return self.type == ObjectiveType.GOAL

    @property
    def is_loan(self) -> bool:
        """Check if this is debt payoff"""
        return self.type == ObjectiveType.LOAN

    def __repr__(self):
        return f"<Objective(id={self.id}, name={self.name}, target={self.target_amount}, type={self.type})>"
