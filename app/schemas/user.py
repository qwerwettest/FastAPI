import uuid
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower().strip()


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.user

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Пароль минимум 8 символов")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserRead(UserBase):
    id: uuid.UUID
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserList(BaseModel):
    total: int
    items: list[UserRead]
