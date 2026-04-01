import hashlib
import hmac
import os
import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

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
            _, iterations_and_salt_and_key = hashed.split("$", 1)
            alg_part, iterations_str, salt, key_hex = hashed.split("$")
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
