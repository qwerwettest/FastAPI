from pydantic import BaseModel, EmailStr

from app.schemas.user import UserRead


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthenticatedUser(BaseModel):
    user: UserRead