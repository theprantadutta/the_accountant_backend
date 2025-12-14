"""Exchange rate schemas for API request/response validation"""
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID


class ExchangeRateBase(BaseModel):
    """Base exchange rate schema"""
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code (ISO 4217)")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code (ISO 4217)")
    api_rate: Optional[Decimal] = Field(None, description="Rate fetched from external API")
    custom_rate: Optional[Decimal] = Field(None, description="User-defined custom rate")
    use_custom_rate: bool = Field(False, description="Whether to use custom rate over API rate")
    api_rate_fetched_at: Optional[datetime] = Field(None, description="When the API rate was last fetched")


class ExchangeRateCreate(ExchangeRateBase):
    """Schema for creating a new exchange rate"""
    id: Optional[UUID] = Field(None, description="Client-generated UUID for sync")


class ExchangeRateUpdate(BaseModel):
    """Schema for updating an exchange rate"""
    api_rate: Optional[Decimal] = None
    custom_rate: Optional[Decimal] = None
    use_custom_rate: Optional[bool] = None
    api_rate_fetched_at: Optional[datetime] = None


class ExchangeRateResponse(ExchangeRateBase):
    """Schema for exchange rate API responses"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    version: int

    class Config:
        from_attributes = True


class ExchangeRateSyncRequest(BaseModel):
    """Schema for syncing exchange rates from client"""
    id: UUID
    from_currency: str
    to_currency: str
    api_rate: Optional[Decimal] = None
    custom_rate: Optional[Decimal] = None
    use_custom_rate: bool = False
    api_rate_fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class BulkApiRatesUpdate(BaseModel):
    """Schema for bulk updating API rates (from external API fetch)"""
    rates: dict[str, Decimal] = Field(..., description="Map of currency code to rate from USD")
    fetched_at: datetime = Field(..., description="When these rates were fetched")


class ConversionRequest(BaseModel):
    """Schema for currency conversion request"""
    amount: Decimal = Field(..., description="Amount to convert")
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)


class ConversionResponse(BaseModel):
    """Schema for currency conversion response"""
    original_amount: Decimal
    converted_amount: Decimal
    from_currency: str
    to_currency: str
    rate_used: Decimal
    is_custom_rate: bool
