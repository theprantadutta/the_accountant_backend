"""Exchange rates CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.exchange_rate import ExchangeRate
from app.schemas.exchange_rate import (
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateResponse,
    BulkApiRatesUpdate,
    ConversionRequest,
    ConversionResponse,
)
from app.utils.time_utils import utc_now

router = APIRouter()


@router.get("", response_model=list[ExchangeRateResponse])
async def list_exchange_rates(
    from_currency: Optional[str] = Query(None, description="Filter by source currency"),
    to_currency: Optional[str] = Query(None, description="Filter by target currency"),
    custom_only: bool = Query(False, description="Only return custom rate overrides"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all exchange rates for the current user"""
    query = db.query(ExchangeRate).filter(ExchangeRate.user_id == current_user.id)

    if from_currency:
        query = query.filter(ExchangeRate.from_currency == from_currency.upper())
    if to_currency:
        query = query.filter(ExchangeRate.to_currency == to_currency.upper())
    if custom_only:
        query = query.filter(ExchangeRate.use_custom_rate == True)

    rates = query.order_by(ExchangeRate.from_currency, ExchangeRate.to_currency).all()
    return rates


@router.post("", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_exchange_rate(
    rate_data: ExchangeRateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update an exchange rate (upsert by currency pair)"""
    # Check for existing rate
    existing = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.from_currency == rate_data.from_currency.upper(),
        ExchangeRate.to_currency == rate_data.to_currency.upper()
    ).first()

    if existing:
        # Update existing
        for field, value in rate_data.model_dump(exclude={'id'}, exclude_unset=True).items():
            if field in ('from_currency', 'to_currency'):
                value = value.upper() if value else value
            setattr(existing, field, value)
        existing.updated_at = utc_now()
        existing.version = (existing.version or 0) + 1
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new
        rate = ExchangeRate(
            id=rate_data.id if rate_data.id else None,
            user_id=current_user.id,
            from_currency=rate_data.from_currency.upper(),
            to_currency=rate_data.to_currency.upper(),
            api_rate=rate_data.api_rate,
            custom_rate=rate_data.custom_rate,
            use_custom_rate=rate_data.use_custom_rate,
            api_rate_fetched_at=rate_data.api_rate_fetched_at,
        )
        db.add(rate)
        db.commit()
        db.refresh(rate)
        return rate


@router.get("/rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get exchange rate for a specific currency pair"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.from_currency == from_currency.upper(),
        ExchangeRate.to_currency == to_currency.upper()
    ).first()

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exchange rate not found for {from_currency}/{to_currency}"
        )

    return rate


@router.get("/{rate_id}", response_model=ExchangeRateResponse)
async def get_exchange_rate_by_id(
    rate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific exchange rate by ID"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.id == rate_id,
        ExchangeRate.user_id == current_user.id
    ).first()

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )

    return rate


@router.put("/{rate_id}", response_model=ExchangeRateResponse)
async def update_exchange_rate(
    rate_id: UUID,
    rate_data: ExchangeRateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an exchange rate"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.id == rate_id,
        ExchangeRate.user_id == current_user.id
    ).first()

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )

    # Update fields
    update_data = rate_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rate, field, value)

    rate.updated_at = utc_now()
    rate.version = (rate.version or 0) + 1
    db.commit()
    db.refresh(rate)
    return rate


@router.delete("/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange_rate(
    rate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an exchange rate"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.id == rate_id,
        ExchangeRate.user_id == current_user.id
    ).first()

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exchange rate not found"
        )

    db.delete(rate)
    db.commit()


@router.post("/bulk-update-api-rates", response_model=dict)
async def bulk_update_api_rates(
    data: BulkApiRatesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update API rates (from external API fetch)

    Rates should be provided as USD-based rates (e.g., {"EUR": 0.95, "GBP": 0.79})
    """
    updated_count = 0
    created_count = 0

    for currency, rate_value in data.rates.items():
        currency_upper = currency.upper()
        if currency_upper == 'USD':
            continue

        existing = db.query(ExchangeRate).filter(
            ExchangeRate.user_id == current_user.id,
            ExchangeRate.from_currency == 'USD',
            ExchangeRate.to_currency == currency_upper
        ).first()

        if existing:
            existing.api_rate = rate_value
            existing.api_rate_fetched_at = data.fetched_at
            existing.updated_at = utc_now()
            existing.version = (existing.version or 0) + 1
            updated_count += 1
        else:
            new_rate = ExchangeRate(
                user_id=current_user.id,
                from_currency='USD',
                to_currency=currency_upper,
                api_rate=rate_value,
                api_rate_fetched_at=data.fetched_at,
                use_custom_rate=False,
            )
            db.add(new_rate)
            created_count += 1

    db.commit()

    return {
        "message": "API rates updated",
        "updated": updated_count,
        "created": created_count,
        "total": len(data.rates)
    }


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    data: ConversionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Convert amount between currencies using stored rates"""
    from_currency = data.from_currency.upper()
    to_currency = data.to_currency.upper()

    # Same currency = no conversion
    if from_currency == to_currency:
        return ConversionResponse(
            original_amount=data.amount,
            converted_amount=data.amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate_used=Decimal('1'),
            is_custom_rate=False
        )

    # Try to find direct rate
    direct_rate = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.from_currency == from_currency,
        ExchangeRate.to_currency == to_currency
    ).first()

    if direct_rate:
        rate = direct_rate.custom_rate if direct_rate.use_custom_rate else direct_rate.api_rate
        if rate:
            return ConversionResponse(
                original_amount=data.amount,
                converted_amount=data.amount * rate,
                from_currency=from_currency,
                to_currency=to_currency,
                rate_used=rate,
                is_custom_rate=direct_rate.use_custom_rate
            )

    # Try conversion via USD
    from_usd_rate = None
    to_usd_rate = None

    if from_currency == 'USD':
        from_usd_rate = Decimal('1')
    else:
        from_rate = db.query(ExchangeRate).filter(
            ExchangeRate.user_id == current_user.id,
            ExchangeRate.from_currency == 'USD',
            ExchangeRate.to_currency == from_currency
        ).first()
        if from_rate:
            rate = from_rate.custom_rate if from_rate.use_custom_rate else from_rate.api_rate
            if rate:
                from_usd_rate = rate

    if to_currency == 'USD':
        to_usd_rate = Decimal('1')
    else:
        to_rate = db.query(ExchangeRate).filter(
            ExchangeRate.user_id == current_user.id,
            ExchangeRate.from_currency == 'USD',
            ExchangeRate.to_currency == to_currency
        ).first()
        if to_rate:
            rate = to_rate.custom_rate if to_rate.use_custom_rate else to_rate.api_rate
            if rate:
                to_usd_rate = rate

    if from_usd_rate and to_usd_rate:
        # Convert: amount * (to_rate / from_rate)
        conversion_rate = to_usd_rate / from_usd_rate
        return ConversionResponse(
            original_amount=data.amount,
            converted_amount=data.amount * conversion_rate,
            from_currency=from_currency,
            to_currency=to_currency,
            rate_used=conversion_rate,
            is_custom_rate=False
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"No exchange rate available for {from_currency} to {to_currency}"
    )


@router.delete("/custom/{from_currency}/{to_currency}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_custom_rate(
    from_currency: str,
    to_currency: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear custom rate override (use API rate instead)"""
    rate = db.query(ExchangeRate).filter(
        ExchangeRate.user_id == current_user.id,
        ExchangeRate.from_currency == from_currency.upper(),
        ExchangeRate.to_currency == to_currency.upper()
    ).first()

    if rate:
        rate.custom_rate = None
        rate.use_custom_rate = False
        rate.updated_at = utc_now()
        rate.version = (rate.version or 0) + 1
        db.commit()
