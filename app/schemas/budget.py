"""Budget schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class BudgetPeriod(str, Enum):
    """Budget period enum"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class BudgetBase(BaseModel):
    """Base budget schema"""
    name: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., decimal_places=2)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    start_date: date
    end_date: Optional[date] = None
    wallet_ids: Optional[List[UUID4]] = None  # Null = all wallets
    category_ids: Optional[List[UUID4]] = None  # Null = all categories
    is_income: bool = False


class BudgetCreate(BudgetBase):
    """Schema for creating a new budget"""
    is_pinned: bool = False
    is_archived: bool = False


class BudgetUpdate(BaseModel):
    """Schema for updating budget"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    period: Optional[BudgetPeriod] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    wallet_ids: Optional[List[UUID4]] = None
    category_ids: Optional[List[UUID4]] = None
    is_income: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


class BudgetResponse(BudgetBase):
    """Schema for budget response"""
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

    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)

    class Config:
        from_attributes = True


class BudgetWithProgress(BudgetResponse):
    """Budget with spending progress"""
    spent: Decimal
    remaining: Decimal
    progress_percent: float  # 0-100


class BudgetListResponse(BaseModel):
    """Response for budget list"""
    items: List[BudgetResponse]
    total: int
