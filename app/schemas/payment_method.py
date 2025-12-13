"""Payment method schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from app.utils.time_utils import to_utc_isoformat


class PaymentMethodBase(BaseModel):
    """Base payment method schema"""
    name: str = Field(..., min_length=1, max_length=100)
    icon_name: str = Field(default="credit_card", max_length=50)
    is_default: bool = False


class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating a new payment method"""
    pass


class PaymentMethodUpdate(BaseModel):
    """Schema for updating payment method"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon_name: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = None


class PaymentMethodResponse(PaymentMethodBase):
    """Schema for payment method response"""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at', 'deleted_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    class Config:
        from_attributes = True


class PaymentMethodListResponse(BaseModel):
    """Response for payment method list"""
    items: List[PaymentMethodResponse]
    total: int
