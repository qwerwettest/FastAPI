"""
SQLAlchemy models for IPChain MVP.

Canonical schema according to specification.
"""

from app.core.database import Base

# Import all models to ensure they are registered with Base.metadata
from app.models.user import (
    User,
    Profile,
    KYCCase,
    SanctionCheck,
    WalletLink,
    UserRole,
    UserStatus,
    KYCCaseStatus,
    SanctionCheckStatus,
)

from app.models.ip_claim import (
    IpClaim,
    IpDocument,
    IpReview,
    Asset,
    TokenIssuance,
    Listing,
    Order,
    Trade,
    IpClaimStatus,
    DocumentType,
    ReviewDecision,
)

from app.models.audit_log import (
    AuditLog,
    WebhookEvent,
    WebhookEventStatus,
)

# Export for convenience
__all__ = [
    # Base
    "Base",
    # User & Identity
    "User",
    "Profile",
    "KYCCase",
    "SanctionCheck",
    "WalletLink",
    "UserRole",
    "UserStatus",
    "KYCCaseStatus",
    "SanctionCheckStatus",
    # IP Claims & Assets
    "IpClaim",
    "IpDocument",
    "IpReview",
    "Asset",
    "TokenIssuance",
    "Listing",
    "Order",
    "Trade",
    "IpClaimStatus",
    "DocumentType",
    "ReviewDecision",
    # Audit & Webhooks
    "AuditLog",
    "WebhookEvent",
    "WebhookEventStatus",
]
