"""Recurring transaction configuration model"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Date, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from app.database import Base
from app.utils.time_utils import utc_now


class RecurrenceType(str, enum.Enum):
    """Recurrence frequency enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RecurringConfig(Base):
    """Configuration for recurring/scheduled transactions"""

    __tablename__ = "recurring_configs"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Reference to template transaction
    base_transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)

    # Recurrence settings
    period_length = Column(Integer, default=1, nullable=False)  # e.g., every 2 weeks
    reoccurrence = Column(
        Enum(RecurrenceType),
        default=RecurrenceType.MONTHLY,
        nullable=False
    )

    # Schedule
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null means infinite
    next_occurrence = Column(Date, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", backref="recurring_configs")
    base_transaction = relationship(
        "Transaction",
        foreign_keys=[base_transaction_id],
        backref="recurring_config_source"
    )

    def calculate_next_occurrence(self) -> date:
        """Calculate the next occurrence date based on current settings"""
        current = self.next_occurrence

        if self.reoccurrence == RecurrenceType.DAILY:
            return current + timedelta(days=self.period_length)
        elif self.reoccurrence == RecurrenceType.WEEKLY:
            return current + timedelta(weeks=self.period_length)
        elif self.reoccurrence == RecurrenceType.MONTHLY:
            return current + relativedelta(months=self.period_length)
        elif self.reoccurrence == RecurrenceType.YEARLY:
            return current + relativedelta(years=self.period_length)

        return current

    @property
    def is_ended(self) -> bool:
        """Check if recurring config has ended"""
        if self.end_date is None:
            return False
        return date.today() > self.end_date

    @property
    def has_pending_occurrences(self) -> bool:
        """Check if there are pending occurrences to process"""
        if not self.is_active:
            return False
        if self.is_ended:
            return False
        return self.next_occurrence <= date.today()

    def __repr__(self):
        return f"<RecurringConfig(id={self.id}, reoccurrence={self.reoccurrence}, period={self.period_length}, active={self.is_active})>"
