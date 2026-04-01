"""
Security utilities - JWT token creation and validation.

JWT claims according to specification:
- sub: user email (subject)
- user_id: user UUID
- email: user email
- role: user role
- status: user status
- iat: issued at
- exp: expiration
- jti: JWT ID (unique identifier)
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserStatus
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _generate_jti() -> str:
    """Generate unique JWT ID."""
    return str(uuid.uuid4())


def create_token(
    subject: str,
    token_type: str,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT token with standard claims.
    
    Args:
        subject: User identifier (typically email)
        token_type: 'access' or 'refresh'
        user_id: User UUID
        email: User email
        role: User role
        status: User status
        expires_delta: Token lifetime
    
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=15))
    
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": _generate_jti(),
    }
    
    # Add optional claims
    if user_id:
        payload["user_id"] = user_id
    if email:
        payload["email"] = email
    if role:
        payload["role"] = role
    if status:
        payload["status"] = status
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    subject: str,
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create access token."""
    return create_token(
        subject=subject,
        token_type="access",
        user_id=user_id,
        email=email,
        role=role,
        status=status,
        expires_delta=expires_delta or timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )


def create_refresh_token(
    subject: str,
    user_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create refresh token."""
    return create_token(
        subject=subject,
        token_type="refresh",
        user_id=user_id,
        expires_delta=expires_delta or timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        ),
    )


def decode_token(token: str, expected_type: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type ('access' or 'refresh')
    
    Returns:
        Decoded token payload
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise credentials_exception from exc

    subject = payload.get("sub")
    token_type = payload.get("type")
    
    if not subject or token_type != expected_type:
        raise credentials_exception

    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Args:
        token: JWT access token from Authorization header
        db: Database session
    
    Returns:
        Current user
    
    Raises:
        HTTPException: If token is invalid or user is blocked
    """
    payload = decode_token(token, expected_type="access")
    subject = payload["sub"]

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(subject)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status in {UserStatus.suspended.value, UserStatus.blocked.value}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь недоступен",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (not suspended/blocked)."""
    if current_user.status != UserStatus.active.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется активация аккаунта",
        )
    return current_user


async def get_current_user_with_role(
    required_roles: list[str],
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user with required role check.
    
    Args:
        required_roles: List of allowed roles
        current_user: Current authenticated user
    
    Returns:
        Current user if role is allowed
    
    Raises:
        HTTPException: If user doesn't have required role
    """
    if current_user.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав",
        )
    return current_user
