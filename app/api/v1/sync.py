"""Sync API endpoints for hybrid sync functionality"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from uuid import UUID
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.sync_log import SyncLog
from app.models.category import Category
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.objective import Objective
from app.models.recurring_config import RecurringConfig
from app.models.associated_title import AssociatedTitle
from app.models.payment_method import PaymentMethod
from app.schemas.sync import (
    SyncPushRequest,
    SyncPushResponse,
    SyncPullRequest,
    SyncPullResponse,
    SyncStatusResponse,
    SyncConflict
)
from app.utils.time_utils import utc_now

router = APIRouter()

# Mapping of table names to model classes
TABLE_MODELS = {
    "categories": Category,
    "wallets": Wallet,
    "transactions": Transaction,
    "budgets": Budget,
    "objectives": Objective,
    "recurring_configs": RecurringConfig,
    "associated_titles": AssociatedTitle,
    "payment_methods": PaymentMethod,
}

# Sync order (respecting foreign key constraints)
SYNC_ORDER = [
    "categories",
    "wallets",
    "payment_methods",
    "transactions",
    "recurring_configs",
    "budgets",
    "objectives",
    "associated_titles",
]


def get_or_create_sync_log(db: Session, user_id: UUID, table_name: str) -> SyncLog:
    """Get or create sync log for a user/table combination"""
    sync_log = db.query(SyncLog).filter(
        SyncLog.user_id == user_id,
        SyncLog.table_name == table_name
    ).first()

    if not sync_log:
        sync_log = SyncLog(
            user_id=user_id,
            table_name=table_name,
            last_server_version=0
        )
        db.add(sync_log)
        db.commit()
        db.refresh(sync_log)

    return sync_log


@router.get("/status", response_model=SyncStatusResponse)
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current sync status for all tables"""
    tables: Dict[str, Dict[str, Any]] = {}

    for table_name, model in TABLE_MODELS.items():
        # Get count
        count = db.query(func.count(model.id)).filter(
            model.user_id == current_user.id
        ).scalar()

        # Get sync log
        sync_log = db.query(SyncLog).filter(
            SyncLog.user_id == current_user.id,
            SyncLog.table_name == table_name
        ).first()

        tables[table_name] = {
            "version": sync_log.last_server_version if sync_log else 0,
            "count": count,
            "last_sync": sync_log.last_sync_at.isoformat() if sync_log and sync_log.last_sync_at else None
        }

    return SyncStatusResponse(tables=tables)


@router.post("/push", response_model=SyncPushResponse)
async def push_changes(
    push_data: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Push local changes to server.
    Returns accepted changes, conflicts, and ID mapping for new records.
    """
    table_name = push_data.table
    if table_name not in TABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown table: {table_name}"
        )

    model = TABLE_MODELS[table_name]
    sync_log = get_or_create_sync_log(db, current_user.id, table_name)

    accepted: list[UUID] = []
    conflicts: list[SyncConflict] = []
    id_mapping: Dict[str, str] = {}  # client_id -> server_id

    for change in push_data.changes:
        try:
            if change.action == "create":
                # Create new record
                import uuid
                server_id = uuid.uuid4()
                record_data = {**change.data, "user_id": current_user.id, "id": server_id}

                # Remove any client-specific fields
                record_data.pop("sync_status", None)
                record_data.pop("local_id", None)

                new_record = model(**record_data)
                db.add(new_record)
                accepted.append(change.id)
                id_mapping[str(change.id)] = str(server_id)

            elif change.action == "update":
                # Find existing record
                record = db.query(model).filter(
                    model.id == change.server_id,
                    model.user_id == current_user.id
                ).first()

                if not record:
                    # Record doesn't exist, treat as conflict
                    conflicts.append(SyncConflict(
                        client_id=change.id,
                        server_id=change.server_id,
                        client_data=change.data,
                        server_data={},
                        conflict_type="delete_conflict"
                    ))
                    continue

                # Check for conflicts (last-write-wins by default)
                # In a more sophisticated system, we'd compare timestamps
                update_data = change.data
                update_data.pop("id", None)
                update_data.pop("user_id", None)
                update_data.pop("sync_status", None)

                for field, value in update_data.items():
                    if hasattr(record, field):
                        setattr(record, field, value)

                accepted.append(change.id)

            elif change.action == "delete":
                # Soft delete if model supports it
                record = db.query(model).filter(
                    model.id == change.server_id,
                    model.user_id == current_user.id
                ).first()

                if record:
                    if hasattr(record, 'deleted_at'):
                        record.deleted_at = utc_now()
                    else:
                        db.delete(record)
                    accepted.append(change.id)

        except Exception as e:
            # Log error but continue processing other changes
            print(f"Error processing change {change.id}: {e}")
            continue

    # Update sync log
    sync_log.last_server_version += 1
    sync_log.last_sync_at = utc_now()

    db.commit()

    return SyncPushResponse(
        server_version=sync_log.last_server_version,
        accepted=accepted,
        conflicts=conflicts,
        id_mapping=id_mapping
    )


@router.post("/pull", response_model=SyncPullResponse)
async def pull_changes(
    pull_data: SyncPullRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Pull server changes since a given version.
    Returns changed records and current server version.
    """
    table_name = pull_data.table
    if table_name not in TABLE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown table: {table_name}"
        )

    model = TABLE_MODELS[table_name]
    sync_log = get_or_create_sync_log(db, current_user.id, table_name)

    # For simplicity, return all records if since_version is 0
    # In a production system, you'd track changes with versions
    query = db.query(model).filter(model.user_id == current_user.id)

    # If there's a deleted_at column, include it but don't filter
    records = query.all()

    # Convert to dicts
    changes = []
    for record in records:
        record_dict = {}
        for column in model.__table__.columns:
            value = getattr(record, column.name)
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            elif isinstance(value, UUID):
                value = str(value)
            record_dict[column.name] = value
        changes.append(record_dict)

    return SyncPullResponse(
        changes=changes,
        server_version=sync_log.last_server_version,
        has_more=False
    )
