"""Associated titles (Smart Categorization) endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.associated_title import AssociatedTitle
from app.models.category import Category
from app.schemas.associated_title import (
    AssociatedTitleCreate,
    AssociatedTitleUpdate,
    AssociatedTitleResponse,
    AssociatedTitleListResponse,
    CategorySuggestion
)

router = APIRouter()


@router.get("", response_model=AssociatedTitleListResponse)
async def list_associated_titles(
    category_id: UUID = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all associated titles for the current user"""
    query = db.query(AssociatedTitle).filter(
        AssociatedTitle.user_id == current_user.id
    )

    if category_id:
        query = query.filter(AssociatedTitle.category_id == category_id)

    total = query.count()
    titles = query.order_by(AssociatedTitle.title).offset(skip).limit(limit).all()

    return AssociatedTitleListResponse(items=titles, total=total)


@router.post("", response_model=AssociatedTitleResponse, status_code=status.HTTP_201_CREATED)
async def create_associated_title(
    title_data: AssociatedTitleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new associated title for smart categorization"""
    # Verify category belongs to user
    category = db.query(Category).filter(
        Category.id == title_data.category_id,
        Category.user_id == current_user.id,
        Category.deleted_at.is_(None)
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Normalize title (lowercase)
    normalized_title = title_data.title.lower().strip()

    # Check if already exists
    existing = db.query(AssociatedTitle).filter(
        AssociatedTitle.user_id == current_user.id,
        AssociatedTitle.title == normalized_title
    ).first()

    if existing:
        # Update existing instead of creating duplicate
        existing.category_id = title_data.category_id
        existing.is_exact_match = title_data.is_exact_match
        db.commit()
        db.refresh(existing)
        return existing

    associated_title = AssociatedTitle(
        user_id=current_user.id,
        title=normalized_title,
        category_id=title_data.category_id,
        is_exact_match=title_data.is_exact_match
    )
    db.add(associated_title)
    db.commit()
    db.refresh(associated_title)
    return associated_title


@router.get("/suggest", response_model=CategorySuggestion)
async def suggest_category(
    title: str = Query(..., description="Transaction title to get suggestion for"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category suggestion based on transaction title"""
    normalized_title = title.lower().strip()

    # First, check exact matches
    exact_match = db.query(AssociatedTitle).filter(
        AssociatedTitle.user_id == current_user.id,
        AssociatedTitle.is_exact_match == True,
        AssociatedTitle.title == normalized_title
    ).first()

    if exact_match:
        return CategorySuggestion(
            category_id=exact_match.category_id,
            confidence="exact",
            matched_title=exact_match.title
        )

    # Then, check contains matches
    contains_matches = db.query(AssociatedTitle).filter(
        AssociatedTitle.user_id == current_user.id,
        AssociatedTitle.is_exact_match == False
    ).all()

    for match in contains_matches:
        if match.title in normalized_title:
            return CategorySuggestion(
                category_id=match.category_id,
                confidence="contains",
                matched_title=match.title
            )

    # No match found
    return CategorySuggestion(
        category_id=None,
        confidence="none",
        matched_title=None
    )


@router.get("/{title_id}", response_model=AssociatedTitleResponse)
async def get_associated_title(
    title_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific associated title"""
    title = db.query(AssociatedTitle).filter(
        AssociatedTitle.id == title_id,
        AssociatedTitle.user_id == current_user.id
    ).first()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated title not found"
        )

    return title


@router.put("/{title_id}", response_model=AssociatedTitleResponse)
async def update_associated_title(
    title_id: UUID,
    title_data: AssociatedTitleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an associated title"""
    title = db.query(AssociatedTitle).filter(
        AssociatedTitle.id == title_id,
        AssociatedTitle.user_id == current_user.id
    ).first()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated title not found"
        )

    # Update fields
    update_data = title_data.model_dump(exclude_unset=True)
    if "title" in update_data:
        update_data["title"] = update_data["title"].lower().strip()

    for field, value in update_data.items():
        setattr(title, field, value)

    db.commit()
    db.refresh(title)
    return title


@router.delete("/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_associated_title(
    title_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an associated title"""
    title = db.query(AssociatedTitle).filter(
        AssociatedTitle.id == title_id,
        AssociatedTitle.user_id == current_user.id
    ).first()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated title not found"
        )

    db.delete(title)
    db.commit()
