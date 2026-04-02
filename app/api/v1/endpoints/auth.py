from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_and_validate_token,
    get_current_user,
)
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import (
    GenericSuccessResponse,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    Token,
    VerifyEmailRequest,
)
from app.schemas.user import UserRead
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Пароли не совпадают")

    if payload.role not in {UserRole.user, UserRole.issuer}:
        raise HTTPException(
            status_code=400,
            detail="Доступна только регистрация с ролью user или issuer",
        )

    existing = await UserService.get_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email уже занят")

    user = await UserService.create_auth_user(
        db,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        legal_name=payload.legal_name,
        country=payload.country,
        require_email_verification=settings.REQUIRE_EMAIL_VERIFICATION,
    )

    await AuditService.write(
        db,
        action="auth.register",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
    )

    if settings.REQUIRE_EMAIL_VERIFICATION:
        verification_token = create_email_verification_token(subject=user.email)
        return Token(access_token=verification_token, refresh_token=None)

    return Token(
        access_token=create_access_token(subject=user.email),
        refresh_token=create_refresh_token(subject=user.email),
    )


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await UserService.get_by_email(db, form_data.username)
    if not user or not user.password_hash or not UserService.verify_password(
        form_data.password, user.password_hash
    ):
        await AuditService.write(
            db,
            action="auth.login_failed",
            entity_type="user",
            payload={"email": form_data.username},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status in {UserStatus.suspended.value, UserStatus.blocked.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен")

    await AuditService.write(
        db,
        action="auth.login_success",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
    )

    access_token = create_access_token(subject=user.email)
    refresh_token = create_refresh_token(subject=user.email)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    token_payload = await decode_and_validate_token(db, payload.refresh_token, expected_type="refresh")
    user = await UserService.get_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось проверить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status in {UserStatus.suspended.value, UserStatus.blocked.value}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь недоступен")

    return Token(
        access_token=create_access_token(subject=user.email),
        refresh_token=create_refresh_token(subject=user.email),
    )


@router.post("/logout", response_model=GenericSuccessResponse)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
):
    token_payload = await decode_and_validate_token(db, payload.refresh_token, expected_type="refresh")
    jti = token_payload.get("jti")
    exp = token_payload.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if isinstance(exp, (int, float)) else exp
        await AuthService.revoke_token(
            db,
            jti=jti,
            token_type="refresh",
            expires_at=expires_at,
        )

    return GenericSuccessResponse(message="Сессия завершена")


@router.post("/verify-email", response_model=GenericSuccessResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    token_payload = await decode_and_validate_token(db, payload.token, expected_type="verify_email")
    user = await UserService.get_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if user.status == UserStatus.pending_email_verification.value:
        await UserService.set_status(db, user, UserStatus.active.value)

    return GenericSuccessResponse(message="Email подтвержден")


@router.post("/password-reset/request", response_model=GenericSuccessResponse)
async def password_reset_request(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await UserService.get_by_email(db, payload.email)
    if user:
        token = create_password_reset_token(subject=user.email)
        await AuditService.write(
            db,
            action="auth.password_reset_requested",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            payload={"reset_token_preview": token[:12]},
        )

    return GenericSuccessResponse(message="Если email существует, инструкция отправлена")


@router.post("/password-reset/confirm", response_model=GenericSuccessResponse)
async def password_reset_confirm(
    payload: PasswordResetConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    token_payload = await decode_and_validate_token(db, payload.token, expected_type="password_reset")
    user = await UserService.get_by_email(db, token_payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    await UserService.set_password(db, user, payload.new_password)
    await AuditService.write(
        db,
        action="auth.password_reset_confirmed",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
    )
    return GenericSuccessResponse(message="Пароль обновлен")


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user