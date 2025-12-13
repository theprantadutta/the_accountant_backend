"""In-App Purchase schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class IAPPlatform(str, Enum):
    """IAP platform"""
    ANDROID = "android"
    IOS = "ios"


class IAPProductType(str, Enum):
    """IAP product types"""
    PREMIUM_MONTHLY = "premium_monthly"
    PREMIUM_YEARLY = "premium_yearly"
    PREMIUM_LIFETIME = "premium_lifetime"


class PurchaseVerifyRequest(BaseModel):
    """Request to verify a purchase"""
    product_id: str = Field(..., max_length=100)
    purchase_token: str  # The token/receipt from the store
    platform: IAPPlatform
    order_id: Optional[str] = Field(None, max_length=255)


class PurchaseVerifyResponse(BaseModel):
    """Response from purchase verification"""
    valid: bool
    product_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None

    @field_serializer('expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)


class PurchaseRestoreRequest(BaseModel):
    """Request to restore purchases"""
    platform: IAPPlatform
    purchase_tokens: list[str]  # List of purchase tokens to verify


class PurchaseRestoreResponse(BaseModel):
    """Response from purchase restoration"""
    restored_count: int
    active_subscription: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_serializer('expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)


class SubscriptionStatusResponse(BaseModel):
    """Response for subscription status"""
    is_premium: bool
    subscription_tier: str
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None

    @field_serializer('expires_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)
