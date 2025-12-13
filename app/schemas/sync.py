"""Sync schemas for hybrid sync functionality"""
from pydantic import BaseModel, UUID4, Field, field_serializer
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from app.utils.time_utils import to_utc_isoformat


class SyncStatus(str, Enum):
    """Sync status for records"""
    SYNCED = "synced"
    PENDING_CREATE = "pending_create"
    PENDING_UPDATE = "pending_update"
    PENDING_DELETE = "pending_delete"
    CONFLICT = "conflict"


class SyncChange(BaseModel):
    """A single change to sync"""
    id: UUID4  # Client-side ID
    server_id: Optional[UUID4] = None  # Server-side ID (null for new records)
    action: str  # 'create', 'update', 'delete'
    data: Dict[str, Any]  # The record data
    client_timestamp: datetime  # When the change was made on client


class SyncPushRequest(BaseModel):
    """Request to push local changes to server"""
    table: str  # Table name
    changes: List[SyncChange]
    client_version: int  # Client's last known server version


class SyncConflict(BaseModel):
    """A sync conflict that needs resolution"""
    client_id: UUID4
    server_id: UUID4
    client_data: Dict[str, Any]
    server_data: Dict[str, Any]
    conflict_type: str  # 'update_conflict', 'delete_conflict'


class SyncPushResponse(BaseModel):
    """Response from push sync"""
    server_version: int  # New server version after push
    accepted: List[UUID4]  # IDs of changes that were accepted
    conflicts: List[SyncConflict]  # Conflicts that need resolution
    id_mapping: Dict[str, str]  # client_id -> server_id for new records


class SyncPullRequest(BaseModel):
    """Request to pull server changes"""
    table: str  # Table name
    since_version: int  # Pull changes since this version


class SyncPullResponse(BaseModel):
    """Response from pull sync"""
    changes: List[Dict[str, Any]]  # Changed records
    server_version: int  # Current server version
    has_more: bool = False  # If there are more changes to pull


class SyncStatusResponse(BaseModel):
    """Overall sync status"""
    tables: Dict[str, Dict[str, Any]]  # table -> {version, count, last_sync}


class SyncLogResponse(BaseModel):
    """Sync log entry"""
    id: UUID4
    user_id: UUID4
    table_name: str
    last_sync_at: Optional[datetime] = None
    last_server_version: int
    created_at: datetime
    updated_at: datetime

    @field_serializer('created_at', 'updated_at', 'last_sync_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return to_utc_isoformat(value)

    class Config:
        from_attributes = True
