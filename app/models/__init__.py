# Import order matters: user models first (referenced by other domains via FK)
from app.models.user import (  # noqa: F401
    User, Profile, KYCCase, SanctionCheck, WalletLink,
    UserRole, UserStatus, KYCCaseStatus, KYCRiskLevel, SanctionCheckStatus,
)
from app.models.patent import (  # noqa: F401
    Patent, PatentDocument, PatentReview,
    PatentStatus, DocumentType, ReviewDecision,
)
from app.models.analytics import (  # noqa: F401
    UserMetricsDaily, PatentMetricsDaily, KYCFunnelStats,
    KYCFunnelStep,
)
from app.models.common import (  # noqa: F401
    AuditLog, WebhookEvent,
    WebhookEventStatus,
)
from app.models.ip_claim import (  # noqa: F401
    IpClaim,
    IpDocument,
    IpReview,
    IpClaimStatus,
    IpReviewDecision,
    TokenRevocation,
)

__all__ = [
    # Users domain
    "User", "Profile", "KYCCase", "SanctionCheck", "WalletLink",
    "UserRole", "UserStatus", "KYCCaseStatus", "KYCRiskLevel", "SanctionCheckStatus",
    # Patents domain
    "Patent", "PatentDocument", "PatentReview",
    "PatentStatus", "DocumentType", "ReviewDecision",
    # Analytics domain
    "UserMetricsDaily", "PatentMetricsDaily", "KYCFunnelStats",
    "KYCFunnelStep",
    # Cross-domain
    "AuditLog", "WebhookEvent",
    "WebhookEventStatus",
    # IP claims domain
    "IpClaim",
    "IpDocument",
    "IpReview",
    "IpClaimStatus",
    "IpReviewDecision",
    "TokenRevocation",
]
