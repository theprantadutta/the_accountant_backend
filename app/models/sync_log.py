"""Sync log model for tracking synchronization state"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
from app.utils.time_utils import utc_now


class SyncLog(Base):
    """Track synchronization state per user per table"""

    __tablename__ = "sync_logs"

    # Identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Sync details
    table_name = Column(String(50), nullable=False, index=True)
    last_sync_at = Column(DateTime, nullable=True)
    last_server_version = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    user = relationship("User", backref="sync_logs")

    def __repr__(self):
        return f"<SyncLog(id={self.id}, table={self.table_name}, version={self.last_server_version})>"
