"""Wallet schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from app.utils.time_utils import to_utc_isoformat


class WalletBase(BaseModel):
    """Base wallet schema"""
    name: str = Field(..., min_length=1, max_length=100)
    icon_name: str = Field(default="wallet", max_length=50)
    color: str = Field(default="#6366F1", pattern=r"^#[0-9A-Fa-f]{6}$")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    is_default: bool = False
    order_index: int = 0


class WalletCreate(WalletBase):
    """Schema for creating a new wallet"""
    balance: Decimal = Decimal("0.00")


class WalletUpdate(BaseModel):
    """Schema for updating wallet"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon_name: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_default: Optional[bool] = None
    order_index: Optional[int] = None


class WalletResponse(WalletBase):
    """Schema for wallet response"""
    id: UUID4
    user_id: UUID4
    balance: Decimal
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at', 'deleted_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    @field_serializer('balance')
    def serialize_balance(self, value: Decimal) -> str:
        return str(value)

    class Config:
        from_attributes = True


class WalletListResponse(BaseModel):
    """Response for wallet list"""
    items: List[WalletResponse]
    total: int
