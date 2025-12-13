"""Budget CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetWithProgress,
    BudgetListResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


def calculate_budget_progress(db: Session, budget: Budget, user_id: UUID) -> BudgetWithProgress:
    """Calculate budget progress based on transactions"""
    # Build transaction filter
    query = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == budget.is_income,
        Transaction.deleted_at.is_(None),
        Transaction.date >= budget.start_date
    )

    # Filter by end date
    if budget.end_date:
        query = query.filter(Transaction.date <= budget.end_date)

    # Filter by wallets if specified
    if budget.wallet_ids:
        query = query.filter(Transaction.wallet_id.in_(budget.wallet_ids))

    # Filter by categories if specified
    if budget.category_ids:
        query = query.filter(Transaction.category_id.in_(budget.category_ids))

    spent = query.scalar() or Decimal("0")
    remaining = budget.amount - spent
    progress_percent = float(spent / budget.amount * 100) if budget.amount > 0 else 0

    return BudgetWithProgress(
        **BudgetResponse.model_validate(budget).model_dump(),
        spent=spent,
        remaining=remaining,
        progress_percent=min(progress_percent, 100)  # Cap at 100%
    )


@router.get("", response_model=BudgetListResponse)
async def list_budgets(
    is_archived: Optional[bool] = Query(False),
    is_pinned: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all budgets for the current user"""
    query = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    )

    if is_archived is not None:
        query = query.filter(Budget.is_archived == is_archived)
    if is_pinned is not None:
        query = query.filter(Budget.is_pinned == is_pinned)

    total = query.count()
    budgets = query.order_by(Budget.is_pinned.desc(), Budget.name).offset(skip).limit(limit).all()

    return BudgetListResponse(items=budgets, total=total)


@router.get("/with-progress", response_model=list[BudgetWithProgress])
async def list_budgets_with_progress(
    is_archived: Optional[bool] = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all budgets with spending progress"""
    query = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    )

    if is_archived is not None:
        query = query.filter(Budget.is_archived == is_archived)

    budgets = query.order_by(Budget.is_pinned.desc(), Budget.name).all()

    return [calculate_budget_progress(db, b, current_user.id) for b in budgets]


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget"""
    budget = Budget(
        user_id=current_user.id,
        **budget_data.model_dump()
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific budget"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    return budget


@router.get("/{budget_id}/progress", response_model=BudgetWithProgress)
async def get_budget_with_progress(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific budget with spending progress"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    return calculate_budget_progress(db, budget, current_user.id)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: UUID,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a budget"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    # Update fields
    update_data = budget_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(budget, field, value)

    db.commit()
    db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a budget"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id,
        Budget.deleted_at.is_(None)
    ).first()

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )

    budget.deleted_at = utc_now()
    db.commit()
