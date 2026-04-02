import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Profile, User
from app.schemas.user import ProfileUpdate, UserCreate, UserUpdate

_ITERATIONS = 260_000
_HASH_ALG = "sha256"


class UserService:

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac(_HASH_ALG, password.encode(), salt.encode(), _ITERATIONS)
        return f"pbkdf2_{_HASH_ALG}${_ITERATIONS}${salt}${key.hex()}"

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            _, iterations_str, salt, key_hex = hashed.split("$")
            iterations = int(iterations_str)
            new_key = hashlib.pbkdf2_hmac(
                _HASH_ALG, plain.encode(), salt.encode(), iterations
            )
            return hmac.compare_digest(new_key.hex(), key_hex)
        except Exception:
            return False

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email.lower().strip()))
        return result.scalar_one_or_none()

    @classmethod
    async def authenticate(cls, db: AsyncSession, email: str, password: str) -> Optional[User]:
        user = await cls.get_by_email(db, email)
        if not user or not user.password_hash:
            return None
        if not cls.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 20):
        total_result = await db.execute(select(func.count()).select_from(User))
        total = total_result.scalar()

        result = await db.execute(select(User).offset(skip).limit(limit))
        users = result.scalars().all()

        return total, users

    @classmethod
    async def create(cls, db: AsyncSession, data: UserCreate) -> User:
        user = User(
            email=data.email,
            password_hash=cls.hash_password(data.password),
            role=data.role,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @classmethod
    async def create_auth_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        role: str,
        legal_name: str | None,
        country: str | None,
        require_email_verification: bool,
    ) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=cls.hash_password(password),
            role=role,
            status="pending_email_verification" if require_email_verification else "active",
        )
        db.add(user)
        await db.flush()

        profile = Profile(
            user_id=user.id,
            full_name=legal_name,
            country=country,
        )
        db.add(profile)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def update(db: AsyncSession, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> None:
        await db.delete(user)
        await db.flush()

    @staticmethod
    async def get_profile(db: AsyncSession, user_id: uuid.UUID) -> Optional[Profile]:
        result = await db.execute(select(Profile).where(Profile.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_profile(db: AsyncSession, user_id: uuid.UUID, data: ProfileUpdate) -> Profile:
        profile = await UserService.get_profile(db, user_id)
        if not profile:
            profile = Profile(user_id=user_id)
            db.add(profile)

        if data.legal_name is not None:
            profile.full_name = data.legal_name
        if data.country is not None:
            profile.country = data.country

        profile.updated_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def set_status(db: AsyncSession, user: User, status_value: str) -> User:
        user.status = status_value
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def set_password(db: AsyncSession, user: User, new_password: str) -> User:
        user.password_hash = UserService.hash_password(new_password)
        await db.flush()
        await db.refresh(user)
        return user
