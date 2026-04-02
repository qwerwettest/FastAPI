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

    @field_validator("role")
    @classmethod
    def forbid_privileged_role_creation(cls, v: UserRole) -> UserRole:
        if v in {UserRole.admin, UserRole.compliance_officer}:
            raise ValueError("Эта роль назначается только вручную в базе данных")
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None

    @field_validator("role")
    @classmethod
    def forbid_privileged_role_update(cls, v: Optional[UserRole]) -> Optional[UserRole]:
        if v in {UserRole.admin, UserRole.compliance_officer}:
            raise ValueError("Эта роль назначается только вручную в базе данных")
        return v


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


class ProfileRead(BaseModel):
    legal_name: Optional[str] = None
    country: Optional[str] = None


class ProfileUpdate(BaseModel):
    legal_name: Optional[str] = None
    country: Optional[str] = None


class RoleStatusSnapshot(BaseModel):
    role: UserRole
    status: UserStatus
