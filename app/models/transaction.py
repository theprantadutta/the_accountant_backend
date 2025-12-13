"""Transaction model"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.database import Base
from app.utils.time_utils import utc_now


class TransactionType(str, enum.Enum):
    """Transaction type enum"""
    REGULAR = "regular"
    TRANSFER = "transfer"
    RECURRING_INSTANCE = "recurring_instance"


class Transaction(Base):
    """Financial transaction record"""

    __tablename__ = "transactions"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Related entities
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_method_id = Column(UUID(as_uuid=True), ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True)

    # Transaction details
    amount = Column(Numeric(15, 2), nullable=False)
    title = Column(String(200), nullable=False)
    notes = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    is_income = Column(Boolean, default=False, nullable=False)

    # Transaction type
    type = Column(
        Enum(TransactionType),
        default=TransactionType.REGULAR,
        nullable=False
    )

    # For transfers - links to the paired transaction in another wallet
    paired_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)

    # For recurring instances - links to the recurring config
    recurring_config_id = Column(UUID(as_uuid=True), ForeignKey("recurring_configs.id", ondelete="SET NULL"), nullable=True)

    # Receipt attachment
    receipt_image_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="transactions")
    wallet = relationship("Wallet", backref="transactions")
    category = relationship("Category", backref="transactions")
    payment_method = relationship("PaymentMethod", backref="transactions")
    paired_transaction = relationship("Transaction", remote_side=[id], backref="paired_with")
    recurring_config = relationship("RecurringConfig", backref="instances")

    @property
    def is_deleted(self) -> bool:
        """Check if transaction is soft deleted"""
        return self.deleted_at is not None

    @property
    def is_transfer(self) -> bool:
        """Check if this is a transfer transaction"""
        return self.type == TransactionType.TRANSFER

    @property
    def is_recurring_instance(self) -> bool:
        """Check if this transaction was created from a recurring config"""
        return self.type == TransactionType.RECURRING_INSTANCE

    def __repr__(self):
        return f"<Transaction(id={self.id}, title={self.title}, amount={self.amount}, is_income={self.is_income})>"
