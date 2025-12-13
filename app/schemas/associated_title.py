"""Associated title (Smart Categorization) schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from app.utils.time_utils import to_utc_isoformat


class AssociatedTitleBase(BaseModel):
    """Base associated title schema"""
    title: str = Field(..., min_length=1, max_length=200)
    category_id: UUID4
    is_exact_match: bool = False


class AssociatedTitleCreate(AssociatedTitleBase):
    """Schema for creating a new associated title"""
    pass


class AssociatedTitleUpdate(BaseModel):
    """Schema for updating associated title"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category_id: Optional[UUID4] = None
    is_exact_match: Optional[bool] = None


class AssociatedTitleResponse(AssociatedTitleBase):
    """Schema for associated title response"""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    class Config:
        from_attributes = True


class AssociatedTitleListResponse(BaseModel):
    """Response for associated title list"""
    items: List[AssociatedTitleResponse]
    total: int


class CategorySuggestion(BaseModel):
    """Response for category suggestion based on title"""
    category_id: Optional[UUID4] = None
    confidence: str  # 'exact', 'contains', 'none'
    matched_title: Optional[str] = None
