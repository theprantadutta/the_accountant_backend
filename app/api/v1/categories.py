"""Category CRUD endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryWithSubcategories,
    CategoryListResponse
)
from app.utils.time_utils import utc_now

router = APIRouter()


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    include_subcategories: bool = Query(False, description="Include nested subcategories"),
    is_income: Optional[bool] = Query(None, description="Filter by income/expense type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all categories for the current user"""
    query = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None)
    )

    if is_income is not None:
        query = query.filter(Category.is_income == is_income)

    if not include_subcategories:
        # Only get parent categories
        query = query.filter(Category.main_category_id.is_(None))

    total = query.count()
    categories = query.order_by(Category.order_index, Category.name).offset(skip).limit(limit).all()

    return CategoryListResponse(items=categories, total=total)


@router.get("/with-subcategories", response_model=list[CategoryWithSubcategories])
async def list_categories_with_subcategories(
    is_income: Optional[bool] = Query(None, description="Filter by income/expense type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all parent categories with their subcategories nested"""
    query = db.query(Category).filter(
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None),
        Category.main_category_id.is_(None)  # Only parents
    )

    if is_income is not None:
        query = query.filter(Category.is_income == is_income)

    parents = query.order_by(Category.order_index, Category.name).all()

    result = []
    for parent in parents:
        subcategories = db.query(Category).filter(
            Category.main_category_id == parent.id,
            Category.deleted_at.is_(None)
        ).order_by(Category.order_index, Category.name).all()

        result.append(CategoryWithSubcategories(
            **CategoryResponse.model_validate(parent).model_dump(),
            subcategories=subcategories
        ))

    return result


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    # If subcategory, verify parent exists and belongs to user
    if category_data.main_category_id:
        parent = db.query(Category).filter(
            Category.id == category_data.main_category_id,
            Category.user_id == current_user.id,
            Category.deleted_at.is_(None)
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

    category = Category(
        user_id=current_user.id,
        **category_data.model_dump()
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific category"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None)
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a category"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None)
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # If updating parent, verify it exists
    if category_data.main_category_id:
        parent = db.query(Category).filter(
            Category.id == category_data.main_category_id,
            Category.user_id == current_user.id,
            Category.deleted_at.is_(None)
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )

    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete a category"""
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None)
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Soft delete
    category.deleted_at = utc_now()

    # Also soft delete subcategories
    db.query(Category).filter(
        Category.main_category_id == category_id,
        Category.deleted_at.is_(None)
    ).update({"deleted_at": utc_now()})

    db.commit()
