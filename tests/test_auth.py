import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_password_reset_token, create_email_verification_token
from app.core.config import settings
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_auth.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def created_user(client):
    response = await client.post(
        "/api/v1/users/",
        json={"email": "auth@example.com", "password": "password123"},
    )
    return response.json()


@pytest.mark.asyncio
async def test_login_returns_jwt(client, created_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


@pytest.mark.asyncio
async def test_login_rejects_invalid_password(client, created_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client, created_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "auth@example.com"


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens(client, created_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_rejects_access_token(client, created_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    access_token = login_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_returns_tokens(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "register@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"]
    assert payload["refresh_token"]


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client, created_user):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "password123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_response.status_code == 200

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_verify_email_endpoint(client):
    prev = settings.REQUIRE_EMAIL_VERIFICATION
    try:
        settings.REQUIRE_EMAIL_VERIFICATION = True

        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "verify@example.com",
                "password": "password123",
                "confirm_password": "password123",
            },
        )
        assert register.status_code == 200

        token = create_email_verification_token("verify@example.com")
        verify = await client.post("/api/v1/auth/verify-email", json={"token": token})
        assert verify.status_code == 200
    finally:
        settings.REQUIRE_EMAIL_VERIFICATION = prev


@pytest.mark.asyncio
async def test_password_reset_confirm(client, created_user):
    request_response = await client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "auth@example.com"},
    )
    assert request_response.status_code == 200

    token = create_password_reset_token("auth@example.com")
    confirm_response = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "new-password-123"},
    )
    assert confirm_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "auth@example.com", "password": "new-password-123"},
    )
    assert login_response.status_code == 200