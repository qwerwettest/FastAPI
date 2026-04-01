from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user
from app.models.user import User, UserStatus
from app.schemas.auth import Token
from app.schemas.user import UserRead
from app.services.user_service import UserService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService.get_by_email(db, form_data.username)
    if not user or not user.password_hash or not UserService.verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status in {UserStatus.suspended.value, UserStatus.blocked.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен")

    access_token = create_access_token(subject=user.email)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user