"""
Authentication service.

Handles password hashing, verification, and JWT token operations.
"""
import hashlib
import hmac
import os
import uuid
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserStatus
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.repositories.user_repository import UserRepository


_ITERATIONS = 260_000
_HASH_ALG = "sha256"


class AuthService:
    """Service for authentication operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using PBKDF2-HMAC-SHA256."""
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac(
            _HASH_ALG, password.encode(), salt.encode(), _ITERATIONS
        )
        return f"pbkdf2_{_HASH_ALG}${_ITERATIONS}${salt}${key.hex()}"

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            parts = hashed.split("$")
            if len(parts) != 4:
                return False
            _, iterations_str, salt, key_hex = parts
            iterations = int(iterations_str)
            new_key = hashlib.pbkdf2_hmac(
                _HASH_ALG, plain.encode(), salt.encode(), iterations
            )
            return hmac.compare_digest(new_key.hex(), key_hex)
        except Exception:
            return False

    async def authenticate(
        self, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Returns User if credentials are valid and user is active, None otherwise.
        """
        user = await self.user_repo.get_by_email(email)
        if not user or not user.password_hash:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if user.status in {UserStatus.suspended.value, UserStatus.blocked.value}:
            return None
        return user

    async def login(
        self, email: str, password: str
    ) -> Tuple[str, str, User]:
        """
        Login user and return tokens.
        
        Returns:
            Tuple of (access_token, refresh_token, user)
        
        Raises:
            HTTPException: If credentials are invalid or user is blocked
        """
        from fastapi import HTTPException, status
        
        user = await self.authenticate(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            subject=user.email,
            user_id=str(user.id),
            role=user.role,
            status=user.status,
        )
        refresh_token = create_refresh_token(
            subject=user.email,
            user_id=str(user.id),
        )
        
        return access_token, refresh_token, user

    async def refresh_tokens(
        self, refresh_token: str
    ) -> Tuple[str, str, User]:
        """
        Refresh access and refresh tokens.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token, user)
        
        Raises:
            HTTPException: If refresh token is invalid or user is blocked
        """
        from fastapi import HTTPException, status
        
        payload = decode_token(refresh_token, expected_type="refresh")
        user = await self.user_repo.get_by_email(payload["sub"])
        
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
        
        new_access_token = create_access_token(
            subject=user.email,
            user_id=str(user.id),
            role=user.role,
            status=user.status,
        )
        new_refresh_token = create_refresh_token(
            subject=user.email,
            user_id=str(user.id),
        )
        
        return new_access_token, new_refresh_token, user

    async def register(
        self,
        email: str,
        password: str,
        role: str = "user",
    ) -> User:
        """
        Register a new user.
        
        Returns:
            Created user
        
        Raises:
            HTTPException: If email is already taken
        """
        from fastapi import HTTPException, status
        
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email уже занят",
            )
        
        user = User(
            email=email.lower().strip(),
            password_hash=self.hash_password(password),
            role=role,
        )
        
        return await self.user_repo.create(user)
