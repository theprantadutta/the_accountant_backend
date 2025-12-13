"""Objective (Goals & Savings) schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class ObjectiveType(str, Enum):
    """Objective type enum"""
    GOAL = "goal"  # Saving up for something
    LOAN = "loan"  # Paying off debt


class ObjectiveBase(BaseModel):
    """Base objective schema"""
    name: str = Field(..., min_length=1, max_length=100)
    icon_name: str = Field(default="flag", max_length=50)
    color: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$")
    target_amount: Decimal = Field(..., decimal_places=2)
    type: ObjectiveType = ObjectiveType.GOAL
    wallet_id: Optional[UUID4] = None
    start_date: date
    end_date: Optional[date] = None


class ObjectiveCreate(ObjectiveBase):
    """Schema for creating a new objective"""
    is_pinned: bool = False
    is_archived: bool = False


class ObjectiveUpdate(BaseModel):
    """Schema for updating objective"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon_name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    target_amount: Optional[Decimal] = Field(None, decimal_places=2)
    type: Optional[ObjectiveType] = None
    wallet_id: Optional[UUID4] = None
    end_date: Optional[date] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class ObjectiveResponse(ObjectiveBase):
    """Schema for objective response"""
    id: UUID4
    user_id: UUID4
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at', 'deleted_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    @field_serializer('start_date', 'end_date')
    def serialize_date(self, value: Optional[date]) -> Optional[str]:
        return value.isoformat() if value else None

    @field_serializer('target_amount')
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)

    class Config:
        from_attributes = True


class ObjectiveWithProgress(ObjectiveResponse):
    """Objective with progress details"""
    current_amount: Decimal  # Sum of linked transactions
    progress_percent: float  # 0-100
    remaining_amount: Decimal
    days_remaining: Optional[int] = None  # Days until end_date
    daily_target: Optional[Decimal] = None  # Amount to save per day to reach goal


class ObjectiveListResponse(BaseModel):
    """Response for objective list"""
    items: List[ObjectiveResponse]
    total: int


class ObjectiveTransactionLink(BaseModel):
    """Schema for linking a transaction to an objective"""
    transaction_id: UUID4


class ObjectiveTransactionResponse(BaseModel):
    """Response for objective-transaction link"""
    id: UUID4
    objective_id: UUID4
    transaction_id: UUID4
    created_at: datetime

    @field_serializer('created_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)
