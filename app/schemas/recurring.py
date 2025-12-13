"""Recurring transaction configuration schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class RecurrenceType(str, Enum):
    """Recurrence frequency enum"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class RecurringConfigBase(BaseModel):
    """Base recurring config schema"""
    base_transaction_id: UUID4
    period_length: int = Field(default=1, ge=1)
    reoccurrence: RecurrenceType = RecurrenceType.MONTHLY
    start_date: date
    end_date: Optional[date] = None


class RecurringConfigCreate(RecurringConfigBase):
    """Schema for creating a new recurring config"""
    pass


class RecurringConfigUpdate(BaseModel):
    """Schema for updating recurring config"""
    period_length: Optional[int] = Field(None, ge=1)
    reoccurrence: Optional[RecurrenceType] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class RecurringConfigResponse(RecurringConfigBase):
    """Schema for recurring config response"""
    id: UUID4
    user_id: UUID4
    next_occurrence: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    @field_serializer('start_date', 'end_date', 'next_occurrence')
    def serialize_date(self, value: Optional[date]) -> Optional[str]:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True


class RecurringConfigListResponse(BaseModel):
    """Response for recurring config list"""
    items: List[RecurringConfigResponse]
    total: int


class RecurringTriggerResponse(BaseModel):
    """Response for triggering recurring transactions"""
    processed_count: int
    created_transaction_ids: List[UUID4]
