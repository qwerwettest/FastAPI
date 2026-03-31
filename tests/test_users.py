import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

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
    response = await client.post("/api/v1/users/", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    })
    return response.json()


async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_create_user(client):
    r = await client.post("/api/v1/users/", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "password123"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


async def test_create_user_duplicate_email(client, created_user):
    r = await client.post("/api/v1/users/", json={
        "email": "test@example.com",
        "username": "other",
        "password": "password123"
    })
    assert r.status_code == 400


async def test_get_user(client, created_user):
    r = await client.get(f"/api/v1/users/{created_user['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created_user["id"]


async def test_get_user_not_found(client):
    r = await client.get("/api/v1/users/999")
    assert r.status_code == 404


async def test_list_users(client, created_user):
    r = await client.get("/api/v1/users/")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


async def test_update_user(client, created_user):
    r = await client.patch(f"/api/v1/users/{created_user['id']}", json={
        "username": "updated_name"
    })
    assert r.status_code == 200
    assert r.json()["username"] == "updated_name"


async def test_delete_user(client, created_user):
    r = await client.delete(f"/api/v1/users/{created_user['id']}")
    assert r.status_code == 204

    r = await client.get(f"/api/v1/users/{created_user['id']}")
    assert r.status_code == 404
