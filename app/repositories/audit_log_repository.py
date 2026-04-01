"""
Audit log repository - data access layer for AuditLog entity.
"""
import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """Repository for Audit Log operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        actor_id: Optional[uuid.UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[str],
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create a new audit log entry."""
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        self.session.add(audit_log)
        await self.session.flush()
        await self.session.refresh(audit_log)
        return audit_log

    async def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Get audit logs for a specific entity."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.entity_type == entity_type)
            .where(AuditLog.entity_id == entity_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_actor(
        self,
        actor_id: uuid.UUID,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Get audit logs for a specific actor."""
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == actor_id)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get all audit logs with pagination."""
        result = await self.session.execute(
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
