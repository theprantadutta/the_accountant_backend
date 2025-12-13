"""Objective (Goals & Savings) CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.objective import Objective, objective_transactions, ObjectiveType
from app.models.transaction import Transaction
from app.schemas.objective import (
    ObjectiveCreate,
    ObjectiveUpdate,
    ObjectiveResponse,
    ObjectiveWithProgress,
    ObjectiveListResponse,
    ObjectiveTransactionLink,
    ObjectiveTransactionResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


def calculate_objective_progress(db: Session, objective: Objective, user_id: UUID) -> ObjectiveWithProgress:
    """Calculate objective progress based on linked transactions"""
    # Sum linked transactions
    current_amount = db.query(func.sum(Transaction.amount)).join(
        objective_transactions,
        Transaction.id == objective_transactions.c.transaction_id
    ).filter(
        objective_transactions.c.objective_id == objective.id,
        Transaction.deleted_at.is_(None)
    ).scalar() or Decimal("0")

    remaining = objective.target_amount - current_amount
    progress_percent = float(current_amount / objective.target_amount * 100) if objective.target_amount > 0 else 0

    # Calculate days remaining and daily target
    days_remaining = None
    daily_target = None
    if objective.end_date:
        days = (objective.end_date - date.today()).days
        days_remaining = max(days, 0)
        if days_remaining > 0 and remaining > 0:
            daily_target = remaining / Decimal(days_remaining)

    return ObjectiveWithProgress(
        **ObjectiveResponse.model_validate(objective).model_dump(),
        current_amount=current_amount,
        progress_percent=min(progress_percent, 100),
        remaining_amount=max(remaining, Decimal("0")),
        days_remaining=days_remaining,
        daily_target=daily_target
    )


@router.get("", response_model=ObjectiveListResponse)
async def list_objectives(
    objective_type: Optional[ObjectiveType] = Query(None),
    is_archived: Optional[bool] = Query(False),
    is_pinned: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all objectives for the current user"""
    query = db.query(Objective).filter(
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    )

    if objective_type:
        query = query.filter(Objective.type == objective_type)
    if is_archived is not None:
        query = query.filter(Objective.is_archived == is_archived)
    if is_pinned is not None:
        query = query.filter(Objective.is_pinned == is_pinned)

    total = query.count()
    objectives = query.order_by(Objective.is_pinned.desc(), Objective.name).offset(skip).limit(limit).all()

    return ObjectiveListResponse(items=objectives, total=total)


@router.get("/with-progress", response_model=list[ObjectiveWithProgress])
async def list_objectives_with_progress(
    objective_type: Optional[ObjectiveType] = Query(None),
    is_archived: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all objectives with progress details"""
    query = db.query(Objective).filter(
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    )

    if objective_type:
        query = query.filter(Objective.type == objective_type)
    if is_archived is not None:
        query = query.filter(Objective.is_archived == is_archived)

    objectives = query.order_by(Objective.is_pinned.desc(), Objective.name).all()

    return [calculate_objective_progress(db, obj, current_user.id) for obj in objectives]


@router.post("", response_model=ObjectiveResponse, status_code=status.HTTP_201_CREATED)
async def create_objective(
    objective_data: ObjectiveCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new objective"""
    objective = Objective(
        user_id=current_user.id,
        **objective_data.model_dump()
    )
    db.add(objective)
    db.commit()
    db.refresh(objective)
    return objective


@router.get("/{objective_id}", response_model=ObjectiveResponse)
async def get_objective(
    objective_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific objective"""
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    return objective


@router.get("/{objective_id}/progress", response_model=ObjectiveWithProgress)
async def get_objective_with_progress(
    objective_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific objective with progress details"""
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    return calculate_objective_progress(db, objective, current_user.id)


@router.put("/{objective_id}", response_model=ObjectiveResponse)
async def update_objective(
    objective_id: UUID,
    objective_data: ObjectiveUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an objective"""
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    # Update fields
    update_data = objective_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(objective, field, value)

    db.commit()
    db.refresh(objective)
    return objective


@router.delete("/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_objective(
    objective_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete an objective"""
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    objective.deleted_at = utc_now()
    db.commit()


# Transaction linking endpoints
@router.post("/{objective_id}/transactions", status_code=status.HTTP_201_CREATED)
async def link_transaction_to_objective(
    objective_id: UUID,
    link_data: ObjectiveTransactionLink,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Link a transaction to an objective"""
    # Verify objective exists
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id,
        Objective.deleted_at.is_(None)
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    # Verify transaction exists
    transaction = db.query(Transaction).filter(
        Transaction.id == link_data.transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Check if already linked
    existing = db.execute(
        objective_transactions.select().where(
            objective_transactions.c.objective_id == objective_id,
            objective_transactions.c.transaction_id == link_data.transaction_id
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction already linked to this objective"
        )

    # Create link
    import uuid
    db.execute(
        objective_transactions.insert().values(
            id=uuid.uuid4(),
            objective_id=objective_id,
            transaction_id=link_data.transaction_id,
            created_at=utc_now()
        )
    )
    db.commit()

    return {"message": "Transaction linked successfully"}


@router.delete("/{objective_id}/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unlink_transaction_from_objective(
    objective_id: UUID,
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unlink a transaction from an objective"""
    # Verify objective belongs to user
    objective = db.query(Objective).filter(
        Objective.id == objective_id,
        Objective.user_id == current_user.id
    ).first()

    if not objective:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )

    # Delete link
    result = db.execute(
        objective_transactions.delete().where(
            objective_transactions.c.objective_id == objective_id,
            objective_transactions.c.transaction_id == transaction_id
        )
    )

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )

    db.commit()
