"""Recurring transaction configuration endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.recurring_config import RecurringConfig
from app.models.transaction import Transaction, TransactionType
from app.schemas.recurring import (
    RecurringConfigCreate,
    RecurringConfigUpdate,
    RecurringConfigResponse,
    RecurringConfigListResponse,
    RecurringTriggerResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


def process_single_recurring(db: Session, config: RecurringConfig) -> list[UUID]:
    """Process a single recurring config, creating transactions as needed"""
    created_ids = []
    today = date.today()

    while config.is_active and config.next_occurrence <= today:
        # Check if ended
        if config.end_date and config.next_occurrence > config.end_date:
            config.is_active = False
            break

        # Get base transaction
        base = db.query(Transaction).filter(
            Transaction.id == config.base_transaction_id,
            Transaction.deleted_at.is_(None)
        ).first()

        if not base:
            config.is_active = False
            break

        # Create new transaction instance
        import uuid
        new_transaction = Transaction(
            id=uuid.uuid4(),
            user_id=config.user_id,
            wallet_id=base.wallet_id,
            category_id=base.category_id,
            payment_method_id=base.payment_method_id,
            amount=base.amount,
            title=base.title,
            notes=base.notes,
            date=config.next_occurrence,
            is_income=base.is_income,
            type=TransactionType.RECURRING_INSTANCE,
            recurring_config_id=config.id
        )
        db.add(new_transaction)
        created_ids.append(new_transaction.id)

        # Calculate next occurrence
        config.next_occurrence = config.calculate_next_occurrence()

    return created_ids


@router.get("", response_model=RecurringConfigListResponse)
async def list_recurring_configs(
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all recurring configurations for the current user"""
    query = db.query(RecurringConfig).filter(
        RecurringConfig.user_id == current_user.id
    )

    if is_active is not None:
        query = query.filter(RecurringConfig.is_active == is_active)

    total = query.count()
    configs = query.order_by(RecurringConfig.next_occurrence).offset(skip).limit(limit).all()

    return RecurringConfigListResponse(items=configs, total=total)


@router.post("", response_model=RecurringConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_config(
    config_data: RecurringConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new recurring configuration"""
    # Verify base transaction belongs to user
    base = db.query(Transaction).filter(
        Transaction.id == config_data.base_transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).first()

    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base transaction not found"
        )

    config = RecurringConfig(
        user_id=current_user.id,
        next_occurrence=config_data.start_date,  # First occurrence is start date
        **config_data.model_dump()
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("/{config_id}", response_model=RecurringConfigResponse)
async def get_recurring_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific recurring configuration"""
    config = db.query(RecurringConfig).filter(
        RecurringConfig.id == config_id,
        RecurringConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring configuration not found"
        )

    return config


@router.put("/{config_id}", response_model=RecurringConfigResponse)
async def update_recurring_config(
    config_id: UUID,
    config_data: RecurringConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a recurring configuration"""
    config = db.query(RecurringConfig).filter(
        RecurringConfig.id == config_id,
        RecurringConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring configuration not found"
        )

    # Update fields
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recurring_config(
    config_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a recurring configuration (does not delete created transactions)"""
    config = db.query(RecurringConfig).filter(
        RecurringConfig.id == config_id,
        RecurringConfig.user_id == current_user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurring configuration not found"
        )

    db.delete(config)
    db.commit()


@router.post("/trigger", response_model=RecurringTriggerResponse)
async def trigger_recurring_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger processing of recurring transactions.
    Creates any pending transactions that are due.
    """
    # Get all active configs with pending occurrences
    configs = db.query(RecurringConfig).filter(
        RecurringConfig.user_id == current_user.id,
        RecurringConfig.is_active == True,
        RecurringConfig.next_occurrence <= date.today()
    ).all()

    all_created_ids = []
    for config in configs:
        created_ids = process_single_recurring(db, config)
        all_created_ids.extend(created_ids)

    db.commit()

    return RecurringTriggerResponse(
        processed_count=len(configs),
        created_transaction_ids=all_created_ids
    )
