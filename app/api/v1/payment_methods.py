"""Payment method CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    PaymentMethodResponse,
    PaymentMethodListResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


@router.get("", response_model=PaymentMethodListResponse)
async def list_payment_methods(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all payment methods for the current user"""
    query = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.deleted_at.is_(None)
    )

    total = query.count()
    payment_methods = query.order_by(PaymentMethod.name).offset(skip).limit(limit).all()

    return PaymentMethodListResponse(items=payment_methods, total=total)


@router.post("", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payment_method_data: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment method"""
    # If this is set as default, unset other defaults
    if payment_method_data.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == True
        ).update({"is_default": False})

    payment_method = PaymentMethod(
        user_id=current_user.id,
        **payment_method_data.model_dump()
    )
    db.add(payment_method)
    db.commit()
    db.refresh(payment_method)
    return payment_method


@router.get("/{payment_method_id}", response_model=PaymentMethodResponse)
async def get_payment_method(
    payment_method_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific payment method"""
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id,
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.deleted_at.is_(None)
    ).first()

    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )

    return payment_method


@router.put("/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: UUID,
    payment_method_data: PaymentMethodUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a payment method"""
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id,
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.deleted_at.is_(None)
    ).first()

    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )

    # If setting as default, unset others
    if payment_method_data.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.id != payment_method_id,
            PaymentMethod.is_default == True
        ).update({"is_default": False})

    # Update fields
    update_data = payment_method_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment_method, field, value)

    db.commit()
    db.refresh(payment_method)
    return payment_method


@router.delete("/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a payment method"""
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment_method_id,
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.deleted_at.is_(None)
    ).first()

    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found"
        )

    # Soft delete
    payment_method.deleted_at = utc_now()
    db.commit()
