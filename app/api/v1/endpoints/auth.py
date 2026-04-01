"""
Authentication endpoints.

According to IPChain MVP specification:
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh
- GET /api/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    AuthUserResponse,
    MinimalProfileSummary,
)
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with email and password.
    
    Creates a new user record, stores secure password hash,
    and returns user data. Email verification may be required
    before full access depending on configuration.
    """
    # Validate passwords match
    try:
        data.validate_passwords_match()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    auth_service = AuthService(db)
    user = await auth_service.register(
        email=data.email,
        password=data.password,
    )
    
    # Build response - user doesn't have profile yet on registration
    return AuthUserResponse(
        id=user.id,
        email=user.email,
        role=user.role,
        status=user.status,
        profile=None,
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login user",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.
    
    Validates credentials and issues JWT tokens.
    Successful and failed login attempts are logged to audit trail.
    """
    auth_service = AuthService(db)
    access_token, refresh_token, _ = await auth_service.login(
        email=form_data.username,
        password=form_data.password,
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,  # 30 minutes
    )


@router.post(
    "/logout",
    summary="Logout user",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Invalidate refresh session.
    
    For MVP: client-side token discard.
    For production: server-side session revocation with refresh token blacklist.
    """
    # TODO: Implement refresh token blacklist for production
    # For now, just return success - client should discard tokens
    return {"message": "Logged out successfully"}


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh tokens",
)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Issue new access token from refresh token.
    
    Validates refresh token and issues new token pair.
    """
    auth_service = AuthService(db)
    access_token, refresh_token, _ = await auth_service.refresh_tokens(
        refresh_token=payload.refresh_token,
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800,
    )


@router.get(
    "/me",
    response_model=AuthUserResponse,
    summary="Get current user",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return current authenticated user.
    
    Returns user identifier, email, role, status,
    optional KYC status as read-only UI field,
    and embedded minimal profile summary.
    """
    user_repo = UserRepository(db)
    user_with_profile = await user_repo.get_with_profile(current_user.id)
    
    # Get KYC status from latest KYC case (read-only for UI gating)
    kyc_status = None
    if user_with_profile and user_with_profile.kyc_cases:
        latest_kyc = sorted(
            user_with_profile.kyc_cases,
            key=lambda x: x.created_at,
            reverse=True,
        )[0]
        kyc_status = latest_kyc.status
    
    # Build profile summary
    profile_summary = None
    if user_with_profile and user_with_profile.profile:
        profile_summary = MinimalProfileSummary(
            legal_name=user_with_profile.profile.legal_name,
            country=user_with_profile.profile.country,
        )
    
    return AuthUserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        status=current_user.status,
        kyc_status=kyc_status,
        profile=profile_summary,
    )
