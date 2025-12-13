"""Associated title model for smart categorization"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class AssociatedTitle(Base):
    """Mapping of transaction titles to categories for smart auto-categorization"""

    __tablename__ = "associated_titles"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Mapping details
    title = Column(String(200), nullable=False, index=True)  # The merchant/payee name pattern
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)

    # Matching behavior
    is_exact_match = Column(Boolean, default=False, nullable=False)  # True = exact, False = contains

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", backref="associated_titles")
    category = relationship("Category", backref="associated_titles")

    def matches(self, transaction_title: str) -> bool:
        """Check if this association matches the given transaction title"""
        normalized_title = transaction_title.lower().strip()
        stored_title = self.title.lower().strip()

        if self.is_exact_match:
            return normalized_title == stored_title
        else:
            return stored_title in normalized_title

    def __repr__(self):
        match_type = "exact" if self.is_exact_match else "contains"
        return f"<AssociatedTitle(id={self.id}, title='{self.title}', match={match_type})>"
