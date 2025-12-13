"""Category model with subcategory support"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class Category(Base):
    """Category for organizing transactions (supports subcategories)"""

    __tablename__ = "categories"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Category details
    name = Column(String(100), nullable=False)
    icon_name = Column(String(50), nullable=False, default="category")
    color = Column(String(7), nullable=False, default="#6366F1")  # Hex color

    # Subcategory support - if set, this is a subcategory
    main_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)

    # Transaction type
    is_income = Column(Boolean, default=False, nullable=False)

    # Display order
    order_index = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    user = relationship("User", backref="categories")
    parent_category = relationship("Category", remote_side=[id], backref="subcategories")

    @property
    def is_subcategory(self) -> bool:
        """Check if this is a subcategory"""
        return self.main_category_id is not None

    @property
    def is_deleted(self) -> bool:
        """Check if category is soft deleted"""
        return self.deleted_at is not None

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, is_income={self.is_income})>"
