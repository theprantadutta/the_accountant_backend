"""Transaction schemas"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class TransactionType(str, Enum):
    """Transaction type enum"""
    REGULAR = "regular"
    TRANSFER = "transfer"
    RECURRING_INSTANCE = "recurring_instance"


class TransactionSpecialType(int, Enum):
    """Transaction special type enum (like Cashew)"""
    NONE = 0           # Default transaction
    UPCOMING = 1       # Future unpaid transaction
    SUBSCRIPTION = 2   # Subscription payment
    REPETITIVE = 3     # Repetitive transaction
    CREDIT = 4         # Money lent to someone
    DEBT = 5           # Money borrowed from someone


class TransactionBase(BaseModel):
    """Base transaction schema"""
    wallet_id: UUID4
    category_id: Optional[UUID4] = None
    payment_method_id: Optional[UUID4] = None
    amount: Decimal = Field(..., decimal_places=2)
    title: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None
    date: datetime
    is_income: bool = False
    type: TransactionType = TransactionType.REGULAR
    # Special type fields (Cashew parity)
    special_type: Optional[int] = 0
    is_paid: bool = True
    original_due_date: Optional[datetime] = None
    skip_paid: bool = False


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction"""
    paired_transaction_id: Optional[UUID4] = None
    recurring_config_id: Optional[UUID4] = None
    receipt_image_url: Optional[str] = Field(None, max_length=500)


class TransactionUpdate(BaseModel):
    """Schema for updating transaction"""
    wallet_id: Optional[UUID4] = None
    category_id: Optional[UUID4] = None
    payment_method_id: Optional[UUID4] = None
    amount: Optional[Decimal] = Field(None, decimal_places=2)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    notes: Optional[str] = None
    date: Optional[datetime] = None
    is_income: Optional[bool] = None
    receipt_image_url: Optional[str] = Field(None, max_length=500)
    # Special type fields
    special_type: Optional[int] = None
    is_paid: Optional[bool] = None
    original_due_date: Optional[datetime] = None
    skip_paid: Optional[bool] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""
    id: UUID4
    user_id: UUID4
    paired_transaction_id: Optional[UUID4] = None
    recurring_config_id: Optional[UUID4] = None
    receipt_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at', 'deleted_at', 'date', 'original_due_date')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        return str(value)

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """Response for transaction list"""
    items: List[TransactionResponse]
    total: int


class TransactionBulkCreate(BaseModel):
    """Schema for bulk creating transactions"""
    transactions: List[TransactionCreate]


class TransactionFilter(BaseModel):
    """Filter options for transaction list"""
    wallet_id: Optional[UUID4] = None
    category_id: Optional[UUID4] = None
    payment_method_id: Optional[UUID4] = None
    is_income: Optional[bool] = None
    type: Optional[TransactionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    search: Optional[str] = None  # Search in title and notes
    # Special type filters
    special_type: Optional[int] = None
    is_paid: Optional[bool] = None
    include_credit_debt: Optional[bool] = None  # Include credit & debt transactions
