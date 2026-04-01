"""
User repository - data access layer for User and Profile entities.
"""
import uuid
from typing import Optional, Tuple, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, Profile, UserRole, UserStatus


class UserRepository:
    """Repository for User and Profile operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive)."""
        result = await self.session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_with_profile(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user with profile loaded."""
        from sqlalchemy.orm import selectinload
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.profile))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 20
    ) -> Tuple[int, List[User]]:
        """Get all users with pagination."""
        total_result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        total = total_result.scalar() or 0

        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        users = result.scalars().all()
        return total, users

    async def create(self, user: User) -> User:
        """Create a new user."""
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        """Update user fields."""
        for field, value in kwargs.items():
            if hasattr(user, field):
                setattr(user, field, value)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user."""
        await self.session.delete(user)
        await self.session.flush()

    async def get_profile(self, user_id: uuid.UUID) -> Optional[Profile]:
        """Get user profile."""
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(self, profile: Profile) -> Profile:
        """Create user profile."""
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update_profile(
        self, profile: Profile, **kwargs
    ) -> Profile:
        """Update profile fields."""
        for field, value in kwargs.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
