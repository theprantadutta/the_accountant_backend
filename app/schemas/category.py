"""Category schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from app.utils.time_utils import to_utc_isoformat


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    icon_name: str = Field(default="category", max_length=50)
    color: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$")
    is_income: bool = False
    order_index: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a new category"""
    main_category_id: Optional[UUID4] = None


class CategoryUpdate(BaseModel):
    """Schema for updating category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon_name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_income: Optional[bool] = None
    order_index: Optional[int] = None
    main_category_id: Optional[UUID4] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: UUID4
    user_id: UUID4
    main_category_id: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at', 'deleted_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    class Config:
        from_attributes = True


class CategoryWithSubcategories(CategoryResponse):
    """Category with nested subcategories"""
    subcategories: List["CategoryResponse"] = []


class CategoryListResponse(BaseModel):
    """Response for category list"""
    items: List[CategoryResponse]
    total: int
