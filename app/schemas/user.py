"""
User schemas - request/response DTOs.

According to IPChain MVP specification.
"""
import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

from app.models.user import UserRole, UserStatus


# ---------------------------------------------------------------------------
# Base schemas
# ---------------------------------------------------------------------------

class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.user

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


class UserUpdate(BaseModel):
    """User update request."""
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class ProfileUpdate(BaseModel):
    """Profile update request."""
    legal_name: Optional[str] = Field(None, max_length=255)
    dob: Optional[datetime] = None
    country: Optional[str] = Field(None, max_length=3)
    address: Optional[str] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProfileRead(BaseModel):
    """Profile response."""
    user_id: uuid.UUID
    legal_name: Optional[str] = None
    country: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserRead(UserBase):
    """User response."""
    id: uuid.UUID
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithProfileRead(BaseModel):
    """User with profile response."""
    id: uuid.UUID
    email: str
    role: UserRole
    status: UserStatus
    profile: Optional[ProfileRead] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserList(BaseModel):
    """User list response."""
    total: int
    items: list[UserRead]


class RoleStatusResponse(BaseModel):
    """User role and status snapshot."""
    user_id: uuid.UUID
    email: str
    role: UserRole
    status: UserStatus
    wallet_address: Optional[str] = None
