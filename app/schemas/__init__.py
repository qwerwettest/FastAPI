# Pydantic schemas for request/response validation

from app.schemas.auth import (
    Token,
    TokenPayload,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    AuthUserResponse,
    AuthenticatedUser,
)

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserRead,
    UserWithProfileRead,
    UserList,
    ProfileRead,
    ProfileUpdate,
    RoleStatusResponse,
)

from app.schemas.patent import (
    PatentPrecheckRequest,
    PatentPrecheckResponse,
)

from app.schemas.ip_claim import (
    CreateIpClaimRequest,
    IpClaimFilterRequest,
    IpClaimResponse,
    IpClaimListResponse,
    UploadDocumentResponse,
    DocumentListResponse,
    IpClaimReviewRequest,
    IpReviewResponse,
)

__all__ = [
    # Auth
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "AuthUserResponse",
    "AuthenticatedUser",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserWithProfileRead",
    "UserList",
    "ProfileRead",
    "ProfileUpdate",
    "RoleStatusResponse",
    # Patent
    "PatentPrecheckRequest",
    "PatentPrecheckResponse",
    # IP Claim
    "CreateIpClaimRequest",
    "IpClaimFilterRequest",
    "IpClaimResponse",
    "IpClaimListResponse",
    "UploadDocumentResponse",
    "DocumentListResponse",
    "IpClaimReviewRequest",
    "IpReviewResponse",
]
