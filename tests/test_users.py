"""
User endpoint tests.

Tests for:
- GET /api/v1/users/me/profile
- PUT /api/v1/users/me/profile
- GET /api/v1/users/me/roles
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_users.db"

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
async def authenticated_user(client):
    """Register and login a test user."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "user@example.com", "password": "password123"},
    )
    return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_get_profile_requires_auth(client):
    response = await client.get("/api/v1/users/me/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_profile(client, authenticated_user):
    response = await client.get(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {authenticated_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_update_profile(client, authenticated_user):
    response = await client.put(
        "/api/v1/users/me/profile",
        json={
            "legal_name": "John Doe",
            "country": "US",
        },
        headers={"Authorization": f"Bearer {authenticated_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["legal_name"] == "John Doe"
    assert data["profile"]["country"] == "US"


@pytest.mark.asyncio
async def test_get_roles(client, authenticated_user):
    response = await client.get(
        "/api/v1/users/me/roles",
        headers={"Authorization": f"Bearer {authenticated_user}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] is not None
    assert data["email"] == "user@example.com"
    assert data["role"] == "user"
    assert data["status"] == "pending_email_verification"
