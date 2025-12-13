"""Transaction CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.transaction import Transaction, TransactionType
from app.models.wallet import Wallet
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionBulkCreate
)
from app.utils.time_utils import utc_now

router = APIRouter()


def update_wallet_balance(db: Session, wallet_id: UUID, amount: Decimal, is_income: bool, reverse: bool = False):
    """Update wallet balance after transaction"""
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if wallet:
        if reverse:
            # Reverse the effect (for delete or update)
            if is_income:
                wallet.balance -= amount
            else:
                wallet.balance += amount
        else:
            # Apply the effect
            if is_income:
                wallet.balance += amount
            else:
                wallet.balance -= amount


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    wallet_id: Optional[UUID] = Query(None),
    category_id: Optional[UUID] = Query(None),
    payment_method_id: Optional[UUID] = Query(None),
    is_income: Optional[bool] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    search: Optional[str] = Query(None, description="Search in title and notes"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List transactions with filters"""
    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    )

    # Apply filters
    if wallet_id:
        query = query.filter(Transaction.wallet_id == wallet_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if payment_method_id:
        query = query.filter(Transaction.payment_method_id == payment_method_id)
    if is_income is not None:
        query = query.filter(Transaction.is_income == is_income)
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(or_(
            Transaction.title.ilike(search_pattern),
            Transaction.notes.ilike(search_pattern)
        ))

    total = query.count()
    transactions = query.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(skip).limit(limit).all()

    return TransactionListResponse(items=transactions, total=total)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    # Verify wallet belongs to user
    wallet = db.query(Wallet).filter(
        Wallet.id == transaction_data.wallet_id,
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    transaction = Transaction(
        user_id=current_user.id,
        **transaction_data.model_dump()
    )
    db.add(transaction)

    # Update wallet balance
    update_wallet_balance(db, transaction.wallet_id, transaction.amount, transaction.is_income)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.post("/bulk", response_model=list[TransactionResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_transactions(
    bulk_data: TransactionBulkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk create transactions (for imports)"""
    created_transactions = []

    for transaction_data in bulk_data.transactions:
        # Verify wallet belongs to user
        wallet = db.query(Wallet).filter(
            Wallet.id == transaction_data.wallet_id,
            Wallet.user_id == current_user.id,
            Wallet.deleted_at.is_(None)
        ).first()

        if not wallet:
            continue  # Skip invalid wallets

        transaction = Transaction(
            user_id=current_user.id,
            **transaction_data.model_dump()
        )
        db.add(transaction)
        created_transactions.append(transaction)

        # Update wallet balance
        update_wallet_balance(db, transaction.wallet_id, transaction.amount, transaction.is_income)

    db.commit()

    # Refresh all
    for t in created_transactions:
        db.refresh(t)

    return created_transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Store old values for balance update
    old_amount = transaction.amount
    old_is_income = transaction.is_income
    old_wallet_id = transaction.wallet_id

    # Update fields
    update_data = transaction_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)

    # Update wallet balances
    # First, reverse old transaction effect
    update_wallet_balance(db, old_wallet_id, old_amount, old_is_income, reverse=True)

    # Then apply new transaction effect
    update_wallet_balance(db, transaction.wallet_id, transaction.amount, transaction.is_income)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a transaction"""
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id,
        Transaction.deleted_at.is_(None)
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )

    # Reverse wallet balance effect
    update_wallet_balance(db, transaction.wallet_id, transaction.amount, transaction.is_income, reverse=True)

    # Soft delete
    transaction.deleted_at = utc_now()
    db.commit()
