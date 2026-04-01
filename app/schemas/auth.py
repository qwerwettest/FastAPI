"""
Authentication schemas - request/response DTOs.

According to IPChain MVP specification.
"""
import uuid
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Token schemas
# ---------------------------------------------------------------------------

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds", default=1800)


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""
    sub: str
    user_id: str
    email: str
    role: str
    status: str
    exp: int
    iat: int
    jti: str


# ---------------------------------------------------------------------------
# Login/Register schemas
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    def validate_passwords_match(self) -> None:
        """Validate that passwords match."""
        if self.password != self.confirm_password:
            raise ValueError("Пароли не совпадают")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


# ---------------------------------------------------------------------------
# User response schemas
# ---------------------------------------------------------------------------

class MinimalProfileSummary(BaseModel):
    """Minimal profile summary for auth response."""
    legal_name: str | None = None
    country: str | None = None


class AuthUserResponse(BaseModel):
    """
    Authenticated user response.
    
    Returns user identifier, email, role, status,
    optional KYC status as read-only UI field,
    and embedded minimal profile summary.
    """
    id: uuid.UUID
    email: str
    role: str
    status: str
    kyc_status: str | None = Field(None, description="Read-only KYC status for UI gating")
    profile: MinimalProfileSummary | None = None


class AuthenticatedUser(BaseModel):
    """Full authentication response with tokens and user data."""
    user: AuthUserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
