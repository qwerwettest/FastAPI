"""
Audit log and webhook event models.

Canonical schema according to IPChain MVP specification.
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    String, DateTime, ForeignKey,
    Index, JSON, Enum as SAEnum,
)
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class WebhookEventStatus(str, enum.Enum):
    """Webhook event processing status."""
    received = "received"
    processed = "processed"
    failed = "failed"
    dead_letter = "dead_letter"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class AuditLog(Base):
    """
    Immutable audit trail for all critical platform actions.
    
    Maps to: audit_logs table
    
    Logged events:
    - Successful/failed login attempts
    - IP claim creation and status changes
    - Review decisions (approve/reject/request_more_info)
    - Token mint operations
    - Trade settlements
    
    PII note: payload should NOT contain raw PII - only business context
    such as old/new status, external IDs, checksums.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_actor_created", "actor_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    # NULL for system-initiated actions
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Non-PII business details: old/new status, external IDs, checksums
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    actor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[actor_id], back_populates="audit_logs"
    )


class WebhookEvent(Base):
    """
    Inbound webhook events from external systems.
    
    Maps to: webhook_events table
    
    Sources:
    - KYC providers (verification results)
    - USPTO API (patent status updates)
    - Other integrations
    
    Security: All webhooks must verify signature and idempotency before processing.
    Raw payload stored for audit/debugging.
    """
    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_events_source_external", "source", "external_id"),
        Index("ix_webhook_events_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum(*[s.value for s in WebhookEventStatus], name="webhook_event_status"),
        nullable=False,
        default=WebhookEventStatus.received,
    )
    # Raw payload - should be encrypted/pseudonymised per data policy
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
