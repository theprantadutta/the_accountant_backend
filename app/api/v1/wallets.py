"""Wallet CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import (
    WalletCreate,
    WalletUpdate,
    WalletResponse,
    WalletListResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


@router.get("", response_model=WalletListResponse)
async def list_wallets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all wallets for the current user"""
    query = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    )

    total = query.count()
    wallets = query.order_by(Wallet.order_index, Wallet.name).offset(skip).limit(limit).all()

    return WalletListResponse(items=wallets, total=total)


@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    wallet_data: WalletCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new wallet"""
    # If this is set as default, unset other defaults
    if wallet_data.is_default:
        db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.is_default == True
        ).update({"is_default": False})

    wallet = Wallet(
        user_id=current_user.id,
        **wallet_data.model_dump()
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/default", response_model=WalletResponse)
async def get_default_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the default wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.is_default == True,
        Wallet.deleted_at.is_(None)
    ).first()

    if not wallet:
        # Return first wallet if no default set
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.deleted_at.is_(None)
        ).order_by(Wallet.created_at).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No wallets found"
        )

    return wallet


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    return wallet


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(
    wallet_id: UUID,
    wallet_data: WalletUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    # If setting as default, unset others
    if wallet_data.is_default:
        db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.id != wallet_id,
            Wallet.is_default == True
        ).update({"is_default": False})

    # Update fields
    update_data = wallet_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wallet, field, value)

    db.commit()
    db.refresh(wallet)
    return wallet


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    wallet_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a wallet"""
    wallet = db.query(Wallet).filter(
        Wallet.id == wallet_id,
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    ).first()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )

    # Check if this is the only wallet
    wallet_count = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.deleted_at.is_(None)
    ).count()

    if wallet_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last wallet"
        )

    # Soft delete
    wallet.deleted_at = utc_now()
    db.commit()
